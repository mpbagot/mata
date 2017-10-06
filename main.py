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

# Collect and handle the command line arguments
ARG_HANDLER = util.ArgumentHandler(sys.argv[1:])

# Initialise the game with the mod loader and argument handler
RUNTIME = game.Game(ARG_HANDLER)
RUNTIME.run()
