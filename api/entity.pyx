from api.item import Inventory

class Player:
    def __init__(self):
        self.username = ''
        self.pos = [0, 0]
        self.health = 100
        self.inventory = Inventory()
        self.isDead = False
        self.tickDamage = None

    def setUsername(self, name):
        '''
        Set the player username to a given name
        '''
        self.username = name

    def toBytes(self):
        return (str([self.username, self.pos, self.health, str(self.tickDamage)]).replace(' ', '')).encode()

    @staticmethod
    def fromBytes(data):
        uname, pos, health, damage = eval(data.decode())
        p = Player()
        p.username = uname
        p.pos = pos
        p.health = health
        if damage:
            p.tickDamage = Damage.fromBytes(damage.encode())
        else:
            p.tickDamage = None
        return p

class Entity:
    def __init__(self):
        self.isDead = False
        self.tickDamage = None

class Damage:
    def __init__(self, amount, source):
        self.amount = amount
        self.source = source

    def __str__(self):
        return ''

    @staticmethod
    def fromBytes(data):
        return Damage(0, None)
