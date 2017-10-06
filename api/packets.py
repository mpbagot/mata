
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

    def onRecieve(self, packetHandler, connection, game):
        '''
        Run any required logic upon receiving the packet
        '''
        raise NotImplementedError('onRecieve method is empty in a packet class!')

class ByteSizePacket(Packet):
    def __init__(self, size=0):
        self.size = size

    def toBytes(self, buf):
        buf.write(self.size.to_bytes(2, 'big'))

    def fromBytes(self, data):
        self.size = int.from_bytes(data.encode(), 'big')

    def onRecieve(self, connection, game):
        # Set the connection's next recieve size to the size gotten from this packet
        connection.setNextPacketSize(self.size)

class ConfirmPacket(Packet):
    def toBytes(self, buf):
        pass

    def fromBytes(self, data):
        pass

    def onRecieve(self, connection, game):
        pass
