from math import sqrt,cos,sin,radians

import pygame

def clamp(v):
    '''
    Clamp the pixel colour to between 0 and 255
    '''
    if v < 0:
        return 0
    if v > 255:
        return 255
    return int(v + 0.5)

class HueShifter:
    def __init__(self):
        self.matrix = [[1,0,0],[0,1,0],[0,0,1]]

    def setHueRotation(self, degrees):
        '''
        Initialise a matrix for hue shifting the pixel
        '''
        cosA = cos(radians(degrees))
        sinA = sin(radians(degrees))
        self.matrix[0][0] = cosA + (1.0 - cosA) / 3.0
        self.matrix[0][1] = 1./3. * (1.0 - cosA) - sqrt(1./3.) * sinA
        self.matrix[0][2] = 1./3. * (1.0 - cosA) + sqrt(1./3.) * sinA
        self.matrix[1][0] = 1./3. * (1.0 - cosA) + sqrt(1./3.) * sinA
        self.matrix[1][1] = cosA + 1./3.*(1.0 - cosA)
        self.matrix[1][2] = 1./3. * (1.0 - cosA) - sqrt(1./3.) * sinA
        self.matrix[2][0] = 1./3. * (1.0 - cosA) - sqrt(1./3.) * sinA
        self.matrix[2][1] = 1./3. * (1.0 - cosA) + sqrt(1./3.) * sinA
        self.matrix[2][2] = cosA + 1./3. * (1.0 - cosA)

    def apply(self, r, g, b):
        '''
        Apply the hue transformation to the pixel
        '''
        rx = r * self.matrix[0][0] + g * self.matrix[0][1] + b * self.matrix[0][2]
        gx = r * self.matrix[1][0] + g * self.matrix[1][1] + b * self.matrix[1][2]
        bx = r * self.matrix[2][0] + g * self.matrix[2][1] + b * self.matrix[2][2]
        return clamp(rx), clamp(gx), clamp(bx)

def hueShiftImage(imgValues, imageName, image, fullPath="resources/other/", attributes=7):
    '''
    Shift the hue of an image using an array of hue shift values
    '''
    fullPath += imageName
    pixArray = pygame.PixelArray(image)

    # Remove the black background
    for y in range(image.get_rect().height):
        for x in range(image.get_rect().width):
            pixArray[x, y] = int.from_bytes([0, 0, 0, 0], 'big')

    # Initialise the hue-shifter and hue-shift the image as necessary
    hueShifter = HueShifter()
    # Loop each part of the image
    for i in range(attributes):
        try:
            value = imgValues[i]
        except IndexError:
            value = [0, 0]
        except TypeError:
            value = [0, 0]
        # Set the hue shift
        hueShifter.setHueRotation(value[1])
        # Generate the full image path and load the image
        imagePath = fullPath+'_{}_{}.png'.format(i, value[0])
        layer = pygame.image.load(imagePath).convert_alpha()
        # Create a pixel array
        pixArray2 = pygame.PixelArray(layer)
        # Colours are ARGB, rather than the standard RGBA
        # Use 'big' encoding to get to bytes from raw value
        for y in range(image.get_rect().height):
            for x in range(image.get_rect().width):
                # Iterate and grab an ARGB pixel tuple for each pixel
                try:
                    colour = [a for a in pixArray2[x, y].to_bytes(4, 'big')]
                except IndexError:
                    print(x, y)
                if colour[0] == 255:
                    # Pixel is fully opaque
                    if value[1] != 0:
                        colour = [colour[0]]+hueShifter.apply(*colour[1:])
                    pixArray[x, y] = int.from_bytes(colour, 'big')
    return image
