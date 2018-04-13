'''
game_screens.py
A module containing the GUI screens of the default client game
'''
# Import the Python Standard libraries
from threading import Thread

# Import the Modding API
from api.gui.gui import *
from api.gui.objects import *
from api.colour import *

# Import stuff from the mod modules
from mods.default.client.gui.extras import *
from mods.default.client.gui.menus import *

class PlayerInventoryScreen(Gui):
    '''
    Player Inventory screen
    '''
    def __init__(self, game):
        super().__init__()

        w = self.screen.get_width()
        h = self.screen.get_height()

        self.backImg = pygame.transform.scale(pygame.image.load('resources/textures/background.png'), [w, h]).convert()
        self.game = game

        self.buttons = []
        self.addItem(PlayerImageBox(scaleRect([200, 500, 50, 200], self.screen), game))

        self.inventory = None

        # Fetch the inventory and fill the screen
        t = Thread(target=self.fetchInventory, args=(game,))
        t.daemon = True
        t.start()

    def fetchInventory(self, game):
        '''
        Fetch the inventory from the server
        '''
        packetPipeline = game.getModInstance('ClientMod').packetPipeline
        packetPipeline.sendToServer(FetchInventoryPacket(game.player.name))

    def drawBackgroundLayer(self):
        self.inventory = self.game.player.inventory
        self.screen.blit(self.backImg, [0, 0])

    def drawMiddleLayer(self, mousePos):
        pass

    def drawForegroundLayer(self, mousePos):
        pass

class PlayerDrawScreen(Gui):
    '''
    Player customisation screen
    '''
    def __init__(self, game):
        super().__init__()

        w = self.screen.get_width()
        h = self.screen.get_height()

        self.backImg = pygame.transform.scale(pygame.image.load('resources/textures/background.png'), [w, h]).convert()
        self.buttons = [StartGameButton(scaleRect([600, 580, 350, 120], self.screen))]
        self.valSliders = [Slider(scaleRect([580, 180+50*a, 390, 20], self.screen), (255, 0, 0)) for a in range(12)]
        self.addItem(PlayerImageBox(scaleRect([300, 528, 30, 170], self.screen), game))

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

        w = self.screen.get_width()
        h = self.screen.get_height()

        font = pygame.font.Font('resources/font/main.ttf', 40)

        # Draw the title
        text = font.render('Customise your Character', True, (0, 0, 0))
        self.screen.blit(text, [w//2-text.get_rect().width//2, (h*5)//64])

class GameScreen(Gui):
    def __init__(self, game):
        super().__init__()
        self.game = game
        self.playerImg = self.game.getModInstance('ClientMod').calculateAvatar(self.game.player.img)

        # Open the HUD overlay
        game.openOverlay(game.getModInstance('ClientMod').hudOverlay, game)

    def drawBackgroundLayer(self):
        # Draw the tile map in the area around the player
        x, y = [self.game.player.pos[a] - self.game.world.centrePos[a] for a in (0, 1)]
        xPos = int(x)+75
        yPos = int(y)+45
        x -= int(x)
        y -= int(y)

        w = (self.screen.get_width()+200)//80
        h = (self.screen.get_height()+200)//80

        # Check if the world is loaded into memory
        if self.game.world and self.game.world.isWorldLoaded():
            xPos1 = xPos-w if xPos >= w else 0
            yPos1 = yPos-h if yPos >= h else 0

            # Pad the top of the map if applicable
            tileMap = [[0] for a in range(abs(yPos-h))] if yPos < h else []
            for row in self.game.world.getTileMap().map[yPos1:yPos+h]:
                # Generate the cropped tilemap of the world
                padding = [0 for a in range(abs(xPos-w))] if xPos < w else []
                tileMap.append(padding+row[xPos1:xPos+w])

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

        w = self.screen.get_width()
        h = self.screen.get_height()

        # Iterate the players and render any unrendered avatars
        for p, player in enumerate(self.game.world.players):
            try:
                if player.smallImg:
                    continue
            except:
                print('rendering image')
                self.game.world.players[p].smallImg = self.game.getModInstance('ClientMod').calculateAvatar(player.img)

        p = self.game.player
        mainAbsPos = p.pos

        # Draw the player images to screen
        for player in self.game.world.players:
            # Get the difference in position
            deltaPos = [player.pos[a]-mainAbsPos[a] for a in range(2)]

            # Get the player image size
            size = player.smallImg.get_rect()

            # Adjust position accordingly, and draw to screen
            pos = [w//2+deltaPos[0]*40-size.width//2, h//2+deltaPos[1]*40-size.height//2]
            if abs(max(pos)) < max(w, h):
                self.screen.blit(player.smallImg, pos)

        # Draw the entity images to screen
        for ent in self.game.world.entities:
            # Get the difference in position
            deltaPos = [ent.pos[a]-mainAbsPos[a] for a in range(2)]

            # Get the entity image size
            entityImage = ent.getImage(self.game.modLoader.gameRegistry.resources)
            size = entityImage.get_rect()

            # Adjust position accordingly, and draw to screen
            pos = [w//2+deltaPos[0]*40-size.width//2, h//2+deltaPos[1]*40-size.height//2]
            if abs(max(pos)) < max(w, h):
                self.screen.blit(entityImage, pos)

        # Draw the vehicle images to screen
        for vehicle in self.game.world.vehicles:
            # Get the difference in position
            deltaPos = [vehicle.pos[a]-mainAbsPos[a] for a in range(2)]

            # Get the entity image size
            vehicleImage = vehicle.getImage(self.game.modLoader.gameRegistry.resources)
            size = vehicleImage.get_rect()

            # Adjust position accordingly, and draw to screen
            pos = [w//2+deltaPos[0]*40-size.width//2, h//2+deltaPos[1]*40-size.height//2]
            if abs(max(pos)) < max(w, h):
                self.screen.blit(vehicleImage, pos)


    def drawForegroundLayer(self, mousePos):
        '''
        Draw the player
        '''
        super().drawForegroundLayer(mousePos)

        size = self.playerImg.get_width()//2
        w = self.screen.get_width()
        h = self.screen.get_height()
        self.screen.blit(self.playerImg, [w//2-size, h//2-size])
