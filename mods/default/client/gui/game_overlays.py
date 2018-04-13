'''
game_overlays.py
A module containing the GUI overlays of the default client game
'''
# Import the Modding API
from api.gui.gui import *
from api.gui.objects import *
from api.colour import *
from api.packets import SendCommandPacket

# Import stuff from the mod modules
from mods.default.client.gui.extras import *
from mods.default.client.gui.menus import *

class HUD(Overlay):
    def __init__(self, game):
        super().__init__()

        h = self.screen.get_height()

        self.game = game
        self.bars = [
                        HorizBar(scaleRect([744, 698, 260, 20], self.screen), (255, 0, 0), self.game.player.health, 'Health'),
                        HorizBar(scaleRect([744, 728, 260, 20], self.screen), (0, 102, 255), self.game.player.exp, 'Experience')
                    ]
        equippedItems = self.game.player.inventory.getEquipped()
        self.itemSlots = [
                            ItemSlot(game, equippedItems[0].getItem(), scaleRect([664, 630], self.screen), (5*h)//64),
                            ItemSlot(game, equippedItems[1].getItem(), scaleRect([664, 700], self.screen), (5*h)//64)
                         ]

    def drawBackgroundLayer(self):
        # Draw the background rectangle
        pygame.draw.rect(self.screen, (173, 144, 106), scaleRect([654, 620, 400, 150], self.screen))
        pygame.draw.rect(self.screen, (65, 55, 40), scaleRect([654, 620, 400, 150], self.screen), 4)

    def drawForegroundLayer(self, mousePos):
        super().drawForegroundLayer(mousePos)

        # Generate a font object
        font = pygame.font.Font('resources/font/main.ttf', 20)
        text = font.render('Username: '+self.game.player.name, True, (255, 255, 255))
        self.screen.blit(text, scaleRect([744, 640], self.screen))

        # Generate a smaller font object
        font = pygame.font.Font('resources/font/main.ttf', 12)
        text = font.render('Level: '+str(self.game.player.level), True, (255, 255, 255))
        self.screen.blit(text, scaleRect([744, 670], self.screen))

class Chat(Overlay):
    def __init__(self, game, tab='global'):
        super().__init__()
        self.game = game
        self.tab = tab
        self.scrollScreen = Scrollbox(scaleRect([804, 438, 110, 90], self.screen))
        self.textarea = TextArea(scaleRect([100, 538, 618, 100], self.screen), (255, 255, 255, 127))

    def drawForegroundLayer(self, mousePos):
        # Fetch the messages from the mod instance
        messages = self.game.getModInstance('ClientMod').chatMessages.get(self.tab, [])

        # Draw the background rectangle
        overlayScreen = pygame.Surface(scaleRect([824, 558], self.screen))
        overlayScreen.set_alpha(191)

        pygame.draw.rect(overlayScreen, (140, 140, 140), scaleRect([0, 0, 824, 558], self.screen))
        pygame.draw.rect(overlayScreen, (170, 170, 170), scaleRect([0, 458, 824, 100], self.screen))

        self.screen.blit(overlayScreen, scaleRect([100, 80], self.screen))

        self.textarea.draw(self.screen, mousePos)

        # Draw the outline boxes
        pygame.draw.rect(self.screen, (40, 40, 40), scaleRect([100, 538, 824, 100], self.screen), 4)
        pygame.draw.rect(self.screen, (40, 40, 40), scaleRect([100, 80, 824, 558], self.screen), 4)
        pygame.draw.rect(self.screen, (40, 40, 40), scaleRect([718, 538, 206, 100], self.screen), 4)

        # Generate a font object
        fontLarge = pygame.font.Font('resources/font/main.ttf', 20)
        # Generate a smaller font object
        fontSmall = pygame.font.Font('resources/font/main.ttf', 12)

        self.scrollScreen.innerScreen.fill(pygame.Color(127, 127, 127, 0))

        messages = [a for a in messages if '\x00' not in a]
        for m, message in enumerate(messages):
            text = fontSmall.render(message, True, (0, 0, 0))

            self.scrollScreen.blit(text, [0, 15*m])

        self.scrollScreen.draw(self.screen, mousePos)

        super().drawForegroundLayer(mousePos)

    def doKeyPress(self, event):
        if event.key == pygame.K_RETURN:
            # Adjust the message
            message = self.textarea.text
            if message[0] != '/':
                message = '/message '+self.tab+' '+message

            # Create the packet
            # Send the message
            packet = SendCommandPacket(message)
            self.game.packetPipeline.sendToServer(packet)
            self.textarea.text = ''
        # Pass the button press to the textarea
        self.textarea.doKeyPress(event)
