import pygame
import sys
import os
import random
import math
from pygame.locals import *
import serial
import time 
from pynput.keyboard import Key, Controller 
import threading
import re
from fourFlexors_WV import FourFlexorsControl

# Initialize Pygame
pygame.init()
SerialObject = serial.Serial('COM4', 9600)
SerialObject.timeout = 1
keyboard = Controller()



# Resource loading functions
def load_image_convert_alpha(filename):
    """Load an image with the given filename from the images directory"""
    return pygame.image.load(os.path.join('images', filename)).convert_alpha()

def load_sound(filename):
    """Load a sound with the given filename from the sounds directory"""
    return pygame.mixer.Sound(os.path.join('sounds', filename))

# Game constants
FPS = 60
SCREEN_WIDTH = 700
SCREEN_HEIGHT = 500
SPEED = 1.5
SCORE = 0
LIVES = 3

# Colors
BLUE = (0, 0, 205)
YELLOW = (255, 255, 102)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)

# Fonts
font = pygame.font.SysFont("lucidaconsole", 60)
font_mid = pygame.font.SysFont("lucidaconsole", 35)
font_small = pygame.font.SysFont("lucidaconsole", 25)
font_medium = pygame.font.SysFont("Arial", 30, bold=True) 
game_over_text = font.render("Game Over", True, WHITE)

# Initialize display
DISPLAYSURF = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("The Best Asteroid Game Ever")

# Load resources
background = load_image_convert_alpha('starry_night.jpg')
shoot_sound = load_sound('fire.wav')
explosion_sound = load_sound('die.wav')
pygame.mixer.music.load(os.path.join('sounds', 'soundtrack.wav'))
pygame.mixer.music.set_volume(0.3)

# Game states
START_SCREEN, PLAYING, GAME_OVER = range(3)
current_state = START_SCREEN

class Missile(pygame.sprite.Sprite):
    """Missile class with directional movement"""
    def __init__(self, position, angle):
        super().__init__()
        self.original_image = load_image_convert_alpha('missile.png')
        self.angle = angle
        self.image = pygame.transform.rotate(self.original_image, self.angle)
        self.rect = self.image.get_rect(center=position)
        self.speed = 15
        self.direction = [
            math.sin(-math.radians(self.angle)),
            -math.cos(math.radians(self.angle))
        ]

    def update(self):
        """Update missile position based on direction"""
        self.rect.x += self.direction[0] * self.speed
        self.rect.y += self.direction[1] * self.speed
        if self.rect.bottom < 0 or self.rect.top > SCREEN_HEIGHT:
            self.kill()

class Enemy_vert(pygame.sprite.Sprite):
    def __init__(self, size="big"):
        super().__init__()
        # Load size-specific image
        if size in {"big", "normal", "small"}:
            self.image = load_image_convert_alpha(f"asteroid-{size}.png")
        else:
            self.image = load_image_convert_alpha("asteroid-big.png")
        self.size = size
        
        # Initialize movement properties
        self.rect = self.image.get_rect()
        self.reset_position()
        self.speed = SPEED

    def reset_position(self):
        """Reset to top with random x position"""
        self.rect.center = (random.randint(40, SCREEN_WIDTH-40), 0)

    def update(self):
        self.rect.move_ip(0, self.speed)
        if self.rect.top > SCREEN_HEIGHT:
            self.reset_position()
            global SCORE
            SCORE += 1

class Enemy_hor(pygame.sprite.Sprite):
    def __init__(self, size="big"):
        super().__init__()
        # Load size-specific image
        if size in {"big", "normal", "small"}:
            self.image = load_image_convert_alpha(f"asteroid-{size}.png")
        else:
            self.image = load_image_convert_alpha("asteroid-big.png")
        self.size = size
        
        # Initialize movement properties
        self.rect = self.image.get_rect()
        self.reset_position()
        self.speed = SPEED

    def reset_position(self):
        """Reset to left with random y position"""
        self.rect.center = (0, random.randint(40, SCREEN_HEIGHT-40))

    def update(self):
        self.rect.move_ip(self.speed, 0)
        if self.rect.left > SCREEN_WIDTH:
            self.reset_position()
            global SCORE
            SCORE += 1

class Enemy_vert(Enemy_vert):
    def split(self):
        """Split into smaller vertical asteroids"""
        if self.size == "big":
            return [Enemy_vert(size="normal") for _ in range(2)]
        elif self.size == "normal":
            return [Enemy_vert(size="small") for _ in range(2)]
        return []

class Enemy_hor(Enemy_hor):
    def split(self):
        """Split into smaller horizontal asteroids"""
        if self.size == "big":
            return [Enemy_hor(size="normal") for _ in range(2)]
        elif self.size == "normal":
            return [Enemy_hor(size="small") for _ in range(2)]
        return []

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = load_image_convert_alpha("ufo.png")
        self.rect = self.image.get_rect(center=(340, 260))
        self.speed = 5 
        self.missiles = pygame.sprite.Group()

    def move(self, pressed_keys):
        if pressed_keys[K_UP] and self.rect.top > 0:
            self.rect.move_ip(0, -self.speed)
        if pressed_keys[K_DOWN] and self.rect.bottom < SCREEN_HEIGHT:
            self.rect.move_ip(0, self.speed)
        if pressed_keys[K_LEFT] and self.rect.left > 0:
            self.rect.move_ip(-self.speed, 0)
        if pressed_keys[K_RIGHT] and self.rect.right < SCREEN_WIDTH:
            self.rect.move_ip(self.speed, 0)

    def shoot(self):
        """Create missile with correct firing position"""
        # Calculate firing position offset
        angle_rad = math.radians(self.angle)
        offset_x = math.sin(-angle_rad) * self.rect.width/2
        offset_y = -math.cos(angle_rad) * self.rect.height/2
        
        # Create missile and add to groups
        missile = Missile(
            (self.rect.centerx + offset_x, self.rect.centery + offset_y),
            self.angle
        )
        self.missiles.add(missile)
        all_sprites.add(missile)
        shoot_sound.play()

    def update(self):
        self.missiles.update()

def show_start_screen():
    title = font.render("Asteroid Blaster", True, WHITE)
    instruction = font_small.render("Press SPACE to Start", True, YELLOW)
    DISPLAYSURF.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 150))
    DISPLAYSURF.blit(instruction, (SCREEN_WIDTH//2 - instruction.get_width()//2, 300))

def show_calibration_screen(): 
    title = font.render("Brace Calibration", True, WHITE)
    instruction = font_small.render("Press SPACE to Return to Start Screen", True, YELLOW)


def reset_game():
    global SCORE, LIVES, current_state
    SCORE = 0
    LIVES = 3
    current_state = PLAYING
    P1.rect.center = (340, 260)
    P1.angle = 0
    enemies.empty()
    all_sprites.empty()
    enemies.add(E1, E2)
    all_sprites.add(P1, E1, E2)
    pygame.mixer.music.play(-1)

# Initialize game objects
P1 = Player()
E1 = Enemy_vert('big')
E2 = Enemy_hor('big')

enemies = pygame.sprite.Group(E1, E2)
all_sprites = pygame.sprite.Group(P1, E1, E2)

INC_SPEED = pygame.USEREVENT + 1
pygame.time.set_timer(INC_SPEED, 1000)

flexStateUp = 700
flexStateDown = 800
flexStateLeft = 600
flexStateRight = 850

# Function to take potentiometer value from Arduino 
def process_serial_input():
    global flexStateUp, flexStateDown, flexStateLeft, flexStateRight
    print("Starting to read data from Arduino")
    while True: 
        if SerialObject.in_waiting >0:

            ReceivedString = SerialObject.readline().decode('utf-8').strip()

            if not ReceivedString:  # Check if the received string is empty
                print("Warning: Empty data received from Arduino")
                continue  # Skip this iteration

            print(f"Received Switch State: {ReceivedString}")

            # Use regex to extract numbers from the string
            match = re.findall(r'flexVal\d+: (\d+)', ReceivedString)

            if not match or len(match) < 2:  # Ensure correct format
                print(f"Warning: Unexpected data format received: '{ReceivedString}'")
                continue  # Skip this iteration

            try:
                # Convert extracted values to integers
                flexVal1 = int(match[0])
                flexVal2 = int(match[1])
                flexVal3 = int(match[2])
                flexVal4 = int(match[3])

               #print(f"Updated Flex Sensor Up: {flexVal1}, Flex Sensor down: {flexVal2}")

            except ValueError:
                print(f"Error: Unable to convert '{match}' to integers")
                continue  # Skip if conversion fails

            except serial.SerialException as e:
                print(f"Serial Error: {e}")
            except Exception as e:
                print(f"Unexpected Error: {e}")

            flexStateUp = flexVal1
            flexStateDown = flexVal2
            flexStateLeft = flexVal3
            flexStateRight = flexVal4

        time.sleep(0.01)

# Start serial processing in a new thread
serial_thread = threading.Thread(target=process_serial_input, daemon=True)
serial_thread.start()


# Main game loop
while True:
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
        if event.type == KEYDOWN:
            if current_state == START_SCREEN and event.key == K_SPACE:
                reset_game()
            elif current_state == PLAYING and event.key == K_SPACE:
                P1.shoot()
        if event.type == INC_SPEED and current_state == PLAYING:
            SPEED += 0.1

    # Use the latest flex sensor values to simulate key presses
    if flexStateUp < 700:
      #  print("Up Arrow Key Released")
       # print("Flex state up: ", flexStateUp)
        keyboard.release(Key.up)

    elif flexStateUp > 700:
        #print("Up Arrow Key Pressed")
      #  print("Flex state up: ", flexStateUp)
        keyboard.press(Key.up)
    
    if flexStateDown < 800:
     #   print("Down Arrow Key Released")
     #   print("Flex state Down: ", flexStateDown)
        keyboard.release(Key.down)

    elif flexStateDown > 800:
     #   print("Down Arrow Key Pressed")
     #   print("Flex state down: ", flexStateDown)
        keyboard.press(Key.down)

    if flexStateLeft < 600:
     #   print("Left Arrow Key Released")
     #   print("Flex state left: ", flexStateLeft)
        keyboard.release(Key.left)

    elif flexStateLeft > 600:
     #   print("Left Arrow Key Pressed")
     #   print("Flex state left: ", flexStateLeft)
        keyboard.press(Key.left)

    if flexStateRight < 850:
     #   print("Right Arrow Key Released")
     #   print("Flex state right: ", flexStateRight)
        keyboard.release(Key.right)

    elif flexStateRight > 850:
     #   print("Right Arrow Key Pressed")
     #   print("Flex state right: ", flexStateRight)
        keyboard.press(Key.right)


    DISPLAYSURF.blit(background, (0, 0))
    
    if current_state == START_SCREEN:
        show_start_screen()
    elif current_state == PLAYING:
        pressed_keys = pygame.key.get_pressed()
        P1.move(pressed_keys)
        all_sprites.update()

        # Missile collision detection
        for missile in P1.missiles:
            hits = pygame.sprite.spritecollide(missile, enemies, False)
            if hits:
                missile.kill()
                explosion_sound.play()
                for enemy in hits:
                    enemies.remove(enemy)
                    all_sprites.remove(enemy)
                    
                    new_enemies = enemy.split()
                    for new_enemy in new_enemies:
                        new_enemy.speed = enemy.speed * 1.2
                        enemies.add(new_enemy)
                        all_sprites.add(new_enemy)
                    
                    SCORE += {"big":20, "normal":50, "small":100}[enemy.size]

        # Player collision detection
        if pygame.sprite.spritecollideany(P1, enemies):
            explosion_sound.play()
            LIVES -= 1
            if LIVES <= 0:
                current_state = GAME_OVER
                pygame.mixer.music.stop()
            else:
                P1.rect.center = (340, 260)
                enemies.empty()
                enemies.add(Enemy_vert('big'), Enemy_hor('big'))

        # Draw HUD
        score_text = font_small.render(f"Score: {SCORE}", True, YELLOW)
        lives_text = font_small.render(f"Lives: {LIVES}", True, YELLOW)
        DISPLAYSURF.blit(score_text, (10, 10))
        DISPLAYSURF.blit(lives_text, (SCREEN_WIDTH-120, 10))

        all_sprites.draw(DISPLAYSURF)
    
    elif current_state == GAME_OVER:
        DISPLAYSURF.blit(game_over_text, (190, 220))
        final_score = font_mid.render(f"Final Score: {SCORE}", True, WHITE)
        DISPLAYSURF.blit(final_score, (130, 300))
        restart_text = font_small.render("Press SPACE to Restart", True, YELLOW)
        DISPLAYSURF.blit(restart_text, (SCREEN_WIDTH//2 - restart_text.get_width()//2, 400))
        
        if pygame.key.get_pressed()[K_SPACE]:
            reset_game()

   # elif current_state == CALIBRATION: 
        #show_calibration_screen() 
        # Flex Sensor calibration method
        #flex_controller.thresholds[flex_calibration.current_sensor] = flex_controller.calibrate_sensor(flex_calibration.current_sensor) 
        #if flex_calibration.update():
         #   current_state = START_SCREEN


    pygame.display.update()
    pygame.time.Clock().tick(FPS)

