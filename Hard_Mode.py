import pygame
import random
import sys
import os
import pygame_gui
import subprocess

# Get the base directory of the script
base_path = os.path.dirname(os.path.abspath(__file__))

# Initialize pygame
pygame.init()

# Screen dimensions and setup
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Crossy Road - Hard Mode")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)

# Clock for controlling frame rate
clock = pygame.time.Clock()
FPS = 30

# Debugging options
DEBUG_MODE = False  # Set to False to disable debugging features

# Game constants
STEP_SIZE = 40
SCALE_FACTOR = 2
SAFE_DISTANCE = STEP_SIZE * 2
LANE_WIDTH = STEP_SIZE * 3

# Player settings
PLAYER_WIDTH = 40
PLAYER_HEIGHT = 40
player_x = 10
player_y = SCREEN_HEIGHT // 2 - PLAYER_HEIGHT // 2

# Car settings
CAR_WIDTH = 60
CAR_HEIGHT = 40
car_speed_min = 7  # Higher starting speeds for hard mode
car_speed_max = 12
cars = []

# Game state variables
score = 0
background_offset = 0
menu_open = False
menu_elements = None
game_over = False
move_speed = 10
last_move_time = pygame.time.get_ticks() / 1000
afk_limit = 10
collision_state = False
win_state = False
WIN_SCORE = 30  # Score needed to win in hard mode

# Initialize pygame_gui manager
manager = pygame_gui.UIManager((SCREEN_WIDTH, SCREEN_HEIGHT))

# Font initialization
font = pygame.font.Font(None, 36)
instruction_font = pygame.font.Font(None, 24)

# Load and scale images
def load_and_scale_image(filename, width, height):
    """Helper function to load and scale an image"""
    try:
        image = pygame.image.load(os.path.join(base_path, filename))
        return pygame.transform.scale(image, (width, height))
    except pygame.error as e:
        print(f"Error loading image {filename}: {e}")
        pygame.quit()
        sys.exit()

# Load all images
try:
    player_image = load_and_scale_image("Greta_Thunberg.png", 
                                       PLAYER_WIDTH * SCALE_FACTOR, 
                                       PLAYER_HEIGHT * SCALE_FACTOR)
    player_collision_image = load_and_scale_image("How_dare_you.png", 
                                                 PLAYER_WIDTH * SCALE_FACTOR, 
                                                 PLAYER_HEIGHT * SCALE_FACTOR)
    player_win_image = load_and_scale_image("Sitting.png", 
                                          PLAYER_WIDTH * SCALE_FACTOR, 
                                          PLAYER_HEIGHT * SCALE_FACTOR)
    car_image = load_and_scale_image("car.png", 
                                    CAR_WIDTH * SCALE_FACTOR, 
                                    CAR_HEIGHT * SCALE_FACTOR)
    background_image = load_and_scale_image("background.png", 
                                           SCREEN_WIDTH, 
                                           SCREEN_HEIGHT)
except Exception as e:
    print(f"Error loading images: {e}")
    pygame.quit()
    sys.exit()

# Update dimensions to match scaled images
PLAYER_WIDTH *= SCALE_FACTOR
PLAYER_HEIGHT *= SCALE_FACTOR
CAR_WIDTH *= SCALE_FACTOR
CAR_HEIGHT *= SCALE_FACTOR

# Initialize the current player image
current_player_image = player_image

# Game Functions
def create_car():
    """Create a new car with proper lane positioning and safe distance from other cars"""
    num_lanes = SCREEN_WIDTH // LANE_WIDTH
    attempts = 0
    max_attempts = 10
    
    # Use all lanes in hard mode, not just even ones
    available_lanes = list(range(0, num_lanes))
    lane_number = random.choice(available_lanes)
    lane_x = lane_number * LANE_WIDTH + LANE_WIDTH // 2  # Center of lane
    
    while attempts < max_attempts:
        # Decide car spawning position and direction
        car_y = random.choice([-CAR_HEIGHT, SCREEN_HEIGHT])
        car_direction = 1 if car_y == -CAR_HEIGHT else -1
        
        # Convert to integers for randint
        min_speed = int(car_speed_min)
        max_speed = int(car_speed_max)
        # Make sure max is at least min+1
        if max_speed <= min_speed:
            max_speed = min_speed + 1
            
        car_speed = random.randint(min_speed, max_speed) * car_direction
        
        # Find cars in the same lane
        cars_in_same_lane = [car for car in cars if abs(car["x"] - lane_x) < LANE_WIDTH // 2]
        
        # If lane is empty, use it
        if not cars_in_same_lane:
            return {"x": lane_x - CAR_WIDTH // 2, "y": car_y, "speed": car_speed, "lane": lane_number}
        
        # Check distance to other cars
        too_close = False
        for car in cars_in_same_lane:
            # For cars coming from top or bottom
            if ((car_y == -CAR_HEIGHT and car["y"] < SCREEN_HEIGHT // 2) or
                (car_y == SCREEN_HEIGHT and car["y"] > SCREEN_HEIGHT // 2)):
                if abs(car["y"] - car_y) < SAFE_DISTANCE:
                    too_close = True
                    break
        
        # If not too close to any car, use this position
        if not too_close:
            return {"x": lane_x - CAR_WIDTH // 2, "y": car_y, "speed": car_speed, "lane": lane_number}
            
        # Try a different lane
        attempts += 1
        lane_number = available_lanes[(available_lanes.index(lane_number) + 1) % len(available_lanes)]
        lane_x = lane_number * LANE_WIDTH + LANE_WIDTH // 2
    
    # Fall back to last attempted position
    return {"x": lane_x - CAR_WIDTH // 2, "y": car_y, "speed": car_speed, "lane": lane_number}

def create_car_cluster():
    """Create a challenging cluster of cars in adjacent lanes (hard mode feature)"""
    num_lanes = SCREEN_WIDTH // LANE_WIDTH
    starting_lane = random.randint(0, num_lanes - 3)  # Leave room for at least 3 cars
    
    cluster = []
    for i in range(3):  # Create 3 cars in adjacent lanes
        lane_number = starting_lane + i
        lane_x = lane_number * LANE_WIDTH + LANE_WIDTH // 2
        car_y = random.choice([-CAR_HEIGHT, SCREEN_HEIGHT])
        car_direction = 1 if car_y == -CAR_HEIGHT else -1
        
        # Stagger speeds slightly to create gaps that close
        car_speed = (random.randint(car_speed_min, car_speed_max) + i) * car_direction
        
        cluster.append({
            "x": lane_x - CAR_WIDTH // 2, 
            "y": car_y, 
            "speed": car_speed, 
            "lane": lane_number
        })
    
    return cluster

def detect_afk(last_move_time, afk_limit=10):
    """Detect if the player is AFK and notify them"""
    global menu_open, game_over, menu_elements

    current_time = pygame.time.get_ticks() / 1000
    time_since_last_move = current_time - last_move_time
    
    # Show warning when we're 3 seconds away from timeout
    if time_since_last_move > afk_limit - 3:
        # Create semi-transparent surface for warning backdrop
        warning_bg = pygame.Surface((400, 80), pygame.SRCALPHA)
        warning_bg.fill((255, 200, 200, 180))  # Semi-transparent red
        screen.blit(warning_bg, (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - 40))
        
        # Calculate remaining time
        time_left = afk_limit - time_since_last_move
        time_left_str = f"{time_left:.1f}" if time_left < 3 else f"{int(time_left)}"
        
        # Display warning and timer
        afk_warning = font.render("Move or the game will end!", True, RED)
        timer_text = font.render(f"Time left: {time_left_str} s", True, BLACK)
        
        screen.blit(afk_warning, (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 - 20))
        screen.blit(timer_text, (SCREEN_WIDTH // 2 - 80, SCREEN_HEIGHT // 2 + 10))

    if time_since_last_move > afk_limit:
        menu_open = True
        game_over = True
        menu_elements = create_menu(game_over=True)
        return True
    return False

def draw_lane_markers():
    """Draw lane markers for debugging"""
    if not DEBUG_MODE:
        return

    num_lanes = SCREEN_WIDTH // LANE_WIDTH
    for i in range(num_lanes + 1):
        x_pos = i * LANE_WIDTH
        # Draw dashed lines
        for y in range(0, SCREEN_HEIGHT, 20):
            pygame.draw.line(screen, BLUE, (x_pos, y), (x_pos, y + 10), 2)
        
        # Draw lane numbers
        if i < num_lanes:
            lane_center = i * LANE_WIDTH + LANE_WIDTH // 2
            lane_text = font.render(str(i), True, BLUE)
            screen.blit(lane_text, (lane_center - 5, 50))

def check_collision(player_rect, car_rect):
    """Check if player collides with car"""
    return (player_rect.x < car_rect.x + car_rect.width and
            player_rect.x + player_rect.width > car_rect.x and
            player_rect.y < car_rect.y + car_rect.height and
            player_rect.y + player_rect.height > car_rect.y)

def create_menu(game_over=False, win=False):
    """Create either regular menu, win menu, or game over menu"""
    panel = pygame_gui.elements.UIPanel(
        relative_rect=pygame.Rect((SCREEN_WIDTH//2-150, SCREEN_HEIGHT//2-120), (300, 240)),
        manager=manager
    )
    
    if win:
        # Win menu
        title_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((50, 20), (200, 30)),
            text="Victory!",
            manager=manager,
            container=panel
        )
        
        score_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((30, 50), (240, 30)),
            text=f"Final Score: {score}",
            manager=manager,
            container=panel
        )
        
        subtitle_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((30, 80), (240, 30)),
            text="You've mastered Hard Mode!",
            manager=manager,
            container=panel
        )
        
        restart_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((50, 110), (200, 40)),
            text="Play Again",
            manager=manager,
            container=panel
        )
        
        change_mode_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((50, 150), (200, 40)),
            text="Change Game Mode",
            manager=manager,
            container=panel
        )
        
        quit_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((50, 190), (200, 40)),
            text="Quit Game",
            manager=manager,
            container=panel
        )
        
        return panel, restart_button, change_mode_button, quit_button
    elif game_over:
        # Game over menu
        title_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((50, 20), (200, 30)),
            text="Game Over!",
            manager=manager,
            container=panel
        )
        
        score_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((30, 50), (240, 30)),
            text=f"Final Score: {score}",
            manager=manager,
            container=panel
        )
        
        subtitle_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((30, 80), (240, 30)),
            text="Do you want to try again?",
            manager=manager,
            container=panel
        )
        
        restart_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((50, 110), (200, 40)),
            text="Try Again",
            manager=manager,
            container=panel
        )
        
        change_mode_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((50, 150), (200, 40)),
            text="Change Game Mode",
            manager=manager,
            container=panel
        )
        
        quit_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((50, 190), (200, 40)),
            text="Quit Game",
            manager=manager,
            container=panel
        )
        
        return panel, restart_button, change_mode_button, quit_button
    else:
        # Regular menu
        continue_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((50, 30), (200, 40)),
            text="Continue",
            manager=manager,
            container=panel
        )
        
        restart_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((50, 80), (200, 40)),
            text="Restart Game",
            manager=manager,
            container=panel
        )
        
        change_mode_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((50, 130), (200, 40)),
            text="Change Game Mode",
            manager=manager,
            container=panel
        )
        
        quit_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((50, 180), (200, 40)),
            text="Quit Game",
            manager=manager,
            container=panel
        )
        
        return panel, continue_button, restart_button, change_mode_button, quit_button

def reset_game():
    """Reset all game variables to starting state"""
    global player_x, player_y, score, background_offset, cars
    global game_over, last_move_time, collision_state, current_player_image, win_state
    
    last_move_time = pygame.time.get_ticks() / 1000
    collision_state = False
    win_state = False
    current_player_image = player_image  # Reset to normal player image
    
    player_x = 10
    player_y = SCREEN_HEIGHT // 2 - PLAYER_HEIGHT // 2
    
    score = 0
    background_offset = 0
    game_over = False
    
    cars.clear()
    for _ in range(8):  # More cars in hard mode
        cars.append(create_car())

def handle_player_movement():
    """Handle continuous player movement while space is held"""
    global player_x, background_offset, score, last_move_time, car_speed_min, car_speed_max, win_state
    
    last_move_time = pygame.time.get_ticks() / 1000
    
    # Don't process movement if player has won
    if win_state:
        return
    
    # Calculate current lane and target
    current_lane = (player_x + PLAYER_WIDTH//2) // LANE_WIDTH
    target_lane = current_lane + 1
    target_x = (target_lane * LANE_WIDTH + LANE_WIDTH // 2) - PLAYER_WIDTH // 2
    
    # Check if player is in the center of the screen
    if player_x >= SCREEN_WIDTH // 2 - PLAYER_WIDTH // 2:
        # Move background and obstacles instead of player
        movement = min(move_speed, LANE_WIDTH)
        background_offset -= movement
        for car in cars:
            car["x"] -= movement
        
        # Increase score when we've moved a full lane width
        if abs(background_offset % LANE_WIDTH) < move_speed:
            score += 1
    else:
        # Move player toward target position
        if player_x < target_x:
            movement = min(move_speed, target_x - player_x)
            player_x += movement
            
            # Track lane change for scoring
            previous_lane = current_lane
            new_lane = (player_x + PLAYER_WIDTH//2) // LANE_WIDTH
            
            # Increase score when we cross into a new lane
            if new_lane > previous_lane:
                score += 1
    
    # Hard mode: Increase difficulty as score increases
    if score > 0 and score % 10 == 0:
        car_speed_min = min(car_speed_min + 0.5, 10)
        car_speed_max = min(car_speed_max + 0.5, 15)

    # Check for win condition
    if score >= WIN_SCORE and not win_state:
        handle_win()

def handle_collision(car):
    """Handle collision between player and car"""
    global collision_state, current_player_image, menu_open, game_over, menu_elements
    
    collision_state = True
    current_player_image = player_collision_image
    
    # Clear and redraw the game screen
    screen.fill(WHITE)
    
    # Draw background
    for i in range(2):
        screen.blit(background_image, ((background_offset % SCREEN_WIDTH) - SCREEN_WIDTH * i, 0))
    
    # Draw all cars except the one that caused the collision
    for other_car in cars:
        if other_car != car:
            screen.blit(car_image, (other_car["x"], other_car["y"]))
    
    # Display the "How dare you!" quote
    quote_text = font.render("How dare you!", True, RED)
    screen.blit(quote_text, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 20))
    
    # Draw collision image
    screen.blit(current_player_image, (player_x, player_y))
    
    # Update the screen
    pygame.display.flip()
    
    # Delay to show collision effect
    pygame.time.delay(2000)
    
    # Transition to game over state
    menu_open = True
    game_over = True
    menu_elements = create_menu(game_over=True)

def handle_win():
    """Handle the win state when player reaches the goal score"""
    global win_state, menu_open, menu_elements, current_player_image
    
    win_state = True
    # Change player image to sitting image
    current_player_image = player_win_image
    
    # Clear and redraw the game screen
    screen.fill(WHITE)
    draw_background()
    
    # Draw all game elements
    for car in cars:
        screen.blit(car_image, (car["x"], car["y"]))
    
    # Draw player with victory pose image
    screen.blit(current_player_image, (player_x, player_y))
    
    # Create semi-transparent overlay for win message
    overlay = pygame.Surface((400, 200), pygame.SRCALPHA)
    overlay.fill((200, 255, 200, 200))  # Semi-transparent green
    screen.blit(overlay, (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - 100))
    
    # Display victory message
    win_text = font.render("Victory!", True, GREEN)
    score_text = font.render(f"Final Score: {score}", True, BLACK)
    message_text = font.render("You've mastered Hard Mode!", True, BLACK)
    
    screen.blit(win_text, (SCREEN_WIDTH // 2 - 70, SCREEN_HEIGHT // 2 - 70))
    screen.blit(score_text, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 30))
    screen.blit(message_text, (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 + 10))
    
    # Update the screen
    pygame.display.flip()
    
    # Delay to show win message
    pygame.time.delay(2000)
    
    # Open menu with win options
    menu_open = True
    menu_elements = create_menu(game_over=False, win=True)

def draw_background():
    """Draw the game background"""
    for i in range(2):
        screen.blit(background_image, ((background_offset % SCREEN_WIDTH) - SCREEN_WIDTH * i, 0))

def draw_game_elements():
    """Draw all game elements (player, cars, score, instructions)"""
    # Draw background
    draw_background()
    
    # Draw lane markers if debugging
    draw_lane_markers()
    
    # Draw player
    screen.blit(current_player_image, (player_x, player_y))
    player_rect = pygame.Rect(player_x, player_y, PLAYER_WIDTH, PLAYER_HEIGHT)
    
    if DEBUG_MODE:
        pygame.draw.rect(screen, BLACK, player_rect, 2)  # Player hitbox
    
    # Process and draw cars
    for car in cars[:]:  # Use a copy to safely modify the list
        # Only move cars if player hasn't won
        if not win_state:
            # Hard mode feature: Random chance for cars to accelerate
            if random.random() < 0.01:  # 1% chance each frame
                car["speed"] *= 1.5  # Accelerate by 50%
            
            car["y"] += car["speed"]
            
            # Remove cars that go off screen and add new ones
            if car["y"] < -CAR_HEIGHT or car["y"] > SCREEN_HEIGHT:
                cars.remove(car)
                cars.append(create_car())
                continue
        
        # Draw car
        screen.blit(car_image, (car["x"], car["y"]))
        car_rect = pygame.Rect(car["x"], car["y"], CAR_WIDTH, CAR_HEIGHT)
        
        if DEBUG_MODE:
            pygame.draw.rect(screen, RED, car_rect, 2)  # Car hitbox
        
        # Check for collision
        if not win_state and check_collision(player_rect, car_rect):
            handle_collision(car)
            return False  # Signal to break out of the rendering loop
    
    # Hard mode features - only enable when not in win state
    if not win_state:
        # Occasionally spawn car clusters
        if random.random() < 0.005 and score > 10:  # 0.5% chance each frame after score > 10
            car_cluster = create_car_cluster()
            cars.extend(car_cluster)
        
        # Periodically change car speeds
        if random.random() < 0.02:  # 2% chance each frame
            for car in cars:
                # 50% chance to speed up, 50% chance to slow down
                speed_factor = 1.2 if random.random() < 0.5 else 0.8
                car["speed"] *= speed_factor
    
    # Display score and instructions
    score_text = font.render(f"Score: {score}/{WIN_SCORE}", True, BLACK)
    instruction_text = instruction_font.render("Press ESC for menu", True, BLACK)
    hold_text = instruction_font.render("Hold SPACE to move", True, BLACK)
    
    screen.blit(score_text, (10, 10))
    screen.blit(instruction_text, (SCREEN_WIDTH - 160, 10))
    screen.blit(hold_text, (SCREEN_WIDTH - 160, 30))
    
    return True  # Signal to continue rendering

def return_to_launcher():
    """Exit the current game and return to the launcher"""
    python_executable = sys.executable
    launcher_file = os.path.join(base_path, "Launcher.py")
    
    try:
        pygame.quit()
        subprocess.run([python_executable, launcher_file])
        sys.exit()
    except Exception as e:
        print(f"Error returning to launcher: {e}")

# Initialize game by creating cars
for _ in range(8):  # More cars in hard mode
    cars.append(create_car())

# Game loop
running = True
while running:
    time_delta = clock.tick(FPS)/1000.0
    
    # Process events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        # Handle escape key to open/close menu
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                menu_open = not menu_open
                if menu_open:
                    menu_elements = create_menu(game_over=False)
                else:
                    manager.clear_and_reset()
                    menu_elements = None
        
        # Process UI events
        if menu_open:
            if event.type == pygame.USEREVENT:
                if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                    if game_over or win_state:  # Handle both game over and win menus the same way
                        if event.ui_element == menu_elements[1]:  # Restart button
                            reset_game()
                            menu_open = False
                            manager.clear_and_reset()
                            menu_elements = None
                        elif event.ui_element == menu_elements[2]:  # Change Mode button
                            return_to_launcher()
                        elif event.ui_element == menu_elements[3]:  # Quit button
                            running = False
                    else:
                        # Regular menu handling
                        if event.ui_element == menu_elements[1]:  # Continue button
                            menu_open = False
                            manager.clear_and_reset()
                            menu_elements = None
                        elif event.ui_element == menu_elements[2]:  # Restart button
                            reset_game()
                            menu_open = False
                            manager.clear_and_reset()
                            menu_elements = None
                        elif event.ui_element == menu_elements[3]:  # Change Mode button
                            return_to_launcher()
                        elif event.ui_element == menu_elements[4]:  # Quit button
                            running = False
            
            # Process all UI events - this should be aligned with the first if, not inside it
            manager.process_events(event)
    
    # Clear the screen
    screen.fill(WHITE)
    
    # Handle game state
    if not menu_open:
        # Handle player movement with space key
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE]:
            handle_player_movement()
        
        # Check for win condition
        if score >= WIN_SCORE and not win_state:
            handle_win()
            continue
        
        # Draw all game elements
        if not draw_game_elements():
            continue  # Skip the rest of this loop iteration if collision occurred
        
        # Check AFK status
        if not game_over and not win_state:
            detect_afk(last_move_time, afk_limit)
    else:
        # If menu is open, render the game in background
        draw_background()
        draw_lane_markers()
        
        # Draw player and cars
        screen.blit(current_player_image, (player_x, player_y))
        if DEBUG_MODE:
            pygame.draw.rect(screen, BLACK, pygame.Rect(player_x, player_y, PLAYER_WIDTH, PLAYER_HEIGHT), 2)
        
        for car in cars:
            screen.blit(car_image, (car["x"], car["y"]))
            if DEBUG_MODE:
                pygame.draw.rect(screen, RED, pygame.Rect(car["x"], car["y"], CAR_WIDTH, CAR_HEIGHT), 2)
        
        # Display score
        score_text = font.render(f"Score: {score}", True, BLACK)
        screen.blit(score_text, (10, 10))
        
        # Dim the game screen under the menu
        dim_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        dim_surface.fill((0, 0, 0, 128))  # Semi-transparent black
        screen.blit(dim_surface, (0, 0))
        
        # Update and draw UI
        manager.update(time_delta)
        manager.draw_ui(screen)
    
    # Update display
    pygame.display.flip()

pygame.quit()