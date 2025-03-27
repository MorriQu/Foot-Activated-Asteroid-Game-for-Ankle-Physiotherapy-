import pygame, sys, os, json, random, time, math
from pygame.locals import *
 
pygame.init() # Initialise Pygame
 
FPS = 60
FramePerSec = pygame.time.Clock()
 
# Predefined some colors
BLUE  = (0, 0, 205)
YELLOW   = (255, 255, 102)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
TEAL = (0, 153, 153)
RED = (255, 0, 0)
GREEN = (0, 255, 0)

# Program information
SCREEN_WIDTH = 700
SCREEN_HEIGHT = 500
SPEED = 1.5 
SCORE = 0
LIVES = 3

#Setting up Fonts
font = pygame.font.SysFont("lucidaconsole", 60)
font_mid = pygame.font.SysFont("lucidaconsole", 30)
font_small = pygame.font.SysFont("Arial", 25)
font_medium = pygame.font.SysFont("Arial", 30, bold=True)
game_over = font.render("Game Over", True, WHITE) 

# Resource loading functions
def load_image_convert_alpha(filename):
    """Load an image with the given filename from the images directory"""
    return pygame.image.load(os.path.join('images', filename)).convert_alpha()

def load_sound(filename):
    """Load a sound with the given filename from the sounds directory"""
    return pygame.mixer.Sound(os.path.join('sounds', filename))

# Create white screen 
DISPLAYSURF = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
DISPLAYSURF.fill(WHITE)
pygame.display.set_caption("Asteroid Blaster")

#Load images for menu
background = load_image_convert_alpha('starry_night.jpg')
home_button_img = load_image_convert_alpha("home-button1.png")
calibrate_img = load_image_convert_alpha("calibrate.png")    
difficulty_img = load_image_convert_alpha("difficulty.png")  
lev1_img = load_image_convert_alpha("lev1.png")
lev2_img = load_image_convert_alpha("lev2.png")
lev3_img = load_image_convert_alpha("lev3.png")
#Load sounds
shoot_sound = load_sound('fire.wav')
explosion_sound = load_sound('die.wav')
pygame.mixer.music.load(os.path.join('sounds', 'soundtrack.wav'))
pygame.mixer.music.set_volume(0.3)

# Calibration Data File
CALIBRATION_FILE = "calibration.json"

# Game State Management
DIFFICULTY_SETTINGS = {
    1: {'base_speed': 1, 'speed_inc': 0.0, 'enemy_count': 2, 'split_speed': 1.0, 'player_speed': 4.0},
    2: {'base_speed': 2.0, 'speed_inc': 0.01, 'enemy_count': 3, 'split_speed': 1.1, 'player_speed': 4.5},
    3: {'base_speed': 2.0, 'speed_inc': 0.0, 'enemy_count': 3, 'split_speed': 1.2, 'spawn_rate': 0.02, 'player_speed': 5.0}
}
selected_difficulty = 1
game_paused = False
menu_state = "main"
PAUSED = False


"""MENU BUTTONS"""
class Button():
      def __init__(self, x, y, image):
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.center = (x,y)
        self.clicked = False

      def draw(self):
            action = False
            pos = pygame.mouse.get_pos()
            if self.rect.collidepoint(pos):
                  if pygame.mouse.get_pressed()[0] == 1 and self.clicked == False:
                        self.clicked = True
                        action = True
            if pygame.mouse.get_pressed()[0] == 0:
                  self.clicked = False
            # DISPLAYSURF.blit(self.image, (self.rect.x, self.rect.y))
            DISPLAYSURF.blit(self.image, self.rect)
            return action

home_button = Button(50, SCREEN_HEIGHT-50, home_button_img)       
calibrate_button = Button(208, 250, calibrate_img)
difficulty_button = Button(491, 250, difficulty_img)
level1_button = Button(137, 250, lev1_img)
level2_button = Button(349, 250, lev2_img)
level3_button = Button(561, 250, lev3_img)

def draw_text(text, font, text_col, x, y):
      img = font.render(text, True, text_col)
      DISPLAYSURF.blit(img, (x,y))


# Calibration UI Class
class CalibrationUI:
    """Hardware calibration interface."""
    def __init__(self):
        self.steps = [
            "STEP 1: Keep sensor neutral, press button",
            "STEP 2: Move left to extreme, press button",
            "STEP 3: Move right to extreme, press button"
        ]
        self.current_step = 0
        self.calibration_data = self.load_calibration()

    def load_calibration(self):
        """Load calibration configuration."""
        try:
            with open(CALIBRATION_FILE) as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                "neutral": 512,
                "left_max": 300,
                "right_max": 724,
                "threshold_percent": 80
            }

    def save_calibration(self):
        """Save calibration configuration."""
        with open(CALIBRATION_FILE, 'w') as f:
            json.dump(self.calibration_data, f)

    def get_current_axis(self):
        """Get current calibration axis"""
        return ["neutral", "left_max", "right_max"][self.current_step]

    def draw(self, screen, pot_value):
        """Drawing calibration interface"""
        screen.fill(BLACK)
        pygame.draw.rect(screen, WHITE, (100, 300, 500, 30), 2)
        bar_width = int((pot_value / 1023) * 500)
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
        for key in ["neutral", "left_max", "right_max"]:
            color = GREEN if key == current_axis else WHITE
            val = self.calibration_data.get(key, 0)
            txt = font_small.render(f"{key.replace('_', ' ').title()}: {val}", True, color)
            screen.blit(txt, (100, y))
            y += 30
        # Threshold percentage
        threshold_text = font_small.render(
            f"Threshold: {self.calibration_data['threshold_percent']}%", 
            True, 
            YELLOW
        )
        screen.blit(threshold_text, (100, 500))
        pygame.display.update()

    def update(self, pot_value):  
        """Update calibration data with current sensor value"""
        current_key = ["neutral", "left_max", "right_max"][self.current_step]
        self.calibration_data[current_key] = pot_value
        self.current_step += 1
        if self.current_step >= len(self.steps):
            self.calibration_data['threshold_percent'] = 80  
            self.save_calibration()
            return True
        return False
    
    def get_simulated_value(self):
        """Generate simulated sensor data"""
        if self.current_step == 0:   # Neutral
            return random.randint(500, 524)
        elif self.current_step == 1: # Left
            return random.randint(200, 300)
        elif self.current_step == 2: # Right
            return random.randint(700, 800)
        return 512

    def reset(self):
        self.current_step = 0
        self.calibration_data = self.load_calibration()

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
        self.speed = DIFFICULTY_SETTINGS[selected_difficulty]['base_speed']

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
        if selected_difficulty == 3:
            if self.size == "big":
                return [Enemy_vert(size="normal") for _ in range(2)]
            elif self.size == "normal":
                return [Enemy_vert(size="small") for _ in range(2)]
        return []

class Enemy_hor(pygame.sprite.Sprite):
    def __init__(self, size="big"):
        super().__init__()
        size = size.lower()
        self.image = load_image_convert_alpha(f"asteroid-{size}.png")
        self.size = size
        self.rect = self.image.get_rect()
        self.reset_position()
        self.speed = DIFFICULTY_SETTINGS[selected_difficulty]['base_speed']

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
        if selected_difficulty == 3:
            if self.size == "big":
                return [Enemy_vert(size="normal") for _ in range(2)]
            elif self.size == "normal":
                return [Enemy_vert(size="small") for _ in range(2)]
        return []

class Player(pygame.sprite.Sprite):
    """Player class representing the spaceship."""
    def __init__(self):
        super().__init__()
        self.image = load_image_convert_alpha("ufo2.png")
        self.rect = self.image.get_rect(center=(340, 260))
        self.speed = DIFFICULTY_SETTINGS[selected_difficulty]['player_speed']  
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
        if selected_difficulty == 3:  
            missile = Missile(self.rect.midtop, self.angle)
            self.missiles.add(missile)
            all_sprites.add(missile)
            shoot_sound.play()


    def update(self):
        """Update the player's missiles."""
        self.missiles.update()
        

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

def reset_game():
    """Reset game state"""
    global SCORE, LIVES, SPEED
    SCORE = 0
    LIVES = 3
    settings = DIFFICULTY_SETTINGS[selected_difficulty]
    SPEED = settings['base_speed']
    game_paused = False 
    
    P1.rect.center = (SCREEN_WIDTH//2, SCREEN_HEIGHT//2)
    enemies.empty()
    all_sprites.empty()
    all_sprites.add(P1)

    for _ in range(settings['enemy_count']):
        if random.random() < 0.5:
            enemy = Enemy_vert('big')
        else:
            enemy = Enemy_hor('big')
        enemies.add(enemy)
        all_sprites.add(enemy)
    
    pygame.mixer.music.play(-1)

# Creating Sprites         
P1 = Player()
E1 = Enemy_vert()
E2 = Enemy_hor()

#Creating Sprites Groups
enemies = pygame.sprite.Group()
enemies.add(E1)
enemies.add(E2)

all_sprites = pygame.sprite.Group()
all_sprites.add(P1)
all_sprites.add(E1)
all_sprites.add(E2)

calibration_ui = CalibrationUI() 
calibration_percent = 80
 
#Adding a new User event 
INC_SPEED = pygame.USEREVENT + 1
pygame.time.set_timer(INC_SPEED, 1000) #call INC_SPEED every 1000ms

# Add game state constants after existing variables
GAME_STATES = {
    "MAIN_MENU": 0,
    "DIFFICULTY_MENU": 1,
    "CALIBRATION": 2,
    "PLAYING": 3,
    "GAME_OVER": 4
}
current_game_state = GAME_STATES["MAIN_MENU"]

#Game Loop
run = True
while run:
    DISPLAYSURF.blit(background, (0,0))
    
    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                if not game_paused and menu_state == "main":
                    game_paused = True 
                elif game_paused and menu_state == "main":
                    game_paused = False  
            if event.key == pygame.K_RETURN and menu_state == "playing":
                PAUSED = not PAUSED
                if PAUSED:
                    menu_state = "main"
                    selected_difficulty = 1 
                    reset_game()
            if event.type == KEYDOWN and event.key == K_SPACE and menu_state == "playing" and selected_difficulty == 3:
                P1.shoot()
        if event.type == INC_SPEED and menu_state == "playing":
            SPEED += DIFFICULTY_SETTINGS[selected_difficulty]['speed_inc']
        
        # Calibration events
        if menu_state == "calibration":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                pot_value = calibration_ui.get_simulated_value()
                if calibration_ui.update(pot_value):
                    menu_state = "difficulty"

    if PAUSED:
        # Draw pause screen
        draw_text("PAUSED", font, WHITE, SCREEN_WIDTH//2-100, SCREEN_HEIGHT//2-30)
        if home_button.draw():
            game_paused = False
            menu_state = "main"
            PAUSED = False
            reset_game()
            selected_difficulty = 1
        
        pygame.display.update()
        FramePerSec.tick(FPS)
        continue

    if game_paused:
        if menu_state == "main":
            if difficulty_button.draw():
                menu_state = "difficulty"
            if calibrate_button.draw():
                menu_state = "calibration"
                calibration_ui.reset()
                calibration_ui.draw(DISPLAYSURF, calibration_ui.get_simulated_value())

        elif menu_state == "difficulty":
            draw_text("Select Difficulty", font_mid, WHITE, 200, 150)
            if level1_button.draw():
                selected_difficulty = 1
                reset_game()
                menu_state = "playing"
                game_paused = False
            if level2_button.draw():
                selected_difficulty = 2
                reset_game()
                menu_state = "playing"
                game_paused = False
            if level3_button.draw():
                selected_difficulty = 3
                reset_game()
                menu_state = "playing"
                game_paused = False
        
        elif menu_state == "calibration":
            calibration_ui.draw(DISPLAYSURF, calibration_ui.get_simulated_value())

    else:
        # Main game play
        if menu_state == "playing":
            # Update game state
            settings = DIFFICULTY_SETTINGS[selected_difficulty]
            pressed_keys = pygame.key.get_pressed()
            P1.move(pressed_keys)
            all_sprites.update()

            # Missile collisions
            for missile in P1.missiles.copy():
                hits = pygame.sprite.spritecollide(missile, enemies, True)
                if hits:
                    missile.kill()
                    explosion_sound.play()
                    for enemy in hits:
                        new_enemies = enemy.split()
                        speed_multiplier = DIFFICULTY_SETTINGS[selected_difficulty]['split_speed']
                        for new_enemy in new_enemies:
                            new_enemy.speed *= speed_multiplier 
                            enemies.add(new_enemy)
                            all_sprites.add(new_enemy)
                        SCORE += {"big":20, "normal":50, "small":100}[enemy.size]

            # Player collision
            if pygame.sprite.spritecollideany(P1, enemies):
                explosion_sound.play()
                LIVES -= 1
                if LIVES <= 0:
                    # Game Over
                    DISPLAYSURF.fill(TEAL)
                    DISPLAYSURF.blit(game_over, (190,200))
                    final_score = font_mid.render(f"Final Score: {SCORE}", True, WHITE)
                    DISPLAYSURF.blit(final_score, (200, 300))
                    pygame.display.update()
                    time.sleep(2)
                    game_paused = True
                    menu_state = "main"
                    selected_difficulty = 1
                    reset_game()
                else:
                    P1.rect.center = (SCREEN_WIDTH//2, SCREEN_HEIGHT//2)
                    enemies.empty()
                    all_sprites.empty()
                    all_sprites.add(P1)
                    for _ in range(settings['enemy_count']):
                        enemy = Enemy_vert('big') if random.random() < 0.5 else Enemy_hor('big')
                        enemies.add(enemy)
                        all_sprites.add(enemy)

            # Spawn new enemies
            if len(enemies) < settings['enemy_count']:
                if random.random() < settings['spawn_rate']:
                    enemy = Enemy_vert('big') if random.random() < 0.5 else Enemy_hor('big')
                    enemies.add(enemy)
                    all_sprites.add(enemy)

            # Draw game elements
            for entity in all_sprites:
                DISPLAYSURF.blit(entity.image, entity.rect)

            # Draw HUD
            score_text = font_small.render(f"Score: {SCORE}", True, YELLOW)
            lives_text = font_small.render(f"Lives: {LIVES}", True, YELLOW)
            DISPLAYSURF.blit(score_text, (10, 10))
            DISPLAYSURF.blit(lives_text, (SCREEN_WIDTH-120, 10))

        else:
            # Main menu
            draw_text("Asteroid Blaster", font, WHITE, 70, 150)
            draw_text("Press SPACE to Play", font_mid, YELLOW, 170, 250)

    # Handle speed increase
    if event.type == INC_SPEED and menu_state == "playing":
        settings = DIFFICULTY_SETTINGS[selected_difficulty]
        SPEED += DIFFICULTY_SETTINGS[selected_difficulty]['speed_inc']

    pygame.display.update()
    FramePerSec.tick(FPS)

pygame.quit()
sys.exit()