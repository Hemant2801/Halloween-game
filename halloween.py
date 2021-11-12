import pygame
from pygame import mixer
import os
import random
import csv

mixer.init()
pygame.init()

SCREEN_WIDTH = 800
SCREEN_HEIGHT = int(SCREEN_WIDTH*0.8)

SCREEN = pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT))
pygame.display.set_caption('HALLOWEEN GAME')

#SET FRAME RATE
clock = pygame.time.Clock()
FPS = 60

#GAME VARIABLES
GRAVITY = 1
SCROLL_THRESHOLD = 200
ROWS = 16
COLUMNS = 150
TILE_SIZE = SCREEN_HEIGHT // ROWS
TILE_TYPES = os.listdir('sprites/tiles')
MAX_LEVEL = 3
screen_scroll = 0
bg_scroll = 0
level = 1
start_game = False
start_intro = False

#PLAYER ACTION VARIALES
run = True
moving_left = False
moving_right = False
shoot = False
throw = False
grenade_thrown = False

#DEFINE COLOUR
BG = (144,201,120)
RED = (255, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
BLACK =(0, 0, 0)
PINK = (235, 65, 54)

#LOADING MUSIC
pygame.mixer.music.load('audio/audio_music2.mp3')
pygame.mixer.music.set_volume(0.6)
pygame.mixer.music.play(-1, 0.0, 5000)# LOOP, BREAK, FADE
jump_snd = pygame.mixer.Sound('audio/audio_jump.wav')
jump_snd.set_volume(0.5)
shot_snd = pygame.mixer.Sound('audio/audio_shot.wav')
shot_snd.set_volume(0.5)
grenade_snd = pygame.mixer.Sound('audio/audio_thunder.wav')
grenade_snd.set_volume(0.3)
water_snd = pygame.mixer.Sound('audio/audio_water.wav')
water_snd.set_volume(0.5)


#LOADING IMAGES
#BUTTON
start_img = pygame.image.load('sprites/button/start_btn.png').convert_alpha()
restart_img = pygame.image.load('sprites/button/restart_btn.png').convert_alpha()
exit_img = pygame.image.load('sprites/button/exit_btn.png').convert_alpha()
#BACKGROUND
pine1_img = pygame.image.load('sprites/background/pine1.png').convert_alpha()
pine2_img = pygame.image.load('sprites/background/pine2.png').convert_alpha()
mountain_img = pygame.image.load('sprites/background/mountain.png').convert_alpha()
sky_img = pygame.image.load('sprites/background/sky_cloud.png').convert_alpha()

#TILE LIST LOADING
tile_list = []
for i in range(len(TILE_TYPES)):
    img = pygame.image.load(f'sprites/tiles/{i}.png')
    img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE)).convert_alpha()
    tile_list.append(img)
bullet_img = pygame.image.load('sprites/icons/slash.png').convert_alpha()
grenade_img = pygame.image.load('sprites/icons/grenade.png').convert_alpha()
health_box_img = pygame.image.load('sprites/icons/health_box.png').convert_alpha()
ammo_box_img = pygame.image.load('sprites/icons/ammo_box.png').convert_alpha()
grenade_box_img = pygame.image.load('sprites/icons/grenade_box.png').convert_alpha()

font = pygame.font.SysFont('Futura', 30)
def draw_text(text, font, text_col, x, y):
    img = font.render(text, True, text_col)
    SCREEN.blit(img, (x,y))

def background_colour(BG):
    SCREEN.fill(BG)
    width = sky_img.get_width()
    #pygame.draw.line(SCREEN, RED, (0,300),(SCREEN_WIDTH,300))
    for x in range(5):
        SCREEN.blit(sky_img, ((x * width) - bg_scroll * 0.3, 0))
        SCREEN.blit(mountain_img, ((x * width)  - bg_scroll * 0.4, SCREEN_HEIGHT - mountain_img.get_height() - 300))
        SCREEN.blit(pine1_img, ((x * width)  - bg_scroll * 0.5, SCREEN_HEIGHT - pine1_img.get_height() - 150))
        SCREEN.blit(pine2_img, ((x * width)  - bg_scroll * 0.7, SCREEN_HEIGHT - pine2_img.get_height()))

#RESET_WORLD
def reset_level():
    enemy_group.empty()
    bullet_group.empty()
    grenade_group.empty()
    item_box_group.empty()
    explosion_group.empty()
    decoration_group.empty()
    water_group.empty()
    exit_group.empty()
    
    #RESET THE WORLD LEVEL
    data = []
    for row in range(ROWS):
        r = [-1] * COLUMNS
        data.append(r)
        
    return data


item_boxes = {
    'Health' : health_box_img,
    'Ammo' : ammo_box_img,
    'Grenade' : grenade_box_img
}

class Button():
	def __init__(self,x, y, image, scale):
		width = image.get_width()
		height = image.get_height()
		self.image = pygame.transform.scale(image, (int(width * scale), int(height * scale)))
		self.rect = self.image.get_rect()
		self.rect.topleft = (x, y)
		self.clicked = False

	def draw(self, surface):
		action = False

		#get mouse position
		pos = pygame.mouse.get_pos()

		#check mouseover and clicked conditions
		if self.rect.collidepoint(pos):
			if pygame.mouse.get_pressed()[0] == 1 and self.clicked == False:
				action = True
				self.clicked = True

		if pygame.mouse.get_pressed()[0] == 0:
			self.clicked = False

		#draw button
		surface.blit(self.image, (self.rect.x, self.rect.y))

		return action

class Character(pygame.sprite.Sprite):
    def __init__(self, char_type, x, y, scale, speed, ammo, grenades):
        pygame.sprite.Sprite.__init__(self)
        
        self.alive = True
        self.char_type = char_type
        self.health = 100
        self.max_health = self.health
        self.speed = speed
        self.skill_cooldown = 0
        self.ammo = ammo
        self.start_ammo = ammo
        #self.attack = False
        self.grenades = grenades
        self.direction = 1
        self.vel_y = 0
        self.jump = False
        self.in_air = True
        self.flip = False
        self.animation_list = []
        self.frame_index = 0
        self.action = 0
        self.update_time = pygame.time.get_ticks()
        #AI SPECIFIC COUNTER
        self.vision = pygame.Rect(0, 0, 150, 20)
        self.move_counter = 0
        self.idling = False
        self.idling_counter = 0
        self.score = 0
        if char_type == 'wizard':
            self.health = 200
        
        #LOADING THE ANIMATIONS
        animation_list = ['idle', 'run', 'jump', 'death', 'attack']
        for animation in animation_list:
            #RESET TEMPORARY LIST
            temp_list = []
            #CHECKS THE MO. OF IMAGES IN A FOLDER
            no_of_frames = len(os.listdir(f'sprites/{self.char_type}/{animation}'))
            for i in range(no_of_frames):
                player_char = pygame.image.load(f'sprites/{self.char_type}/{animation}/{i}.png').convert_alpha()
                char = pygame.transform.scale(player_char,(int(player_char.get_width() * scale), int(player_char.get_height() * scale)))
                temp_list.append(char)
            self.animation_list.append(temp_list)
            
        self.img = self.animation_list[self.action][self.frame_index]
        self.rect = self.img.get_rect() #creates a rectangular box around the character to control it.
        self.rect.center = (x,y)
        self.width = self.img.get_width()
        self.height = self.img.get_height()
        
    def update(self):
        self.update_animation()
        self.death()
        #COOLDOWN UPDATE
        if self.skill_cooldown > 0:
            self.skill_cooldown -= 1
    
    def move(self, move_left, move_right):
        #RESET MOVEMENT VARIABLES
        screen_scroll = 0
        dx = 0
        dy = 0
        
        #MOVES THE CHARACTER LEFT AND RIGHT
        if move_left:
            dx = -self.speed
            self.flip = True
            self.direction = -1
        if move_right:
            dx = self.speed
            self.flip = False
            self.direction = 1
            
        #JUMP
        if self.jump == True and self.in_air == False:
            self.vel_y = -15
            self.jump = False
            self.in_air = True
        
        #APPLY GRAVITY
        self.vel_y += GRAVITY
        if self.vel_y > 10:
            self.vel_y
        dy += self.vel_y
        
        #COLLISION CHECKING
        for tile in world.obstacle_list:
            #COLLISIN CHECK IN X DIRECTION
            if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                dx = 0
                #CHECK IF ENEMY HAS COLLIDED WITH A WALL
                if self.char_type == 'reaper' or self.char_type == 'skeleton' or self.char_type == 'wizard':
                    self.direction *= -1
                    self.move_counter = 0
            #CHECK COLLISION IN Y DIRECTION
            if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                #CHECK IF BELOW THE GROUND
                if self.vel_y < 0:
                    self.vel_y = 0
                    self.in_air = False
                    dy = tile[1].bottom - self.rect.top
                #CHECK IF ABOVE THE GROUND
                elif self.vel_y >= 0:
                    self.vel_y = 0
                    self.in_air = False
                    dy = tile[1].top - self.rect.bottom
                    
        #CHECK FOR COLLISION IN WATER
        health = True
        if pygame.sprite.spritecollide(self, water_group, False):
            self.health = 0
            #health
            
        #CHECK COLLISION WITH EXIT
        level_complete = False
        if pygame.sprite.spritecollide(self, exit_group, False):
            level_complete = True
                
            
        #CHECK IF PLAYER HAS FALL OF THE MAP
        if self.rect.bottom > SCREEN_HEIGHT:
            self.health = 0
        
        if self.char_type == 'player':
            if self.rect.left + dx < 0 or self.rect.right + dx > SCREEN_WIDTH:
                dx = 0
        
        #UPDATES RECTANGLE POSITION
        self.rect.x += dx
        self.rect.y += dy
        
        #UPDATE SCROLL BASED ON PLAYERS POSITION
        if self.char_type == 'player':
            if (self.rect.right > SCREEN_WIDTH - SCROLL_THRESHOLD and bg_scroll < (world.level_length * TILE_SIZE) - SCREEN_WIDTH) or (self.rect.left < SCROLL_THRESHOLD and screen_scroll > abs(dx)):
                self.rect.x -= dx
                screen_scroll = -dx
        
        return screen_scroll, level_complete
        
    def shoot(self):
        if self.skill_cooldown == 0 and self.ammo > 0:
            self.skill_cooldown = 85
            if self.char_type == 'player':
                self.skill_cooldown = 45
            bullet = Bullet(self.rect.centerx + (0.75 * self.rect.size[0] * self.direction), self.rect.centery, self.direction, self.flip)
            bullet_group.add(bullet)
            self.ammo -= 1
            shot_snd.play()
        
    def ai(self):
        if self.alive and player.alive:
            if self.idling == False and random.randint(1, 200) == 1:
                self.update_action(0)#0 : IDLE
                self.idling = True
                self.idling_counter = 50
            #CHECK IF PLAYER IS IN RANGE OF THE AI
            if self.vision.colliderect(player.rect):
                #STOPS RUNNING AND FACE THE PLAYER
                self.update_action(4)#4 : attack
                #SHOOT
                self.shoot()
            else:
                if self.idling == False:
                    if self.direction == 1:
                        ai_moving_right = True
                    else:
                        ai_moving_right = False
                    ai_moving_left = not ai_moving_right
                    self.move(ai_moving_left, ai_moving_right)
                    self.update_action(1)#1 : RUN
                    self.move_counter += 1
                    #UPDATE AI VISION AS THE ENEMY MOVES
                    self.vision.center = (self.rect.centerx + 75 * self.direction, self.rect.centery)
                    # pygame.draw.rect(SCREEN, RED, self.vision)
                    
                    if self.move_counter > TILE_SIZE:
                        self.direction *= -1
                        self.move_counter *= -1
                else:
                    self.idling_counter -= 1
                    if self.idling_counter <= 0:
                        self.idling = False
                
        self.rect.x += screen_scroll
    
    def update_animation(self):
        #UPDATE ANIMATION
        animation_colldown = 100
        #UPDATE IMAGE
        self.img = self.animation_list[self.action][self.frame_index]
        #CHECKS THE TIME PASSED FROM THE LAST UPDATE
        if pygame.time.get_ticks() - self.update_time > animation_colldown:
            self.update_time = pygame.time.get_ticks()
            self.frame_index += 1
        #CHECKS THE LENGTH OF ANIMATION LIST
        if self.frame_index >= len(self.animation_list[self.action]):
            if self.action == 3:
                self.frame_index = len(self.animation_list[self.action]) - 1
            else:
                self.frame_index = 0
            
    def update_action(self, new_action):
        #CHECKS FWHATHER THE ACTION IS DIFFERENT FORM THE PREVIOUS ACTION
        if new_action != self.action:
            self.action = new_action
            #UPDATING THE ANIMATION SETTING
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()
    
    def death(self):
        if self.health <= 0:
                self.health = 0
                self.speed = 0
                self.alive = False
                self.update_action(3)
            
    def draw(self):
        SCREEN.blit(pygame.transform.flip(self.img, self.flip , False ), self.rect) # (what and where)

class World():
    def __init__(self):
        self.obstacle_list = []
        
    def process_data(self, data):
        self.level_length = len(data[0])
        #ITERATE THROUGH DATA FILE TO PROCESS DATA
        for y, row in enumerate(data):
            for x, tile in enumerate(row):
                if tile >= 0:
                    img = tile_list[tile]
                    img_rect = img.get_rect()
                    img_rect.x = x * TILE_SIZE
                    img_rect.y = y * TILE_SIZE
                    tile_data = (img, img_rect)
                    
                    if tile >= 0 and tile <= 8:
                        self.obstacle_list.append(tile_data)
                    elif tile >= 9 and tile <= 10:
                        water = Water(img, x * TILE_SIZE, y * TILE_SIZE)
                        water_group.add(water)
                    elif tile >= 11 and tile <= 14:
                        decoration = Decoration(img, x * TILE_SIZE, y * TILE_SIZE)
                        decoration_group.add(decoration)
                    elif tile == 15: #CREATE PLAYER
                        player = Character('player', x * TILE_SIZE, y * TILE_SIZE, 1.25, 5, 20, 5)
                        health_bar = HealthBar(10,10, player.health, player.health)
                    elif tile == 16: #CREATE ENEMIES
                        enemy1 = Character('reaper', x * TILE_SIZE, y * TILE_SIZE, 1.25, 3, 50, 0)
                        enemy_group.add(enemy1)
                    elif tile == 17: #AMMO BOX
                        item_box = ItemRefill('Ammo', x * TILE_SIZE, y * TILE_SIZE)
                        item_box_group.add(item_box)
                    elif tile == 18: #GRENADE BOX
                        item_box = ItemRefill('Grenade', x * TILE_SIZE, y * TILE_SIZE)
                        item_box_group.add(item_box)
                    elif tile == 19: #HEALTHBOX
                        item_box = ItemRefill('Health', x * TILE_SIZE, y * TILE_SIZE)
                        item_box_group.add(item_box)
                    elif tile == 20: #CREATE EXIT
                        img = pygame.transform.scale(img, (130, 240)).convert_alpha()
                        exit = Exit(img, x * TILE_SIZE, y * TILE_SIZE)
                        exit_group.add(exit)
                    elif tile == 21: #CREATE ENEMIES
                        enemy1 = Character('ghost', x * TILE_SIZE, y * TILE_SIZE, 1, 3, 50, 0)
                        enemy_group.add(enemy1)
                    elif tile == 22: #CREATE ENEMIES
                        enemy2 = Character('wizard', x * TILE_SIZE, y * TILE_SIZE, 1.20, 3, 250, 0)
                        enemy_group.add(enemy2)
                    
        return player, health_bar
    
    def draw(self):
        for tile in self.obstacle_list:
            tile[1][0] += screen_scroll
            SCREEN.blit(tile[0], tile[1])
    
class Decoration(pygame.sprite.Sprite):
    def __init__(self, img, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))
    
    def update(self):
        self.rect.x += screen_scroll
    
class Water(pygame.sprite.Sprite):
    def __init__(self, img, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))
        
    def update(self):
        self.rect.x += screen_scroll
    
class Exit(pygame.sprite.Sprite):
    def __init__(self, img, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height() + 20))
    
    def update(self):
        self.rect.x += screen_scroll
    
class ItemRefill(pygame.sprite.Sprite):
    def __init__(self, item_type, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.item_type = item_type
        self.image = item_boxes[self.item_type]
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2 , y + (TILE_SIZE - self.image.get_height()))
        
    def update(self):
        #SCROLL
        self.rect.x += screen_scroll
        #CHECKING FOR COLLLISION WITH THE PLAYER
        if pygame.sprite.collide_rect(self,player):
            #CHECK FOR THE ITEM BOX PICKED
            if self.item_type == 'Health':
                player.health += 25
                if player.health > player.max_health:
                    player.health = player.max_health
            elif self.item_type == 'Ammo':
                player.ammo += 15
            elif self.item_type == 'Grenade':
                player.grenades += 7
            #DELETE THE ITEM BOX
            self.kill()
    
class HealthBar():
    def __init__(self, x, y, health, max_health):
        self.x = x
        self.y = y
        self.health = health
        self.max_health = max_health
        
    def draw(self, health):
        #CHANGING THE hEALTH
        self.health = health
        #CALCULATE HEALTH
        ratio = self.health / self.max_health
        pygame.draw.rect(SCREEN, BLACK, (self.x - 2, self.y -2, 154, 24))
        pygame.draw.rect(SCREEN, RED, (self.x, self.y, 150, 20))
        pygame.draw.rect(SCREEN, GREEN, (self.x, self.y, 150 * ratio, 20))

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, direction, flip):
        pygame.sprite.Sprite.__init__(self)
        self.speed = 10
        self.flip = flip
        self.direction = direction 
        self.image = pygame.transform.flip(bullet_img, self.flip, False)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        
    def update(self):
        self.rect.x += (self.direction * self.speed) +screen_scroll
        
        #CHECKS IF BULLT HAS LEFT THE SCREEN
        if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
            self.kill()
        #CHECK FOR COLLISION WITH LEVEL
        for tile in world.obstacle_list:
            if tile[1].colliderect(self.rect):
                self.kill()
        #CHECKS BULLET COLLISION
        if pygame.sprite.spritecollide(player, bullet_group, False):
            if player.alive:
                player.health -= 5
                self.kill()
        for enemy in enemy_group:
            if pygame.sprite.spritecollide(enemy, bullet_group, False):
                if enemy.alive:
                    enemy.health -= 20
                    #print(enemy.health)
                    self.kill()
                
class Grenade(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        pygame.sprite.Sprite.__init__(self)
        self.timer = 100
        self.vel_y = -11
        self.speed = 8
        self.image = grenade_img
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.direction = direction
        
    def update(self):
        self.vel_y += GRAVITY
        dx = self.direction * self.speed
        dy = self.vel_y
        
        #CHECK FOR COLLISION WITH LEVEL
        for tile in world.obstacle_list:
            #CHECKS IF GRENADE HAS STRUCK THE WALL
            if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                self.direction *= -1
                dx = self.direction * self.speed
            #CHECK COLLISION IN Y DIRECTION
            if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                self.speed = 0
                #CHECK IF BELOW THE GROUND (THROWN UPWARD)
                if self.vel_y < 0:
                    self.vel_y = 0
                    dy = tile[1].bottom - self.rect.top
                #CHECK IF ABOVE THE GROUND (FALLLING)
                elif self.vel_y >= 0:
                    self.vel_y = 0
                    dy = tile[1].top - self.rect.bottom
        
        
        #UPDATE GRENADE POSITION
        self.rect.x += dx + screen_scroll
        self.rect.y += dy
        
        #COUNTDOWN TIMER
        self.timer -= 1
        if self.timer <= 0:
            self.kill()
            grenade_snd.play()
            explosion = Explosion(self.rect.x, self.rect.y, 0.7)
            explosion_group.add(explosion)
            #EXPLOSION DAMAGE TO ANYONE
            if abs(self.rect.centerx - player.rect.centerx) < TILE_SIZE * 2 and abs(self.rect.centery - player.rect.centery) < TILE_SIZE * 2:
                player.health -= 50
            for enemy in enemy_group:
                if abs(self.rect.centerx - enemy.rect.centerx) < TILE_SIZE * 2 and abs(self.rect.centery - enemy.rect.centery) < TILE_SIZE * 2:
                    enemy.health -= 50
            
        
class Explosion(pygame.sprite.Sprite):
    def __init__(self, x, y, scale):
        pygame.sprite.Sprite.__init__(self)
        self.images =[]
        path = 'sprites/explosion'
        for num in range(1 , len(os.listdir(path))):
            img = pygame.image.load(f'{path}/{num}.png').convert_alpha()
            img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
            self.images.append(img)
        self.frame_index = 0
        self.image = self.images[self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.counter = 0
        
    def update(self):
        #SCROLL
        self.rect.x += screen_scroll
        explosion_speed = 4
        
        #UPDATE EXPLOSION
        self.counter += 1
        if self.counter >= explosion_speed:
            self.counter = 0
            self.frame_index += 1
            #IF EXPLOSION IS COMPLETE THAN DELETE IT AND RESET THE INDEX
            if self.frame_index >= len(self.images):
                self.kill()
            else:
                self.image = self.images[self.frame_index]

class ScreenFade():
    def __init__(self, direction, colour, speed):
        self.direction = direction
        self.colour = colour
        self.speed = speed
        self.fade_counter = 0
        
    def fade(self):
        fade_complete = False
        self.fade_counter += self.speed
        
        if self.direction == 1:#WHOLE SCREEN FADES
            pygame.draw.rect(SCREEN, self.colour, (0 - self.fade_counter, 0, SCREEN_WIDTH // 2, SCREEN_HEIGHT))
            pygame.draw.rect(SCREEN, self.colour, (SCREEN_WIDTH // 2 + self.fade_counter, 0, SCREEN_WIDTH, SCREEN_HEIGHT))
            pygame.draw.rect(SCREEN, self.colour, (0 , 0 - self.fade_counter, SCREEN_WIDTH, SCREEN_HEIGHT // 2))
            pygame.draw.rect(SCREEN, self.colour, (0 , SCREEN_HEIGHT // 2 + self.fade_counter, SCREEN_WIDTH, SCREEN_HEIGHT))
        if self.direction == 2:# VERTICAL SCREEN FADE
            pygame.draw.rect(SCREEN, self.colour, (0, 0, SCREEN_WIDTH, 0 + self.fade_counter))
        if self.fade_counter >= SCREEN_WIDTH:
            fade_complete = True
        
        return fade_complete
        
#CRETAE BG FADE
intro_fade = ScreenFade(1, BLACK, 4)
death_fade = ScreenFade(2, PINK, 4)

#CREATE BUTTON
start_button = Button(SCREEN_WIDTH // 2 - 130, SCREEN_HEIGHT // 2 - 150, start_img, 1)
restart_button = Button(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 50, restart_img, 2)
exit_button = Button(SCREEN_WIDTH // 2 - 110, SCREEN_HEIGHT // 2 + 50, exit_img, 1)

#CREATE SPRITES GROUP
enemy_group = pygame.sprite.Group()
bullet_group = pygame.sprite.Group()
grenade_group = pygame.sprite.Group()
explosion_group = pygame.sprite.Group()
item_box_group = pygame.sprite.Group()
water_group = pygame.sprite.Group()
decoration_group = pygame.sprite.Group()
exit_group = pygame.sprite.Group()

#CREATE EMPTY TILE LIST
world_data = []
for row in range(ROWS):
    r = [-1] * COLUMNS
    world_data.append(r)

with open(f'sprites/world_level/level{level}_data.csv', newline = '') as csvfile:
    df = csv.reader(csvfile, delimiter = ',')
    for x, row in enumerate(df):
        for y, tile in enumerate(row):
            world_data[x][y] = int(tile)
world = World()
player, health_bar = world.process_data(world_data)

while run:
    
    clock.tick(FPS)
    
    if start_game == False:
        #MAIN MENU
        SCREEN.fill(BG)
        #ADD BUTTON
        if start_button.draw(SCREEN):
            start_game = True
            start_intro = True
        if exit_button.draw(SCREEN):
            run = False
    
    else:
        #DRAW BACKGROUND
        background_colour(BG)
        #DRAW WORLD MAP
        world.draw()
        #SHOW HEALTH
        health_bar.draw(player.health)
        #SHOW AMMO
        draw_text(f'SHOT :', font, WHITE , 10, 40)
        for x in range(player.ammo):
            SCREEN.blit(bullet_img, (90 + x*10, 45))
        #SHOW GRENADES
        draw_text(f'GRENADE :', font, WHITE , 10, 65)
        for x in range(player.grenades):
            SCREEN.blit(grenade_img, (135 + x*16, 67))
        
        player.update()
        player.draw()
        
        for enemy in enemy_group:
            enemy.ai()
            enemy.update()
            enemy.draw()
            
        #UPDATE AND DRAW GROUPS
        bullet_group.update()
        grenade_group.update()
        explosion_group.update()
        item_box_group.update()
        water_group.update()
        decoration_group.update()
        exit_group.update()
        
        bullet_group.draw(SCREEN)
        grenade_group.draw(SCREEN)
        explosion_group.draw(SCREEN)
        item_box_group.draw(SCREEN)
        water_group.draw(SCREEN)
        decoration_group.draw(SCREEN)
        exit_group.draw(SCREEN)
        
        #SHOW INTRO
        if start_intro == True:
            if intro_fade.fade():
                start_intro = False
                intro_fade.fade_counter = 0
        
        #UPDATE PLAYER ACTIONS
        if player.alive:
            #SHOOTS BULLETS
            if shoot:
                player.shoot()
            #THROW GRENADES
            elif throw and grenade_thrown == False and player.grenades > 0:
                throw = Grenade(player.rect.centerx + (0.5 * player.rect.size[0] * player.direction), player.rect.top, player.direction)
                grenade_group.add(throw)
                player.grenades -= 1
                grenade_thrown = True 
                
            #PLAYER ACTIONS
            if player.in_air:
                player.update_action(2) #2 : jump
            elif shoot:
                player.update_action(4) #4 : attack
            elif moving_left or moving_right:
                player.update_action(1) #1 : run
            else:
                player.update_action(0) #0 : idle
            screen_scroll, level_complete = player.move(moving_left, moving_right)
            bg_scroll -= screen_scroll
            
            #CHECK IF PLAYER HAS COMPLETED THE LEVEL
            if  level_complete:
                start_intro = True
                level += 1
                bg_scroll = 0
                world_data = reset_level()
                if level <= MAX_LEVEL:
                    with open(f'sprites/world_level/level{level}_data.csv', newline = '') as csvfile:
                        df = csv.reader(csvfile, delimiter = ',')
                        for x, row in enumerate(df):
                            for y, tile in enumerate(row):
                                world_data[x][y] = int(tile)
                    world = World()
                    player, health_bar = world.process_data(world_data)
            
        else:
            screen_scroll = 0
            if death_fade.fade():
                if restart_button.draw(SCREEN):
                    death_fade.fade_counter = 0
                    start_intro = True
                    bg_scroll = 0
                    world_data = reset_level()
                    with open(f'sprites/world_level/level{level}_data.csv', newline = '') as csvfile:
                        df = csv.reader(csvfile, delimiter = ',')
                        for x, row in enumerate(df):
                            for y, tile in enumerate(row):
                                world_data[x][y] = int(tile)
                    world = World()
                    player, health_bar = world.process_data(world_data)
            
            
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
            
        #MOVEMENT OF THE CHARACTER
        if event.type == pygame.KEYDOWN:
            if (event.key == pygame.K_a) or (event.key == pygame.K_LEFT):
                moving_left = True
            if (event.key == pygame.K_d) or (event.key == pygame.K_RIGHT):
                moving_right = True
            if event.key == pygame.K_SPACE:
                shoot = True
            if event.key == pygame.K_q:
                throw = True
            if ((event.key == pygame.K_w) or (event.key == pygame.K_UP)) and player.alive :
                player.jump = True
                jump_snd.play()
            if event.key == pygame.K_ESCAPE:
                run = False
            
        if event.type == pygame.KEYUP:
            if (event.key == pygame.K_a) or (event.key == pygame.K_LEFT):
                moving_left = False
            if (event.key == pygame.K_d) or (event.key == pygame.K_RIGHT):
                moving_right = False
            if event.key == pygame.K_SPACE:
                shoot = False
            if event.key == pygame.K_q:
                throw = False
                grenade_thrown = False
    
    
    
    pygame.display.update()
    
pygame.quit()