# M.A.T.A (Medieval Attack-Trade-Alliance)

For my HSC major project, I am creating a simple MMORPG that allows players to play together on either a local network or over the internet.
The game can be played singleplayer, but is created with the multiplayer experience in mind.

### Automatic Setup:

To run the game, you should only need python installed (Python 3.4 is the best).
Then, in a Terminal, Powershell or Command Prompt window, run:
> py launcher.py

Use the command line arguments detailed at the bottom of this readme to control the game's behaviour.

### Manual Setup:

If for some reason, the launcher does not work, the game can be launched manually by following a few steps.
Firstly, ensure that your computer has the following dependencies installed:

##### Windows

###### Required:
- Python 3 (3.4 is preferred)
- [Visual Studio C++ Build Tools](https://wiki.python.org/moin/WindowsCompilers) (Not needed for Python 3.4)

##### Linux:
###### Required:
- python3

###### Optional:
- python3-dev
- cython3

###### Required Python3 Packages (installed using pip3):
  - pygame
  - noise

The next step is to compile or pythonify the api (instructions in the api folder README).

Then, just run the main.py file in the Python interpreter, optionally using the below command line arguments.

### Command Line Arguments:

Presently, there are only 3 command line arguments which can be used.
These are:

##### The _--mode_ Argument:

The _--mode_ argument is used to set which mode the game should run in.
This argument requires a second keyword immediately following it. There are 3 possible keywords
 - COMBINED (Default. Starts a server in the background and launches a client game in the foreground.)
 - SERVER (Launch a dedicated server available over a local or remote connection.)
 - CLIENT (Launch a client-side game which can connect to external server games)

If the above is ambiguous, the argument is used as such:
> python3 main.py [--type <u>keyword</u>]

##### The _--disableMods_ Argument:

The _--disableMods_ argument does exactly what it sounds it should. It disables any mods and functionality beyond the base game. This argument is useful for temporarily playing without mods.

This argument requires no extra keywords:
> python3 main.py [--disableMods]

##### The _--address_ Argument:

This argument is only used to prefill an IP address for a client game upon launch. It serves no purpose on a server game.

This argument requires a keyword, the ip address:
> python3 main.py [--address <u>address</u>]
