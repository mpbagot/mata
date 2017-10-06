'''
network.py
A module for all packet handling between the server and client.
'''
# Import the game's modules
import util

# Import the Python standard libraries
import socket

class PacketHandler:
    def __init__(self, side):
        self.nextSize = 37
        self.side = side
        self.connections = []
        self.safePackets = []

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

    def setNextPacketSize(self, size):
        '''
        Set the size of the next packet to be recieved
        '''
        self.nextSize = size

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
        # TODO send the packet
        for conn in self.connections:
            if conn.username == username:
                pass

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
        # TODO send the packet
        pass

class Connection:
    def __init__(self):
        self.username = ''

class Packet:
    def toBytes(self, buf):
        '''
        Convert the data to a bytestring and write it to a buffer
        '''
        raise NotImplementedError('toBytes method is empty in a packet class!')

    def fromBytes(self, data):
        '''
        Read the data from the binary buffer, and convert it to a usable form
        '''
        raise NotImplementedError('fromBytes method is empty in a packet class!')

    def onRecieve(self, packetHandler, game):
        '''
        Run any required logic upon receiving the packet
        '''
        raise NotImplementedError('onRecieve method is empty in a packet class!')
