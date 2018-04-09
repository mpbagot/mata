from api.entity import EntityBase, Player

class Vehicle(EntityBase):
    def __init__(self):
        super().__init__()
        self.health = float('inf')
        self.riders = {'driver' : None, 'other' : []}
        self.image = None

        self.isDestroyed = False

    def mountRider(self, entity, game):
        '''
        Attempt to add a rider to this vehicle
        Returns True if successful, False if not
        '''
        # Check if a valid entity
        if not isinstance(entity, EntityBase):
            print('[WARNING] Invalid rider for vehicle')
            return False
        # Check for rider quantity overflow
        if len(self.riders['other'])+int(bool(self.riders['driver'])) >= self.getMaxRiders():
            return False
        # Check if rider is mounted to another vehicle
        if entity.ridingEntity:
            game.getVehicle(entity.ridingEntity).unmountRider(entity)

        # If everything is ok, mount the entity in the appropriate position
        game.getPlayer(entity.name).setPos(self.pos)

        if entity.name in self.riders['other'] or self.riders['driver'] == entity.name:
            return False
        if not self.riders['driver']:
            self.riders['driver'] = entity.name
        else:
            self.riders['other'].append(entity.name)
        entity.ridingEntity = self.uuid
        return True

    def unmountRider(self, entity):
        '''
        Attempt to remove a rider from this vehicle
        '''
        # Check the main driver
        driver = self.riders.get('driver')
        if entity.name == driver:
            self.riders['driver'] = None
            return
        # Iterate the other connected riders, compare the entity and remove it if possible
        for r, rider in enumerate(self.riders['other']):
            if entity.name == rider:
                self.riders['other'].pop(r)
                entity.ridingEntity = None
                return

    def getSpeed(self, rider):
        '''
        Get the movement speed of this entity riding this vehicle
        '''
        # If the rider is a player
        # Return the speed, multiplied by 1 or 0 for whether player is the driver
        return self.speed * int(self.isDriver(rider))

    def getMaxRiders(self):
        '''
        Return the maximum number of riders this vehicle can hold
        '''
        return 1

    def isDriver(self, obj):
        '''
        Return if the given Entity is the driver
        '''
        if obj.isPlayer():
            return obj.name == self.riders['driver']
        else:
            return obj.uuid == self.riders['driver']

    def isPassenger(self, obj):
        '''
        Return if the given entity is a passenger
        '''
        if obj.isPlayer():
            return obj.name in self.riders['other']
        else:
            return obj.uuid in self.riders['other']

    def onVehicleUpdate(self, game):
        '''
        Update this vehicle
        '''
        # TODO Update vehicle method with more logic
        if self.riders['driver'] is not None:
            self.pos = list(game.getPlayer(self.riders['driver']).pos)
        for ridername in self.riders['other']:
            game.getPlayer(ridername).pos = list(self.pos)

    def hasAttribute(self, name):
          '''
          Return whether the class (and classes which extend this) has a given attribute
          '''
          try:
              a = self.__getattribute__(name)
              return True
          except AttributeError:
              return False

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
        return (str([self.__class__.__name__, self.name, self.uuid, self.pos, self.riders]).replace(', ', ',')).encode()

    @staticmethod
    def fromBytes(vBytes, vehicleClassList):
        vehicleClass, *vehicleProps = eval(vBytes)
        finalVehicle = vehicleClassList.get(vehicleClass, Vehicle)()

        finalVehicle.setRegistryName(vehicleProps[0])
        finalVehicle.uuid = vehicleProps[1]
        finalVehicle.pos = vehicleProps[2]
        finalVehicle.riders = vehicleProps[3]

        return finalVehicle
