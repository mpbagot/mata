import time

IDLE = 0
RUNNING = 1

START = 2
CONTINUE = 3
END = 4
SKIP = 5

class AIHandler:
    def __init__(self):
        self.registeredAI = [[] for a in range(10)]
        self.time = time.time()

    def registerAITask(self, task, weight):
        '''
        Register an AI task with a certain weighting
        Low weighting values have priority over high weightings
        '''
        if not isinstance(weight, int):
            raise TypeError('AI Task weighting is not an integer')
        if -1 < weight < 9:
            self.registeredAI[weight].append(task)
        else:
            raise ValueError('AI Task weighting is not between 0 and 9')

    def runAITick(self, game):
        '''
        Run the registered AI tasks for a tick
        '''
        # Calculate the change in time, but clip it to half a second
        deltaTime = min(time.time()-self.time, 500)
        self.time = time.time()

        # Loop each layer and task in order
        for l in range(9, -1, -1):
            for t, task in enumerate(self.registeredAI[l]):
                # Check if the task should run, and run if able
                if task.status == IDLE:
                    shouldRun = self.registeredAI[l][t].shouldStartExecute(game)
                    if shouldRun not in [START, SKIP]:
                        raise TypeError('Returned value is not a valid execution state')

                    if shouldRun == START:
                        self.registeredAI[l][t].startExecution(game)
                        self.registeredAI[l][t].status = RUNNING

                # Check if the task should continue, and run if able
                elif task.status == RUNNING:
                    shouldRun = self.registeredAI[l][t].shouldContinueExecute(game)
                    if shouldRun not in [CONTINUE, SKIP, END]:
                        raise TypeError('Returned value is not a valid execution state')

                    if shouldRun == CONTINUE:
                        self.registeredAI[l][t].continueExecution(game, deltaTime)
                    elif shouldRun == END:
                        self.registeredAI[l][t].endExecution(game)
                        self.registeredAI[l][t].status = IDLE

                else:
                    raise TypeError('Task status is not a valid execution state')

                # Skip the task if it should
                if shouldRun == SKIP:
                    self.registeredAI[l][t].skipExecution(game, deltaTime)

    def hasAttribute(self, name):
        '''
        Return whether the class (and classes which extend this) has a given attribute
        '''
        try:
            a = self.__getattribute__(name)
            return True
        except AttributeError:
            return False

class AITask:
    def __init__(self, entity):
        self.status = IDLE
        self.entity = entity

    def shouldStartExecute(self, game):
        '''
        Return whether or not the ai task should start running on a given tick
        '''
        return SKIP

    def shouldContinueExecute(self, game):
        '''
        Return whether or not the ai task should continue running on a given tick
        '''
        return SKIP

    def startExecution(self, game):
        '''
        Execute a one-shot task or begin executing a continuous task
        '''
        pass

    def continueExecution(self, game, deltaTime):
        '''
        Execute a continuous task for a tick
        '''
        pass

    def endExecution(self, game):
        '''
        Execute logic when the task stops execution
        '''
        pass

    def skipExecution(self, game, deltaTime):
        '''
        Execute code during a skipped tick
        '''
        pass

    def hasAttribute(self, name):
        '''
        Return whether the class (and classes which extend this) has a given attribute
        '''
        try:
            a = self.__getattribute__(name)
            return True
        except AttributeError:
            return False

class PickupAITask(AITask):
    def __init__(self, entity):
        super().__init__(entity)
        self.lifeTime = 0

    def shouldStartExecute(self, game):
        '''
        Return whether or not the ai task should start running on a given tick
        '''
        return START

    def shouldContinueExecute(self, game):
        '''
        Return whether or not the ai task should continue running on a given tick
        '''
        return CONTINUE

    def continueExecution(self, game, deltaTime):
        '''
        Execute a continuous task for a tick
        '''
        self.lifeTime += deltaTime

        # Check for a player coming near, and respond accordingly
        players = game.getWorld(self.entity.dimension).getPlayersNear(self.entity.pos, 2)
        if len(players) > 0:
            x, y = self.entity.pos
            distances = [((a.pos[0]-x)**2+(a.pos[1]-y)**2)**0.5 for a in players]
            closest = players[distances.index(min(distances))]
            closest.inventory.addItemstack(self.entity.getItem())
            self.entity.isDead = True

        # If the pickup has existed for more than 30 seconds
        if self.lifeTime > 30000:
            self.entity.isDead = True
