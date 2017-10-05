'''
2D Game Engine
- Mod Engine
- Networking Engine
- Integrated or Dedicated Server
'''
# Import the game submodules
import mod
import util
import game

# Import the Python standard libraries
import sys

# Initialise the ModLoader
modLoader = mod.ModLoader()

# Collect and handle the command line arguments
arguments = sys.argv[1:]
argHandler = util.ArgumentHandler(arguments)

# Initialise the game with the mod loader and argument handler
runtime = game.Game(modLoader, argHandler)
runtime.run()
