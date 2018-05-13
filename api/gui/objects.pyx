import pygame

from api.gui.gui import *
from api.item import Armour, ItemStack, NullItem

class Scrollbox:
    def __init__(self, rect):
        self.scrollValue = 0
        self.defaultRect = rect[:2]
        self.rect = self.defaultRect
        self.defaultPos = rect[2:]
        self.pos = self.defaultPos
        self.maxHeight = 0
        self.objects = []
        self.innerScreen = pygame.Surface(self.defaultRect).convert_alpha()

        sliderRect = [self.defaultPos[0]+int(rect[0]*0.97), self.defaultPos[1]+30, int(rect[0]*0.025), rect[1]-60]
        self.scrollSlider = Slider(sliderRect, (0, 0, 0))

    def onResize(self, screen):
        '''
        Resize the scrollbox
        '''
        self.rect = scaleRect(self.defaultRect, screen)
        self.pos = scaleRect(self.defaultPos, screen)
        self.scrollSlider.onResize(screen)

    def draw(self, screen, mousePos):
        '''
        Draw the scrollbox to a given screen
        '''
        # Draw the innerscreen
        while self.objects:
            # Iterate the objects, and draw with scroll adjustment applied
            obj, pos = self.objects[0]
            pos = list(pos)
            pos[1] -= self.scrollValue
            self.innerScreen.blit(obj, pos)
            del self.objects[0]

        screen.blit(self.innerScreen, self.pos)

        self.innerScreen = pygame.Surface(self.rect).convert_alpha()

        # Then draw the slider onto it
        self.scrollSlider.draw(screen, mousePos)

        self.scrollValue = int(self.scrollSlider.value*self.maxHeight)

    def blit(self, surface, pos):
        '''
        Draw a surface to the scrollbox's inner screen
        '''
        try:
            self.rect[1]
        except AttributeError:
            return

        self.objects.append([surface, pos])
        testMaxHeight = pos[1]+surface.get_height()-self.rect[1]
        if testMaxHeight > self.maxHeight-10 and testMaxHeight > 0:
            self.maxHeight = testMaxHeight

class ItemSlot:
    def __init__(self, game, item, pos, size):
        self.defaultPos = [a+3 for a in pos]
        self.pos = self.defaultPos
        self.resources = game.modLoader.gameRegistry.resources
        self.coverColour = (0, 0, 0)
        self.setItem(item)
        self.button = Button(list(pos+[size, size]), '', True)

    def setItem(self, item):
        '''
        Set the itemstack for this itemslot
        '''
        self.item = item
        self.itemImage = self.item.getImage(self.resources)

    def onResize(self, screen):
        '''
        Resize the itemslot
        '''
        self.button.onResize(screen)
        self.pos = scaleRect(self.defaultPos, screen)
        self.pos[1] += 1

    def draw(self, screen, mousePos):
        '''
        Draw the itemslot to a given screen
        '''
        # self.pos = scaleRect(self.defaultPos, screen)
        # self.pos[1] += 1

        # Draw the border of the itemslot
        self.button.draw(screen, [0, 0])

        # Draw the item image
        imageSize = [self.button.rect[2]-5 for a in range(2)]
        if self.itemImage:
            imgRect = screen.blit(pygame.transform.scale(self.itemImage, imageSize), self.pos)

        tagColour = (0, 0, 0)

        if self.button.isHovered(mousePos):
            # Draw a semi transparent square over the itemslot
            square = pygame.Surface(imageSize)
            square.set_alpha(128)
            square.fill(self.coverColour)
            screen.blit(square, self.pos)
            tagColour = (255, 255, 255)

        # Draw the stackSize label
        font = pygame.font.Font('resources/font/main.ttf', imageSize[0]//3)
        text = font.render(str(self.item.stackSize), True, tagColour)
        tagPos = list(self.pos)
        tagPos[1] += imageSize[1]-text.get_height()
        tagPos[0] += text.get_height()*1/10
        screen.blit(text, tagPos)

class ArmourSlot(ItemSlot):
    def __init__(self, game, item, pos, size):
        super().__init__(game, item, pos, size)
        self.coverColour = (153, 0, 0)

    def setItem(self, item):
        self.itemImage = None
        self.item = ItemStack(NullItem(), 0)

        if not isinstance(item, Armour) and item.getRegistryName() != 'null_item':
            print('[ERROR] Non-armour item cannot be placed in ArmourSlot')
            return
        super().setItem(item)

class Slider:
    def __init__(self, rect, colour):
        self.defaultRect = rect
        self.rect = self.defaultRect
        self.value = 0

        self.pad = rect[2]//2 if rect[2] < rect[3] else rect[3]//2
        self.isVertical = self.pad == rect[2]//2

        if self.isVertical:
            self.bar = VertBar(rect, colour)
        else:
            self.bar = HorizBar(rect, colour)

    def onResize(self, screen):
        '''
        Resize the slider
        '''
        self.rect = scaleRect(self.defaultRect, screen)
        self.bar.onResize(screen)

    def draw(self, screen, mousePos):
        '''
        Draw the slider to a given screen
        '''
        # Update the slider value if the mouse is dragging the circle
        if self.isHovered(mousePos) and pygame.mouse.get_pressed()[0]:
            if self.isVertical:
                self.value = abs(mousePos[1]-self.rect[1])/self.rect[3]
            else:
                self.value = abs(mousePos[0]-self.rect[0])/self.rect[2]

        # Draw the bar
        self.bar.draw(screen, mousePos)

        # Draw the circle over the top of the bar
        if self.isVertical:
            circlePos = [int(self.rect[0]+self.pad), int(self.rect[1]+self.rect[3]*self.value)]
        else:
            circlePos = [int(self.rect[0]+self.rect[2]*self.value), int(self.rect[1]+self.pad)]
        pygame.draw.circle(screen, (255, 255, 255), circlePos, int(self.pad*1.5))

    def isHovered(self, mousePos):
        '''
        Determine if a given mousePos is hovering over the slider
        '''
        x, y = mousePos
        if y > self.rect[1]-self.pad and y < self.rect[1]+self.rect[3]+self.pad:
            if x > self.rect[0]-self.pad and x < self.rect[0]+self.rect[2]+self.pad:
                return True
        return False

class HorizBar:
    def __init__(self, rect, colour, percentage=1, label=''):
        self.defaultPos = rect[:2]
        self.pos = self.defaultPos
        self.defaultWidth = rect[2]
        self.width = self.defaultWidth
        self.defaultHeight = rect[3]+rect[3]%2
        self.height = self.defaultHeight
        self.percentage = percentage
        self.colour = colour
        self.label = label

    def onResize(self, screen):
        '''
        Resize the HorizBar
        '''
        self.pos = scaleRect(self.defaultPos, screen)
        self.width, self.height = scaleRect([self.defaultWidth, self.defaultHeight], screen)

    def draw(self, screen, mousePos):
        lineLength = self.width-self.height

        # Get the left and right points of the bar's circles
        leftPos = [self.pos[0]+self.height//2, self.pos[1]+self.height//2]
        rightPos = [leftPos[0]+lineLength, leftPos[1]]
        # Get the end points of the line
        leftLinePos = [leftPos[0], leftPos[1]-1]
        rightLinePos = [rightPos[0], rightPos[1]-1]

        # Draw the grey underbar
        pygame.draw.line(screen, (192, 192, 192), leftLinePos, rightLinePos, self.height)
        pygame.draw.circle(screen, (192, 192, 192), leftPos, self.height//2)
        pygame.draw.circle(screen, (192, 192, 192), rightPos, self.height//2)

        # Draw the bar over the top
        # Get the scaled position of the end of the bar
        scaledRightPos = [leftPos[0] + round(lineLength * self.percentage), rightLinePos[1]]
        pygame.draw.line(screen, self.colour, leftLinePos, scaledRightPos, self.height)
        # Draw the end circles of the bar
        scaledRightPos[1] += 1
        pygame.draw.circle(screen, self.colour, leftPos, self.height//2)
        pygame.draw.circle(screen, self.colour, scaledRightPos, self.height//2)

        # Draw the label
        if self.label:
            font = pygame.font.Font('resources/font/main.ttf', self.height-4)
            text = font.render(self.label, True, (255, 255, 255))
            pos = [self.pos[0]+8, self.pos[1]]
            screen.blit(text, pos)

class VertBar(HorizBar):
    def draw(self, screen, mousePos):
        lineLength = self.height-self.width

        # Get the top and bottom points of the bar's circles
        topPos = [self.pos[0]+self.width//2, self.pos[1]+self.width//2]
        bottomPos = [topPos[0], topPos[1]+lineLength]
        # Get the end points of the line
        topLinePos = [topPos[0]-1, topPos[1]]
        bottomLinePos = [bottomPos[0]-1, bottomPos[1]]

        # Draw the grey underbar
        pygame.draw.line(screen, (192, 192, 192), topLinePos, bottomLinePos, self.width)
        pygame.draw.circle(screen, (192, 192, 192), topPos, self.width//2)
        pygame.draw.circle(screen, (192, 192, 192), bottomPos, self.width//2)

        # Draw the bar over the top
        # Get the scaled position of the end of the bar
        scaledTopPos = [topPos[0]-1, bottomLinePos[1] - round(lineLength * self.percentage)]
        pygame.draw.line(screen, self.colour, bottomLinePos, scaledTopPos, self.width)
        # Draw the end circles of the bar
        scaledTopPos[0] += 1
        pygame.draw.circle(screen, self.colour, bottomPos, self.width//2)
        pygame.draw.circle(screen, self.colour, scaledTopPos, self.width//2)

        # Draw the label
        if self.label:
            font = pygame.font.Font('resources/font/main.ttf', self.width-4)
            for c, char in enumerate(self.label):
                text = font.render(self.label, True, (255, 255, 255))
                pos = [self.pos[0], self.pos[1]+8+(c*self.width-4)]
                screen.blit(text, pos)

class Button:
    def __init__(self, rect, label, isSquare=False, enabled=True):
        self.defaultRect = rect
        self.rect = self.defaultRect
        self.label = label
        self.font = pygame.font.Font('resources/font/main.ttf', 30)
        self.enabled = enabled
        self.isSquare = isSquare

    def onResize(self, screen):
        '''
        Resize the Button
        '''
        self.rect = scaleRect(self.defaultRect, screen)
        if self.isSquare:
            self.rect = self.rect[:2]+[min(self.rect[2:])]*2

    def draw(self, screen, mousePos):
        '''
        Draw the button to the given surface
        '''
        colour1 = (65, 55, 40)
        if self.isHovered(mousePos) or not self.enabled:
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

class TextArea:
    def __init__(self, rect, colour):
        self.defaultRect = rect
        self.rect = self.defaultRect
        self.colour = colour
        self.text = ''
        self.font = pygame.font.Font('resources/font/main.ttf', 20)

    def onResize(self, screen):
        '''
        Resize the TextArea
        '''
        self.rect = scaleRect(self.defaultRect, screen)

    def draw(self, screen, mousePos):
        # Set up the background of the textarea
        background = pygame.Surface(self.rect[2:]).convert_alpha()
        background.fill(pygame.Color(*self.colour))

        # Draw the lines of text
        lines = self.getLines()
        for l, line in enumerate(lines):
            line = self.font.render(line, True, (0, 0, 0))
            background.blit(line, [10, 10+20*l])

        # draw the textarea to the screen
        screen.blit(background, self.rect[:2])

    def doKeyPress(self, event):
        '''
        Handle a key press event on this textbox
        '''
        if event.key == pygame.K_BACKSPACE:
            self.text = self.text[:-1]
        elif event.key != pygame.K_RETURN:
            self.text += event.unicode

    def getLines(self):
        '''
        Split the text within this textarea into lines
        '''
        lines = []
        i = 0
        text = self.text
        # loop the text and split it into lines
        while text:
            i += 1
            if self.getTextWidth(text[:i]) >= self.rect[2]-20:
                # Add the line, crop the text and reset the iterator
                lines.append(text[:i-1])
                text = text[i-1:]
                i = 0
            elif text[:i] == text:
                # Add a flashing bar to the end of the text entry
                text += '|' if (pygame.time.get_ticks()//300)%2 else ''
                lines.append(text)
                break

        return lines

    def getTextWidth(self, text):
        return self.font.render(text, True, (0, 0, 0)).get_width()
