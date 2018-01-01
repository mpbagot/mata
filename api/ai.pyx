IDLE = 0
RUNNING = 1

START = 2
CONTINUE = 3
END = 4
SKIP = 5

class AIHandler:
    def __init__(self):
        self.registeredAI = [[] for a in range(10)]

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

    def runAITick(self):
        '''
        Run the registered AI tasks for a tick
        '''
        for l in range(9, -1, -1):
            for t, task in enumerate(self.registeredAI[l]):
                # Check if the task should run, and run if able
                if task.status == IDLE:
                    shouldRun = self.registeredAI[l][t].shouldStartExecute()
                    if shouldRun not in [START, SKIP]:
                        raise TypeError('Returned value is not a valid execution state')

                    if shouldRun == START:
                        self.registeredAI[l][t].startExecution()
                        self.registeredAI[l][t].status = RUNNING

                # Check if the task should continue, and run if able
                elif task.status == RUNNING:
                    shouldRun = self.registeredAI[l][t].shouldContinueExecute()
                    if shouldRun not in [CONTINUE, SKIP, END]:
                        raise TypeError('Returned value is not a valid execution state')

                    if shouldRun == CONTINUE:
                        self.registeredAI[l][t].continueExecution()
                    elif shouldRun == END:
                        self.registeredAI[l][t].endExecution()
                        self.registeredAI[l][t].status = IDLE

                else:
                    raise TypeError('Task status is not a valid execution state')

                if shouldRun == SKIP:
                    self.registeredAI[l][t].skipExecution()


class AITask:
    def __init__(self, entity):
        self.status = IDLE
        self.entity = entity

    def shouldStartExecute(self):
        '''
        Return whether or not the ai task should start running on a given tick
        '''
        return SKIP

    def shouldContinueExecute(self):
        '''
        Return whether or not the ai task should continue running on a given tick
        '''
        return SKIP

    def startExecution(self):
        '''
        Execute a one-shot task or begin executing a continuous task
        '''
        pass

    def continueExecution(self):
        '''
        Execute a continuous task for a tick
        '''
        pass
