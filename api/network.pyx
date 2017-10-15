'''
network.py
A module for all packet handling between the server and client.
'''
# Import the game's modules
import util
from api.packets import *

# Import the Python standard libraries
import socket
import re
import time
import io
from threading import Thread
from multiprocessing import Process

class PacketHandler:
    def __init__(self, game, side):
        self.nextSize = 37
        self.game = game
        self.side = side
        self.connections = []
        self.safePackets = [ByteSizePacket, LoginPacket,
                            DisconnectPacket, SyncPlayerPacketClient,
                            SyncPlayerPacketServer
                           ]

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
        try:
            self.socket.connect((address, util.DEFAULT_PORT))
        except socket.gaierror:
            return 'Invalid Hostname or IP Address'
        except ConnectionRefusedError:
            return 'Connection Refused By Server'
        self.connections.append(Connection(self.socket, address))
        # Fork a connection handling thread
        t = Thread(target=self.handleConn, args=(len(self.connections)-1,))
        t.daemon = True
        t.start()
        # Fire the login event
        self.game.fireEvent('onPlayerLogin', self.game.player)
        # Send a login packet
        self.sendToServer(LoginPacket(self.game.player))

    def pollForConnections(self):
        '''
        A server-side method to poll for incoming connections from clients
        '''
        self.socket.listen(util.MAX_PLAYERS)
        while True:
            conn, addr = self.socket.accept()
            self.connections.append(Connection(conn, addr))
            # Fork a connection handling thread
            t = Thread(target=self.handleConn, args=(len(self.connections)-1,))
            t.daemon = True
            t.start()

    def handleConn(self, connIndex):
        '''
        Handle communication on the given connection
        '''
        conn = self.connections[connIndex].connObj
        while True:
            # Receive the packet data
            try:
                data = conn.recv(self.connections[connIndex].nextSize)
                data = data.decode()[1:-1]
                if not data:
                    raise ConnectionResetError
            except ConnectionResetError:
                if self.side == util.SERVER:
                    print('A Client has disconnected')
                if self.side != util.SERVER:
                    self.game.fireEvent('onDisconnect')
                del self.connections[connIndex]
                return
            except UnicodeDecodeError:
                print(data)
            try:
                dataDictionary = {a.split(':')[0][1:-1] : a.split(':')[1][1:-1] for a in re.findall('".*?":".*?"', data, re.DOTALL)}
            except IndexError:
                print('errored', data)

            try:
                print('Received '+dataDictionary['type'])
            except KeyError:
                print(dataDictionary)
                print(data, self.connections[connIndex].nextSize)

            if dataDictionary['type'] == 'ByteSizePacket':
                self.handlePacket(dataDictionary, connIndex)
            else:
                t = Thread(target=self.handlePacket, args=(dataDictionary, connIndex))
                t.daemon = True
                t.start()
                self.connections[connIndex].setNextPacketSize(37)

    def handlePacket(self, dataDictionary, connIndex):
        '''
        Handle a packet in a separate thread
        '''
        # Loop through the registered packets and handle the received data accordingly
        for packet in self.safePackets:
            if packet.__name__ == dataDictionary['type']:
                # Initialise the packet, and handle it accordingly
                p = packet()
                p.fromBytes(dataDictionary['data'].encode())
                response = p.onReceive(self.connections[connIndex], self.game)
                self.game.fireEvent('onPacketReceived', p)
                if response:
                    # Send any required response and reset the receive size
                    if isinstance(response, list):
                        for res in response:
                            print('sending packet {} in response to {}'.format(res.__class__.__name__, packet.__name__))
                            self.connections[connIndex].sendPacket(res)
                    else:
                        print('sending packet {} in response to {}'.format(response.__class__.__name__, packet.__name__))
                        self.connections[connIndex].sendPacket(response)
                if packet.__name__ == 'DisconnectPacket':
                    self.connections[connIndex].connObj.close()
                    return
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
        print('Sending packet: '+packet.__class__.__name__)
        # Prepare the packet buffer
        buf = io.BytesIO()
        buf.write('{'.encode())
        buf.write('"type":"{}","data":"'.format(packet.__class__.__name__).encode())
        buf2 = io.BytesIO()
        packet.toBytes(buf2)
        packetString = buf2.getvalue().decode().replace('"', '\"').encode()
        buf.write(packetString)
        buf.write('"}'.encode())

        # Get the packet length to send first
        byteSize = len(buf.getvalue())

        # Initialise the ByteSizePacket and buffer
        byteBuf = io.BytesIO()
        sizePacket = ByteSizePacket(byteSize)

        # Write the packet data to the buffer
        byteBuf.write('{'.encode())
        byteBuf.write('"type":"{}","data":"'.format(sizePacket.__class__.__name__).encode())
        sizePacket.toBytes(byteBuf)
        byteBuf.write('"}'.encode())

        # Sanitise and send the two packets one after the other
        self.connObj.send(byteBuf.getvalue())
        self.connObj.send(buf.getvalue())

    def setNextPacketSize(self, size):
        '''
        Set the size of the next packet to be recieved
        '''
        print('setting packet size to ' + str(size))
        self.nextSize = size
