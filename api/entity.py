class Player:
    def __init__(self):
        self.username = 'admin'

    def toBytes(self):
        return b'player'

    @staticmethod
    def fromBytes(self):
        return Player()

class Entity:
    def __init__(self):
        pass
