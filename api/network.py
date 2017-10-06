'''
network.py
A module for all packet handling between the server and client.
'''
# Import the game's modules
import util
from api.packets import ConfirmPacket, ByteSizePacket

# Import the Python standard libraries
import socket
import io
from threading import Thread
from multiprocessing import Process

class PacketHandler:
    def __init__(self, game, side):
        self.nextSize = 37
        self.game = game
        self.side = side
        self.connections = []
        self.safePackets = []

        self.socket = socket.socket()

        if side == util.SERVER:
            self.socket.bind((socket.gethostname(), util.DEFAULT_PORT))
            connPoll = Thread(target=self.pollForConnections)
            connPoll.daemon = True
            connPoll.start()

    def connectToServer(self, address):
        '''
        A client-side method to connect to a chosen server
        '''
        self.socket.connect((address, util.DEFAULT_PORT))
        self.connections.append(Connection(self.socket, address))
        t = Thread(target=self.handleConn, args=(len(self.connections)-1,))
        t.daemon = True
        t.start()

    def pollForConnections(self):
        '''
        A server-side method to poll for incoming connections from clients
        '''
        self.socket.listen(util.MAX_PLAYERS)
        while True:
            conn, addr = self.socket.accept()
            self.connections.append(Connection(conn, addr))
            t = Thread(target=self.handleConn, args=(len(self.connections)-1,))
            t.daemon = True
            t.start()

    def handleConn(self, connIndex):
        '''
        Handle communication on the given connection
        '''
        conn = self.connections[connIndex].connObj
        while True:
            # Recieve the packet data
            data = conn.recv(self.connections[connIndex].nextSize).decode()[1:-1]
            dataDictionary = {a.split(':')[0][1:-1] : a.split(':')[1][1:-1] for a in data.split(',')}
            # Loop through the registered packets and handle the recieved data accordingly
            for packet in self.safePackets:
                if packet.__name__ == dataDictionary['type']:
                    # Initialise the packet, and handle it accordingly
                    p = packet()
                    p.fromBytes(dataDictionary['data'])
                    # TODO get the game instance
                    response = p.onRecieve(self.connections[connIndex], self.game)
                    if packet.__name__ not in ['ConfirmPacket', 'ByteSizePacket'] and response is None:
                        response = ConfirmPacket()
                    if response:
                        # If the packet is not a bytesize or confirmation packet,
                        # then send a response and reset the receive size
                        self.connections[connIndex].sendPacket(response)
                        self.connections[connIndex].setNextPacketSize(37)
                    break

    def registerPacket(self, packetClass):
        '''
        Register a packet class as safe
        '''
        self.safePackets.append(packetClass)

    def isPacketSafe(self, packet):
        '''
        Return if the packet is one of the registered packet types
        '''
        return any([isinstance(packet, a) for a in self.safePackets])

    def sendToAll(self, packet):
        '''
        Send a packet to all Clients
        '''
        if not self.isPacketSafe(packet):
            # Reject the packet
            print('[ERROR] Packet was not sent to clients because it was not registered.')
            return
        if self.side == util.CLIENT:
            print('[WARNING] Cannot send a packet to clients from a client runtime!')
            return
        for conn in self.connections:
            self.sendToPlayer(packet, conn.username)

    def sendToPlayer(self, packet, username):
        '''
        Send a packet to a client with the given username
        '''
        if not self.isPacketSafe(packet):
            # Reject the packet
            print('[ERROR] Packet was not sent to clients because it was not registered.')
            return
        if self.side == util.CLIENT:
            print('[WARNING] Cannot send a packet to clients from a client runtime!')
            return
        for conn in self.connections:
            if conn.username == username:
                conn.sendPacket(packet)

    def sendToServer(self, packet):
        '''
        Send a Packet to the server
        '''
        if not self.isPacketSafe(packet):
            # Reject the packet
            print('[ERROR] Packet was not sent to server because it was not registered.')
            return
        if self.side == util.SERVER:
            print('[WARNING] Cannot send a packet to server from a server runtime!')
            return
        self.connections[0].sendPacket(packet)

class Connection:
    def __init__(self, conn, addr):
        self.username = ''
        self.connObj = conn
        self.address = addr
        self.nextSize = 37

    def sendPacket(self, packet):
        '''
        Send a packet on this connection
        '''
        # Prepare the packet buffer
        buf = io.BytesIO()
        buf.write('{"type":"{}","data":"'.format(packet.__class__.__name__).encode())
        packet.toBytes(buf)
        buf.write('"}'.encode())

        # Get the packet length to send first
        byteSize = len(buf.getvalue())

        # Initialise the ByteSizePacket and buffer
        byteBuf = io.BytesIO()
        sizePacket = ByteSizePacket(byteSize)

        # Write the packet data to the buffer
        byteBuf.write('{"type":"{}","data":"'.format(sizePacket.__class__.__name__).encode())
        sizePacket.toBytes(byteBuf)
        byteBuf.write('"}'.encode())

        # Send the two packets one after the other
        self.connObj.send(byteBuf.getvalue())
        self.connObj.send(buf.getvalue())

    def setNextPacketSize(self, size):
        '''
        Set the size of the next packet to be recieved
        '''
        self.nextSize = size
