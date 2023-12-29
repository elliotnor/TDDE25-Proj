import pygame
from pygame.locals import *
from pygame.color import *
import pymunk
import ai
import images
import gameobjects
import maps


def create_walls(current_map, space):
    """Define and create the border of the map"""
    static_body = space.static_body
    static_lines = [pymunk.Segment(static_body, (0.0, 0.0), (0.0,float(current_map.height)), 0.01),
                    pymunk.Segment(static_body,(0.0, float(current_map.height)), (float(current_map.width),float(current_map.height)), 0.01),  
                    pymunk.Segment(static_body,(0.0, 0.0), (float(current_map.width), 0.0), 0.01),  
                    pymunk.Segment(static_body,(float(current_map.width),0.0),(float(current_map.width), float(current_map.height)), 0.01)]  
    space.add(*static_lines)
    for line in static_lines:
        line.collision_type = 4


def create_boxes(current_map,space, game_objects_list):
    """Detect and place the boxes"""
    for x in range(0, current_map.width):
        for y in range(0,  current_map.height):
            box_type  = current_map.boxAt(x, y)
            if(box_type != 0):
                box = gameobjects.get_box_with_type(x, y, box_type, space)    
                game_objects_list.append(box) 


def create_bases(current_map, gameobjects, game_objects_list):
    """Create the bases for each tank"""
    for i in range(0, len(current_map.start_positions)):
        pos = current_map.start_positions[i]  
        bases = gameobjects.GameVisibleObject(pos[0], pos[1], images.bases[i])
        game_objects_list.append(bases)
