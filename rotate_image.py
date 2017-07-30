import pygame, time
from pygame.locals import *

SIZE = 640, 480
pygame.init()
screen = pygame.display.set_mode(SIZE)
done = False
image = pygame.image.load('Characters/char1.1.png').convert_alpha()
rect=image.get_rect()

i=0
while not done:
	i+=1
	screen.fill((0, 255, 255))
	rotated_image = pygame.transform.rotate(image, i)
	rect=rotated_image.get_rect()
	rect.center=(100,100)
	pygame.draw.rect(screen, (255,255,255), rect)
	screen.blit(rotated_image, rect)
	pygame.draw.circle(screen, (0,0,255), rect.center, 2)
	pygame.display.update()
	time.sleep(.01)
	
	for e in pygame.event.get():
		if e.type == QUIT or (e.type == KEYDOWN and e.key == K_ESCAPE):
			done = True
			break    