import sys
import os
from datetime import datetime
from threading import Thread

import util

width, height = (800, 600)

def writeLog(message):
    global logFile

    logFile.write(message+'\n')

logFile = open('launcher.log', 'a')

writeLog('='*80)
writeLog("Starting Launcher. System time is "+str(datetime.now())[11:])
writeLog('Setting platform dependent values...')

pythonCommand = "python3" if sys.platform == "linux" else "py"
pipCommand = "pip3" if sys.platform == "linux" else "py -m pip"
scriptEnd = '.sh' if sys.platform == "linux" else ".bat"

writeLog('Platform is: '+sys.platform.upper())

class Button:
    def __init__(self, rect, label):
        self.rect = rect
        self.label = label
        self.font = pygame.font.Font('resources/font/main.ttf', 30)

    def draw(self, screen, mousePos):
        '''
        Draw the button to the given surface
        '''
        colour1 = (65, 55, 40)
        if self.isHovered(mousePos):
            colour2 = (138, 114, 84)
        else:
            colour2 = (173, 144, 106)

        # Draw the button
        pygame.draw.rect(screen, colour2, self.rect, 0)
        pygame.draw.rect(screen, colour1, self.rect, 4)

        # Draw the label on the button
        label = self.getLabelObject()
        screen.blit(label, self.getLabelPos(label))

    def getLabelObject(self):
        '''
        Return a cropped version of the label to fit into the button width
        '''
        label = self.label
        text = self.font.render(label, True, (0, 0, 0))
        while text.get_rect().width+10 > self.rect[2]:
            label = label[1:]
            text = self.font.render(label, True, (0, 0, 0))
        return text

    def getLabelPos(self, label):
        '''
        Return the position to blit the button's label to
        '''
        return [self.rect[0]+self.rect[2]//2-label.get_rect().width//2, self.rect[1]+self.rect[3]//2-20]

    def isHovered(self, mousePos):
        '''
        Return if the given mousePos is above this button
        '''
        x, y = mousePos
        if x > self.rect[0] and x < self.rect[0]+self.rect[2]:
            if y > self.rect[1] and y < self.rect[1]+self.rect[3]:
                return True
        return False

class TextBox(Button):
    def __init__(self, rect, label):
        super().__init__(rect, label)
        self.text = ''

    def getLabelObject(self):
        '''
        Return a cropped version of the label if no input text has been entered
        '''
        if not self.text:
            label = self.label
        else:
            label = ''
        text = self.font.render(label, True, (64, 64, 64))
        while text.get_rect().width+10 > self.rect[2]:
            label = label[1:]
            text = self.font.render(label, True, (64, 64, 64))
        return text

    def getTextObject(self):
        '''
        Return a cropped version of the current input text
        '''
        label = self.text
        text = self.font.render(label, True, (0, 0, 0))
        while text.get_rect().width+10 > self.rect[2]:
            label = label[1:]
            text = self.font.render(label, True, (0, 0, 0))
        return text

    def draw(self, screen, mousePos):
        '''
        Draw the button to the given surface
        '''
        super().draw(screen, mousePos)

        # Draw the input text on the button
        label = self.getTextObject()
        screen.blit(label, self.getLabelPos(label))

    def doKeyPress(self, event):
        '''
        Handle a key press event on this textbox
        '''
        if event.key == pygame.K_BACKSPACE:
            self.text = self.text[:-1]
        elif event.key != pygame.K_RETURN:
            self.text += event.unicode

def firstTimeSetup():
    '''
    Perform first-time setup of game dependencies
    '''
    global setupStep
    global overlay
    global errorMessage

    # Install noise
    if shouldInstallNoise():
        setupStep = "Installing noise library..."
        writeLog(setupStep)
        errorCode = os.system(pipCommand + ' install noise')
        if errorCode != 0:
            # Do something about the error here
            errorMessage = 'Noise library failed to install'
            writeLog(errorMessage)
            return
        setupStep = "Noise library installation complete!"
        writeLog(setupStep)

    # Compile or Pythonify the API
    if shouldSetupAPI():
        setupStep = "Setting up API..."
        writeLog(setupStep)
        errorCode = os.system('./compile_api'+scriptEnd)
        if errorCode != 0:
            errorCode = os.system('./pythonify_api'+scriptEnd)
            if errorCode != 0:
                # Do something about the error here
                errorMessage = 'Failed to compile or pythonify the api.'
                writeLog(errorMessage)
                return
        setupStep = "API setup complete!"
        writeLog(setupStep)

    errorMessage = 'Setup completed successfully!'
    writeLog("Setup completed successfully!")

def shouldInstallPygame():
    '''
    Return whether Pygame needs to be installed
    '''
    try:
        import pygame
        return False
    except ImportError:
        return True

def shouldInstallNoise():
    '''
    Return whether the noise library needs to be installed
    '''
    try:
        import noise
        return False
    except ImportError:
        return True

def shouldSetupAPI():
    '''
    Return whether the api needs to be compiled/pythonified
    '''
    try:
        from api.colour import HueShifter
        return False
    except ImportError:
        return True

def shouldSetup():
    '''
    Return whether the first time setup needs to be run
    '''
    return shouldSetupAPI() or shouldInstallNoise() or shouldInstallPygame()

def drawMain(mousePos):
    '''
    Draw the main graphics of the launcher
    '''
    global screen
    global playButton
    global width
    global height

    x = pygame.image.load('resources/textures/background.png').convert()
    screen.blit(x, [0, 0])

    font = pygame.font.Font('resources/font/main.ttf', 30)

    text = font.render('Extra Arguments:', True, (0, 0, 0))
    screen.blit(text, [width//5, height//2-40])

    playButton.draw(screen, mousePos)
    argBox.draw(screen, mousePos)

def drawOverBox(surface):
    '''
    Draw a surface as an overlaid box
    '''
    global screen
    global width
    global height

    darkener = pygame.Surface((width, height))
    darkener.set_alpha(191)

    darkener.fill((0, 0, 0))
    screen.blit(darkener, [0, 0])

    pos = [width//4, height//4]
    screen.blit(surface, pos)

def getErrorBox(message, mousePos):
    '''
    Generate an error message box
    '''
    global errorButton
    global width
    global height

    box = pygame.Surface((width//2, height//2))

    box.fill((236, 196, 145))

    font = pygame.font.Font('resources/font/main.ttf', 20)

    text = font.render(message, True, (0, 0, 0))
    box.blit(text, [width//4-text.get_width()//2, height//4-text.get_height()//2])

    # Draw a button to say okay
    errorButton = Button([width//8, height//3, width//4, width//10], 'Close')
    errorButton.draw(box, mousePos)

    return box

def getInstallBox():
    '''
    Generate a box with the installation information in it
    '''
    global setupStep
    global width
    global height

    box = pygame.Surface((width//2, height//2))

    box.fill((236, 196, 145))

    font = pygame.font.Font('resources/font/main.ttf', 20)

    text = font.render(setupStep, True, (0, 0, 0))
    box.blit(text, [10, 10])

    font2 = pygame.font.Font('resources/font/main.ttf', 50)

    text = font2.render(('. '*(1+(pygame.time.get_ticks()%1500)//500))[:-1], True, (0, 0, 0))
    box.blit(text, [5*width//24, 2*height//6])

    return box

def launchGame():
    '''
    Launch the game based on the config
    '''
    global config
    global logFile

    writeLog('Launching Game.')
    writeLog('Exiting Launcher.')

    pygame.quit()
    os.system(pythonCommand + ' main.py {}'.format(argBox.text))
    return

    mode = 'COMBINED'
    pygame.quit()
    os.system(pythonCommand+' main.py --type {}'.format(mode))

# Install Pygame
if shouldInstallPygame():
    setupStep = "Installing Pygame..."
    writeLog(setupStep)
    errorCode = os.system(pipCommand + ' install pygame')
    if errorCode != 0:
        # Do something about the error here
        errorMessage = 'Pygame library failed to install'
        writeLog(errorMessage)
        sys.quit()
    setupStep = "Pygame installation complete!"
    writeLog(setupStep)

import pygame

pygame.init()

screen = pygame.display.set_mode((width, height))

writeLog('Display mode set. Surface size is '+str((screen.get_width(), screen.get_height())))

overlay = None
errorMessage = ''
errorButton = None

config = {}
argBox = TextBox([width//5, height//2, 3*width//5, height//15], 'Extra Arguments')
playButton = Button([width//4+width//24, 3*height//4, width//2-width//12, height//7.5], "Launch Game")

setupStep = ""
if shouldSetup():
    writeLog('Running first-time setup...')
    overlay = getInstallBox()
    t = Thread(target=firstTimeSetup, args=())
    t.daemon = True
    t.start()

while True:
    pos = pygame.mouse.get_pos()
    errorPos = list(pos)
    errorPos[0] -= width//4
    errorPos[1] -= height//4

    for event in pygame.event.get():
        # Handle the events
        if event.type == pygame.QUIT:
            writeLog("Exiting Launcher...")
            pygame.quit()
            sys.exit()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                writeLog("Exiting Launcher...")
                pygame.quit()
                sys.exit()
            else:
                argBox.doKeyPress(event)

        if event.type == pygame.MOUSEBUTTONDOWN:
            # Handle the presses on the main buttons and stuff
            if playButton.isHovered(pos):
                launchGame()
            try:
                if errorButton.isHovered(errorPos):
                    overlay = None
                    errorMessage = ''
                    errorButton = None
            except AttributeError:
                pass

    screen.fill((255, 255, 255))

    # Draw the stuff to screen here
    if overlay:
        drawMain(pos)
        drawOverBox(overlay)
    else:
        drawMain(pos)

    if shouldSetup():
        overlay = getInstallBox()
    elif errorMessage:
        overlay = getErrorBox(errorMessage, errorPos)

    pygame.display.flip()
