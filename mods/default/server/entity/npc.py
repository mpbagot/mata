from api.entity import *
from api.ai import *
from api.item import PlayerInventory

from mods.default.items import Teeth

import util

import random

class NPC(Entity):
    def __init__(self):
        super().__init__()
        self.setRegistryName('NPC')
        self.health = 30
        self.speed = 6
        self.inventory = PlayerInventory()

        # Set up the tasks
        self.aiHandler.registerAITask(EvadeAITask(self), 0)
        self.aiHandler.registerAITask(WanderAITask(self, 20), 3)
        self.aiHandler.registerAITask(GroupAITask(self), 6)
        self.setImage('tile_water')#'entity_npc')
        self.pos = [random.randint(-5, 5), random.randint(-5, 5)]

class WanderAITask(AITask):
    def __init__(self, entity, wanderRange):
        super().__init__(entity)
        self.walkTime = 0
        self.idleTime = 0
        self.range = wanderRange
        self.wanderTarget = entity.pos

    def shouldStartExecute(self, game):
        '''
        Return whether or not the ai task should start running on a given tick
        '''
        return START if self.idleTime <= 0 else SKIP

    def shouldContinueExecute(self, game):
        '''
        Return whether or not the ai task should continue running on a given tick
        '''
        return CONTINUE if self.walkTime >= 0 else END

    def getWanderTarget(self):
        displacement = [random.randint(-self.range, self.range) for a in (0, 1)]
        self.wanderTarget = [self.entity.pos[a]+displacement[a] for a in (0, 1)]

    def startExecution(self, game):
        self.walkTime = random.randint(1, 5)
        self.getWanderTarget()

    def continueExecution(self, game, deltaTime):
        '''
        Execute a continuous task for a tick
        '''
        self.walkTime -= deltaTime

        # Calculate the walking velocity and apply the displacement to the entity position
        velocity = [min((self.wanderTarget[a]-self.entity.pos[a])/self.walkTime, self.entity.speed) for a in (0, 1)]
        self.entity.pos = [self.entity.pos[a]+velocity[a]*deltaTime for a in (0, 1)]

    def endExecution(self, game):
        self.idleTime = random.randint(3, 20)

    def skipExecution(self, game, deltaTime):
        self.idleTime -= deltaTime

class GroupAITask(AITask):
    def __init__(self, entity):
        super().__init__(entity)
        self.time = 0
        self.startThreshold = 30

    def shouldStartExecute(self, game):
        '''
        Return whether or not the ai task should start running on a given tick
        '''
        return START if random.randint(0, 100) == 70 else SKIP

    def shouldContinueExecute(self, game):
        '''
        Return whether or not the ai task should continue running on a given tick
        '''
        return CONTINUE if random.randint(0, 10) != 7 else END

    def getGroup(self, game):
        nearEntities = game.getWorld(self.entity.dimension).getEntitiesNear(self.entity.pos, self.startThreshold+1)
        return [a for a in nearEntities if isinstance(a, self.entity.__class__)]

    def getDistance(self, game, entity, vec=None):
        '''
        Get the distance to the closest player and name of that player
        '''
        # Calculate the distance
        if vec is None:
            x, y = self.getVector(game, entity)
        else:
            x, y = vec
        return (x**2 + y**2)**0.5

    def getVector(self, game, entity):
        '''
        Get the 2D vector from this entity to the given one
        '''
        if isinstance(entity, int):
            # Evading an entity
            target = game.getEntity(entity)
        elif isinstance(entity, str):
            # Evading a player
            target = game.getPlayer(entity)
        else:
            target = None

        # Return an out-of-range value if the entity couldn't be found
        if target is None:
            return [400, 400]

        # Calulate the vector
        x, y = self.entity.pos
        return [(target.pos[0]-x), (target.pos[1]-y)]

    def getWeightVector(self, game, entity):
        '''
        Get a weighting vector used to calculate the direction to move to evade enemies
        '''
        # Get the actual vector to the target
        defaultVec = self.getVector(game, entity)
        # If the vector is out-of-bounds, nullify it so as not to skew results
        if defaultVec == [400, 400]:
            return None
        # Get the distance
        dist = self.getDistance(game, entity, defaultVec)
        # Multiply, invert and return
        multiplier = self.safeThreshold/dist - 1
        return [a*multiplier for a in defaultVec]

    def continueExecution(self, game, deltaTime):
        '''
        Execute a continuous task for a tick
        '''
        self.time += deltaTime

        # Get the direction weights
        weights = []
        for e in self.getGroup(game):
            # Get the weight vector
            weight = self.getWeightVector(game, e)
            if weight:
                weights.append(weight)

        # Get the average of the vectors
        if weights:
            direction = [sum([b[a] for b in weights])/len(weights) for a in (0, 1)]
            # Normalise, then calculate and apply the appropriate displacement
            mag = (direction[0]**2 + direction[1]**2)**-0.5
            displacement = [a * mag * deltaTime * self.entity.speed for a in direction]
        else:
            displacement = [0, 0]

        self.entity.pos = [self.entity.pos[a]+displacement[a] for a in (0, 1)]

class EvadeAITask(AITask):
    def __init__(self, entity):
        super().__init__(entity)
        self.toEvade = {}
        self.time = 0
        self.safeThreshold = 30

    def shouldStartExecute(self, game):
        '''
        Return whether or not the ai task should start running on a given tick
        '''
        return START if any([self.getDistance(game, a.uuid or a.name) < self.safeThreshold//1.5 for a in self.toEvade]) else SKIP

    def shouldContinueExecute(self, game):
        '''
        Return whether or not the ai task should continue running on a given tick
        '''
        return CONTINUE if any([self.getDistance(game, a.uuid or a.name) < self.safeThreshold for a in self.toEvade]) else END

    def getDistance(self, game, entity, vec=None):
        '''
        Get the distance to an entity
        '''
        # Calculate the distance
        if vec is None:
            x, y = self.getVector(game, entity)
        else:
            x, y = vec
        return (x**2 + y**2)**0.5

    def getVector(self, game, entity):
        '''
        Get the 2D vector from this entity to the given one
        '''
        if isinstance(entity, int):
            # Evading an entity
            target = game.getEntity(entity)
        elif isinstance(entity, str):
            # Evading a player
            target = game.getPlayer(entity)
        else:
            target = None

        # Return an out-of-range value if the entity couldn't be found
        if target is None:
            return [400, 400]

        # Calulate the vector
        x, y = self.entity.pos
        return [(target.pos[0]-x), (target.pos[1]-y)]

    def getWeightVector(self, game, entity):
        '''
        Get a weighting vector used to calculate the direction to move to evade enemies
        '''
        # Get the actual vector to the target
        defaultVec = self.getVector(game, entity)
        # If the vector is out-of-bounds, nullify it so as not to skew results
        if defaultVec == [400, 400]:
            return None
        # Get the distance
        dist = self.getDistance(game, entity, defaultVec)
        # Multiply, invert and return
        multiplier = 1-self.safeThreshold/dist
        return [a*multiplier for a in defaultVec]

    def continueExecution(self, game, deltaTime):
        '''
        Execute a continuous task for a tick
        '''
        self.time += deltaTime

        # Add any entity that has attacked this entity to the evasion list
        if self.entity.tickDamage and self.entity.tickDamage.source:
            self.toEvade[self.entity.tickDamage.source] = self.time

        # Remove entities that have left this entity alone for a while (~1 hour)
        weights = []
        for e in list(self.toEvade.keys()):
            if self.toEvade.get(e, self.time) - self.time > 3600:
                self.toEvade.pop(e)
            else:
                # If not deleting, get the weight vector
                weight = self.getWeightVector(game, e)
                if weight:
                    weights.append(weight)

        # Get the average of the vectors
        if weights:
            direction = [sum([b[a] for b in weights])/len(weights) for a in (0, 1)]
            # Normalise, then calculate and apply the appropriate displacement
            mag = (direction[0]**2 + direction[1]**2)**-0.5
            displacement = [a * mag * deltaTime * self.entity.speed for a in direction]
        else:
            displacement = [0, 0]

        self.entity.pos = [self.entity.pos[a]+displacement[a] for a in (0, 1)]
