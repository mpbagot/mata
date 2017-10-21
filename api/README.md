This package contains the entire modding API for this game.
Each module here holds the code required to implement a certain object/thing in a mod.

#Object Registration Order:

The three loading functions are used to register any objects the mod adds.
Objects should be registered accordingly:

PreLoad:
 - Properties
 - Resources/Sounds
 - Items
 - Vehicles

Load:
 - Entities
 - GUI
 - Packets (and PacketHandlers)

PostLoad:
 - Events
 - Biomes
 - Houses
 - Commands

#Sided Registration:

Most objects must be registered on both the client and server, however some should be registered on only one side.
Generally, it is as follows:

Server:
 - Commands

Client:
 - Resources and Sounds
 - GUIs and Overlays

Both:
 - Biomes
 - Dimensions
 - Entities
 - Items
 - Houses
 - Packets
 - Vehicles
 - Properties*
 - Events*

*These objects only need to be registered on the side they are being used on. This can be server, client or both.
Note: Custom Packets will be needed to handle the synchronisation of properties.
