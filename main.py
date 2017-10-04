'''
2D Game Engine
- Mod Engine
- Networking Engine
- Integrated or Dedicated Server
'''
# Import the game submodules
import network
import mod
import util
import game

# Import the Python standard libraries
import sys

# Initialise the ModLoader
modLoader = mod.ModLoader()
# TODO allow mods to add custom packet pipelines/handlers
# packetHandler = network.PacketHandler()

# Collect and handle the command line arguments
arguments = sys.argv[1:]
argHandler = util.ArgumentHandler(arguments)

# Initialise the game with the mod loader and argument handler
runtime = game.Game(modLoader, argHandler)
runtime.run()
