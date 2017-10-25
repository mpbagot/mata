from api.gui import *
from mods.default.packets import *

class StartGameButton(Button):
    def __init__(self, rect):
        super().__init__(rect, 'Play!')

    def onClick(self, game):
        # Generate the image values array
        values = game.openGUI[1].valSliders
        playerImg = [slider.value for slider in values]

        # Set it and sync it to the server
        game.player.img = playerImg
        packetPipeline = game.getModInstance('ClientMod').packetPipeline
        packetPipeline.sendToServer(SendPlayerImagePacket(game.player))

        # Show the game screen
        game.openGui(game.getModInstance('ClientMod').gameGui, game)

class PlayButton(Button):
    def __init__(self, rect):
        super().__init__(rect, 'Play')

    def onClick(self, game):
        # Grab the variables from the textboxes
        username = game.openGUI[1].textboxes[0].text
        address = game.openGUI[1].textboxes[1].text

        # Set the player username
        game.player.setUsername(username)
        game.openGui(game.getModInstance('ClientMod').loadingGui)

        # Try to connect
        error = game.getModInstance('ClientMod').packetPipeline.connectToServer(address)

        # Display an error if it fails for any reason
        if error:
            game.openGui(game.getModInstance('ClientMod').mainMenuGui)
            game.openGUI[1].error = error
            game.openGUI[1].textboxes[0].text = username

class ExitButton(Button):
    def __init__(self, rect):
        super().__init__(rect, 'Exit')

    def onClick(self, game):
        game.quit()

class MenuButton(Button):
    def __init__(self, rect):
        super().__init__(rect, 'Return To Menu')

    def onClick(self, game):
        game.openGui(game.getModInstance('ClientMod').mainMenuGui)
