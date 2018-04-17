'''
items.py
A module with definitions of all the default items for MATA
'''
from api.item import *
from api import combat

class Dirt(Item):
    def __init__(self, resources):
        super().__init__(resources)
        self.setRegistryName('dirt')
        self.image = 'tile_dirt'

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
