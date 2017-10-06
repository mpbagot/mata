'''
client_gui.py
A module containing the GUI's of the default client game
'''
# Import the Python Standard Libraries

# Import the Modding API
from api.gui import *

class MainMenu(Gui):
    pass

class DisconnectMessage(Gui):
    def __init__(self, message):
        super().__init__()
        self.message = message

    def drawBackgroundLayer(self):
        self.screen.blit(pygame.image.load('resources/textures/background.png').convert(), [0, 0])

    def drawMiddleLayer(self, mousePos):
        font = pygame.font.Font('resources/font/main.ttf', 40)
        text = font.render(self.message, True, (0, 0, 0))
        self.screen.blit(text, [512-text.get_rect().width//2, 360])
