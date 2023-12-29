#--Import external libraries
import pygame
from pygame.locals import *
from pygame.color import *
#-- Initialise the display
pygame.init()
pygame.display.set_mode()

#-- Import the remaining external libraries
import pymunk
import argparse
from pygame import mixer
import sys

#-- Import the game files
import ai
import images
import gameobjects
import maps
import create_objects

#-- Set game parameters
time_cond   = False     #Set time limit on / off
time_limit  = 10        #Set the time limit (seconds)
round_count = False      #Set round counter on / off
round_limit = 2         #Set the round limit
score_count = True     #Set score limit on / off
score_limit = 2         #Set the score limit
fog_war     = False     #Set fog of war on / off
current_map = maps.map0 #Set the current map

#-- Initialise the clock
clock = pygame.time.Clock()

#-- Initialise the physics engine
space = pymunk.Space()
space.gravity = (0.0,  0.0)
space.damping = 0.1 # Adds friction to the ground for all objects

#-- Constants
FRAMERATE = 50

#   List of all game objects
game_objects_list   = []
tanks_list          = []   
bullets_list        = []      
ai_list             = []       
explosion_list      = []    
game_round_time     = pygame.time.get_ticks()
round_              = 1 
   
#-- Start the display
screen = pygame.display.set_mode(current_map.rect().size)

#-- Generate the background
background = pygame.Surface(screen.get_size())
for x in range(0, current_map.width):
    for y in range(0,  current_map.height):
        background.blit(images.grass,  (x*images.TILE_SIZE, y*images.TILE_SIZE))

#-- Create the map borders
create_objects.create_walls(current_map, space)
    
#-- Create the boxes
create_objects.create_boxes(current_map, space, game_objects_list)

#-- Create the tanks
for i in range(0, len(current_map.start_positions)):
    pos = current_map.start_positions[i]
    tank = gameobjects.Tank(pos[0], pos[1], pos[2], images.tanks[i], space)     #Add the player tanks
    tanks_list.append(tank)
    game_objects_list.append(tank)
    gameobjects.Tank.post_update(tank)
    
    aintel = ai.Ai(tank, game_objects_list, tanks_list, space, current_map)     #Add the Ai
    ai_list.append(aintel)

    tank.respawn_time = pygame.time.get_ticks()     #Store the time of respawn
    tank.spawn_time = pygame.time.get_ticks()       #Store the time of spawn

#-- Create the bases
create_objects.create_bases(current_map, gameobjects, game_objects_list)

#-- Create the flag
flag = gameobjects.Flag(current_map.flag_position[0], current_map.flag_position[1])
game_objects_list.append(flag)

#-- Define the differet collision types between objects
collision_types = {"Bullet":1, "Tank":2, "Box":3, "Wall":4}



def collision_bullet_tank(arb, space, data): #defines the properties of a collision between bullets and tanks    
    """Handles the collisions between bullets and tanks"""
    
    bullet_shape = arb.shapes[0]
    bullet_object = bullet_shape.parent
    space.remove(bullet_shape, bullet_shape.body)   
    if bullet_object: 
        game_objects_list.remove(bullet_object)  #remove the bullet upon collision
    
    tank.hitpoints = tank.hitpoints -1  #subtract one hitoint per collision
    tank_shape = arb.shapes[1]
    tank_object = tank_shape.parent
    
    if tank.hitpoints <= 0:     #Destroy the tank when hitpoints get to zero
        tank.respawn_time = pygame.time.get_ticks()
        if abs(tank.spawn_time - tank.respawn_time) >= 3000:    #Protects the player for 3 seconds after respawn
            pygame.mixer.music.load("data/explosion.wav")   #Loads the explosion sound
            pygame.mixer.music.play()                       #Plays the explosion sound
            pygame.mixer.music.load("data/jungle.wav")
            pygame.mixer.music.play()
            
            exp = gameobjects.Explosion(tank_object.body.position, tank_object.body.position, images.explosion)
            game_objects_list.append(exp)   #projects the explosion
            
            tank_object.body.position = tank_object.start_position
            
            explosion_list.append(exp)
            tank.hitpoints =  2 #resets the hitpoints of the tank
            tank.spawn_time = tank.respawn_time
            
            if tank_object.flag != None: #Ensures that the flag is dropped if carried by the shot tank
                tank_object.flag = None
                flag.is_on_tank = False
    return False
handler = space.add_collision_handler(collision_types["Bullet"], collision_types["Tank"])
handler.pre_solve = collision_bullet_tank
    

def collision_bullet_box(arb, space, data):
    """Handles the collisions between boxes and bullets"""
    try:
        bullet_shape = arb.shapes[0]
        box_shape = arb.shapes[1]
        box_object = box_shape.parent
        bullet_object = bullet_shape.parent
        space.remove(bullet_shape, bullet_shape.body) 
        game_objects_list.remove(bullet_object)     #despawns the bullet

        if box_object.sprite == images.woodbox:
            pygame.mixer.music.load("data/explosion.wav")   #Loads the explosion sound
            pygame.mixer.music.play() 
            pygame.mixer.music.load("data/jungle.wav")
            pygame.mixer.music.play()                      #Plays the explosion sound
            
            exp = gameobjects.Explosion(box_object.body.position, box_object.body.position, images.explosion)   
            game_objects_list.append(exp)   #Displays the explosion animation
            explosion_list.append(exp)
            
            space.remove(box_shape, box_shape.body)
            game_objects_list.remove(box_object)    #despawns the box
        return False
    except ValueError:
        return False    
handler = space.add_collision_handler(1, 3)
handler.pre_solve = collision_bullet_box
    

def collision_bullet_wall(arb, space, data):
    """Handles the collisions between map borders and bullets"""
    bullet_shape = arb.shapes[0]
    bullet_object = bullet_shape.parent
    space.remove(bullet_shape, bullet_shape.body) 
    game_objects_list.remove(bullet_object)     #despawns the bullet
    return False
handler = space.add_collision_handler(1, 4)
handler.pre_solve = collision_bullet_wall
    

def write_text(mess, coord):
    """Handles the formation of the text displayed when time/round limit is active"""
    white = (250, 250, 250) #sets the colour to white
    font = pygame.font.SysFont('arial', 20) #Sets teh font to 'arial'
    text = font.render(mess, True, white)
    textrec = text.get_rect()
    textrec.center = (coord[0], coord[1])
    return screen.blit(text, textrec)



#----- Main Loop -----#

#-- Control whether the game is running or not
running = True
pygame.mixer.music.load("data/jungle.wav")
pygame.mixer.music.play()
skip_update = 0
game_round_time = pygame.time.get_ticks()
set_ = 1    #Helps keep track of the current round
if set_ == 1:        
    while running:
        gametime = pygame.time.get_ticks() #starts the ingame clock

        #-- Handle the events
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE): #If escape is pressed: quit the game
                running = False

            parser = argparse.ArgumentParser()
            parser.add_argument("--singleplayer", help="singleplayer",action="store_true") #toggles between single/multiplayer
            parser.add_argument("--multiplayer",help="multiplayer", action="store_true")
            args = parser.parse_args()

            if args.singleplayer or args.multiplayer:

                #-- Keys for player 1
                if event.type == KEYDOWN:
                    if event.key == K_UP:
                        tanks_list[0].accelerate()

                    elif event.key == K_DOWN:
                        tanks_list[0].decelerate()

                    elif event.key == K_LEFT:
                        tanks_list[0].turn_left()

                    elif event.key == K_RIGHT:
                        tanks_list[0].turn_right()

                    elif event.key == K_RETURN:
                        if (pygame.time.get_ticks() - tanks_list[0].last_shot) >= 500:
                            game_objects_list.append(tanks_list[0].shoot(space))
                            tanks_list[0].last_shot = pygame.time.get_ticks()

            if args.multiplayer:

                #-- Keys for player 2        
                if event.type == KEYDOWN:
                    if event.key == K_w:
                        tanks_list[1].accelerate()

                    elif event.key == K_s:
                        tanks_list[1].decelerate()

                    elif event.key == K_a:
                        tanks_list[1].turn_left()

                    elif event.key == K_d:
                        tanks_list[1].turn_right() 

                    elif event.key == K_SPACE:
                        if (pygame.time.get_ticks() - tanks_list[1].last_shot) >= 500:
                            game_objects_list.append(tanks_list[1].shoot(space))
                            tanks_list[1].last_shot = pygame.time.get_ticks()

            if event.type == KEYUP:
            # -- Player 1
                if event.key == K_UP or event.key == K_DOWN:
                    tanks_list[0].stop_moving()

                elif event.key == K_LEFT or event.key == K_RIGHT:
                    tanks_list[0].stop_turning()
            # -- Player 2
                elif event.key == K_s or event.key == K_w:
                    tanks_list[1].stop_moving()

                elif event.key == K_a or event.key == K_d:
                    tanks_list[1].stop_turning()

        #-- handles the despawning of explosions 
        for exp in explosion_list:
            exp.exp_timer += 1  
            if exp.exp_timer > 10:
                explosion_list.remove(exp)
                game_objects_list.remove(exp) #despawns the explosion


        #-- Update physics
        if skip_update == 0:
            for obj in game_objects_list:
                obj.update()
            skip_update = 2
        else:
            skip_update -= 1

        #   Grab the flag / score / win the game
        for tank in tanks_list:
            tank.try_grab_flag(flag)
            if tank.has_won():
                print("------------") #Separates the scoreboards
                round_ += 1 #Adds one round to the round counter
                pygame.mixer.music.load("data/win.wav") #Loads the 'win sound' 
                pygame.mixer.music.play()               #Plays the 'win sound'
                pygame.mixer.music.load("data/jungle.wav")
                pygame.mixer.music.play()
                tank.flag = None
                flag.is_on_tank = False     
                flag.start_pos(current_map.flag_position[0], current_map.flag_position[1])  #Returns the flag to its original position
                game_objects_list.append(flag)
                tank.tank_score += 1    #provides the scoring player with a point
                for tank in tanks_list:
                    print ("Player", tanks_list.index(tank)+1,":",tank.tank_score) #prints the scoreboard
                    if score_count == True:         #If the scoring limit is active and reached: End the game
                        if tank.tank_score >= score_limit: 
                            running = False
                    if round_count == True:         #If the round limit is active and reached: End the game
                        if round_ > round_limit:
                            running = False
                            
                    
        space.step(1 / FRAMERATE)

        #--Update object that depends on an other object position (for instance a flag)
        for obj in game_objects_list:
            obj.post_update()

        #--Handles the fog of war feature
        if fog_war:
            fog_war = pygame.Surface(current_map.rect().size) #creates a surface for the fog to be displayed on
            fog_war.fill((0,0,0)) #fill with black
            pygame.draw.circle(fog_war,(60,60,60), tanks_list[0].body.position*current_map.rect().size[0] // current_map.width, 100) #creates a transparent circle
            fog_war.set_colorkey((60, 60, 60))
            screen.blit(fog_war,(0,0)) #display the fog of war overlay

        #--Ensures that the ai is updated every frame
        if args.singleplayer: #Determines how many ai tanks there should be (1)
            for ai in ai_list[1:]: 
                ai.tank.try_grab_flag(flag)
                ai.get_flag() 
                ai.decide()
                ai.tank.post_update()

        #--Ensures that the ai is updated every frame
        if args.multiplayer: #Determines how many ai tanks there should be (2)
            for ai in ai_list[2:]:
                ai.tank.try_grab_flag(flag)
                ai.get_flag()
                ai.decide()
                ai.tank.post_update()

        # Controls text on screen
        if time_cond == True: #Displays the game timer
            write_text(f"Clock: {gametime//1000}", (50, 20))
            write_text(f"Time limit: {time_limit}",(70, 45))
        
        if round_count == True: #Displays the round counter
            write_text(f"Round: {round_}", (150,20)) #Types the score

        #-- Ends the game if the time limit is active and reached
        if time_cond == True:
            if gametime >= time_limit*1000:
                print("Game Over - Time is out")
                running = False

        #-- Update the display
        pygame.display.flip()
        clock.tick(FRAMERATE)
        screen.blit(background, (0, 0))
        for obj in game_objects_list:
            obj.update_screen(screen)
        for tank in tanks_list:
            tank.update_screen(screen)

