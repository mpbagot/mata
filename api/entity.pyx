from api.item import Inventory
from api.ai import AIHandler

class Player:
    '''
    A base class for storing the player information
    '''
    def __init__(self):
        self.username = ''
        self.pos = [0, 0]
        self.relPos = [0, 0]
        self.health = 100
        self.level = 1
        self.exp = 0
        self.img = []
        self.inventory = Inventory()
        self.isDead = False
        self.tickDamage = None
        self.dimension = 0
        self.properties = {}
        self.synced = False

    def setInventory(self, inv):
        self.inventory = inv

    def getInventory(self):
        return self.inventory

    def setProperty(self, propName, propVal):
        self.properties[propName] = propVal

    def getProperty(self, propName):
        return self.properties.get(propName)

    def getAbsPos(self):
        '''
        Get the absolute position of the player, rounded to 2 decimal places
        '''
        return [round(self.relPos[0]+self.pos[0], 2), round(self.relPos[1]+self.pos[1], 2)]

    def setUsername(self, name):
        '''
        Set the player username to a given name
        '''
        self.username = name

    def toBytes(self):
        '''
        Get a string representation of the player object
        '''
        return (str([self.username, self.pos, self.health, str(self.tickDamage)]).replace(', ', ',')).encode()

    @staticmethod
    def fromBytes(data):
        '''
        Get a player object from a string representation
        '''
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
    '''
    A base class for new entities
    '''
    def __init__(self):
        self.name = ''
        self.isDead = False
        self.tickDamage = None
        self.hp = 100
        self.pos = [0, 0]
        self.aiHandler = AIHandler()

    def __str__(self):
        return self.name

class Damage:
    '''
    A base class for damage types
    '''
    def __init__(self, amount, source):
        self.amount = amount
        self.source = source

    def __str__(self):
        return ''

    @staticmethod
    def fromBytes(data):
        return Damage(0, None)
