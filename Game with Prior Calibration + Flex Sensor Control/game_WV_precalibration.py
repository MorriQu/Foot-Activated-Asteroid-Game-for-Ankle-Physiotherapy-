# Morri's game with flex sensor control and a calibration start screen 
# - need to work on setting movement thresholds to calibration values 

import pygame
import sys
import os
import json
import random
import math
from pygame.locals import *
import serial
import time 
from pynput.keyboard import Key, Controller 
import threading
import re

# Initialize Pygame
pygame.init()
SerialObject = serial.Serial('COM3', 9600)
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
font = pygame.font.SysFont("Arial", 60, bold=True)          
font_mid = pygame.font.SysFont("Arial", 35, bold=True)
font_small = pygame.font.SysFont("Arial", 25)
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

# Calibration Data File
CALIBRATION_FILE = "calibration_fourFlexors.json"

# Game states
START_SCREEN, CALIBRATION, PLAYING, GAME_OVER = range(4)
current_state = START_SCREEN

# Calibration UI Class
class CalibrationUI:
    """Hardware calibration interface."""
    def __init__(self):
        self.steps = [
            "Calibrate up: Pull toes up as far as possible",
            "Calibrate down: Push toes down as far as possible",
            "Calibrate left: Move foot left as far as possible", 
            "Calibrate right: Move foot right as far as possible"
        ]
        self.current_step = 0
        self.current_rep = 0 
        self.calibration_data = self.load_calibration()

    def load_calibration(self):
        """Load calibration configuration."""
        try:
            with open(CALIBRATION_FILE) as f:
                return json.load(f)
        except FileNotFoundError:
            print("Calibration configuration file not found")

    def save_calibration(self):
        """Save calibration configuration."""
        with open(CALIBRATION_FILE, 'w') as f:
            json.dump(self.calibration_data, f)

    def get_current_axis(self):
        """Get current calibration axis"""
        return ["Up max", "Down max", "Left max", "Right max"][self.current_step]

    def draw(self, screen, flex_value):
        """Drawing calibration interface"""
        screen.fill(BLACK)
        pygame.draw.rect(screen, WHITE, (100, 300, 500, 30), 2)
        bar_width = int((flex_value / 1023) * 500)
        pygame.draw.rect(screen, YELLOW, (100, 300, bar_width, 30))
        # Show step-by-step tips
        step_text = font_medium.render(
            self.steps[self.current_step], 
            True, 
            WHITE
        )
        screen.blit(step_text, (100, 200))
        # Displays the current calibration value
        current_axis = self.get_current_axis()
        y = 350
        for key in ["Up max", "Down max", "Left max", "Right max"]:
            color = GREEN if key == current_axis else WHITE
            val = self.calibration_data.get(key, 0)
            txt = font_small.render(f"{key.replace('_', ' ').title()}: {val}", True, color)
            screen.blit(txt, (100, y))
            y += 30
        pygame.display.update()

    def update(self, flex_value):  
        """Update calibration data with current sensor value"""
        current_key = ["Up max", "Down max", "Left max", "Right max"][self.current_step]
        self.calibration_data[current_key] = flex_value
        self.current_step += 1
        if self.current_step >= len(self.steps):
            self.calibration_data['threshold_percent'] = 80  
            # self.save_calibration()
            return True
        return False
    
    def get_arduino_value(self):
        if self.current_step == 0:   # Up
            return flexStateUp
        elif self.current_step == 1: # Down
            return flexStateDown
        elif self.current_step == 2: # Left
            return flexStateLeft
        elif self.current_step == 3: # Right
            return flexStateRight
        


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
        self.rect.center = (random.randint(40, SCREEN_WIDTH-40), -50)

    def update(self):
        self.rect.move_ip(0, self.speed)
        if self.rect.top > SCREEN_HEIGHT:
            self.reset_position()
            global SCORE
            SCORE += 1

    def split(self):
        """Split vertical enemy into smaller ones."""
        if self.size == "big":
            return [Enemy_vert(size="normal") for _ in range(2)]
        elif self.size == "normal":
            return [Enemy_vert(size="small") for _ in range(2)]
        return []

class Enemy_hor(pygame.sprite.Sprite):
    # def __init__(self, size="big"):
    #     super().__init__()
    #     # Load size-specific image
    #     if size in {"big", "normal", "small"}:
    #         self.image = load_image_convert_alpha(f"asteroid-{size}.png")
    #     else:
    #         self.image = load_image_convert_alpha("asteroid-big.png")
    #     self.size = size
    #     self.rect = self.image.get_rect()
    #     self.reset_position()
    #     self.speed = SPEED

    def __init__(self, size="big"):
        super().__init__()
        size = size.lower()
        self.image = load_image_convert_alpha(f"asteroid-{size}.png")
        self.size = size
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
    
    def split(self):
        """Split horizontal enemy into smaller ones."""
        if self.size == "big":
            return [Enemy_hor(size="normal") for _ in range(2)]
        elif self.size == "normal":
            return [Enemy_hor(size="small") for _ in range(2)]
        return []

class Player(pygame.sprite.Sprite):
    """Player class representing the spaceship."""
    def __init__(self):
        super().__init__()
        self.image = load_image_convert_alpha("ufo.png")
        self.rect = self.image.get_rect(center=(340, 260))
        self.speed = 5
        self.missiles = pygame.sprite.Group()
        self.angle = 0

    def move(self, pressed_keys):
        """Move the player using arrow keys."""
        if pressed_keys[K_UP] and self.rect.top > 0:
            self.rect.move_ip(0, -5)
        if pressed_keys[K_DOWN] and self.rect.bottom < SCREEN_HEIGHT:
            self.rect.move_ip(0, 5)
        if pressed_keys[K_LEFT] and self.rect.left > 0:
            self.rect.move_ip(-5, 0)
        if pressed_keys[K_RIGHT] and self.rect.right < SCREEN_WIDTH:
            self.rect.move_ip(5, 0)

    def shoot(self):
        """Create a missile that always fires upward from the player's midtop."""
        missile = Missile(self.rect.midtop, self.angle)
        self.missiles.add(missile)
        all_sprites.add(missile)
        shoot_sound.play()

    def update(self):
        """Update the player's missiles."""
        self.missiles.update()

def show_start_screen():
    """Display start screen"""
    DISPLAYSURF.fill(BLACK)
    title = font.render("Asteroid Blaster", True, WHITE)
    instruction = font_small.render("Press SPACE to Start", True, YELLOW)
    DISPLAYSURF.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 150))
    DISPLAYSURF.blit(instruction, (SCREEN_WIDTH//2 - instruction.get_width()//2, 300))
    pygame.display.update()

def reset_game():
    """Reset game state"""
    global SCORE, LIVES, SPEED
    SCORE = 0
    LIVES = 3
    SPEED = 1.5
    P1.rect.center = (SCREEN_WIDTH//2, SCREEN_HEIGHT//2)
    enemies.empty()
    all_sprites.empty()
    all_sprites.add(P1)

    for _ in range(2):
        if random.random() < 0.5:
            enemy = Enemy_vert('big')
        else:
            enemy = Enemy_hor('big')
        enemies.add(enemy)
        all_sprites.add(enemy)
    
    pygame.mixer.music.play(-1)

# Initialize game objects
P1 = Player()
enemies = pygame.sprite.Group()
all_sprites = pygame.sprite.Group(P1)
calibration_ui = CalibrationUI() 
calibration_percent = 80
thresholds = calibration_ui.load_calibration()

INC_SPEED = pygame.USEREVENT + 1
pygame.time.set_timer(INC_SPEED, 1000)

clock = pygame.time.Clock()

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

            if not match or len(match) < 4:  # Ensure correct format
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
        if current_state == CALIBRATION and event.type == KEYDOWN:
            if event.key == K_SPACE:
                flex_value = calibration_ui.get_arduino_value()
                if calibration_ui.update(flex_value):
                    current_state = PLAYING
                    reset_game()
        if current_state == PLAYING and event.type == KEYDOWN:
            if event.key == K_SPACE:
                P1.shoot()
        if current_state == START_SCREEN and event.type == KEYDOWN:
            if event.key == K_SPACE:
                current_state = PLAYING


 
    # print("Thresholds:", thresholds) # for debugging
    
    print("Flex state up: ", flexStateUp, "Flex state Down: ", flexStateDown, "Flex state left: ", flexStateLeft, "Flex state right: ", flexStateRight)
    # Use the latest flex sensor values to simulate key presses
    if flexStateUp < thresholds["thresholds"][0]:
      #  print("Up Arrow Key Released")
       # print("Flex state up: ", flexStateUp)
        keyboard.release(Key.up)

    elif flexStateUp > thresholds["thresholds"][0]:
        #print("Up Arrow Key Pressed")
       # print("Flex state up: ", flexStateUp)
        keyboard.press(Key.up)
    
    if flexStateDown < thresholds["thresholds"][1]:
     #   print("Down Arrow Key Released")
       # print("Flex state Down: ", flexStateDown)
        keyboard.release(Key.down)

    elif flexStateDown > thresholds["thresholds"][1]:
     #   print("Down Arrow Key Pressed")
       # print("Flex state down: ", flexStateDown)
        keyboard.press(Key.down)

    if flexStateLeft < thresholds["thresholds"][2]:
     #   print("Left Arrow Key Released")
       # print("Flex state left: ", flexStateLeft)
        keyboard.release(Key.left)

    elif flexStateLeft > thresholds["thresholds"][2]:
     #   print("Left Arrow Key Pressed")
     #   print("Flex state left: ", flexStateLeft)
        keyboard.press(Key.left)

    if flexStateRight < thresholds["thresholds"][3]:
     #   print("Right Arrow Key Released")
     #   print("Flex state right: ", flexStateRight)
        keyboard.release(Key.right)

    elif flexStateRight > thresholds["thresholds"][3]:
     #   print("Right Arrow Key Pressed")
     #   print("Flex state right: ", flexStateRight)
        keyboard.press(Key.right)

    DISPLAYSURF.blit(background, (0, 0))
    
    # Start screen
    if current_state == START_SCREEN:
        show_start_screen()
    
    # Calibration screen
    elif current_state == CALIBRATION:
        calibration_ui.draw(DISPLAYSURF, calibration_ui.get_arduino_value())
    
    # Playing state
    elif current_state == PLAYING:
        # Update game state
        pressed_keys = pygame.key.get_pressed()
        P1.move(pressed_keys)
        all_sprites.update()
        
        # 碰撞检测：导弹与敌人
        for missile in P1.missiles.copy():
            hits = pygame.sprite.spritecollide(missile, enemies, True)
            if hits:
                missile.kill()
                explosion_sound.play()
                for enemy in hits:
                    new_enemies = enemy.split()
                    for new_enemy in new_enemies:
                        new_enemy.speed *= 1.2
                        enemies.add(new_enemy)
                        all_sprites.add(new_enemy)
                    SCORE += {"big":20, "normal":50, "small":100}[enemy.size]
        
        # 碰撞检测：玩家与敌人
        if pygame.sprite.spritecollideany(P1, enemies):
            explosion_sound.play()
            LIVES -= 1
            if LIVES <= 0:
                current_state = GAME_OVER
                pygame.mixer.music.stop()
            else:
                P1.rect.center = (SCREEN_WIDTH//2, SCREEN_HEIGHT//2)
                # 重置敌人
                enemies.empty()
                all_sprites.empty()
                all_sprites.add(P1)
                for _ in range(2):
                    if random.random() < 0.5:
                        enemy = Enemy_vert('big')
                    else:
                        enemy = Enemy_hor('big')
                    enemies.add(enemy)
                    all_sprites.add(enemy)
        
        # 持续生成敌人（修复问题4）
        if len(enemies) < 2:
            if random.random() < 0.02:  # 2%概率每帧生成新敌人
                if random.random() < 0.5:
                    enemy = Enemy_vert('big')
                else:
                    enemy = Enemy_hor('big')
                enemies.add(enemy)
                all_sprites.add(enemy)
        
        # 绘制游戏元素
        all_sprites.draw(DISPLAYSURF)
        
        # 绘制HUD（修复问题2）
        score_text = font_small.render(f"Score: {SCORE}", True, YELLOW)
        lives_text = font_small.render(f"Lives: {LIVES}", True, YELLOW)
        DISPLAYSURF.blit(score_text, (10, 10))
        DISPLAYSURF.blit(lives_text, (SCREEN_WIDTH-120, 10))
    
    # Game over screen
    elif current_state == GAME_OVER:
        DISPLAYSURF.fill(BLACK)
        DISPLAYSURF.blit(game_over_text, (190, 220))
        final_score = font_mid.render(f"Final Score: {SCORE}", True, WHITE)
        DISPLAYSURF.blit(final_score, (130, 300))
        restart_text = font_small.render("Press SPACE to Restart", True, YELLOW)
        DISPLAYSURF.blit(restart_text, (SCREEN_WIDTH//2 - restart_text.get_width()//2, 400))
        
        if pygame.key.get_pressed()[K_SPACE]:
            current_state = START_SCREEN
            reset_game()

    pygame.display.update()
    clock.tick(FPS)