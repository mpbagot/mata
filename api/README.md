This package contains the entire modding API for this game.
Each module here holds the code required to implement a certain aspect in a mod.

The three loading functions are used to register any objects the mod adds.
Objects should be registered accordingly:

PreLoad:
 - Properties
 - Music/Sounds
 - Items
 - Vehicles

Load:
 - Entities
 - GUI
 - Packets

PostLoad:
 - Events
 - Biomes
 - Houses
 - Commands
