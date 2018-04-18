from api.entity import *
from api.ai import *

from mods.default.items import Teeth

import util

from random import randint

class Bear(Entity):
    def __init__(self):
        super().__init__()
        self.setRegistryName('Bear')
        self.health = 30
        self.speed = 9
        self.aiHandler.registerAITask(AttackAITask(self), 0)
        self.setImage('entity_bear')
        self.pos = [randint(-5, 5), randint(-5, 5)]

class AttackAITask(AITask):
    def __init__(self, entity):
        super().__init__(entity)
        self.cooldown = 0

    def shouldStartExecute(self, game):
        '''
        Return whether or not the ai task should start running on a given tick
        '''
        return START if self.getDistance(game)[0] < 15 else SKIP

    def shouldContinueExecute(self, game):
        '''
        Return whether or not the ai task should continue running on a given tick
        '''
        return CONTINUE if self.getDistance(game)[0] < 15 else END

    def getDistance(self, game):
        '''
        Get the distance to the closest player and name of that player
        '''
        # Fetch all players that are somewhat close
        closePlayers = game.getWorld(self.entity.dimension).getPlayersNear(self.entity.pos, 20)

        x, y = self.entity.pos
        # Start further than the max
        closest = [50, None]
        # Loop and look for the closest player
        for p in closePlayers:
            dist = ((x-p.pos[0])**2 + (y-p.pos[1])**2)**0.5
            if dist < closest[0]:
                closest = [dist, p]

        # Return the closest player
        return closest

    def continueExecution(self, game, deltaTime):
        '''
        Execute a continuous task for a tick
        '''
        self.cooldown -= deltaTime

        target = self.getDistance(game)[1]
        targetPos = target.pos
        distance = ((target.pos[0] - self.entity.pos[0])**2 + (target.pos[1] - self.entity.pos[1])**2)**0.5

        # TODO Implement a proper path finding algorithm
        # For now, just run in a straight line towards the player
        velocity = self.entity.speed
        try:
            ratio = (velocity*deltaTime)/distance
        except ZeroDivisionError:
            ratio = 0

        pos = [self.entity.pos[a] * (1 - ratio) + ratio * targetPos[a] for a in (0, 1)]
        self.entity.pos = pos

        # If the entity is really close, ATTACK!
        if self.cooldown < 0 and distance <= 0.5:
            Teeth().calcDamage(game, self.entity.uuid, [target])
            self.cooldown = 3

    def skipExecution(self, game, deltaTime):
        self.cooldown -= deltaTime
