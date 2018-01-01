from api.entity import *
from api.ai import *

class Bear(Entity):
    def __init__(self):
        super().__init__()
        self.name = 'Bear'
        self.aiHandler.registerAITask(WalkAITask(self), 0)

class WalkAITask(AITask):
    def __init__(self, entity):
        super().__init__(entity)
        self.pauseTicks = 0
        self.walkTicks = 0

    def shouldStartExecute(self):
        '''
        Return whether or not the ai task should start running on a given tick
        '''
        return START if self.pauseTicks > 60 else SKIP

    def shouldContinueExecute(self):
        '''
        Return whether or not the ai task should continue running on a given tick
        '''
        return CONTINUE if self.walkTicks < 60 else END

    def startExecution(self):
        self.pauseTicks = 0

    def continueExecution(self):
        '''
        Execute a continuous task for a tick
        '''
        self.entity.pos[0] += 0.5
        self.walkTicks += 1

    def skipExecution(self):
        self.pauseTicks += 1

    def endExecution(self):
        '''
        Reset the walk ticks
        '''
        self.walkTicks = 0
