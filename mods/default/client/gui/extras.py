from api.gui import *

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
