'''
client_gui.py
A module containing the GUI screens of the default client game
'''
# Import the Python Standard libraries
from threading import Thread

# Import the Modding API
from api.gui import *
from api.colour import *
from mods.default.client.gui.extras import *
from mods.default.client.gui.menus import *

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

class PlayerInventoryScreen(Gui):
    '''
    Player Inventory screen
    '''
    def __init__(self, game):
        super().__init__()
        self.buttons = []
        self.addItem(PlayerImage([200, 500], [50, 200]))

        # Fetch the inventory and fill the screen
        t = Thread(target=self.fillScreen, args=(game,))
        t.daemon = True
        t.start()

    def fillScreen(self, game):
        # TODO fetch the inventory, and populate the screen with itemslots
        packetPipeline = game.getModInstance('ClientMod').packetPipeline
        packetPipeline.sendToServer(FetchInventoryPacket(game.player.username))


    def drawBackgroundLayer(self):
        self.screen.blit(self.backImg, [0, 0])

class PlayerDrawScreen(Gui):
    '''
    Player customisation screen
    '''
    def __init__(self, game):
        super().__init__()
        self.backImg = pygame.image.load('resources/textures/background.png').convert()
        self.buttons = [StartGameButton([600, 580, 350, 120])]
        self.valSliders = [Slider([580, 180, 390, 20], (255, 0, 0))]
        self.addItem(PlayerImageBox([300, 528], [30, 170], game))

    def drawBackgroundLayer(self):
        self.screen.blit(self.backImg, [0, 0])

        values = self.valSliders
        self.extraItems[0].colours = [round(slider.value*360-180, 1) for slider in values]

    def drawMiddleLayer(self, mousePos):
        super().drawMiddleLayer(mousePos)
        font = pygame.font.Font('resources/font/main.ttf', 40)

        # Draw the title
        text = font.render('Customise your Character', True, (0, 0, 0))
        self.screen.blit(text, [512-text.get_rect().width//2, 60])

class GameScreen(Gui):
    def __init__(self, game):
        super().__init__()
        self.game = game
        self.playerImg = self.game.getModInstance('ClientMod').calculateAvatar(self.game.player.img)

        # Open the HUD overlay
        game.openOverlay(game.getModInstance('ClientMod').hudOverlay, game)

    def drawBackgroundLayer(self):
        # Draw the tile map in the area around the player
        x, y = self.game.player.relPos
        xPos = int(x)+75
        yPos = int(y)+45
        x -= int(x)
        y -= int(y)

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
        '''
        Draw the trees, entities, vehicles, dropped items, buildings
        '''
        super().drawMiddleLayer(mousePos)

        x = self.screen.get_rect().width
        y = self.screen.get_rect().height

        # Iterate the players and render any unrendered avatars
        for p, player in enumerate(self.game.world.players):
            if player.img != None:
                try:
                    if player.smallImg:
                        continue
                except AttributeError:
                    self.game.world.players[p].smallImg = self.game.getModInstance('ClientMod').calculateAvatar(player.img)

        # Draw the player images to screen
        for player in self.game.world.players:
            # Get the difference in position
            mainAbsPos = self.game.player.getAbsPos()
            deltaPos = [player.pos[a]-mainAbsPos[a] for a in range(2)]
            size = player.smallImg.get_rect()

            # Adjust position accordingly, and draw to screen
            pos = [x//2+deltaPos[0]*size-size//2, y//2+deltaPos[1]*size-size//2]
            self.screen.blit(player.smallImg, pos)

    def drawForegroundLayer(self, mousePos):
        '''
        Draw the player
        '''
        super().drawForegroundLayer(mousePos)

        size = self.playerImg.get_rect().width//2
        x = self.screen.get_rect().width
        y = self.screen.get_rect().height
        self.screen.blit(self.playerImg, [x//2-size, y//2-size])
