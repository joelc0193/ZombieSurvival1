import pygame, sys, time, random, graph
import cPickle as pickle
from pygame.locals import *
from math import *
from copy import deepcopy
import sys
# Used to pickle the graph and dictionary
sys.setrecursionlimit(1000000000)

# frames per second setting
FPS = 30
fpsClock = pygame.time.Clock()

# Set up display area
WIDTH = 1300
HEIGHT = 720
DISPLAYSURF = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Zombie Survival')

# Define colors
BLACK=(0,0,0)
WHITE=(255,255,255)
RED=(255,0,0)
LIME=(0,255,0)
BLUE=(0,0,255)
YELLOW=(255,255,0)
CYAN=(0,255,255)
MAGENTA=(255,0,255)
SILVER=(192,192,192)
GRAY=(128,128,128)
MAROON=(128,0,0)
GREEN=(0,128,0)
PURPLE=(128,0,128)
TEAL=(0,128,128)
NAVY=(0,0,128)

def switched_rooms(thing): # Find if thing switched rooms or not
	if thing.switched_rooms:
		return False
	elif not (thing.current_room.rect.left<=thing.center_xcoord and thing.current_room.rect.right>=thing.center_xcoord and thing.current_room.rect.bottom>=thing.center_ycoord and thing.current_room.rect.top<=thing.center_ycoord):
		return True
	else:
		return False

def switched_areas(thing): # find if thing switched areas or not
	if thing.switched_areas:
		return False
	if thing.current_area!=None:
		if not (thing.current_area.rect.left<=thing.center_xcoord and thing.current_area.rect.right>=thing.center_xcoord and thing.current_area.rect.bottom>=thing.center_ycoord and thing.current_area.rect.top<=thing.center_ycoord):
			return True
		else:
			return False
	else:
		return False

def update_player_location():  # MOves the character
	for event in GameState['events']:
		# Check to see if a key was pressed or released and updates the state of that keypress
		if event.type==KEYUP or event.type==KEYDOWN:
			if event.key==273 or event.key==119:
				if event.type==KEYDOWN:
					character.move_up=True
				else:
					character.move_up=False
			if event.key==274 or event.key==115:
				if event.type==KEYDOWN:
					character.move_down=True
				else:
					character.move_down=False
			if event.key==275 or event.key==100:
				if event.type==KEYDOWN:
					character.move_right=True
				else:
					character.move_right=False
			if event.key==276 or event.key==97:
				if event.type==KEYDOWN:
					character.move_left=True
				else:
					character.move_left=False
	
	# Updates character location based on state of corresponding keys
	walk_x=character.center_xcoord
	walk_y=character.center_ycoord
	if character.move_up==True:
		walk_y-=5
	if character.move_down==True:
		walk_y+=5
	if character.move_right==True:
		walk_x+=5
	if character.move_left==True:
		walk_x-=5

	# If the character is not told to stay in place
	if not (walk_x==character.center_xcoord and walk_y==character.center_ycoord):
		# finds the direction where the character is headed
		character.angle_walk=angle_finder(character.center_xcoord, character.center_ycoord , walk_x, walk_y)
		# finds new x location based on speed of character and angle headed
		character.center_xcoord+=character.speed*cos(character.angle_walk)
		character.walking_rect=pygame.Rect((character.center_xcoord-7.5), character.center_ycoord-7.5, 15, 15)
		# Checks to see if the character's new x location does not cause it to crash a wall
		for wall in current_level.walls:
			# If it crashes a wall, moves back
			if wall.rect.colliderect(character.walking_rect):
				character.center_xcoord-=character.speed*cos(character.angle_walk)
				character.walking_rect=pygame.Rect((character.center_xcoord-7.5), character.center_ycoord-7.5, 15, 15)
		# finds new y location based on speed of character and angle headed
		character.center_ycoord+=character.speed*sin(character.angle_walk)
		character.walking_rect=pygame.Rect((character.center_xcoord-7.5), character.center_ycoord-7.5, 15, 15)
		# checks to see if the character's new y location does not cause it to crash a wall
		for wall in current_level.walls:
			if wall.rect.colliderect(character.walking_rect):
				character.center_ycoord-=character.speed*sin(character.angle_walk)
				character.walking_rect=pygame.Rect((character.center_xcoord-7.5), character.center_ycoord-7.5, 15, 15)
		# Draws the character
	character.center_coords=(character.center_xcoord, character.center_ycoord)
	character.prepare()
	character.draw()

	# checks to see if character switched rooms
	character.switched_rooms=switched_rooms(character)
	# If character switched rooms, find new room
	if character.switched_rooms:
		character.current_room.entities_on.remove(character)
		character.current_room=find_current_location(character.center_coords, current_level.rooms)
		character.current_room.entities_on.add(character)
	# checks to see if character switches areas
	character.switched_areas=switched_areas(character)
	# if character switched area, finds new area
	if character.switched_areas:
		character.current_area.entities_on.remove(character)
		character.current_area=find_current_location(character.center_coords, current_level.areas)	
		character.current_area.entities_on.add(character)

	# finds new angle that character has to in order to be facing the cursor
	character.angle = angle_finder(character.center_xcoord, character.center_ycoord, GameState['xcoord_cursor'], GameState['ycoord_cursor'])

def generate_Zombies(): # calls each spawn object's generate_zombie function
	for zombie_spawn in current_level.zombie_spawns:
		zombie_spawn.generate_Zombie(3)

# updates the zombies's image as it walks
def update_zombie_state_image(zombie):
	now=time.time()
	if (zombie.time_of_last_generated_state==0) or (now-zombie.time_of_last_generated_state>=zombie.update_state_image_delay):
		zombie.time_of_last_generated_state = now # update the time of last zombie update to now
		zombie.current_character_state_number=(zombie.current_character_state_number+1)%8
		zombie.image=zombie.character_states_images['char'+str(zombie.character_series)+'.'+str(zombie.current_character_state_number)] # Find the image stored under the key generateed above
	return zombie.image

def move_zombies():
	# For each area that has at least one zombie on it, finds shortest path from that area to the character's area and gives it to each zombie that's on it
	if character.switched_areas:
		for zombie in GameState['zombies_collection']:
			generated_path=current_level.paths[(zombie.current_area.center_xcoord,zombie.current_area.center_ycoord),(character.current_area.center_xcoord, character.current_area.center_ycoord)][0]
			# If the len of the path is 1, that means that the zombie is on the character's area. else, the zombie goes to the second node because the first is the center of the zombie's current area
			if not len(generated_path)==1:
				zombie.path=generated_path[1::]
				zombie.distance=current_level.paths[(zombie.current_area.center_xcoord,zombie.current_area.center_ycoord),(character.current_area.center_xcoord, character.current_area.center_ycoord)][1]
			else:
				zombie.path=[(character.center_xcoord, character.center_ycoord)]
				zombie.distance=distance(zombie.center_xcoord, zombie.center_ycoord, character.center_xcoord, character.center_ycoord)
	
	# for each zombie...
	for zombie in GameState['zombies_collection']:
		# updates the zombie path so that tha last coordinate is the character's coordinates
		zombie.update_path()
		zombie.following_path=True
		# update direction that zombie should face
		zombie.angle=angle_finder(zombie.center_xcoord, zombie.center_ycoord , zombie.path[0][0], zombie.path[0][1])
		# draw the zombie
		zombie.prepare()
		zombie.draw()

		# If zombie has reached the node that he was walking towards, and that node is not the character's location, deletes that node and zombie keeps going with journey
		if zombie.center_coords==zombie.path[0]:
			if not len(zombie.path)==1:
				del zombie.path[0]

		# find future zombie location coordinates
		distanc=distance(zombie.center_xcoord+zombie.speed*cos(zombie.angle), zombie.center_ycoord+zombie.speed*sin(zombie.angle), zombie.path[0][0], zombie.path[0][1])
		if distanc<=zombie.speed:
			zombie.center_xcoord=zombie.path[0][0]
			zombie.center_ycoord=zombie.path[0][1]
		else:
			zombie.center_xcoord+=zombie.speed*cos(zombie.angle)
			zombie.center_ycoord+=zombie.speed*sin(zombie.angle)

		zombie.center_coords=(zombie.center_xcoord, zombie.center_ycoord)
		# rotate zombie so that he faces node that he is walking towards
		zombie.rotated_image = rotate_image(zombie, 'zombie')

		# find if zombie switched rooms and area
		zombie.switched_rooms=switched_rooms(zombie)
		zombie.switched_areas=switched_areas(zombie)
		# if zombie switched rooms, find new room
		if zombie.switched_rooms:
			zombie.current_room.entities_on.remove(zombie)
			zombie.current_room=find_current_location(zombie.center_coords, current_level.rooms)
			zombie.current_room.entities_on.add(zombie)
		# if zombie switched area, find new area
		if zombie.switched_areas:
			zombie.current_area.entities_on.remove(zombie)
			zombie.current_area=find_current_location(zombie.center_coords, current_level.areas)
			zombie.current_area.entities_on.add(zombie)
		# find the distance between the character and the zombie
		zombie.distance=distance(zombie.center_xcoord, zombie.center_ycoord, character.center_xcoord, character.center_ycoord)

def new_cursor_location():
	for event in GameState['events']:
		if event.type==MOUSEMOTION:  # If mouse was moves, updates cursor's location
			GameState['xcoord_cursor'] = event.pos[0]
			GameState['ycoord_cursor'] = event.pos[1]
		# If mouse button was clicked, sets flag so that generate_function knows to keep generating bullets
		if event.type==MOUSEBUTTONDOWN:
			GameState['MouseButtonDown']=True
			generate_projectiles()
		elif event.type==MOUSEBUTTONUP: # If mouse button was released, sets flag so that no more projectiles are produced
			GameState['MouseButtonDown']=False
		if event.type==QUIT or (event.type==KEYDOWN and event.key==27):  # If close window or esc button was pressed, stops game
			pygame.quit()
			sys.exit()

def generate_projectiles(): # generates projectile
	if GameState['MouseButtonDown']==True: # If button is still clicked keeps track of the time when it was clicked
		now=time.time()
		if GameState['projectile_last_time']==0: # If this was the first click...
			GameState['projectile_last_time']=now
			bullet = Projectile(GameState['ProjColor'], character.center_xcoord+(10)*cos(character.angle), character.center_ycoord+(10)*sin((character.angle)), GameState['ProjRadius'], character.angle, GameState['ProjSpeed'], 1, 1) # Creates a projectile object
			bullet.current_area=find_current_location(bullet.center_coords, current_level.areas)
			bullet.current_area.entities_on.add(bullet)
		elif (now-GameState['projectile_last_time']>GameState['Bullet_Delay']): # If this was not the first click...
			total_number=int((now-GameState['projectile_last_time'])/GameState['Bullet_Delay'])
			for bullet_number in range(1,total_number+1):
				bullet = Projectile(GameState['ProjColor'], character.center_xcoord+(10)*cos(character.angle), character.center_ycoord+(10)*sin((character.angle)), GameState['ProjRadius'], character.angle, GameState['ProjSpeed'], bullet_number, total_number) # Creates a projectile object
				bullet.current_area=find_current_location(bullet.center_coords, current_level.areas)
				bullet.current_area.entities_on.add(bullet)
			GameState['projectile_last_time']=now
	if GameState['MouseButtonDown']==False: # If button is not clicked...
		GameState['projectile_last_time']=0

def update_projectile_locations(): # updates the bullets
	for bullet in GameState['projectiles']: # For each projectile
		# If projectile is not out of bounds
		if (bullet.center_xcoord <= WIDTH and bullet.center_xcoord >=0) and (bullet.center_ycoord <= HEIGHT and bullet.center_ycoord >=0): 
			# updates the new coordinates based on angle of direction and draws onto DISPLAYSURF
			bullet.prepare()
			zombies_hit=pygame.sprite.spritecollide(bullet.wall_check, GameState['zombies_collection'], False, pygame.sprite.collide_mask)
			for zombie in zombies_hit:
				zombie.was_hit(bullet)
				bullet.hit(zombie)
				if zombie.health<=0:
					zombie.kill()
				if bullet.penetration<=0:
					bullet.remove=True
					break
			wall_hit=pygame.sprite.spritecollide(bullet.wall_check, current_level.walls, False, pygame.sprite.collide_mask)
			if not wall_hit:
				bullet.draw()
				bullet.center_xcoord+=(bullet.speed*((bullet.bullet_number/bullet.total_number)))*cos(bullet.angle)
				bullet.center_ycoord+=(bullet.speed*((bullet.bullet_number/bullet.total_number)))*sin(bullet.angle)
				bullet.bullet_number=1
				bullet.total_number=1
				bullet.center_coords=(bullet.center_xcoord, bullet.center_ycoord)
				
				bullet.switched_areas=switched_areas(bullet)
				if bullet.switched_areas:
					bullet.current_area=find_current_location((bullet.center_xcoord, bullet.center_ycoord), current_level.areas)
			else:
				bullet.remove=True

		else:
			bullet.remove=True

	GameState['projectiles'].update()

def update_character_state(): # updates the character state image and rotates it
	now=time.time()
	if character.move_up == False and character.move_down == False and character.move_left == False and character.move_right == False:
		character.time_of_last_generated_state = 0
		character.current_character_state_number=2
	# if this is the first character state or if enough time has passed since last character state
	elif (character.time_of_last_generated_state==0) or (now-character.time_of_last_generated_state>=character.update_state_image_delay):
		character.time_of_last_generated_state = now # update the time of last character update to now
		character.current_character_state_number=(character.current_character_state_number+1)%8
	# Rotates character
	character.rotated_image = rotate_image(character, 'character')
	# Draws character
	character.image=character.character_states_images['char'+str(character.character_series)+'.'+str(character.current_character_state_number)] # Find the image stored under the key generateed above

def rotate_image(thing,string): # rotates images
	if string=='character' or string=='zombie':
		location = thing.center_coords 
		rotated_sprite = pygame.transform.rotate(thing.image, -degrees(thing.angle))
		thing.rect=rotated_sprite.get_rect()
		thing.rect.center = thing.center_coords
		return rotated_sprite
	elif string=='bullet':
		loc = thing.image.get_rect().center  #rot_image is not defined 
		rot_sprite = pygame.transform.rotate(thing.image, -degrees(thing.angle))
		rot_sprite.get_rect().center = loc
		return rot_sprite
	elif string=='wall_check':
		loc = thing.image.get_rect().center  #rot_image is not defined 
		rot_sprite = pygame.transform.rotate(thing.image, -degrees(thing.angle+(3.14159/2)))
		return rot_sprite

def angle_finder(x1,y1,rotate_to_x2,rotate_to_y2): # finds angkes
	return atan2((rotate_to_y2-y1),(rotate_to_x2-x1))

def find_current_location(coords, locations): # finds current location
	for location in locations:
		if location.rect.collidepoint(coords[0], coords[1]):
			return location
 	closest_location=None
 	distanc=0
 	for location in locations:
 		d=distance(coords[0], coords[1], location.center_xcoord, location.center_ycoord)
 		if d<distance:
 			distanc=d
 			closest_location=location
 	return closest_location

def distance(x1, y1, x2, y2): # finds distance between two things
    return sqrt((x1 - x2)**2 + (y1 - y2)**2)
    pass

def draw_game(args):
	DISPLAYSURF.fill(BLACK)
	DISPLAYSURF.blit(current_level.image, (current_level.xcoord,current_level.ycoord)) # Load map image
	if args[0]==1:
		for room in current_level.rooms:
			room.draw()
	if args[1]:
		for wall in current_level.walls:
			wall.draw()	
	if args[2]:
		for area in current_level.areas:
			area.draw()
	if args[3]:
	 	for node in current_level.nodes:
	 		pygame.draw.circle(DISPLAYSURF, GREEN, node, 4)

GameState={
'zombies_collection':pygame.sprite.Group(),
# All nodes locations
'graph_level_nodes_list':[(200,200)],
'room_coordinates_list': [(0,0),(200,0),(400,0)],
'current_level_areas':[(0,0),(100,0),(0,100),(100,100)],
'character_switched_rooms':True,
# Initial directions to move character in
'Up':False,
'Down':False,
'Left':False,
'Right':False,
# Projectile Information
'ProjRadius':3,
'ProjColor':BLACK,
'ProjSpeed':15,
'Bullet_Delay': 1,
# Keep track of direction of bullet
'xcoord_cursor':0,
'ycoord_cursor':0,
'MouseButtonDown':False,
# Projectiles to keep track of
'projectiles':pygame.sprite.Group(),
# Keep track of time in between bullets fired
'projectile_last_time':0,
'now':0,
# Character States
'char1.1':pygame.image.load('Characters/char1.1.png'),
'char1.2':pygame.image.load('Characters/char1.2.png'),
'char1.3':pygame.image.load('Characters/char1.3.png'),
'char1.4':pygame.image.load('Characters/char1.4.png'),
'char1.5':pygame.image.load('Characters/char1.5.png'),
'char1.6':pygame.image.load('Characters/char1.6.png'),
'char1.7':pygame.image.load('Characters/char1.7.png'),
'char1.0':pygame.image.load('Characters/char1.0.png'),
'currentchar':1,
'currentcharState':0,
'char_last_time':0,
'currentcharImage':pygame.image.load('Characters/char1.2.png'),
# Angle between cursor and character
'angle':0,
'x_image_center':0,
'y_image_center':0,
'zombie_delay':1,
'colors':[BLACK, WHITE, RED, LIME, BLUE, YELLOW, CYAN, MAGENTA, MAROON, GREEN, PURPLE, TEAL, NAVY],
'whatever':False,
'zombie_speeds':[2, 2, 2],
}

class Level:
	def __init__(self, image, zombie_spawns_coordinates, rooms, areas, coords, walls, nodes):
		self.zombie_cap=20
		self.image=image.convert_alpha()
		self.walls=walls
		self.zombie_spawns=zombie_spawns_coordinates
		self.xcoord=coords[0]
		self.ycoord=coords[1]
		self.nodes=nodes
		for index, spawn_coordinates in enumerate(zombie_spawns_coordinates):
			self.zombie_spawns[index]=Zombie_Spawn(self.zombie_spawns[index][0], self.zombie_spawns[index][1], GameState['zombie_delay'], 1, index)
		self.areas=areas
		for index, area in enumerate(self.areas):
			index_colors=index%len(GameState['colors'])
			self.areas[index]=Area(GameState['colors'][index_colors], area[0][0], area[0][1], area[1][0], area[1][1])
			self.areas[index].prepare()
			self.areas[index].draw()
		self.rooms=rooms
		for index, room in enumerate(self.rooms):
			index_colors=index%len(GameState['colors'])
			self.rooms[index]=Room(GameState['colors'][index_colors], room[0][0], room[0][1], room[1][0], room[1][1], nodes)
			self.rooms[index].prepare()
			self.rooms[index].draw()
		self.obstacles=pygame.sprite.Group()
		for index, wall in enumerate(self.walls):
			index_colors=index%len(GameState['colors'])
			self.walls[index]=Wall(GameState['colors'][index_colors], wall[0][0], wall[0][1], wall[1][0], wall[1][1], self.obstacles)
			self.walls[index].draw()
		self.original_graph=graph.Graph()
		for node in self.nodes:
			self.original_graph.add_vertex(node)
		self.nodes_copy=self.nodes
		## This is used in part to make the graph of the nodes. Uncomment in when working on a new level
		# for index1, node1 in enumerate(self.nodes_copy):
		# 	for index2, node2 in enumerate(self.nodes_copy):
		# 		if node1!=node2:
		# 			DISPLAYSURF.fill(BLACK)
		# 			DISPLAYSURF.blit(self.image, (self.xcoord,self.ycoord))
		# 			for wall in self.walls:
		# 				wall.draw()
		# 			wall_check=Wall_Check(node1, node2, 1)
		#			wall_check.prepare()
		# 			wall_check.draw()
		# 			walls_hit = pygame.sprite.spritecollide(wall_check, self.walls, False, pygame.sprite.collide_mask)
		# 			if not walls_hit:
		# 				distanc=distance(node1[0], node1[1], node2[0], node2[1])
		# 				self.original_graph.add_edge(node1, node2, distanc)

class Wall(pygame.sprite.Sprite):
	def __init__(self, color, x1coord, y1coord, x2coord, y2coord, group):
		pygame.sprite.Sprite.__init__(self, group)
		self.image=pygame.image.load('black_image.png').convert_alpha()
		self.image=pygame.transform.scale(self.image, (x2coord-x1coord,y2coord-y1coord))
		self.x1coord = x1coord
		self.y1coord = y1coord
		self.x2coord = x2coord
		self.y2coord = y2coord
		self.color=color
		self.rect = pygame.Rect(x1coord, y1coord, x2coord-x1coord, y2coord-y1coord)
	def prepare(self):
		self.surface=pygame.Surface((self.x2coord-self.x1coord,self.y2coord-self.y1coord))
		self.mask=pygame.mask.from_surface(self.image)
	def draw(self):
		DISPLAYSURF.blit(self.image, (self.x1coord,self.y1coord))
	def was_hit(self, bullet):
		bullet.penetration=0

class Room:
	def __init__(self, color, x1coord, y1coord, x2coord, y2coord, nodes):
		self.color = color
		self.x1coord = x1coord
		self.y1coord = y1coord
		self.x2coord = x2coord
		self.y2coord = y2coord
		self.color=color
		self.entities_on=pygame.sprite.Group()
		self.rect = pygame.Rect(x1coord, y1coord, x2coord-x1coord, y2coord-y1coord)
		self.entities_on=pygame.sprite.Group()
		self.nodes=[]
		for node in nodes:
			if self.rect.collidepoint(node):
				self.nodes.append(node)
	def prepare(self):
		self.surface=pygame.Surface((abs(self.x2coord-self.x1coord),abs(self.y2coord-self.y1coord)))  # the size of the rect
		self.surface.set_alpha(128)               # alpha level
		self.surface.fill((self.color))           # this fills the entire surface
	def draw(self):
		DISPLAYSURF.blit(self.surface, (self.x1coord,self.y1coord))

class Area:
	def __init__(self, color, x1coord, y1coord, x2coord, y2coord):
		self.color = color
		self.x1coord = x1coord
		self.y1coord = y1coord
		self.x2coord = x2coord
		self.y2coord = y2coord
		self.rect = pygame.Rect(x1coord, y1coord, x2coord-x1coord, y2coord-y1coord)
		self.entities_on=pygame.sprite.Group()
		self.center_xcoord=(self.x1coord+self.x2coord)/2
		self.center_ycoord=(self.y1coord+self.y2coord)/2
		self.path=None
	def prepare(self):
		self.surface=pygame.Surface((abs(self.x2coord-self.x1coord),abs(self.y2coord-self.y1coord)))  # the size of the rect
		self.surface.set_alpha(128)                # alpha level
		self.surface.fill((self.color))           # this fills the entire surface
	def draw(self):
		DISPLAYSURF.blit(self.surface, (self.x1coord,self.y1coord))
	def shortest_path(self, thing):
		self.starting_node=(self.center_xcoord, self.center_ycoord)
		self.ending_node=(thing.current_area.center_xcoord,thing.current_area.center_ycoord)
		self.path=current_level.paths[self.starting_node, self.ending_node]
		
class Character(pygame.sprite.Sprite):
	def __init__(self, xcoord, ycoord, speed, character_series, number_of_character_states):
		pygame.sprite.Sprite.__init__(self)
		self.health=30
		self.speed=5
		self.angle_walk=0
		self.switched_rooms=True
		self.move_up=False
		self.move_down=False
		self.move_left=False
		self.move_right=False
		self.character_series=character_series
		self.number_of_character_states=number_of_character_states
		self.center_xcoord=xcoord
		self.center_ycoord=ycoord
		self.time_of_last_generated_state=0
		self.current_character_state_number=2
		self.image=pygame.image.load('Characters/char1.1.png')
		self.character_states_images={}
		self.current_room=None
		self.rotated_image=None
		self.angle=0
		self.update_state_image_delay=.2
		self.rect = self.image.get_rect(centerx=self.center_xcoord, centery=self.center_ycoord)
		self.current_area=None
		self.switched_areas=True
		self.center_coords=(self.center_xcoord, self.center_ycoord)
		self.walking_rect=pygame.Rect(self.center_coords[0]-7.5, self.center_coords[1]-7.5, 15, 15)
		for state in range(0,self.number_of_character_states):
			self.character_states_images['char'+str(self.character_series)+'.'+str(state)]=pygame.image.load('Characters/char'+str(self.character_series)+'.'+str(state)+'.png')
	def prepare(self):
		update_character_state()
		self.rotated_image=rotate_image(self, 'character')
		self.mask = pygame.mask.from_surface(self.rotated_image,0)
	def draw(self):
		DISPLAYSURF.blit(self.rotated_image, self.rect)

class Projectile(pygame.sprite.Sprite):
	def __init__(self, color, center_xcoord, center_ycoord, radius, angle, ProjSpeed, bullet_number, total_number):
		pygame.sprite.Sprite.__init__(self, GameState['projectiles'])
		self.image=pygame.image.load('Bullets/bullet.png')
		self.width=5
		self.height=5
		self.image=pygame.transform.scale(self.image, (self.width, self.height))
		self.damage=20
		self.color = color
		self.center_xcoord = center_xcoord
		self.center_ycoord = center_ycoord
		self.rect=self.image.get_rect(centerx=self.center_xcoord, centery=self.center_ycoord)
		self.radius = radius
		self.color = color
		self.angle = angle
		self.speed = ProjSpeed
		self.penetration = 10
		self.rect = DISPLAYSURF.blit(self.image, self.rect)
		self.bullet_number=float(bullet_number)
		self.total_number=float(total_number)
		self.current_area=character.current_area
		self.switched_areas=True
		self.image=rotate_image(self, 'bullet')
		self.remove=False
		self.wall_check=None
		self.center_coords=(self.center_xcoord, self.center_ycoord)
	def prepare(self):
		self.wall_check=Wall_Check((self.center_xcoord, self.center_ycoord), (self.center_xcoord+cos(self.angle)*self.speed, self.center_ycoord+sin(self.angle)*self.speed), self.width)
		self.mask = pygame.mask.from_surface(self.image,0)
		self.rect.center=(self.center_xcoord, self.center_ycoord)
		self.wall_check.prepare()
	def draw(self):
		DISPLAYSURF.blit(self.image, self.rect)
	def hit(self, zombie):
		self.penetration-=zombie.penetration
	def update(self):
		if self.remove==True:
			self.kill()

class Zombie_Spawn:
	def __init__(self, xcoord, ycoord, zombie_delay, highest_zombie, spawn_index):
		self.xcoord=xcoord
		self.ycoord=ycoord
		self.zombie_last_time=0
		self.zombie_delay=zombie_delay
		self.highest_zombie=highest_zombie
		self.spawn_index=spawn_index
		self.area=None
	def generate_Zombie(self, highest_zombie):
		# Generates zombies
		now=time.time()
		if (self.zombie_last_time==0) or (now-self.zombie_last_time>self.zombie_delay) and len(GameState['zombies_collection'])<current_level.zombie_cap:
			rand_number=int(random.random()*highest_zombie)
			generated_zombie = Zombie(self.xcoord, self.ycoord, GameState['zombie_speeds'][rand_number], 1, 8, self.spawn_index, self.area)
			generated_zombie.current_room=find_current_location((generated_zombie.center_xcoord, generated_zombie.center_ycoord), current_level.rooms)
			generated_zombie.current_room.entities_on.add(generated_zombie)
			generated_zombie.current_area=find_current_location((generated_zombie.center_xcoord, generated_zombie.center_ycoord), current_level.areas)
			generated_zombie.path=current_level.paths[(generated_zombie.current_area.center_xcoord,generated_zombie.current_area.center_ycoord),(character.current_area.center_xcoord, character.current_area.center_ycoord)][0]
			generated_zombie.distance=current_level.paths[(generated_zombie.current_area.center_xcoord,generated_zombie.current_area.center_ycoord),(character.current_area.center_xcoord, character.current_area.center_ycoord)][1]
			self.zombie_last_time=now
	def find_area(self):
		# Finds the area that the spawn is in
		for area in current_level.areas:
			if self.xcoord>area.x1coord and self.xcoord<area.x2coord and self.ycoord>area.y1coord and self.ycoord<area.y2coord:
				self.area=area
				break

class Zombie(pygame.sprite.Sprite):
	def __init__(self, xcoord, ycoord, speed, character_series, number_of_character_states, spawn_index, area):
		pygame.sprite.Sprite.__init__(self, GameState['zombies_collection'])
		self.speed=4
		width=None
		height=None
		self.center_xcoord = xcoord
		self.center_ycoord = ycoord
		self.rect = pygame.image.load('Characters/char1.2.png').get_rect()
		self.bullets_in=pygame.sprite.Group()
		self.health=100
		self.penetration=5
		self.switched_rooms=True
		self.current_room=None
		self.angle=None
		self.rotated_image=None
		self.time_of_last_generated_state=0
		self.update_state_image_delay=.2
		self.current_character_state_number=2
		self.character_states_images={}
		self.character_series=character_series
		self.number_of_character_states=number_of_character_states
		self.current_area=area
		self.switched_areas=True
		self.spawn_index=spawn_index
		self.path=self.current_area.path
		self.following_path=False
		self.center_coords=(self.center_xcoord, self.center_ycoord)
		self.distance=distance(self.center_xcoord, self.center_ycoord, character.center_xcoord, character.center_ycoord)
		for state in range(0,self.number_of_character_states):
			self.character_states_images['char'+str(self.character_series)+'.'+str(state)]=pygame.image.load('Characters/char'+str(self.character_series)+'.'+str(state)+'.png')
	def prepare(self):
		self.image=update_zombie_state_image(self)
		self.angle=angle_finder(self.center_xcoord, self.center_ycoord , self.path[0][0], self.path[0][1])
		self.rotated_image = rotate_image(self, 'zombie')
		self.rect = self.rotated_image.get_rect(centerx=self.center_xcoord, centery=self.center_ycoord)
		self.mask = pygame.mask.from_surface(self.rotated_image,0)
	def draw(self):
		DISPLAYSURF.blit(self.rotated_image, (self.rect.left, self.rect.top))		
	def was_hit(self, bullet):
		if not self.bullets_in.has(bullet):
			self.bullets_in.add(bullet)
			self.health-=bullet.damage
	def update_path(self):
		if len(self.path)==1:
			self.path=[(character.center_xcoord,character.center_ycoord)]

class Wall_Check:
	def __init__(self, node1, node2, width):
		self.image=pygame.image.load('black_image.png').convert_alpha()
		self.node1=node1
		self.node2=node2
		self.distanc=distance(self.node1[0], self.node1[1], self.node2[0], self.node2[1])
		self.angle=angle=angle_finder(self.node1[0], self.node1[1], self.node2[0], self.node2[1])
		self.width=width
		self.height=abs(node2[1]-node2[1])
		self.image=pygame.transform.scale(self.image, (self.width,int(self.distanc)))
		self.centerx=abs(node1[0]-node2[0])
		self.centery=abs(node1[1]-node2[1])
		self.image=rotate_image(self, 'wall_check')
		self.rect=self.image.get_rect()
		self.xcoord=min([self.node1[0], self.node2[0]])
		self.ycoord=min([self.node1[1], self.node2[1]])
		self.rect=self.image.get_rect(left=self.xcoord, top=self.ycoord)
	def prepare(self):
		self.mask=pygame.mask.from_surface(self.image)
	def draw(self):
		DISPLAYSURF.blit(self.image, (self.rect))

GameState['levels']=[]
rooms=[[(184,98),(620,314)], [(184,314),(620,410)], [(184,410),(430,590)], [(430,410),(557,590)], [(557,410),(814,590)], [(814,410),(975,590)], [(975,345),(1157,590)], [(620,218),(1157,345)], [(620,98),(1157,218)], [(620,345),(975,410)]]
walls=[[(164, 98),(184, 590)], [(164, 590), (568,609)], [(164,78),(1175,98)], [(1155,98),(1175, 609)], [(804,590),(1155,609)], [(965, 335),(1111,353)], [(965,353),(984,545)], [(617,98),(627,317)],[(681,211),(1107,222)], [(235,307),(562,318)],[(184,404),(370,413)],[(425,404),(435,590)],[(549,398),(568,547)],[(568,398),(804,418)],[(804,398),(824,547)], [(558,570),(813,595)]]
nodes=[(231,325),(231,302), (568,325), (568,301),(375,396), (375,420), (441,397), (420,396), (542, 389), (543, 555), (573, 556), (831, 392), (611, 324), (632, 326), (673, 230), (672, 206), (1115, 206), (1114, 228), (959, 327), (796, 557), (827, 560),(959, 551),(1120, 330),(1120, 362), (989,553)]
areas=[[(806, 546), (814, 571)], [(549, 546), (559, 590)], [(559, 546), (568, 570)], [(813, 546), (822, 590)], [(164, 98), (278, 152)], [(278, 98), (392, 152)], [(164, 152), (278, 206)], [(278, 152), (392, 206)], [(392, 98), (506, 152)], [(506, 98), (620, 152)], [(392, 152), (506, 206)], [(506, 152), (620, 206)], [(164, 206), (278, 260)], [(278, 206), (392, 260)], [(164, 260), (278, 314)], [(278, 260), (392, 314)], [(392, 206), (506, 260)], [(506, 206), (620, 260)], [(392, 260), (506, 314)], [(506, 260), (620, 314)], [(184, 314), (238, 337)], [(238, 314), (293, 337)], [(184, 337), (238, 360)], [(238, 337), (293, 360)], [(293, 314), (347, 337)], [(347, 314), (402, 337)], [(293, 337), (347, 360)], [(347, 337), (402, 360)], [(184, 360), (238, 383)], [(238, 360), (293, 383)], [(184, 383), (238, 407)], [(238, 383), (293, 407)], [(293, 360), (347, 383)], [(347, 360), (402, 383)], [(293, 383), (347, 407)], [(347, 383), (402, 407)], [(402, 314), (439, 337)], [(439, 314), (476, 337)], [(402, 337), (439, 360)], [(439, 337), (476, 360)], [(476, 314), (513, 337)], [(513, 314), (551, 337)], [(476, 337), (513, 360)], [(513, 337), (551, 360)], [(402, 360), (439, 383)], [(439, 360), (476, 383)], [(402, 383), (439, 407)], [(439, 383), (476, 407)], [(476, 360), (513, 383)], [(513, 360), (551, 383)], [(476, 383), (513, 407)], [(513, 383), (551, 407)], [(551, 314), (568, 335)], [(568, 314), (585, 335)], [(551, 335), (568, 356)], [(568, 335), (585, 356)], [(585, 314), (602, 335)], [(602, 314), (620, 335)], [(585, 335), (602, 356)], [(602, 335), (620, 356)], [(551, 356), (568, 377)], [(568, 356), (585, 377)], [(551, 377), (568, 399)], [(568, 377), (585, 399)], [(585, 356), (602, 377)], [(602, 356), (620, 377)], [(585, 377), (602, 399)], [(602, 377), (620, 399)], [(184, 411), (245, 455)], [(245, 411), (307, 455)], [(184, 455), (245, 500)], [(245, 455), (307, 500)], [(307, 411), (368, 455)], [(368, 411), (430, 455)], [(307, 455), (368, 500)], [(368, 455), (430, 500)], [(184, 500), (245, 545)], [(245, 500), (307, 545)], [(184, 545), (245, 590)], [(245, 545), (307, 590)], [(307, 500), (368, 545)], [(368, 500), (430, 545)], [(307, 545), (368, 590)], [(368, 545), (430, 590)], [(430, 407), (446, 430)], [(446, 407), (462, 430)], [(430, 430), (446, 453)], [(446, 430), (462, 453)], [(462, 407), (478, 430)], [(478, 407), (494, 430)], [(462, 430), (478, 453)], [(478, 430), (494, 453)], [(430, 453), (446, 476)], [(446, 453), (462, 476)], [(430, 476), (446, 500)], [(446, 476), (462, 500)], [(462, 453), (478, 476)], [(478, 453), (494, 476)], [(462, 476), (478, 500)], [(478, 476), (494, 500)], [(430, 500), (446, 522)], [(446, 500), (462, 522)], [(430, 522), (446, 545)], [(446, 522), (462, 545)], [(462, 500), (478, 522)], [(478, 500), (494, 522)], [(462, 522), (478, 545)], [(478, 522), (494, 545)], [(430, 545), (446, 567)], [(446, 545), (462, 567)], [(430, 567), (446, 590)], [(446, 567), (462, 590)], [(462, 545), (478, 567)], [(478, 545), (494, 567)], [(462, 567), (478, 590)], [(478, 567), (494, 590)], [(494, 407), (508, 430)], [(508, 407), (522, 430)], [(494, 430), (508, 453)], [(508, 430), (522, 453)], [(522, 407), (536, 430)], [(536, 407), (550, 430)], [(522, 430), (536, 453)], [(536, 430), (550, 453)], [(494, 453), (508, 476)], [(508, 453), (522, 476)], [(494, 476), (508, 500)], [(508, 476), (522, 500)], [(522, 453), (536, 476)], [(536, 453), (550, 476)], [(522, 476), (536, 500)], [(536, 476), (550, 500)], [(494, 500), (508, 522)], [(508, 500), (522, 522)], [(494, 522), (508, 545)], [(508, 522), (522, 545)], [(522, 500), (536, 522)], [(536, 500), (550, 522)], [(522, 522), (536, 545)], [(536, 522), (550, 545)], [(494, 545), (508, 567)], [(508, 545), (522, 567)], [(494, 567), (508, 590)], [(508, 567), (522, 590)], [(522, 545), (536, 567)], [(536, 545), (550, 567)], [(522, 567), (536, 590)], [(536, 567), (550, 590)], [(568, 417), (597, 437)], [(597, 417), (627, 437)], [(568, 437), (597, 458)], [(597, 437), (627, 458)], [(627, 417), (656, 437)], [(656, 417), (686, 437)], [(627, 437), (656, 458)], [(656, 437), (686, 458)], [(568, 458), (597, 479)], [(597, 458), (627, 479)], [(568, 479), (597, 500)], [(597, 479), (627, 500)], [(627, 458), (656, 479)], [(656, 458), (686, 479)], [(627, 479), (656, 500)], [(656, 479), (686, 500)], [(686, 417), (716, 437)], [(716, 417), (746, 437)], [(686, 437), (716, 458)], [(716, 437), (746, 458)], [(746, 417), (776, 437)], [(776, 417), (806, 437)], [(746, 437), (776, 458)], [(776, 437), (806, 458)], [(686, 458), (716, 479)], [(716, 458), (746, 479)], [(686, 479), (716, 500)], [(716, 479), (746, 500)], [(746, 458), (776, 479)], [(776, 458), (806, 479)], [(746, 479), (776, 500)], [(776, 479), (806, 500)], [(568, 500), (597, 517)], [(597, 500), (627, 517)], [(568, 517), (597, 535)], [(597, 517), (627, 535)], [(627, 500), (656, 517)], [(656, 500), (686, 517)], [(627, 517), (656, 535)], [(656, 517), (686, 535)], [(568, 535), (597, 553)], [(597, 535), (627, 553)], [(568, 553), (597, 571)], [(597, 553), (627, 571)], [(627, 535), (656, 553)], [(656, 535), (686, 553)], [(627, 553), (656, 571)], [(656, 553), (686, 571)], [(686, 500), (716, 517)], [(716, 500), (746, 517)], [(686, 517), (716, 535)], [(716, 517), (746, 535)], [(746, 500), (776, 517)], [(776, 500), (806, 517)], [(746, 517), (776, 535)], [(776, 517), (806, 535)], [(686, 535), (716, 553)], [(716, 535), (746, 553)], [(686, 553), (716, 571)], [(716, 553), (746, 571)], [(746, 535), (776, 553)], [(776, 535), (806, 553)], [(746, 553), (776, 571)], [(776, 553), (806, 571)], [(369, 407), (383, 408)], [(383, 407), (397, 408)], [(369, 408), (383, 410)], [(383, 408), (397, 410)], [(397, 407), (411, 408)], [(411, 407), (426, 408)], [(397, 408), (411, 410)], [(411, 408), (426, 410)], [(369, 410), (383, 412)], [(383, 410), (397, 412)], [(369, 412), (383, 414)], [(383, 412), (397, 414)], [(397, 410), (411, 412)], [(411, 410), (426, 412)], [(397, 412), (411, 414)], [(411, 412), (426, 414)], [(822, 400), (858, 447)], [(858, 400), (894, 447)], [(822, 447), (858, 495)], [(858, 447), (894, 495)], [(894, 400), (930, 447)], [(930, 400), (966, 447)], [(894, 447), (930, 495)], [(930, 447), (966, 495)], [(822, 495), (858, 542)], [(858, 495), (894, 542)], [(822, 542), (858, 590)], [(858, 542), (894, 590)], [(894, 495), (930, 542)], [(930, 495), (966, 542)], [(894, 542), (930, 590)], [(930, 542), (966, 590)], [(966, 544), (969, 555)], [(969, 544), (973, 555)], [(966, 555), (969, 567)], [(969, 555), (973, 567)], [(973, 544), (977, 555)], [(977, 544), (981, 555)], [(973, 555), (977, 567)], [(977, 555), (981, 567)], [(966, 567), (969, 578)], [(969, 567), (973, 578)], [(966, 578), (969, 590)], [(969, 578), (973, 590)], [(973, 567), (977, 578)], [(977, 567), (981, 578)], [(973, 578), (977, 590)], [(977, 578), (981, 590)], [(981, 353), (1002, 381)], [(1002, 353), (1023, 381)], [(981, 381), (1002, 410)], [(1002, 381), (1023, 410)], [(1023, 353), (1044, 381)], [(1044, 353), (1066, 381)], [(1023, 381), (1044, 410)], [(1044, 381), (1066, 410)], [(981, 410), (1002, 439)], [(1002, 410), (1023, 439)], [(981, 439), (1002, 468)], [(1002, 439), (1023, 468)], [(1023, 410), (1044, 439)], [(1044, 410), (1066, 439)], [(1023, 439), (1044, 468)], [(1044, 439), (1066, 468)], [(1066, 353), (1088, 381)], [(1088, 353), (1111, 381)], [(1066, 381), (1088, 410)], [(1088, 381), (1111, 410)], [(1111, 353), (1134, 381)], [(1134, 353), (1157, 381)], [(1111, 381), (1134, 410)], [(1134, 381), (1157, 410)], [(1066, 410), (1088, 439)], [(1088, 410), (1111, 439)], [(1066, 439), (1088, 468)], [(1088, 439), (1111, 468)], [(1111, 410), (1134, 439)], [(1134, 410), (1157, 439)], [(1111, 439), (1134, 468)], [(1134, 439), (1157, 468)], [(981, 468), (1002, 498)], [(1002, 468), (1023, 498)], [(981, 498), (1002, 529)], [(1002, 498), (1023, 529)], [(1023, 468), (1044, 498)], [(1044, 468), (1066, 498)], [(1023, 498), (1044, 529)], [(1044, 498), (1066, 529)], [(981, 529), (1002, 559)], [(1002, 529), (1023, 559)], [(981, 559), (1002, 590)], [(1002, 559), (1023, 590)], [(1023, 529), (1044, 559)], [(1044, 529), (1066, 559)], [(1023, 559), (1044, 590)], [(1044, 559), (1066, 590)], [(1066, 468), (1088, 498)], [(1088, 468), (1111, 498)], [(1066, 498), (1088, 529)], [(1088, 498), (1111, 529)], [(1111, 468), (1134, 498)], [(1134, 468), (1157, 498)], [(1111, 498), (1134, 529)], [(1134, 498), (1157, 529)], [(1066, 529), (1088, 559)], [(1088, 529), (1111, 559)], [(1066, 559), (1088, 590)], [(1088, 559), (1111, 590)], [(1111, 529), (1134, 559)], [(1134, 529), (1157, 559)], [(1111, 559), (1134, 590)], [(1134, 559), (1157, 590)], [(620, 218), (664, 249)], [(664, 218), (709, 249)], [(620, 249), (664, 281)], [(664, 249), (709, 281)], [(709, 218), (754, 249)], [(754, 218), (799, 249)], [(709, 249), (754, 281)], [(754, 249), (799, 281)], [(620, 281), (664, 313)], [(664, 281), (709, 313)], [(620, 313), (664, 345)], [(664, 313), (709, 345)], [(709, 281), (754, 313)], [(754, 281), (799, 313)], [(709, 313), (754, 345)], [(754, 313), (799, 345)], [(799, 218), (843, 247)], [(843, 218), (888, 247)], [(799, 247), (843, 277)], [(843, 247), (888, 277)], [(888, 218), (933, 247)], [(933, 218), (978, 247)], [(888, 247), (933, 277)], [(933, 247), (978, 277)], [(799, 277), (843, 307)], [(843, 277), (888, 307)], [(799, 307), (843, 337)], [(843, 307), (888, 337)], [(888, 277), (933, 307)], [(933, 277), (978, 307)], [(888, 307), (933, 337)], [(933, 307), (978, 337)], [(799, 337), (840, 339)], [(840, 337), (882, 339)], [(799, 339), (840, 341)], [(840, 339), (882, 341)], [(882, 337), (924, 339)], [(924, 337), (966, 339)], [(882, 339), (924, 341)], [(924, 339), (966, 341)], [(799, 341), (840, 343)], [(840, 341), (882, 343)], [(799, 343), (840, 345)], [(840, 343), (882, 345)], [(882, 341), (924, 343)], [(924, 341), (966, 343)], [(882, 343), (924, 345)], [(924, 343), (966, 345)], [(978, 218), (1022, 247)], [(1022, 218), (1067, 247)], [(978, 247), (1022, 277)], [(1022, 247), (1067, 277)], [(1067, 218), (1112, 247)], [(1112, 218), (1157, 247)], [(1067, 247), (1112, 277)], [(1112, 247), (1157, 277)], [(978, 277), (1022, 307)], [(1022, 277), (1067, 307)], [(978, 307), (1022, 337)], [(1022, 307), (1067, 337)], [(1067, 277), (1112, 307)], [(1112, 277), (1157, 307)], [(1067, 307), (1112, 337)], [(1112, 307), (1157, 337)], [(1108, 337), (1120, 341)], [(1120, 337), (1132, 341)], [(1108, 341), (1120, 345)], [(1120, 341), (1132, 345)], [(1132, 337), (1144, 341)], [(1144, 337), (1157, 341)], [(1132, 341), (1144, 345)], [(1144, 341), (1157, 345)], [(1108, 345), (1120, 349)], [(1120, 345), (1132, 349)], [(1108, 349), (1120, 353)], [(1120, 349), (1132, 353)], [(1132, 345), (1144, 349)], [(1144, 345), (1157, 349)], [(1132, 349), (1144, 353)], [(1144, 349), (1157, 353)], [(620, 98), (664, 128)], [(664, 98), (709, 128)], [(620, 128), (664, 158)], [(664, 128), (709, 158)], [(709, 98), (754, 128)], [(754, 98), (799, 128)], [(709, 128), (754, 158)], [(754, 128), (799, 158)], [(620, 158), (664, 188)], [(664, 158), (709, 188)], [(620, 188), (664, 218)], [(664, 188), (709, 218)], [(709, 158), (754, 188)], [(754, 158), (799, 188)], [(709, 188), (754, 218)], [(754, 188), (799, 218)], [(799, 98), (843, 128)], [(843, 98), (888, 128)], [(799, 128), (843, 158)], [(843, 128), (888, 158)], [(888, 98), (933, 128)], [(933, 98), (978, 128)], [(888, 128), (933, 158)], [(933, 128), (978, 158)], [(799, 158), (843, 188)], [(843, 158), (888, 188)], [(799, 188), (843, 218)], [(843, 188), (888, 218)], [(888, 158), (933, 188)], [(933, 158), (978, 188)], [(888, 188), (933, 218)], [(933, 188), (978, 218)], [(978, 98), (1022, 128)], [(1022, 98), (1067, 128)], [(978, 128), (1022, 158)], [(1022, 128), (1067, 158)], [(1067, 98), (1112, 128)], [(1112, 98), (1157, 128)], [(1067, 128), (1112, 158)], [(1112, 128), (1157, 158)], [(978, 158), (1022, 188)], [(1022, 158), (1067, 188)], [(978, 188), (1022, 218)], [(1022, 188), (1067, 218)], [(1067, 158), (1112, 188)], [(1112, 158), (1157, 188)], [(1067, 188), (1112, 218)], [(1112, 188), (1157, 218)], [(620, 345), (664, 358)], [(664, 345), (709, 358)], [(620, 358), (664, 372)], [(664, 358), (709, 372)], [(709, 345), (753, 358)], [(753, 345), (798, 358)], [(709, 358), (753, 372)], [(753, 358), (798, 372)], [(620, 372), (664, 386)], [(664, 372), (709, 386)], [(620, 386), (664, 400)], [(664, 386), (709, 400)], [(709, 372), (753, 386)], [(753, 372), (798, 386)], [(709, 386), (753, 400)], [(753, 386), (798, 400)], [(798, 345), (840, 358)], [(840, 345), (882, 358)], [(798, 358), (840, 372)], [(840, 358), (882, 372)], [(882, 345), (924, 358)], [(924, 345), (966, 358)], [(882, 358), (924, 372)], [(924, 358), (966, 372)], [(798, 372), (840, 386)], [(840, 372), (882, 386)], [(798, 386), (840, 400)], [(840, 386), (882, 400)], [(882, 372), (924, 386)], [(924, 372), (966, 386)], [(882, 386), (924, 400)], [(924, 386), (966, 400)]]

level_1=Level(pygame.image.load('Maps/map1.png'), [(200,200)], rooms, areas, (-370,-200), walls, nodes)
GameState['levels'].append(level_1)

current_level=GameState['levels'][0]
for zombie_spawn in current_level.zombie_spawns:
	zombie_spawn.find_area()

character = Character(250, 350, 3, '1', 8)
character.current_room=find_current_location((character.center_xcoord, character.center_ycoord), current_level.rooms)
character.current_area=find_current_location((character.center_xcoord, character.center_ycoord), current_level.areas)

# g=deepcopy(current_level.original_graph)

# for area in current_level.areas:
# 	node=(area.center_xcoord,area.center_ycoord)
# 	g.add_vertex((area.center_xcoord,area.center_ycoord))

# a=0
# b=g.num_vertices**2
# for node1 in g:
# 	for node2 in g:
# 		starting_node=node1.id
# 		ending_node=node2.id
# 		if not (round(ending_node[0]),round(ending_node[1]))==(round(starting_node[0]), round(starting_node[1])):
# 			wall_check=Wall_Check((round(starting_node[0]), round(starting_node[1])), (round(ending_node[0]),round(ending_node[1])), 1)
# 			walls_hit = pygame.sprite.spritecollide(wall_check, current_level.walls, False, pygame.sprite.collide_mask)
# 			if not walls_hit:
# 				distanc=distance(starting_node[0], starting_node[1], ending_node[0], ending_node[1])
# 				g.add_edge(starting_node, ending_node, distanc)
# 		print a,b
# 		a+=1

# current_level.graph=g
# current_level.original_graph=g

# with open('level_1_graph.pkl', 'wb') as output:
#     pickle.dump(g, output, pickle.HIGHEST_PROTOCOL)

with open('level_1_graph.pkl', 'rb') as input:
    current_level.graph = pickle.load(input)

with open('level_1_graph.pkl', 'rb') as input:
    current_level.original_graph = pickle.load(input)

# paths={}

# i=0
# a=0
# b=current_level.graph.num_vertices**2
# for node1 in current_level.graph:
# 	current_level.graph=deepcopy(current_level.original_graph)
# 	for node2 in current_level.graph:
# 		starting_node=node1.id
# 		ending_node=node2.id
# 		graph.dijkstra(current_level.graph, current_level.graph.get_vertex(starting_node), current_level.graph.get_vertex(ending_node))
# 		target = current_level.graph.get_vertex(ending_node)
# 		path = [target.get_id()]
# 		graph.shortest(target, path)
# 		path = path[::-1]
# 		paths[starting_node, ending_node]=path
# 		a+=1
# 		print a, b

# with open('level_1_paths.pkl', 'wb') as output:
#     pickle.dump(paths, output, pickle.HIGHEST_PROTOCOL)

# with open('level_1_paths.pkl', 'rb') as input:
#     current_level.paths = pickle.load(input)

# for key in current_level.paths:
# 	total_d=0
# 	for i in range(0, len(current_level.paths[key])-1):
# 		total_d+=distance(current_level.paths[key][i][0], current_level.paths[key][i][1], current_level.paths[key][i+1][0], current_level.paths[key][i+1][1])
# 	current_level.paths[key]=[current_level.paths[key], total_d]

# with open('level_1_paths.pkl', 'wb') as output:
#     pickle.dump(current_level.paths, output, pickle.HIGHEST_PROTOCOL)

with open('level_1_paths.pkl', 'rb') as input:
    current_level.paths = pickle.load(input)

# i=0
# for area in current_level.areas:
# 	area.shortest_path(character)
# 	i, len(current_level.areas)
# 	i+=1

# for area in current_level.areas:
# 	area.surface=None
# 	area.mask=None

# with open('level_1_areas.pkl', 'wb') as output:
#     pickle.dump(current_level.areas, output, pickle.HIGHEST_PROTOCOL)

with open('level_1_areas.pkl', 'rb') as input:
    current_level.areas = pickle.load(input)

current_level=GameState['levels'][0]

for area in current_level.areas:
	area.prepare()
for room in current_level.rooms:
	room.prepare()
for wall in current_level.rooms:
	room.prepare()

for index in range(0,len(current_level.areas)):
	current_level.nodes.append((current_level.areas[index].center_xcoord,current_level.areas[index].center_ycoord))

def main():
	pygame.init()
	global fpsClock, DISPLAYSURF, GameState, character, current_level
	# Game
	while True:
		GameState['whatever']=True
		# Draws the game. (rooms, walls, areas, nodes)
		draw_game([0, 0, 0,0])
		# Gets all the events
		GameState['events']=pygame.event.get()
		# Moves and draws player
		update_player_location()
		# Makes bullets based on time of click and time elapsed between last time click was checked and now
		generate_projectiles()
		# Updates each bullet's location and draws it on DISPLAYSURF
		update_projectile_locations()
		# Calls the generate function of each spawn location
		generate_Zombies()
		# Moves Zombies
		move_zombies()
		# Determines the location of cursor and if quit game
		new_cursor_location()
		# updates game window with final DISPLAYSURF
		pygame.display.update()
		# Waits a certin amount of time before starting loop again
		fpsClock.tick(FPS)

if __name__ =="__main__":
	main()