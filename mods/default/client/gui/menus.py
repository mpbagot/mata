from api.gui.gui import *
from api.gui.objects import *
from mods.default.client.gui.extras import *

class MainMenu(Gui):
    '''
    Main Menu screen with a player login form
    '''
    def __init__(self):
        super().__init__()

        w = self.screen.get_width()
        h = self.screen.get_height()

        self.backImg = pygame.transform.scale(pygame.image.load('resources/textures/background.png'), [w, h]).convert()
        self.error = ''
        self.buttons = [
                        PlayButton(scaleRect([400, 350, 224, 50], self.screen)),
                        ExitButton(scaleRect([400, 450, 224, 50], self.screen))
                       ]
        self.textboxes = [
                          TextBox(scaleRect([375, 180, 274, 40], self.screen), 'Username'),
                          TextBox(scaleRect([375, 250, 274, 40], self.screen), 'Server Address')
                         ]

    def drawBackgroundLayer(self):
        self.screen.blit(self.backImg, [0, 0])

    def drawMiddleLayer(self, mousePos):
        w = self.screen.get_width()
        h = self.screen.get_height()

        font = pygame.font.Font('resources/font/main.ttf', 40)

        # Draw the title
        text = font.render('M.A.T.A', True, (0, 0, 0))
        self.screen.blit(text, [w//2-text.get_width()//2, (h*5)//64])

        # Draw the error message
        text = font.render(self.error, True, (255, 0, 0))
        self.screen.blit(text, [w//2-text.get_width()//2, h//7])

class MessageScreen(Gui):
    def __init__(self, message):
        super().__init__()
        w = self.screen.get_width()
        h = self.screen.get_height()
        self.message = message
        self.backImg = pygame.transform.scale(pygame.image.load('resources/textures/background.png'), [w, h]).convert()

    def drawBackgroundLayer(self):
        self.screen.blit(self.backImg, [0, 0])

    def drawMiddleLayer(self, mousePos):
        w = self.screen.get_width()
        h = self.screen.get_height()

        font = pygame.font.Font('resources/font/main.ttf', 40)
        text = font.render(self.message, True, (0, 0, 0))
        self.screen.blit(text, [w//2-text.get_rect().width//2, h//2-54])

class DimLoadingScreen(MessageScreen):
    def __init__(self, message, game):
        super().__init__(message)
        self.game = game

    def drawForegroundLayer(self, mousePos):
        super().drawForegroundLayer(mousePos)

        pygame.display.flip()

        dimension = self.game.getDimension(self.game.player.dimension)
        dimension.generate(self.game.player.pos, self.game.modLoader.gameRegistry)

        self.game.restoreGui()

class DisconnectMessage(MessageScreen):
    def __init__(self, message):
        super().__init__(message)

        w = self.screen.get_width()
        h = self.screen.get_height()

        self.buttons = [MenuButton(scaleRect([300, 500, 424, 80], self.screen))]

class LoadingScreen(MessageScreen):
    def __init__(self):
        super().__init__('Loading...')
