import pygame
import os

main_dir = os.path.split(os.path.abspath(__file__))[0]

def load_image(file):
    """ Load an image from the data directory. """
    file = os.path.join(main_dir, 'data', file)
    try:
        surface = pygame.image.load(file)
    except pygame.error:
        raise SystemExit('Could not load image "%s" %s'%(file, pygame.get_error()))
    return surface.convert_alpha()

TILE_SIZE = 40 # Define the default size of tiles

#-- Sprites
explosion = load_image('explosion.png') # Image of an explosion
grass     = load_image('grass.png') # Image of a grass tile
rockbox   = load_image('rockbox.png') # Image of a rock box (wall)
metalbox  = load_image('metalbox.png') # Image of a metal box
woodbox   = load_image('woodbox.png') # Image of a wood box
flag      = load_image('flag.png') # Image of flag
bullet = load_image('bullet.png') #Image of bullet
bullet = pygame.transform.scale(bullet, (10, 10)) #Rescale the image
bullet = pygame.transform.rotate(bullet, -90) #Rotate the images


# List of image of tanks of different colors
tanks     = [load_image('tank_orange.png'), load_image('tank_blue.png'), load_image('tank_white.png'),
             load_image('tank_yellow.png'), load_image('tank_red.png'),  load_image('tank_gray.png')]


# List of image of bases corresponding to the color of each tank
bases     = [load_image('base_orange.png'), load_image('base_blue.png'), load_image('base_white.png'),
             load_image('base_yellow.png'), load_image('base_red.png'),  load_image('base_gray.png')]
