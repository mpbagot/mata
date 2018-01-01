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
                        HorizBar([744, 698], 260, 20, (255, 0, 0), self.game.player.health, 'Health'),
                        HorizBar([744, 728], 260, 20, (0, 102, 255), self.game.player.exp, 'Experience')
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

class Chat(Overlay):
    def __init__(self, game, tab='global'):
        super().__init__()
        self.game = game
        self.tab = tab
        self.scrollScreen = Scrollbox([804, 438], [110, 90])

    def drawForegroundLayer(self, mousePos):
        # Fetch the messages from the mod instance
        messages = self.game.getModInstance('ClientMod').chatMessages.get(self.tab, [])

        # Draw the background rectangle
        overlayScreen = pygame.Surface((824, 558))
        overlayScreen.set_alpha(191)

        pygame.draw.rect(overlayScreen, (140, 140, 140), [0, 0, 824, 558])
        pygame.draw.rect(overlayScreen, (170, 170, 170), [0, 458, 824, 100])

        self.screen.blit(overlayScreen, [100, 80])

        # Draw the outline boxes
        pygame.draw.rect(self.screen, (40, 40, 40), [100, 538, 824, 100], 4)
        pygame.draw.rect(self.screen, (40, 40, 40), [100, 80, 824, 558], 4)
        pygame.draw.rect(self.screen, (40, 40, 40), [718, 538, 206, 100], 4)

        # Generate a font object
        fontLarge = pygame.font.Font('resources/font/main.ttf', 20)
        # Generate a smaller font object
        fontSmall = pygame.font.Font('resources/font/main.ttf', 12)

        self.scrollScreen.innerScreen.fill(pygame.Color(127, 127, 127, 0))

        for m, message in enumerate(messages):
            text = fontSmall.render(message, True, (0, 0, 0))
            self.scrollScreen.blit(text, [0, 15*m])

        self.scrollScreen.draw(self.screen, mousePos)

        super().drawForegroundLayer(mousePos)

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
        self.valSliders = [Slider([580, 180+50*a, 390, 20], (255, 0, 0)) for a in range(12)]#, Slider([580, 230, 390, 20], (255, 0, 0))]
        self.addItem(PlayerImageBox([300, 528], [30, 170], game))

    def drawBackgroundLayer(self):
        self.screen.blit(self.backImg, [0, 0])

        values = self.valSliders
        self.extraItems[0].colours = [[int(values[s].value*5), round(values[s+1].value*360-180, 1)] for s in range(0, len(values), 2)]
        # Set the eye type to 0
        self.extraItems[0].colours[1][0] = 0

        for s in range(0, len(self.valSliders), 2):
            # If it's the eye type slider, leave it at 0 always
            if s == 2:
                self.valSliders[s].displayValue = 0
            else:
                self.valSliders[s].displayValue = int(self.valSliders[s].value*5)
            self.valSliders[s+1].displayValue = round(values[s+1].value*360-180)

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
            try:
                if player.smallImg:
                    continue
            except:
                print('rendering image')
                self.game.world.players[p].smallImg = self.game.getModInstance('ClientMod').calculateAvatar(player.img)

        p = self.game.player
        mainAbsPos = p.getAbsPos()

        # Draw the player images to screen
        for player in self.game.world.players:
            # Get the difference in position
            deltaPos = [player.pos[a]-mainAbsPos[a] for a in range(2)]

            # Get the player image size
            size = player.smallImg.get_rect()

            # Adjust position accordingly, and draw to screen
            pos = [x//2+deltaPos[0]*size.width-size.width//2, y//2+deltaPos[1]*size.height-size.height//2]
            self.screen.blit(player.smallImg, pos)

        # Draw the entity images to screen
        for ent in self.game.world.entities:
            # Get the difference in position
            deltaPos = [ent.pos[a]-mainAbsPos[a] for a in range(2)]

            # Get the entity image size
            entityImage = ent.getImage(self.game.modLoader.gameRegistry.resources)
            size = entityImage.get_rect()

            # Adjust position accordingly, and draw to screen
            pos = [x//2+deltaPos[0]*size.width-size.width//2, y//2+deltaPos[1]*size.height-size.height//2]
            self.screen.blit(entityImage, pos)

    def drawForegroundLayer(self, mousePos):
        '''
        Draw the player
        '''
        super().drawForegroundLayer(mousePos)

        size = self.playerImg.get_rect().width//2
        x = self.screen.get_rect().width
        y = self.screen.get_rect().height
        self.screen.blit(self.playerImg, [x//2-size, y//2-size])
