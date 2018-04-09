from api.item import Inventory
from api.ai import AIHandler

import util

from copy import deepcopy

class EntityBase:
    def __init__(self):
        self.name = ''
        self.uuid = 0
        self.health = 100
        self.pos = [0, 0]

        self.speed = 0.2

        self.isDead = False
        self.tickDamage = None

        self.properties = {}
        self.dimension = 0

        self.ridingEntity = None

    def getSpeed(self, game):
        '''
        Get the movement speed of this entity
        '''
        # If riding in a vehicle, use its speed
        if self.ridingEntity:
            return game.getVehicle(self.ridingEntity).getSpeed(self)
        # Otherwise, use the player's speed
        return self.speed

    def setProperty(self, propName, propVal):
        self.properties[propName] = propVal

    def getProperty(self, propName):
        return self.properties.get(propName)

    def hasAttribute(self, name):
          '''
          Return whether the class (and classes which extend this) has a given attribute
          '''
          try:
              a = self.__getattribute__(name)
              return True
          except AttributeError:
              return False

    def isPlayer(self):
        '''
        Return whether this object is a player
        '''
        return False

class Player(EntityBase):
    '''
    A base class for storing the player information
    '''
    def __init__(self):
        super().__init__()
        self.level = 1
        self.exp = 0
        self.img = []
        self.inventory = Inventory()

        # Boolean for synchronisation status on client
        # Timestamp for last synchronisation on server
        self.synced = False

    def __eq__(self, other):
        return isinstance(other, Player) and self.name == other.name

    def isPlayer(self):
        '''
        Return whether this object is a player
        '''
        return True

    def setInventory(self, inv):
        self.inventory = inv

    def getInventory(self):
        return self.inventory

    def setPos(self, pos):
        '''
        Set a new absolute position
        '''
        self.pos = list(pos)

    def getPos(self):
        '''
        Get the position of the player, rounded to 2 decimal places
        '''
        return [round(self.pos[0], 2), round(self.pos[1], 2)]

    def switchDimension(self, dimension, game):
        '''
        Switch the current dimension for this player
        '''
        # Delete the old player
        world = game.getWorld(self.dimension)
        for p, player in enumerate(world.players):
            if player.name == self.name:
                del world.players[p]

        # Set the dimension, and replace it
        self.dimension = dimension
        game.setPlayer(self)

    def setUsername(self, name):
        '''
        Set the player username to a given name
        '''
        self.name = name

    def toBytes(self):
        '''
        Get a string representation of the player object
        '''
        return (str([self.name, self.getPos(), self.health, str(self.tickDamage), self.dimension]).replace(', ', ',')).encode()

    @staticmethod
    def fromBytes(data):
        '''
        Get a player object from a string representation
        '''
        uname, pos, health, damage, dimension = eval(data.decode())
        p = Player()
        p.name = uname
        p.pos = pos
        p.health = health
        p.dimension = dimension
        if damage:
            p.tickDamage = Damage.fromBytes(damage.encode())
        else:
            p.tickDamage = None
        return p

class Entity(EntityBase):
    '''
    A base class for new entities
    '''
    def __init__(self):
        super().__init__()
        self.aiHandler = AIHandler()
        self.image = None

    def __eq__(self, other):
        return isinstance(other, Entity) and self.uuid == other.uuid

    def __str__(self):
        x = super().__repr__()
        return x.split()[-1][:-1] + ' {} {}'.format(self.name, self.uuid)

    def __repr__(self):
        x = super().__repr__()
        return x.split()[-1][:-1] + ' {} {} {}'.format(self.name, self.uuid, self.pos)

    def setRegistryName(self, name):
        self.name = name

    def getRegistryName(self):
        return self.name

    def getImage(self, resources):
        try:
            return resources.get(self.image)
        except KeyError:
            raise KeyError('Image "{}" has not been registered in the Game Registry'.format(self.image))

    def setImage(self, image):
        self.image = image

    def toBytes(self):
        return (str([self.__class__.__name__, self.name, self.uuid, self.pos, self.health, str(self.tickDamage)]).replace(', ', ',')).encode()

    @staticmethod
    def fromBytes(eBytes, entityClassList):
        entityClass, *entityProps = eval(eBytes)
        finalEntity = entityClassList.get(entityClass, Entity)()

        finalEntity.setRegistryName(entityProps[0])
        finalEntity.uuid, finalEntity.pos, finalEntity.health, finalEntity.tickDamage = entityProps[1:]

        return finalEntity

class Damage:
    '''
    A base class for damage types
    '''
    def __init__(self, amount, source):
        self.amount = amount
        self.source = source

    def __str__(self):
        return ''

    def hasAttribute(self, name):
        '''
        Return whether the class (and classes which extend this) has a given attribute
        '''
        try:
            a = self.__getattribute__(name)
            return True
        except AttributeError:
            return False

    @staticmethod
    def fromBytes(data):
        return Damage(0, None)
