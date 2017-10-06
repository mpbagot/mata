'''
2D Game Engine
- Mod Engine
- Networking Engine
- Integrated or Dedicated Server
'''
# Import the Python standard libraries
import sys

# Import the game submodules
import mod
import util
import game

# Initialise the ModLoader
MODLOADER = mod.ModLoader()

# Collect and handle the command line arguments
ARGHANDLER = util.ArgumentHandler(sys.argv[1:])

# Initialise the game with the mod loader and argument handler
RUNTIME = game.Game(MODLOADER, ARGHANDLER)
RUNTIME.run()
