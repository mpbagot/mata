import pygame

class Gui:
    def __init__(self):
        self.screen = pygame.display.get_surface()
        self.buttons = []
        self.textboxes = []
        self.bars = []
        self.valSliders = []
        self.itemSlots = []
        self.extraItems = []
        self.currentTextBox = None

    def drawBackgroundLayer(self):
        '''
        Draw the background layer of the GUI screen
        '''
        pass

    def drawMiddleLayer(self, mousePos):
        '''
        Draw the middleground layer of the GUI screen
        '''
        for slot in self.itemSlots:
            slot.draw(self.screen, mousePos)
        for item in self.extraItems:
            item.draw(self.screen, mousePos)
        for slider in self.valSliders:
            slider.draw(self.screen, mousePos)

    def drawForegroundLayer(self, mousePos):
        '''
        Draw the foreground layer of the GUI screen
        '''
        for button in self.buttons:
            button.draw(self.screen, mousePos)
        for box in self.textboxes:
            box.draw(self.screen, mousePos)
        for bar in self.bars:
            bar.draw(self.screen, mousePos)

    def addItem(self, item):
        '''
        Add an Item to be drawn
        '''
        if 'draw' not in dir(item):
            raise Exception('Invalid Item Being Added To Gui.')
        self.extraItems.append(item)

    def hasAttribute(self, name):
        '''
        Return whether the class (and classes which extend this) has a given attribute
        '''
        try:
            a = self.__getattribute__(name)
            return True
        except AttributeError:
            return False

class Overlay(Gui):
    def doKeyPress(self, event):
        '''
        Handle a key press event
        '''
        pass

def scaleRect(rect, screen):
    '''
    Scale a rect to a given screen size from a default of 1024x768
    '''
    w = screen.get_width()
    h = screen.get_height()

    # Calculate the x and y scaling coefficients
    x_coeff = w/1024
    y_coeff = h/768

    # Multiply the x and y positions by the respective coefficients
    rect[0] *= x_coeff
    rect[1] *= y_coeff

    # Attempt to multiply the width and height if the input rect is a full rect, not position
    try:
        rect[2] *= x_coeff
        rect[3] *= y_coeff
    except IndexError:
        pass

    # Floor all of the values and return
    return [int(a) for a in rect]
