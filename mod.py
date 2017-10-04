'''
mod.py
Module containing the Mod loading and Mod API code for the game
'''

class ModLoader:
    def __init__(self):
        self.modsToLoad = []

    def registerModByName(self, name):
        '''
        Search the mod folder for a mod with the given mod name, and load it
        '''
        pass

    def registerMod(self, modClass):
        '''
        Load a mod from a class that is a child of 'Mod'
        '''
        if not isinstance(modClass, Mod):
            raise Exception('Illegal Class type of {}. Expected child of "Mod"'.format(modClass.__class__.__name__))
        self.modsToLoad.append(modClass)

    def loadRegisteredMods(self):
        pass

class Mod:
    def __init__(self):
        pass
