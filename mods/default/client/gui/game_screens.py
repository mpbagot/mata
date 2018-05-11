'''
game_screens.py
A module containing the GUI screens of the default client game
'''
# Import the Python Standard libraries
from threading import Thread
import math
import time

# Import the Modding API
from api.gui.gui import *
from api.gui.objects import *
from api.packets import *
from api.colour import *
from api.item import *

# Import stuff from the mod modules
from mods.default.client.gui.extras import *
from mods.default.client.gui.menus import *

import util

class TradeScreen(Gui):
    '''
    Trading screen
    '''
    def __init__(self, game, other, isInitiator):
        super().__init__()
        self.game = game
        self.resources = self.game.modLoader.gameRegistry.resources

        self.otherPlayer = other

        # Fetch the other player's inventory
        game.getModInstance('ClientMod').packetPipeline.sendToServer(FetchInventoryPacket(other))
        game.getModInstance('ClientMod').packetPipeline.sendToServer(FetchInventoryPacket(game.player.name))

        self.isInitiator = isInitiator

        # Store the item being moved around the inventory
        self.moveItem = None

        self.offer = None

        # Initialise Pygame assets
        self.backImg = pygame.image.load('resources/textures/background.png').convert()

        otherPlayer = game.getPlayer(other) or game.getEntity(other)
        if otherPlayer:
            self.inv1 = game.player.inventory
            self.inv2 = otherPlayer.inventory

        self.initialiseObjects()

    def setupSlots(self):
        '''
        Setup the itemslots
        '''
        self.itemSlots = []
        # Make the slotsize accessible in the middle and foreground methods
        self.slotSize = 60
        # Loop the rows and columns and create an empty inventory grid
        invs = [self.inv1, self.inv2]
        for y in range(4):
            for x in range(8):
                slotPos = [((x//2 + 1) * (self.slotSize + 8)) + (x%2 * self.slotSize*5), 160 + y * (self.slotSize + 8)]
                slot = ItemSlot(self.game, invs[x%2].getItem(y * 4 + x//2), slotPos, self.slotSize)
                self.itemSlots.append(slot)

    def initialiseObjects(self):
        '''
        Initialise the buttons and inv slots for the gui
        '''
        self.setupSlots()

        # Initialise the chat textbox
        self.textarea = TextArea([768, 618, 256, 150], (255, 255, 255))

        if self.isInitiator:
            # Standard buttons, offer, cancel
            self.buttons = [
                                OfferTradeButton([100, 600, 200, 100], "Offer"),
                                CancelTradeButton([400, 600, 200, 100], "Cancel Trade")
                              ]

        else:
            self.offerButtons = [
                                 AcceptTradeButton([100, 600, 200, 100], "Accept"),
                                 DeclineTradeButton([400, 600, 200, 100], "Decline")
                                ]
            self.buttons = [CancelTradeButton([250, 600, 300, 100], "Cancel Trade")]

    def drawBackgroundLayer(self):
        w = self.screen.get_width()
        h = self.screen.get_height()

        self.setupSlots()

        self.screen.blit(pygame.transform.scale(self.backImg, [3*w//4+1, h]), [0, 0])
        pygame.draw.rect(self.screen, (170, 170, 170), [3*w//4, 0, w//4+1, h])

        if self.isInitiator:
            self.buttons[0].enabled = not self.offer

    def drawMiddleLayer(self, mousePos):
        super().drawMiddleLayer(mousePos)

        h = self.screen.get_height()

        font = pygame.font.Font('resources/font/main.ttf', h//25)

        player1Name = font.render(self.game.player.name + "'s Inventory", True, (0, 0, 0))
        player2Name = font.render(self.otherPlayer + "'s Inventory", True, (0, 0, 0))

        leftPos = scaleRect([368, 120], self.screen)
        rightPos = scaleRect([68, 120], self.screen)

        if self.isInitiator:
            self.screen.blit(player1Name, leftPos)
            self.screen.blit(player2Name, rightPos)
        else:
            self.screen.blit(player2Name, leftPos)
            self.screen.blit(player1Name, rightPos)

    def drawForegroundLayer(self, mousePos):
        super().drawForegroundLayer(mousePos)

        w = self.screen.get_width()
        h = self.screen.get_height()

        font = pygame.font.Font('resources/font/main.ttf', 60)
        fontSmall = pygame.font.Font('resources/font/main.ttf', 15)

        # Draw the messages in the chat on the left of the screen
        messages = self.game.getModInstance('ClientMod').chatMessages.get(self.otherPlayer, [])
        messages = [a for a in messages if '\x00' not in a]
        # Loop the messages from last to first, drawing from the bottom to top
        textareaHeight = self.textarea.rect[-1]+20
        for m, message in enumerate(messages[(h - textareaHeight)//15::-1]):
            text = fontSmall.render(message, True, (0, 0, 0))

            self.screen.blit(text, [3 * w//4 + 5, (h - textareaHeight) - 15 * m])

        self.textarea.draw(self.screen, mousePos)

        if self.moveItem:
            slot = self.itemSlots[self.moveItem[0]]
            stack = self.moveItem[1]
            # Draw the item image
            imageSize = [slot.button.rect[2]-5 for a in range(2)]
            boxPos = [mousePos[a]-imageSize[a]//2 for a in (0, 1)]
            itemImage = stack.getItem().getImage(self.resources)
            imgRect = self.screen.blit(pygame.transform.scale(itemImage, imageSize), boxPos)

            # Draw the stackSize label
            font = pygame.font.Font('resources/font/main.ttf', imageSize[0]//3)
            text = font.render(str(self.moveItem[1].stackSize), True, (0, 0, 0))
            tagPos = list(boxPos)
            tagPos[1] += imageSize[1]-text.get_height()
            tagPos[0] += text.get_height()*1/10
            self.screen.blit(text, tagPos)

        # Draw the notice strip if required
        bools = [bool(self.isInitiator), bool(self.offer)]
        if all(bools) or not any(bools):
            if self.isInitiator:
                text = font.render("Making Offer...", True, (0, 0, 0))
            else:
                text = font.render("Awaiting Offer...", True, (0, 0, 0))
            # Draw the strip across the screen
            pygame.draw.rect(self.screen, (236, 196, 145), [5, h//2 - int(text.get_height() * 1.25), (3 * w)//4 - 10, text.get_height() * 2])
            # Then draw the text over it
            self.screen.blit(text, [(w*0.75 - text.get_width())//2, h//2 - (text.get_height() * 0.75)])

    def doKeyPress(self, event):
        if event.key == pygame.K_RETURN:
            # Adjust the message
            message = self.textarea.text
            # Skip blank messages
            if not message:
                return

            # Format a non-command as required
            if message[0] != '/':
                message = '/message '+self.otherPlayer+' '+message

            # Create the packet
            # Send the message
            packet = SendCommandPacket(message)
            self.game.packetPipeline.sendToServer(packet)
            self.textarea.text = ''
        # Pass the button press to the textarea
        self.textarea.doKeyPress(event)


class PlayerInventoryScreen(Gui):
    '''
    Player Inventory screen
    '''
    def __init__(self, game):
        super().__init__()

        # Initialise Pygame assets
        self.backImg = pygame.image.load('resources/textures/background.png').convert()
        font = pygame.font.Font('resources/font/main.ttf', 60)
        self.title = font.render('Inventory', True, (0, 0, 0))

        # Store the game instance and Pygame assets
        self.game = game
        self.resources = game.modLoader.gameRegistry.resources

        # Fetch the inventory
        self.inventory = game.player.inventory
        self.invSynced = False

        # Generate the gui objects (itemslots, buttons etc)
        self.buttons = [InvBackButton([470, 620, 528, 80], 'Close Inventory')]
        self.addItem(PlayerImageBox([250, 450, 599, 120], game))
        self.extraItems[0].colours = game.player.img

        # Store the item being moved around the inventory
        self.moveItem = None

        self.itemSlots = []
        # Make the slotsize accessible in the middle and foreground methods
        self.slotSize = 90
        # Loop the rows and columns and create an empty inventory grid
        for y in range(4):
            for x in range(4):
                slotPos = [(x + 1) * (self.slotSize + 8), 120 + y * (self.slotSize + 8)]
                slot = ItemSlot(game, self.inventory.getItem(y * 4 + x), slotPos, self.slotSize)
                self.itemSlots.append(slot)

        for i, itemstack in enumerate(self.inventory.getEquipped()):
            slotPos = [859, 120 + self.slotSize//4 + i * (self.slotSize + 40)]
            if i != 2:
                self.itemSlots.append(ItemSlot(game, itemstack, slotPos, self.slotSize + 30))
            else:
                self.itemSlots.append(ArmourSlot(game, itemstack, slotPos, self.slotSize + 30))

        self.fetchInventory(game)

    def setInventory(self, inv):
        '''
        Set the inventory for this screen
        '''
        self.inventory = inv

        self.itemSlots = []
        # Make the slotsize accessible in the middle and foreground methods
        self.slotSize = 90
        # Loop the rows and columns and create an empty inventory grid
        for y in range(4):
            for x in range(4):
                slotPos = [(x + 1) * (self.slotSize + 8), 120 + y * (self.slotSize + 8)]
                slot = ItemSlot(self.game, self.inventory.getItem(y * 4 + x), slotPos, self.slotSize)
                self.itemSlots.append(slot)

        for i, itemstack in enumerate(self.inventory.getEquipped()):
            slotPos = [859, 120 + self.slotSize//4 + i * (self.slotSize + 40)]
            if i != 2:
                self.itemSlots.append(ItemSlot(self.game, itemstack, slotPos, self.slotSize + 30))
            else:
                self.itemSlots.append(ArmourSlot(self.game, itemstack, slotPos, self.slotSize + 30))

    def fetchInventory(self, game):
        '''
        Fetch the inventory from the server
        '''
        packetPipeline = game.getModInstance('ClientMod').packetPipeline
        packetPipeline.sendToServer(FetchInventoryPacket(game.player.name))

    def drawBackgroundLayer(self):
        w = self.screen.get_width()
        h = self.screen.get_height()

        self.setInventory(self.game.player.inventory)
        self.screen.blit(pygame.transform.scale(self.backImg, [w, h]), [0, 0])

    def drawMiddleLayer(self, mousePos):
        super().drawMiddleLayer(mousePos)

        w = self.screen.get_width()
        h = self.screen.get_height()

        # Draw the menu title
        self.screen.blit(self.title, [(w-self.title.get_width())//2, -10])

    def drawForegroundLayer(self, mousePos):
        super().drawForegroundLayer(mousePos)

        w = self.screen.get_width()
        h = self.screen.get_height()

        if not self.invSynced:
            font = pygame.font.Font('resources/font/main.ttf', 40)
            text = font.render('Loading Inventory...', True, (0, 0, 0))
            # Draw the background
            pygame.draw.rect(self.screen, (236, 196, 145), [5, h//2 - int(text.get_height() * 1.25), w - 10, text.get_height() * 2])
            # Then the message
            self.screen.blit(text, [(w - text.get_width())//2, h//2 - (text.get_height() * 0.75)])

        if self.moveItem:
            slot = self.itemSlots[self.moveItem[1]]
            stack = self.moveItem[2]
            # Draw the item image
            imageSize = [slot.button.rect[2]-5 for a in range(2)]
            boxPos = [mousePos[a]-imageSize[a]//2 for a in (0, 1)]
            itemImage = stack.getItem().getImage(self.resources)
            imgRect = self.screen.blit(pygame.transform.scale(itemImage, imageSize), boxPos)

            # Draw the stackSize label
            font = pygame.font.Font('resources/font/main.ttf', imageSize[0]//3)
            text = font.render(str(self.moveItem[2].stackSize), True, (0, 0, 0))
            tagPos = list(boxPos)
            tagPos[1] += imageSize[1]-text.get_height()
            tagPos[0] += text.get_height()*1/10
            self.screen.blit(text, tagPos)

class PlayerDrawScreen(Gui):
    '''
    Player customisation screen
    '''
    def __init__(self, game):
        super().__init__()

        w = self.screen.get_width()
        h = self.screen.get_height()

        self.backImg = pygame.image.load('resources/textures/background.png').convert()
        self.buttons = [StartGameButton([600, 580, 350, 120])]
        self.valSliders = [Slider([450 + (a%2)*(250), 180 + 60 * (a//2), 210, 20], (255, 0, 0)) for a in range(12)]
        self.addItem(PlayerImageBox(scaleRect([300, 528, 30, 170], self.screen), game))

    def drawBackgroundLayer(self):
        w = self.screen.get_width()
        h = self.screen.get_height()

        self.screen.blit(pygame.transform.scale(self.backImg, [w, h]), [0, 0])

        values = self.valSliders
        self.extraItems[0].colours = [[int(values[s].value * 5), round(values[s + 1].value * 360 - 180, 1)] for s in range(0, len(values), 2)]
        # Set the eye type to 0
        self.extraItems[0].colours[1][0] = 0

        for s in range(0, len(self.valSliders), 2):
            # If it's the eye type slider, leave it at 0 always
            if s == 2:
                self.valSliders[s].displayValue = 0
            else:
                self.valSliders[s].displayValue = int(self.valSliders[s].value * 5)
            self.valSliders[s + 1].displayValue = round(values[s + 1].value * 360 - 180)

    def drawMiddleLayer(self, mousePos):
        super().drawMiddleLayer(mousePos)

        w = self.screen.get_width()
        h = self.screen.get_height()

        font = pygame.font.Font('resources/font/main.ttf', 40)

        # Draw the title
        text = font.render('Customise your Character', True, (0, 0, 0))
        self.screen.blit(text, [w//2 - text.get_rect().width//2, (h * 5)//64])

        font = pygame.font.Font('resources/font/main.ttf', 20)

        text = font.render('Type:', True, (0, 0, 0))
        self.screen.blit(text, [(w*5)//11, h//5])

        text = font.render('Colour:', True, (0, 0, 0))
        self.screen.blit(text, [(3.5*w)//5, h//5])

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
        xPos = int(x) + 75
        yPos = int(y) + 45
        x -= int(x)
        y -= int(y)

        w = (self.screen.get_width() + 200)//80
        h = (self.screen.get_height() + 200)//80

        # Check if the world is loaded into memory
        if self.game.world and self.game.world.isWorldLoaded():
            xPos1 = xPos-w if xPos >= w else 0
            yPos1 = yPos-h if yPos >= h else 0

            # Pad the top of the map if applicable
            tileMap = [[0] for a in range(abs(yPos - h))] if yPos < h else []
            for row in self.game.world.getTileMap().map[yPos1:yPos + h]:
                # Generate the cropped tilemap of the world
                padding = [0 for a in range(abs(xPos - w))] if xPos < w else []
                tileMap.append(padding + row[xPos1:xPos + w])

            # Iterate and blit the tiles to screen
            for r, row in enumerate(tileMap):
                for t, tile in enumerate(row):
                    if tile:
                        self.screen.blit(tile.tileTypes[tile.tileIndex].img, [round(40 * (t - 1 - x)), round(40 * (r - 1 - y))])

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
                if player.img:
                    print('rendering image')
                    self.game.world.players[p].smallImg = self.game.getModInstance('ClientMod').calculateAvatar(player.img)

        p = self.game.player
        mainAbsPos = p.pos

        # Draw the player images to screen
        for player in self.game.world.players:
            # Get the difference in position
            deltaPos = [player.pos[a] - mainAbsPos[a] for a in range(2)]

            # Get the player image size
            if not player.img:
                continue

            size = player.smallImg.get_rect()

            # Adjust position accordingly, and draw to screen
            pos = [w//2 + deltaPos[0] * 40 - size.width//2, h//2 + deltaPos[1] * 40 - size.height//2]
            if abs(max(pos)) < max(w, h):
                # theta = util.calcDirection(player.pos, player.lastPos)
                # direction = round(2*theta + 2) % 4
                # frame = round(math.sin(12*math.pi*time.time()))
                # img = player.smallImg[direction][frame]
                # self.screen.blit(img, pos)
                self.screen.blit(player.smallImg, pos)

        # Draw the entity and the vehicle images to screen
        for ent in self.game.world.entities + self.game.world.vehicles:
            # Get the difference in position
            deltaPos = [ent.pos[a]-mainAbsPos[a] for a in range(2)]

            # Get the entity image size
            try:
                entityImage = ent.getImage(self.game.modLoader.gameRegistry.resources)
            except KeyError:
                continue
            size = entityImage.get_rect()

            # Adjust position accordingly, and draw to screen
            pos = [w//2 + deltaPos[0] * 40 - size.width//2, h//2 + deltaPos[1] * 40 - size.height//2]
            if abs(max(pos)) < max(w, h):
                self.screen.blit(entityImage, pos)

    def drawForegroundLayer(self, mousePos):
        '''
        Draw the player
        '''
        super().drawForegroundLayer(mousePos)

        # TODO Change this later
        size = self.playerImg.get_width()//2
        # size = self.playerImg[0][0].get_width()//2

        w = self.screen.get_width()
        h = self.screen.get_height()

        # Draw the player image to the screen
        # theta = util.calcDirection(self.game.player.pos, self.game.player.lastPos)
        # direction = round(2*theta + 2) % 4
        # frame = round(math.sin(12*math.pi*time.time()))
        # img = self.playerImg[direction][frame]
        # self.screen.blit(img, [w//2 - size, h//2-size])
        self.screen.blit(self.playerImg, [w//2 - size, h//2 - size])
