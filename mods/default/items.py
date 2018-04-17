'''
items.py
A module with definitions of all the default items for MATA
'''
from api.item import *
from api import combat

class Dirt(Item):
    def __init__(self, resources):
        super().__init__(resources)
        self.setRegistryName('Dirt')
        self.image = 'tile_dirt'

class Gold(Item):
    def __init__(self, resources):
        super().__init__(resources)
        self.setRegistryName('Gold')
        self.image = 'item_gold'

class Sword(Weapon):
    def __init__(self, resources):
        super().__init__(resources)
        self.setRegistryName('Steel Sword')
        self.image = 'weapon_steel_sword'
        self.attack = 10
        self.spread = combat.WIDE_ARC
        self.range = combat.MELEE
        self.damageClass = combat.NORMAL
        self.knockback = combat.KNOCK_STRONG

class Teeth(Weapon):
    '''
    An unobtainable weapon used for entity attack calculations
    '''
    def __init__(self, resources):
        super().__init__(resources)
        self.setRegistryName('Teeth Weapon')
        self.attack = 5
        self.spread = combat.FULL_ARC
        self.range = combat.MELEE
        self.damageClass = combat.LIFE
        self.knockback = combat.KNOCK_NONE
