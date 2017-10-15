'''
client_gui.py
A module containing the GUI screens of the default client game
'''
# Import the Modding API
from api.gui import *

class PlayButton(Button):
    def onClick(self, game):
        game.player.setUsername(game.openGUI[1].textboxes[0].text)
        game.getModInstance('ClientMod').packetPipeline.connectToServer(game.openGUI[1].textboxes[1].text)
        game.openGui(game.getModInstance('ClientMod').loadingGui)

class ExitButton(Button):
    def onClick(self, game):
        game.quit()

class MenuButton(Button):
    def onClick(self, game):
        game.openGui(game.getModInstance('ClientMod').mainMenuGui)

class MainMenu(Gui):
    '''
    Main Menu screen with a player login form
    '''
    def __init__(self):
        super().__init__()
        self.buttons = [PlayButton([400, 350, 224, 50], 'Play'), ExitButton([400, 450, 224, 50], 'Exit')]
        self.textboxes = [TextBox([375, 180, 274, 40], 'Username'), TextBox([375, 250, 274, 40], 'Server Address')]

    def drawBackgroundLayer(self):
        self.screen.blit(pygame.image.load('resources/textures/background.png').convert(), [0, 0])

    def drawMiddleLayer(self, mousePos):
        font = pygame.font.Font('resources/font/main.ttf', 40)
        text = font.render('Game\'s Main Menu', True, (0, 0, 0))
        self.screen.blit(text, [512-text.get_rect().width//2, 60])

class GameScreen(Gui):
    def __init__(self, game):
        super().__init__()
        self.game = game

    def drawBackgroundLayer(self):
        # Draw the tile map in the area around the player
        x, y = self.game.player.relPos
        xPos = int(x+75)
        yPos = int(y+45)
        # If the world is loaded into memory
        if self.game.world and self.game.world.world:
            xPos1 = xPos-20 if xPos >= 20 else 0
            yPos1 = yPos-14 if yPos >= 14 else 0
            # Pad the top of the map if applicable
            tileMap = [[0] for a in range(abs(yPos-14))] if yPos < 14 else []
            for row in self.game.world.world.map[yPos1:yPos+14]:
                # Generate the cropped tilemap of the world
                padding = [0 for a in range(abs(xPos-20))] if xPos < 20 else []
                tileMap.append(padding+row[xPos1:xPos+20])
            # Iterate and blit the tiles to screen
            for r, row in enumerate(tileMap):
                for t, tile in enumerate(row):
                    if tile:
                        self.screen.blit(tile.tileTypes[tile.tileIndex].img, [int(39.5*(t-x%1)), 40*(r-y%1)])

    def drawMiddleLayer(self, mousePos):
        # Draw the trees, entities, vehicles, dropped items, buildings
        pass

    def drawForegroundLayer(self, mousePos):
        super().drawForegroundLayer(mousePos)
        # Draw the player
        pass

class MessageScreen(Gui):
    def __init__(self, message):
        super().__init__()
        self.message = message

    def drawBackgroundLayer(self):
        self.screen.blit(pygame.image.load('resources/textures/background.png').convert(), [0, 0])

    def drawMiddleLayer(self, mousePos):
        font = pygame.font.Font('resources/font/main.ttf', 40)
        text = font.render(self.message, True, (0, 0, 0))
        self.screen.blit(text, [512-text.get_rect().width//2, 330])

class DisconnectMessage(MessageScreen):
    def __init__(self, message):
        super().__init__(message)
        self.buttons = [MenuButton([300, 500, 424, 80], 'Return To Menu')]

class LoadingScreen(MessageScreen):
    def __init__(self):
        super().__init__('Loading...')
