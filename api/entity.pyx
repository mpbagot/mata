from api.item import *
from api.ai import AIHandler, PickupAITask

import util

class EntityBase:
    def __init__(self):
        self.name = ''
        self.uuid = 0
        self.health = 100
        self.pos = [0, 0]
        self.lastPos = [0, 0]

        self.speed = 0.2

        self.isDead = False
        self.tickDamage = None

        self.properties = {}
        self.dimension = 0

        self.ridingEntity = None

    def getPos(self):
        '''
        Get the position of the entity, rounded to 2 decimal places
        '''
        return [round(self.pos[0], 2), round(self.pos[1], 2)]

    def setPos(self, pos):
        '''
        Set a new absolute position
        '''
        self.lastPos = list(self.pos)
        self.pos = list(pos)

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
        name = len(self.name).to_bytes(1, 'big')+self.name.encode()
        pos = str(self.getPos()).encode()
        hp = self.health.to_bytes(4, 'big')
        dimension = self.dimension.to_bytes(2, 'big')

        damage = self.tickDamage.toBytes() if isinstance(self.tickDamage, Damage) else NullDamage().toBytes()

        return name + pos + hp + dimension + damage

    @staticmethod
    def fromBytes(data):
        '''
        Get a player object from a string representation
        '''
        nameLength = data[0]
        name = data[1:nameLength+1].decode().strip()
        data = data[1+nameLength:]

        # Walk the string to find the position value, because we can't just dump float data into the stream -_-
        posBuf = ''
        for character in data:
            posBuf += chr(character)
            if character == ord(']'):
                break
        # Eval it into an array
        pos = eval(posBuf)
        data = data[len(posBuf):]

        health = int.from_bytes(data[:4], 'big')
        dimension = int.from_bytes(data[4:6], 'big')
        data = data[6:]

        damAmount = data[:3]
        damType = data[3]
        damLength = data[4]
        damSource = data[5:5+damLength]
        data = data[5+damLength:]
        damage = Damage.fromBytes(damType, damSource, damAmount)

        # Restore all the sent values into a new player object
        p = Player()
        p.name = name
        p.pos = pos
        p.health = health
        p.dimension = dimension
        p.tickDamage = damage

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
        name = len(self.name).to_bytes(1, 'big') + self.name.encode()
        uuid = self.uuid.to_bytes(8, 'big')
        pos = str(self.getPos()).encode()
        hp = self.health.to_bytes(4, 'big')
        dimension = self.dimension.to_bytes(2, 'big')

        damage = self.tickDamage.toBytes() if isinstance(self.tickDamage, Damage) else NullDamage().toBytes()

        return name + uuid + pos + hp + dimension + damage + self.__class__.__name__.encode()

    @staticmethod
    def fromBytes(data, entityClassList):
        nameLength = data[0]
        name = data[1:nameLength+1].decode().strip()
        data = data[nameLength+1:]

        uuid = int.from_bytes(data[:8], 'big')
        data = data[8:]

        # Walk the string to find the position value, because we can't just dump float data into the stream -_-
        posBuf = ''
        for character in data:
            posBuf += chr(character)
            if character == ord(']'):
                break
        # Eval it into an array
        pos = eval(posBuf)
        data = data[len(posBuf):]

        health = int.from_bytes(data[:4], 'big')
        dimension = int.from_bytes(data[4:6], 'big')
        data = data[6:]

        damAmount = data[:3]
        damType = data[3]
        damLength = data[4]
        damSource = data[5:5+damLength]
        data = data[5+damLength:]
        damage = Damage.fromBytes(damType, damSource, damAmount)

        entityClass = data.decode().strip()

        # Create the entity and fill in its information
        finalEntity = entityClassList.get(entityClass, Entity)()

        finalEntity.setRegistryName(name)
        finalEntity.uuid, finalEntity.pos = uuid, pos
        finalEntity.health, finalEntity.dimension = health, dimension
        finalEntity.tickDamage = damage

        return finalEntity

class Pickup(Entity):
    def __init__(self):
        super().__init__(self)
        self.health = 2**31
        self.setRegistryName('Pickup')
        self.aiHandler.registerAITask(PickupAITask(self), 0)
        self.stack = None

    def setItemstack(self, stack):
        if not isinstance(item, ItemStack):
            print('[WARNING] Invalid item being set for pickup')
        self.setImage(stack.getItem().image)
        self.stack = stack

    def getItem(self):
        return self.stack

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

    def toBytes(self):
        if isinstance(self.source, int):
            sourceData = b'u' + b'\x08' + self.source.to_bytes(8, 'big')
        else:
            length = len(self.source).to_bytes(1, 'big')
            sourceData = b'n' + length + self.source.encode()
        return self.amount.to_bytes(3, 'big') + sourceData

    @staticmethod
    def fromBytes(type, source, amount):
        amount = int.from_bytes(amount, 'big')

        if amount == 0:
            return NullDamage()

        if type == ord('n'):
            sourceData = source.decode()
        else:
            sourceData = int.from_bytes(source, 'big')

        return Damage(amount, sourceData)

class NullDamage(Damage):
    def __init__(self):
        super().__init__(0, '')
