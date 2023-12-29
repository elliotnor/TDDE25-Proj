import images
import pygame
import pymunk
import math
DEBUG = False # Change this to set it in debug mode


def physics_to_display(x):
    """ This function is used to convert coordinates in the physic engine into the display coordinates """
    return x * images.TILE_SIZE


class GameObject:
    """ Mostly handles visual aspects (pygame) of an object.
        Subclasses need to implement two functions:
        - screen_position    that will return the position of the object on the screen
        - screen_orientation that will return how much the object is rotated on the screen (in degrees). """


    def __init__(self, sprite):
        self.sprite         = sprite


    def update(self):
        """ Placeholder, supposed to be implemented in a subclass.
            Should update the current state (after a tick) of the object."""
        return


    def post_update(self):
        """ Should be implemented in a subclass. Make updates that depend on
            other objects than itself."""
        return


    def update_screen(self, screen):
        """ Updates the visual part of the game. Should NOT need to be changed
            by a subclass."""
        sprite = self.sprite
        p = self.screen_position() # Get the position of the object (pygame coordinates)
        sprite = pygame.transform.rotate(sprite, self.screen_orientation()) # Rotate the sprite using the rotation of the object
        offset = pymunk.Vec2d(sprite.get_size()) / 2.
        p = p - offset
        screen.blit(sprite, p) # Copy the sprite on the screen



class GamePhysicsObject(GameObject):
    """ This class extends GameObject and it is used for objects which have a
        physical shape (such as tanks and boxes). This class handle the physical
        interaction of the objects.
    """

    def __init__(self, x, y, orientation, sprite, space, movable):
        """ Takes as parameters the starting coordinate (x,y), the orientation, the sprite (aka the image
            representing the object), the physic engine object (space) and whether the object can be
            moved (movable).
        """
        super().__init__(sprite)

        # Half dimensions of the object converted from screen coordinates to physic coordinates
        half_width          = 0.5 * self.sprite.get_width() / images.TILE_SIZE
        half_height         = 0.5 * self.sprite.get_height() / images.TILE_SIZE

        # Physical objects have a rectangular shape, the points correspond to the corners of that shape.
        points              = [[-half_width, -half_height],
                            [-half_width, half_height],
                            [half_width, half_height],
                            [half_width, -half_height]]
        self.points = points
        # Create a body (which is the physical representation of this game object in the physic engine)
        if(movable):
            # Create a movable object with some mass and moments
            # (considering the game is a top view game, with no gravity,
            # the mass is set to the same value for all objects)."""
            mass = 10
            moment = pymunk.moment_for_poly(mass, points)
            self.body         = pymunk.Body(mass, moment)
        else:
            self.body         = pymunk.Body(body_type=pymunk.Body.STATIC) # Create a non movable (static) object

        self.body.position  = x, y
        self.body.angle     = math.radians(orientation)       # orientation is provided in degress, but pymunk expects radians.
        self.shape          = pymunk.Poly(self.body, points)  # Create a polygon shape using the corner of the rectangle
        self.shape.parent = self

        # Set some value for friction and elasticity, which defines interraction in case of a colision
        self.shape.friction = 0.5
        self.shape.elasticity = 0.1

        # Add the object to the physic engine
        if(movable):
            space.add(self.body, self.shape)
        else:
            space.add(self.shape)


    def screen_position(self):
        """ Converts the body's position in the physics engine to screen coordinates. """
        return physics_to_display(self.body.position)

    def screen_orientation(self):
        """ Angles are reversed from the engine to the display. """
        return -math.degrees(self.body.angle)

    def update_screen(self, screen):
        super().update_screen(screen)
        # debug draw
        if DEBUG:
            ps = [self.body.position+p for p in self.points]
            ps = [physics_to_display(p) for p in ps]
            ps += [ps[0]]
            pygame.draw.lines(screen, pygame.color.THECOLORS["red"], False, ps, 1)


def clamp(min_max, value):
    """ Convenient helper function to bound a value to a specific interval. """
    return min(max(-min_max, value), min_max)


class Tank(GamePhysicsObject):
    """ Extends GamePhysicsObject and handles aspects which are specific to our tanks. """
    ACCELERATION = 0.4
    NORMAL_MAX_SPEED = 2.3
    FLAG_MAX_SPEED = NORMAL_MAX_SPEED * 0.6

    def __init__(self, x, y, orientation, sprite, space):
        super().__init__(x, y, orientation, sprite, space, True)
        self.acceleration = 0
        self.rotation = 0
        self.last_shot = 0
        self.shape.parent = self
        self.shape.collision_type = 2
        self.respawn_time = 0
        self.spawn_time = 0
        self.tank_score = 0
        self.flag                 = None                      # This variable is used to access the flag object
        self.max_speed        = Tank.NORMAL_MAX_SPEED         # Set the maximum speed to the tank
        self.start_position       = pymunk.Vec2d(x, y)        # Define the start position
        self.hitpoints = 2

    def accelerate(self):
        """ Call this function to make the tank move forward. """
        self.acceleration = 1

    def stop_moving(self):
        """ Call this function to make the tank stop moving. """
        self.acceleration  = 0
        self.body.velocity = pymunk.Vec2d.zero()

    def decelerate(self):
        """ Call this function to make the tank move backward. """
        self.acceleration = -1

    def turn_left(self):
        """ Makes the tank turn left (counter clock-wise). """
        self.rotation = -1

    def turn_right(self):
        """ Makes the tank turn right (clock-wise). """
        self.rotation = 1

    def stop_turning(self):
        """ Call this function to make the tank stop turning. """
        self.rotation = 0
        self.body.angular_velocity = 0
        
    def shoot(self, space):                         
        """Handles the shooting action"""
        x = self.body.position[0] - (math.sin(self.body.angle))/1.5
        y = self.body.position[1] + (math.cos(self.body.angle))/1.5
        orientation = math.degrees(self.body.angle)
        pygame.mixer.music.load("data/shoot.wav")   #Load the shooting sound
        pygame.mixer.music.play()                   #Play the shooting sound
        return Bullet(x, y, orientation, images.bullet, space, True)
    
                                       
            
    def update(self):
        """ A function to update the objects coordinates. Gets called at every tick of the game. """
        # Creates a vector in the direction we want accelerate / decelerate
        acceleration_vector = pymunk.Vec2d(0, self.ACCELERATION * self.acceleration).rotated(self.body.angle)
        
        # Applies the vector to our velocity
        self.body.velocity += acceleration_vector
        
        # Makes sure that we dont exceed our speed limit
        velocity = clamp(self.max_speed, self.body.velocity.length)
        self.body.velocity = pymunk.Vec2d(velocity, 0).rotated(self.body.velocity.angle)

        # Updates the rotation
        self.body.angular_velocity += self.rotation * self.ACCELERATION
        self.body.angular_velocity = clamp(self.max_speed, self.body.angular_velocity)


    def post_update(self):
        # If the tank carries the flag, then update the positon of the flag
        if(self.flag != None):
            self.flag.x           = self.body.position[0]
            self.flag.y           = self.body.position[1]
            self.flag.orientation = -math.degrees(self.body.angle)
        else:
            self.max_speed = Tank.NORMAL_MAX_SPEED


    def try_grab_flag(self, flag):
        """ Call this function to try to grab the flag, if the flag is not on other tank
            and it is close to the current tank, then the current tank will grab the flag.
        """
        # Check that the flag is not on other tank
        if(not flag.is_on_tank):
            # Check if the tank is close to the flag
            flag_pos = pymunk.Vec2d(flag.x, flag.y)
            if((flag_pos - self.body.position).length < 0.5):
                self.flag           = flag
                flag.is_on_tank     = True
                pygame.mixer.music.load("data/success.wav")     #Load the pickup sound
                pygame.mixer.music.play()                       #Play the pickup sound
                self.max_speed  = Tank.FLAG_MAX_SPEED           #Ensure the tank doesn't exceed the speed limit


    def has_won(self):
        """ Check if the current tank has won"""
        return self.flag != None and (self.start_position - self.body.position).length < 0.2
    
class Bullet(GamePhysicsObject):
    """This class extends the GamePhysicsObject class to handle bullets"""
    ACCELERATION = 0.0
    NORMAL_MAX_SPEED = 2.5
    
    def __init__(self, x, y, orientation, sprite, space, movable):
        super().__init__(x, y, orientation, sprite, space, True)
        self.velocity       = 7 
        self.shape.parent = self
        self.shape.collision_type = 1 
        
    def update(self):
        """Updates the bullet position"""
        self.body.velocity = pymunk.Vec2d(0, self.velocity).rotated(self.body.angle)
       

class Box(GamePhysicsObject):
    """ This class extends the GamePhysicsObject to handle box objects. """
    def __init__(self, x, y, sprite, movable, space, destructable):
        """ It takes as arguments the coordinate of the starting position of the box (x,y) and the box model (boxmodel). """
        super().__init__(x, y, 0, sprite, space, movable)
        self.destructable = destructable
        self.shape.parent = self
        self.shape.collision_type = 3

def get_box_with_type(x, y, type, space):
    (x, y) = (x + 0.5, y + 0.5) # Offsets the coordinate to the center of the tile
    if type == 1: # Creates a non-movable non-destructable rockbox
        return Box(x, y, images.rockbox, False, space, False)
    if type == 2: # Creates a movable destructable woodbox
        return Box(x, y, images.woodbox, True, space, True)
    if type == 3: # Creates a movable non-destructable metalbox
        return Box(x, y, images.metalbox, True, space, False)


class GameVisibleObject(GameObject):
    """ This class extends GameObject for object that are visible on screen but have no physical representation (bases and flag) """
    def __init__(self, x, y, sprite):
        """ It takes argument the coordinates (x,y) and the sprite. """
        self.x            = x
        self.y            = y
        self.orientation  = 0
        super().__init__(sprite)

    def screen_position(self):
        return physics_to_display(pymunk.Vec2d(self.x, self.y))

    def screen_orientation(self):
        return self.orientation


class Flag(GameVisibleObject):
    """ This class extends GameVisibleObject for representing flags."""
    def __init__(self, x, y):
        self.is_on_tank   = False
        super().__init__(x, y,  images.flag)

    def start_pos(self, x, y):
        """Used to reset the flag's position when a point is scored"""
        self.x = x
        self.y = y


class Explosion(GameVisibleObject):
    """This class extends GameVisibleObject for representing explosions"""
    def __init__ (self ,x ,y, sprite):
        self.exp_timer = 0
        super().__init__(x, y, images.explosion)
