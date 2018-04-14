from api.gui.gui import *
from api.gui.objects import *
from mods.default.client.gui.extras import *

class MainMenu(Gui):
    '''
    Main Menu screen with a player login form
    '''
    def __init__(self):
        super().__init__()

        self.buttons = [
            PlayButton([400, 350, 224, 50]),
            ExitButton([400, 450, 224, 50])
        ]
        self.textboxes = [
            TextBox([375, 180, 274, 40], 'Username'),
            TextBox([375, 250, 274, 40], 'Server Address')
        ]

        self.backImg = pygame.image.load('resources/textures/background.png').convert()
        self.error = ''

    def drawBackgroundLayer(self):
        w = self.screen.get_width()
        h = self.screen.get_height()

        self.screen.blit(pygame.transform.scale(self.backImg, [w, h]), [0, 0])

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
