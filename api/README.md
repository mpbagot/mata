# Modding API for Game
This package contains the entire modding API for this game.
Each module here holds the code required to implement a certain object/thing in a mod.
The API is a collection of .pyx files to allow them to be compiled with Cython3.

## Compiling the API:

#### Dependencies:
###### Linux and Mac OS:
 - python3
 - python3-dev
 - cython3

###### Windows:
 - Python 3
 - Anything else...

#### Instructions:
With Python and the dependencies installed, compiling should simply be a case of running one of the following 3 commands in the root directory of the game.
> python3 compile_api.py build_ext --inplace

> python compile_api.py build_ext --inplace

> py compile_api.py build_ext --inplace

## Object Registration Order:

The three loading functions are used to register any objects the mod adds.
Objects should be registered accordingly:

#### PreLoad:
 - Properties
 - Resources/Sounds
 - Items
 - Vehicles

#### Load:
 - Entities
 - GUI
 - Packets (and PacketHandlers)

#### PostLoad:
 - Events
 - Biomes
 - Houses
 - Commands

## Sided Registration:

Most objects must be registered on both the client and server, however some should be registered on only one side.
Generally, it is as follows:

#### Server:
 - Commands

#### Client:
 - Resources and Sounds
 - GUIs and Overlays

#### Both:
 - Biomes
 - Dimensions
 - Entities
 - Items
 - Houses
 - Packets
 - Vehicles
 - Properties*
 - Events*

\* These objects only need to be registered on the side they are being used on. This can be server, client or both.

*__Note:__* Custom Packets will be needed to handle the synchronisation of properties.
