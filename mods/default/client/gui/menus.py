from api.gui import *
from mods.default.client.gui.extras import *

class MainMenu(Gui):
    '''
    Main Menu screen with a player login form
    '''
    def __init__(self):
        super().__init__()
        self.backImg = pygame.image.load('resources/textures/background.png').convert()
        self.error = ''
        self.buttons = [PlayButton([400, 350, 224, 50]), ExitButton([400, 450, 224, 50])]
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
        self.buttons = [MenuButton([300, 500, 424, 80])]

class LoadingScreen(MessageScreen):
    def __init__(self):
        super().__init__('Loading...')
