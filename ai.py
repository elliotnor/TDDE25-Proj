import math
import pymunk
import maps
from pymunk import Vec2d
import pygame   
import gameobjects
from collections import defaultdict, deque

# NOTE: use only 'map0' during development!

MIN_ANGLE_DIF = math.radians(3) # 3 degrees, a bit more than we can turn each tick


def angle_between_vectors(vec1, vec2):
    """ Since Vec2d operates in a cartesian coordinate space we have to
        convert the resulting vector to get the correct angle for our space.
    """
    vec = vec1 - vec2 
    vec = vec.perpendicular()
    return vec.angle

def periodic_difference_of_angles(angle1, angle2): 
    """Returns the periodic difference of the angles."""
    return  (angle1% (2*math.pi)) - (angle2% (2*math.pi))



class Ai:
    """ A simple ai that finds the shortest path to the target using 
    a breadth first search. Also capable of shooting other tanks and or wooden
    boxes. """

    def __init__(self, tank,  game_objects_list, tanks_list, space, currentmap):
        self.tank               = tank
        self.game_objects_list  = game_objects_list
        self.tanks_list         = tanks_list
        self.space              = space
        self.currentmap         = currentmap
        self.flag = None
        self.MAX_X = currentmap.width - 1 
        self.MAX_Y = currentmap.height - 1
        self.last_shot = 0
        self.last_distance = 25

        self.move_cycle = self.move_cycle_gen()
        self.update_grid_pos()

    def update_grid_pos(self):
        """ This should only be called in the beginning, or at the end of a move_cycle. """
        self.grid_pos = self.get_tile_of_position(self.tank.body.position)


    def decide(self):
        """ Main decision function that gets called on every tick of the game. """
        self.maybe_shoot()
        next(self.move_cycle)
        

    def ai_shoot(self):   
        """The shoot function for the ai. Gets called every time the ai needs to shoot."""                      
        if abs(pygame.time.get_ticks() - self.last_shot) >= 1000:
            self.last_shot = pygame.time.get_ticks()
            bullet = self.tank.shoot(self.space)
            self.game_objects_list.append(bullet)
            pygame.mixer.music.load("data/shoot.wav")
            pygame.mixer.music.play()


    def maybe_shoot(self):
        """ Makes a raycast query in front of the tank. If another tank
            or a wooden box is found, then we shoot. 
        """
        
        ray_start   = 0.8
        ray_end     = max(self.MAX_X, self.MAX_Y)*1.4

        tank_angle = self.tank.body.angle + math.pi/2

        start_coord = (ray_start * math.cos(tank_angle) + self.tank.body.position[0], ray_start * math.sin(tank_angle) + self.tank.body.position[1])
        end_coord = (ray_end * math.cos(tank_angle) + self.tank.body.position[0], ray_end * math.sin(tank_angle) + self.tank.body.position[1])
        
        ray_cast = self.space.segment_query_first(start_coord, end_coord, 0, pymunk.ShapeFilter())
        if hasattr(ray_cast, 'shape'):
            if ray_cast.shape.collision_type == 2:
                self.ai_shoot()
            if ray_cast.shape.collision_type == 3: 
                if ray_cast.shape.parent.destructable:
                    self.ai_shoot()


    def correct_position(self, next_coord, last_distance):
        """ If new_distance (the euclidean distance on the current tick) is larger 
            than last_distance(euclidean distance on the last tick) return True
        """
        tank_position = self.tank.body.position 
        new_distance = abs(next_coord.get_distance(tank_position))

        if last_distance < new_distance:
            return True
        return False
    

    def move_cycle_gen (self):
        """ A generator that iteratively goes through all the required steps
            to move to our goal.
        """ 
        
        while True:  
            if self.find_shortest_path(self.filter_grid_neighbors):
                path = self.find_shortest_path(self.filter_grid_neighbors)
            else:
                path = self.find_shortest_path(self.metalbox_filter_grid_neighbors)
            if not path:      
                yield
                continue 

            path.popleft()
            next_coord = Vec2d(path.popleft()) + (0.5, 0.5) if path else next_coord
            tank_position = self.tank.body.position
            tank_body_angle = self.tank.body.angle
            
            target_angle = angle_between_vectors(tank_position, Vec2d(next_coord))
            periodic_target_angle = periodic_difference_of_angles(target_angle, tank_body_angle)
    
            if MIN_ANGLE_DIF < periodic_target_angle < math.pi or MIN_ANGLE_DIF > periodic_target_angle < -math.pi: 
                self.tank.turn_right()
            else: 
                self.tank.turn_left()
            
            while abs(periodic_target_angle) > MIN_ANGLE_DIF:
                target_angle = angle_between_vectors(self.tank.body.position, Vec2d(next_coord))
                periodic_target_angle = periodic_difference_of_angles(target_angle, self.tank.body.angle)
                yield

            self.tank.stop_turning()
            self.tank.accelerate()
            
            self.last_distance = next_coord.get_distance(self.tank.body.position)
            while not self.correct_position(next_coord, self.last_distance):
                tank_position = self.tank.body.position
                self.last_distance = abs(tank_position.get_distance(next_coord))
                yield
            
            self.tank.stop_moving()
            self.update_grid_pos()
            
                        
    def find_shortest_path(self, filter_function):
        """ A simple Breadth First Search using integer coordinates as our nodes.
            Edges are calculated as we go, using an external function.
        """
        shortest_path = []
        source_node = self.tank.body.position 
        path = []
        queue = deque([])
        queue.append((source_node.int_tuple, path))            #insert our source node into the queue
        visited_tiles = set(source_node)                

        while queue:
            next_tile, path = queue.popleft()               #remove the first node from the queue
            if next_tile == self.get_target_tile().int_tuple: #if node is our target:
                shortest_path = path + [next_tile] 
                return deque(shortest_path)

            current_neigbors = self.get_tile_neighbors(next_tile, filter_function) 
           
            for neighbor in current_neigbors:               #for every neighbor to the node:
                if neighbor.int_tuple not in visited_tiles:     #if the neighbor has not already been visited
                    queue.append((neighbor, path+[next_tile]))                    #add it to the queue
                    visited_tiles.add(neighbor.int_tuple)       #add it to our set of visited nodes 
        return deque(shortest_path)
            
    def get_target_tile(self):
        """ Returns position of the flag if we don't have it. If we do have the flag,
            return the position of our home base.
        """
        if self.tank.flag != None:
            x, y = self.tank.start_position
        else:
            self.get_flag() # Ensure that we have initialized it.
            x, y = self.flag.x, self.flag.y
        return Vec2d(int(x), int(y))

    def get_flag(self):
        """ This has to be called to get the flag, since we don't know
            where it is when the Ai object is initialized.
        """
        if self.flag == None:
        # Find the flag in the game objects list
            for obj in self.game_objects_list:
                if isinstance(obj, gameobjects.Flag):
                    self.flag = obj
                    break
        return self.flag

    def get_tile_of_position(self, position_vector):
        """ Converts and returns the float position of our tank to an integer position. """
        x, y = position_vector
        return Vec2d(int(x), int(y))

    def get_tile_neighbors(self, coord_vec, filter_function):
        """ Returns all bordering grid squares of the input coordinate. Depending on the 
            filter_function: A bordering square can be considered accessible if it's a 
            grassbox, woodbox, or a metalbox
        """
        legal_tiles = []
        coord = Vec2d(coord_vec)
        neighbor_tiles = []
        neighbor_positions = [(0,1), (-1,0), (0,-1), (1,0)] # Find the coordinates of the tiles' four neighbors
        for i in neighbor_positions:
            neighbor_tiles.append(coord + i) 
        for n in neighbor_tiles:
            if filter_function(n):
                legal_tiles.append(n)
        return legal_tiles

           
    def filter_grid_neighbors (self, coord):
        """Filters through the neighbors and returns the tiles that the tank can move to. Does not return the metalbox as true."""
        coordinates = coord.int_tuple
        
        if coordinates[0] <= self.MAX_X:  
            if coordinates[0] >= 0:  
                if coordinates[1] <= self.MAX_Y:
                    if coordinates[1] >= 0:
                        if self.currentmap.boxAt(int(coord[0]), int(coord[1])) == 0 or self.currentmap.boxAt(int(coord[0]), int(coord[1])) == 2:
                            return True
        return False
        
    def metalbox_filter_grid_neighbors (self, coord):
        """Filters through the neighbors and returns the tiles that the tank can move to. This filter function returns metalboxes as true."""
        coordinates = coord.int_tuple
        
        if coordinates[0] <= self.MAX_X:  
            if coordinates[0] >= 0:  
                if coordinates[1] <= self.MAX_Y:
                    if coordinates[1] >= 0:
                        if self.currentmap.boxAt(int(coord[0]), int(coord[1])) == 0 or self.currentmap.boxAt(int(coord[0]), int(coord[1])) == 2 or self.currentmap.boxAt(int(coord[0]), int(coord[1])) == 3:
                            return True
        return False

SimpleAi = Ai # Legacy
