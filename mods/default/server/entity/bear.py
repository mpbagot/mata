from api.entity import *
from api.ai import *

from random import randint

class Bear(Entity):
    def __init__(self):
        super().__init__()
        self.setRegistryName('Bear')
        self.aiHandler.registerAITask(WalkAITask(self), 0)
        self.setImage('entity_bear')
        self.pos = [randint(-5, 5), randint(-5, 5)]

class WalkAITask(AITask):
    def __init__(self, entity):
        super().__init__(entity)
        self.pauseTicks = 0
        self.walkTicks = 0

    def shouldStartExecute(self, game):
        '''
        Return whether or not the ai task should start running on a given tick
        '''
        return START if self.pauseTicks > 60 else SKIP

    def shouldContinueExecute(self, game):
        '''
        Return whether or not the ai task should continue running on a given tick
        '''
        return CONTINUE if self.walkTicks < 60 else END

    def startExecution(self, game):
        self.pauseTicks = 0

    def continueExecution(self, game, deltaTime):
        '''
        Execute a continuous task for a tick
        '''
        self.entity.pos[0] += 0.5
        self.walkTicks += 1

    def skipExecution(self, game, deltaTime):
        self.pauseTicks += 1

    def endExecution(self, game):
        '''
        Reset the walk ticks
        '''
        self.walkTicks = 0
