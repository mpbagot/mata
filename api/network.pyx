'''
network.py
A module for all packet handling between the server and client.
'''
# Import the game's modules
import util
from api.packets import *

# Import the Python standard libraries
import socket
import math
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
        self.connections = {}
        self.safePackets = [ByteSizePacket, LoginPacket,
                            DisconnectPacket, SyncPlayerPacket,
                            ResetPlayerPacket, InvalidLoginPacket,
                            SetupClientPacket, SendCommandPacket
                           ]

        self.socket = socket.socket()

        # Bind the socket if the PacketHandler is server-side
        if side == util.SERVER:
            self.socket.bind(('0.0.0.0', util.DEFAULT_PORT))
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
        except OSError:
            pass

        self.connections[max(self.connections, default=0)+1] = Connection(self.socket, address)
        # Fork a connection handling thread
        t = Thread(target=self.handleConn, args=(max(self.connections, default=0),))
        t.daemon = True
        t.start()
        # Fire the login event
        self.game.fireEvent('onClientConnected')

    def pollForConnections(self):
        '''
        A server-side method to poll for incoming connections from clients
        '''
        self.socket.listen(util.MAX_PLAYERS)
        while True:
            conn, addr = self.socket.accept()
            self.connections[max(self.connections, default=0)+1] = Connection(conn, addr)
            # Fork a connection handling thread
            t = Thread(target=self.handleConn, args=(max(self.connections, default=0),))
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
                data = conn.recv(self.connections[connIndex].nextSize)[1:-1]
                # data = data.decode()
                if not data:
                    raise ConnectionResetError
            except ConnectionResetError as e:
                print(e)
                # Properly disconnect if the connection is reset from the other side
                if self.side == util.CLIENT:
                    self.game.fireEvent('onDisconnect', 'Server Connection Reset')
                else:
                    del self.connections[connIndex]
                return
            except UnicodeDecodeError:
                pass

            # Parse the byte data of the packet
            try:
                # dataDictionary = {a.split(':')[0][1:-1] : (':'.join(a.split(':')[1:])[1:-1]).encode() for a in re.findall('".*?":".*?"', data, re.DOTALL)}
                dataDictionary = {a.split(b':')[0][1:-1] : b':'.join(a.split(b':')[1:])[1:-1] for a in re.findall(b'".*?":".*?"', data, re.DOTALL)}
                dataDictionary = {a.decode() : dataDictionary[a] for a in dataDictionary.keys()}
            except IndexError:
                dataDictionary = {}

            try:
                x = ('Received '+dataDictionary['type'].decode())
            except KeyError:
                print('[ERROR] Packet corrupted. This is probably an issue with a mod you are using.')
                continue

            # Handle the packet synchronously or asynchronously as required
            if dataDictionary['type'] == b'ByteSizePacket':
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
            if packet.__name__ == dataDictionary['type'].decode():
                # Initialise the packet, and handle it accordingly
                try:
                    p = packet()
                    p.fromBytes(dataDictionary['data'])

                    # Pass the connection list in if a login packet
                    if packet.__name__ == 'LoginPacket':
                        response = p.onReceive(self.connections[connIndex], self.side, self.game, self.connections)
                    else:
                        response = p.onReceive(self.connections[connIndex], self.side, self.game)

                except Exception as e:
                    print('Packet unable to be handled correctly.')
                    print('Error is as follow:')
                    print(e)
                    return

                self.game.fireEvent('onPacketReceived', p)

                # Send packet(s) in response to the received packet
                if response:
                    # Send any required response and reset the receive size
                    if isinstance(response, list):
                        for res in response:
                            # print('sending packet {} in response to {}'.format(res.__class__.__name__, packet.__name__))
                            self.connections[connIndex].sendPacket(res)
                    else:
                        # print('sending packet {} in response to {}'.format(response.__class__.__name__, packet.__name__))
                        self.connections[connIndex].sendPacket(response)
                break

    def closeConnection(self, username):
        '''
        A server-side method for closing a connection to a client
        '''
        # Loop the connections and find a connection matching the username
        for conn in self.connections:
            if self.connections[conn].username == username:
                # Close the socket object and delete the connection object from memory
                self.connections[conn].connObj.close()
                del self.connections[conn]
                return

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
            self.sendToPlayer(packet, self.connections[conn].username)

    def sendToNearby(self, packet, username, radius=16):
        '''
        Send a packet to all players within a certain distance of a given player
        '''
        if not self.isPacketSafe(packet):
            # Reject the packet
            print('[ERROR] Packet was not sent to clients because it was not registered.')
            return
        if self.side == util.CLIENT:
            print('[WARNING] Cannot send a packet to clients from a client runtime!')
            return
        player = self.game.world.players[self.game.getPlayerIndex(username)]
        pos = player.pos

        # Loop all players and find the distance to the given player
        for p in self.game.world.players:
            print(math.sqrt((p.pos[0]-pos[0])**2 + (p.pos[1]-pos[1])**2))
            if math.sqrt((p.pos[0]-pos[0])**2 + (p.pos[1]-pos[1])**2) <= radius:
                self.sendToPlayer(packet, p.username)

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
            if self.connections[conn].username == username:
                self.connections[conn].sendPacket(packet)
                return

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
        self.connections[1].sendPacket(packet)

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
        # print('Sending packet: '+packet.__class__.__name__)
        # Prepare the packet buffer
        buf = io.BytesIO()
        buf.write('{'.encode())
        buf.write('"type":"{}","data":"'.format(packet.__class__.__name__).encode())

        # Initialise a new buffer
        buf2 = io.BytesIO()
        packet.toBytes(buf2)

        # Sanitise the packet data bytes and append them to the packet buffer
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

        # Run error checks here to stop the server from crashing
        try:
            # Sanitise and send the two packets one after the other
            self.connObj.send(byteBuf.getvalue())
            self.connObj.send(buf.getvalue())
        except Exception as e:
            if isinstance(e, ConnectionResetError):
                # The client might still be connected
                print('[ERROR] The Packet Failed To Send For Some Reason.')
            elif isinstance(e, BrokenPipeError):
                # The client is completely disconnected
                print('[WARNING] The Client Has Disconnected Badly. Clearing Connection...')
                # Disconnect the client
                del self
            else:
                print('[ERROR] An Error Occured!'+str(e))

    def setNextPacketSize(self, size):
        '''
        Set the size of the next packet to be recieved
        '''
        self.nextSize = size
