class AIHandler:
    def __init__(self):
        self.registeredAI = [[] for a in range(10)]

    def registerAIProcess(self, process, weight):
        '''
        Register an AI process with a certain weighting
        Low weighting values have priority over high weightings
        '''
        if 0 < weight < 9:
            self.registeredAI[weight].append(process)
        else:
            raise Exception('AI Process weighting is not between 0 and 9')

    def runAITick(self):
        '''
        Run the registered AI processes for a tick
        '''
        for level in self.registeredAI[::-1]:
            for process in level:
                # TODO Run the process
                pass

class AIProcess:
    def __init__(self):
        pass
