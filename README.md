# M.A.T.A (Medieval Attack-Trade-Alliance)

For my HSC major project, I am creating a simple MMORPG that allows players to play together on either a local network or over the internet.
The game can be played singleplayer, but is created with the multiplayer experience in mind.

### Setting up:

Getting the game running from source code only involves a couple of steps.
Firstly, ensure that your computer has the following dependencies installed:

##### Windows

- Python 3 (3.4 is preferred)
- [Visual Studio C++ Build Tools](https://wiki.python.org/moin/WindowsCompilers) (Not needed for Python 3.4) 

Once these dependencies are installed, simply run the setup.bat script, and run:
> py main.py

##### Linux:

 - Python3 Packages (Installed using pip3):
  - pygame
  - noise
 - python3
 - python3-dev
 - cython3

Once these dependencies are installed, simply compile the API (instructions in api folder's README.md), and run:
> python3 main.py

Extra command line arguments (see below) can also be added to change the game's behaviour if you wish.

### Command Line Arguments:

Presently, there are only 3 command line arguments which can be used.
These are:

##### The _--type_ Argument:

The _--type_ argument is used to set which mode the game should run in.
This argument requires a second keyword immediately following it. There are 3 possible keywords
 - COMBINED (Default. Starts a server in the background and launches a client game in the foreground. Equivalent to launching a client and server separately.)
 - SERVER (Launch a dedicated server available over a local or remote connection.)
 - CLIENT (Launch a client-side game which can connect to external server games)

If the above is ambiguous, the argument is used as such:
> python3 main.py [--type <u>keyword</u>]

##### The _--disableMods_ Argument:

The _--disableMods_ argument does exactly what it sounds it should. It disables any mods and functionality beyond the base game. This argument is mostly useful for temporarily playing without mods, or for troubleshooting game errors that arise from mods.

This argument requires no extra keywords:
> python3 main.py [--disableMods]

##### The _--address_ Argument:

This argument is only used to prefill an IP address for a client game upon launch. It serves no purpose on a server game.

This argument requires a keyword, the ip address:
> python3 main.py [--address <u>address</u>] 
