'''
client_gui.py
A module containing the GUI screens of the default client game
'''
# Import the Modding API
from api.gui import *

class HUD(Overlay):
    def __init__(self, game):
        super().__init__()
        self.game = game
        self.bars = [
                        Bar([744, 698], 260, 20, (255, 0, 0), self.game.player.health, 'Health'),
                        Bar([744, 728], 260, 20, (0, 102, 255), self.game.player.exp, 'Experience')
                    ]
        equippedItems = self.game.player.inventory.getEquipped()
        self.itemSlots = [
                            ItemSlot(equippedItems[0], [664, 630], 60),
                            ItemSlot(equippedItems[1], [664, 700], 60)
                         ]

    def drawBackgroundLayer(self):
        # Draw the background rectangle
        pygame.draw.rect(self.screen, (173, 144, 106), [654, 620, 400, 150])
        pygame.draw.rect(self.screen, (65, 55, 40), [654, 620, 400, 150], 4)

    def drawForegroundLayer(self, mousePos):
        super().drawForegroundLayer(mousePos)
        # Generate a font object
        font = pygame.font.Font('resources/font/main.ttf', 20)
        text = font.render('Username: '+self.game.player.username, True, (255, 255, 255))
        self.screen.blit(text, [744, 640])
        # Generate a smaller font object
        font = pygame.font.Font('resources/font/main.ttf', 12)
        text = font.render('Level: '+str(self.game.player.level), True, (255, 255, 255))
        self.screen.blit(text, [744, 670])


class PlayButton(Button):
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
        self.backImg = pygame.image.load('resources/textures/background.png').convert()
        self.error = ''
        self.buttons = [PlayButton([400, 350, 224, 50], 'Play'), ExitButton([400, 450, 224, 50], 'Exit')]
        self.textboxes = [TextBox([375, 180, 274, 40], 'Username'), TextBox([375, 250, 274, 40], 'Server Address')]

    def drawBackgroundLayer(self):
        self.screen.blit(self.backImg, [0, 0])

    def drawMiddleLayer(self, mousePos):
        font = pygame.font.Font('resources/font/main.ttf', 40)
        # Draw the title
        text = font.render('Game\'s Main Menu', True, (0, 0, 0))
        self.screen.blit(text, [512-text.get_rect().width//2, 60])
        # Draw the error message
        text = font.render(self.error, True, (255, 0, 0))
        self.screen.blit(text, [512-text.get_rect().width//2, 110])

class GameScreen(Gui):
    def __init__(self, game):
        super().__init__()
        self.game = game
        # Open the HUD overlay
        game.openOverlay(game.getModInstance('ClientMod').hudOverlay, game)

    def drawBackgroundLayer(self):
        # Draw the tile map in the area around the player
        x, y = self.game.player.relPos
        xPos = int(x)+75
        yPos = int(y)+45
        x -= int(x)
        y -= int(y)
        # x, y = round(x%1, 1), round(y%1, 1)
        # Check if the world is loaded into memory
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
                        self.screen.blit(tile.tileTypes[tile.tileIndex].img, [round(40*(-1+t-x)), round(40*(-1+r-y))])

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
        self.backImg = pygame.image.load('resources/textures/background.png').convert()

    def drawBackgroundLayer(self):
        self.screen.blit(self.backImg, [0, 0])

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
