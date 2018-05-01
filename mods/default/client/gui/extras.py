from math import cos, pi
from threading import Thread

from api.gui.gui import *
from api.gui.objects import *
from api.colour import *
from api.packets import DisconnectPacket
from mods.default.packets import *

class StartGameButton(Button):
    def __init__(self, rect):
        super().__init__(rect, 'Play!')

    def onClick(self, game):
        # Generate the image values array
        values = game.getGui()[1].valSliders
        playerImg = [[int(values[s].value * 5), round(values[s + 1].value * 360 - 180, 1)] for s in range(0, len(values), 2)]

        # Set it and sync it to the server
        game.player.img = playerImg
        game.player.smallImg = game.getModInstance('ClientMod').calculateAvatar(game.player.img)
        packetPipeline = game.getModInstance('ClientMod').packetPipeline
        packetPipeline.sendToServer(SendPlayerImagePacket(game.player))

        # Show the game screen
        game.openGui(game.getModInstance('ClientMod').gameGui, game)

class PlayButton(Button):
    def __init__(self, rect):
        super().__init__(rect, 'Play')

    def onClick(self, game):
        # Grab the variables from the textboxes
        username = game.getGui()[1].textboxes[0].text
        address = game.getGui()[1].textboxes[1].text

        # Set the player username
        game.player.setUsername(username)
        game.openGui(game.getModInstance('ClientMod').loadingGui)

        # Try to connect in another thread
        t = Thread(target=self.asyncConnect, args=(game, username, address))
        t.daemon = True
        t.start()

    def asyncConnect(self, game, username, address):
        '''
        Connect to the server, and handle errors as required in the background
        '''
        game.establishConnection(address)
        error = game.getModInstance('ClientMod').packetPipeline.connectToServer(address)

        # Display an error if it fails for any reason
        if error:
            game.openGui(game.getModInstance('ClientMod').mainMenuGui)
            game.getGui()[1].error = error
            game.getGui()[1].textboxes[0].text = username

class ChatTabButton(Button):
    def onClick(self, game):
        for o, overlay in enumerate(game.getOverlays()):
            if overlay[0] == game.getModInstance('ClientMod').chatOverlay:
                game.getOverlays()[o][1].tab = self.label

class BackButton(Button):
    def onClick(self, game):
        game.restoreGui()

class InvBackButton(BackButton):
    def onClick(self, game):
        # Send the inv to the server to record rearrangements etc
        game.getModInstance('ClientMod').packetPipeline.sendToServer(SendInventoryPacket(game.player.name, game.player.inventory))
        super().onClick(game)

class ResumeButton(Button):
    def __init__(self, rect, label="Resume Game"):
        super().__init__(rect, label)

    def onClick(self, game):
        pauseOverlay = game.getModInstance('ClientMod').pauseOverlay
        if game.getGUIState().isOverlayOpen(pauseOverlay):
            game.getGUIState().closeOverlay(game.getModInstance('ClientMod').pauseOverlay)

class ExitButton(Button):
    def __init__(self, rect, label="Exit"):
        super().__init__(rect, label)

    def onClick(self, game):
        game.quit()

class OptionsButton(Button):
    def onClick(self, game):
        pass

class MenuButton(Button):
    def __init__(self, rect, disconnect=False):
        super().__init__(rect, 'Exit To Menu')
        self.disconnect = disconnect

    def onClick(self, game):
        if self.disconnect:
            # Try to disconnnect if required
            game.packetPipeline.sendToServer(DisconnectPacket())

        # Return to the main menu
        game.openGui(game.getModInstance('ClientMod').mainMenuGui)

class PlayerImageBox:
    def __init__(self, rect, game):
        self.defaultRect = rect[:2]
        if rect[0] > rect[1]:
            raise Exception('Invalid Player Image Dimensions!')
        self.defaultPos = rect[2:]

        # Current rotation amount
        self.rot = [1, 1]
        # Current rotation velocity
        self.rotVel = [0, 0]

        self.prevPos = pygame.mouse.get_pos()

        self.game = game

        # Initialise the colours and player image
        self.prevColours = None
        self.colours = None
        self.img = None

    def draw(self, screen, mousePos):
        self.rect = scaleRect(self.defaultRect, screen)
        self.pos = scaleRect(self.defaultPos, screen)

        # Update the rotation from rotation velocity
        self.rot[0] += self.rotVel[0]
        self.rot[1] += self.rotVel[1]

        # Decelerate the rotational velocity
        if abs(self.rotVel[0]) < 0.08:
            self.rotVel[0] = 0.006
        else:
            self.rotVel[0] -= (1 if self.rotVel[0] > 0 else -1)*0.01

        if abs(self.rotVel[1]) < 0.08:
            self.rotVel[1] = 0
        else:
            self.rotVel[1] -= (1 if self.rotVel[1] > 0 else -1)*0.01

        # Get the width,s height and flip booleans
        width = int(abs(self.rect[0]*cos(self.rot[0])))
        height = int(abs(self.rect[1]*cos(self.rot[1])))
        flipX = self.rot[0] < 0
        flipY = self.rot[1] < 0

        # Draw the rect underneath
        pygame.draw.rect(screen, (0, 0, 0), self.pos+self.rect)
        # Draw the silver border
        pygame.draw.rect(screen, (127, 127, 127), self.pos+self.rect, 3)

        # Draw the player
        pos = [self.pos[0]+(self.rect[0]-width)//2, self.pos[1]+(self.rect[1]-height)//2]

        # Generate the image
        if self.colours != self.prevColours or self.img == None:
            self.img = self.game.getModInstance('ClientMod').calculateAvatar(self.colours)
            # self.img = self.game.getModInstance('ClientMod').generateLargePlayerImage(self.colours)

        # Flip, rotate and draw the image
        img = pygame.transform.flip(self.img, flipX, flipY)
        img = pygame.transform.scale(img, [width, height])
        screen.blit(img, pos)

        # If the player is clicking and dragging, update the rotational velocity
        if pygame.mouse.get_pressed()[0] and self.isHovered(mousePos):
            # set the rotational velocity
            self.rotVel = [(2*pi*(mousePos[a]-self.prevPos[a]))/self.rect[a] for a in range(2)]

        self.prevPos = list(mousePos)

    def isHovered(self, mousePos):
        x, y = mousePos
        if x in range(self.pos[0], self.pos[0]+self.rect[0]):
            if y in range(self.pos[1], self.pos[1]+self.rect[1]):
                return True
        return False
