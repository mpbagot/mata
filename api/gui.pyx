import pygame

class Gui:
    def __init__(self):
        self.screen = pygame.display.get_surface()
        self.buttons = []
        self.textboxes = []
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
        pass

    def drawForegroundLayer(self, mousePos):
        '''
        Draw the foreground layer of the GUI screen
        '''
        for button in self.buttons:
            button.draw(self.screen, mousePos)
        for box in self.textboxes:
            box.draw(self.screen, mousePos)

class Overlay(Gui):
    def doKeyPress(self, event):
        '''
        Handle a key press event
        '''
        pass

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

    def onClick(self, game):
        '''
        Handle a click event on this button
        '''
        pass

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
