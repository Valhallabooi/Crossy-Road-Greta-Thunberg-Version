import pygame
import random
import sys
import os
import pygame_gui

# Get the base directory of the script
base_path = os.path.dirname(os.path.abspath(__file__))

# Initialize pygame
pygame.init()

# Screen dimensions and setup
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Crossy Road")

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
if DEBUG_MODE:
    print("Debugging mode is enabled.")

# Game constants
STEP_SIZE = 40
SCALE_FACTOR = 2
SAFE_DISTANCE = STEP_SIZE * 4
LANE_WIDTH = STEP_SIZE * 3

# Player settings
PLAYER_WIDTH = 40
PLAYER_HEIGHT = 40
player_x = 10  # Start near the left edge
player_y = SCREEN_HEIGHT // 2 - PLAYER_HEIGHT // 2  # Center vertically

# Car settings
CAR_WIDTH = 60
CAR_HEIGHT = 40
car_speed_min = 3
car_speed_max = 7
cars = []

# Score system
score = 0
font = pygame.font.Font(None, 36)
instruction_font = pygame.font.Font(None, 24)

# Game state variables
background_offset = 0
menu_open = False
menu_elements = None
game_over = False
move_speed = 8
last_move_time = pygame.time.get_ticks() / 1000  # Initialize with current time
afk_limit = 10  # Number of seconds before considering player AFK
collision_state = False  # Tracks if the player is in a collision

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

# Initialize pygame_gui manager
manager = pygame_gui.UIManager((SCREEN_WIDTH, SCREEN_HEIGHT))

# Initialize the current player image
current_player_image = player_image

# Helper functions
def create_car():
    """Create a new car with proper lane positioning and safe distance from other cars"""
    num_lanes = SCREEN_WIDTH // LANE_WIDTH
    attempts = 0
    max_attempts = 10
    
    # Use all lanes, not just even ones
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
        # Make sure max is at least min
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
            # For cars coming from top
            if car_y == -CAR_HEIGHT and car["y"] < SCREEN_HEIGHT // 2:
                if abs(car["y"] - car_y) < SAFE_DISTANCE:
                    too_close = True
                    break
            # For cars coming from bottom
            elif car_y == SCREEN_HEIGHT and car["y"] > SCREEN_HEIGHT // 2:
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

# Add a function to create a cluster of cars
def create_car_cluster():
    """Create a challenging cluster of cars in adjacent lanes"""
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
    """
    Detect if the player is AFK (Away From Keyboard) and notify them.
    If the player remains AFK for too long, end the game.
    """
    global menu_open, game_over, menu_elements

    current_time = pygame.time.get_ticks() / 1000  # Convert milliseconds to seconds
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
        
        # Main warning text
        afk_warning = font.render("Move or the game will end!", True, RED)
        screen.blit(afk_warning, (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 - 20))
        
        # Countdown timer text
        timer_text = font.render(f"Time left: {time_left_str} s", True, BLACK)
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
        return  # Skip drawing if debugging is disabled

    num_lanes = SCREEN_WIDTH // LANE_WIDTH
    for i in range(num_lanes + 1):  # +1 for rightmost boundary
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

def create_menu(game_over=False):
    """Create either regular menu or game over menu"""
    # Create a panel for the menu
    panel = pygame_gui.elements.UIPanel(
        relative_rect=pygame.Rect((SCREEN_WIDTH//2-150, SCREEN_HEIGHT//2-100), (300, 200)),
        manager=manager
    )
    
    if game_over:
        # Game over menu with title and subtitle
        title_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((50, 20), (200, 30)),
            text="Game Over!",
            manager=manager,
            container=panel
        )
        
        # Add final score display
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
        
        # Create buttons for game over menu
        restart_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((50, 110), (200, 40)),
            text="Try Again",
            manager=manager,
            container=panel
        )
        
        # Quit button for game over menu
        quit_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((50, 150), (200, 40)),
            text="Quit Game",
            manager=manager,
            container=panel
        )
        
        return panel, restart_button, quit_button
    else:
        # Regular menu buttons
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
        
        # Quit button for regular menu
        quit_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((50, 130), (200, 40)),
            text="Quit Game",
            manager=manager,
            container=panel
        )
        
        return panel, continue_button, restart_button, quit_button

def reset_game():
    """Reset all game variables to starting state"""
    global player_x, player_y, score, background_offset, cars, game_over, last_move_time, collision_state, current_player_image
    
    # Reset AFK timer
    last_move_time = pygame.time.get_ticks() / 1000
    
    # Reset collision state
    collision_state = False
    
    # Reset current player image to normal
    current_player_image = player_image
    
    # Reset player position
    player_x = 10
    player_y = SCREEN_HEIGHT // 2 - PLAYER_HEIGHT // 2
    
    # Reset score and background
    score = 0
    background_offset = 0
    game_over = False
    
    # Clear and recreate cars
    cars.clear()
    for _ in range(5):
        cars.append(create_car())

def handle_player_movement():
    """Handle continuous player movement while space is held"""
    global player_x, background_offset, score, last_move_time, car_speed_min, car_speed_max
    
    # Update last move time whenever player moves
    last_move_time = pygame.time.get_ticks() / 1000
    
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
            
            # Track the previous lane to detect when we cross into a new lane
            previous_lane = current_lane
            new_lane = (player_x + PLAYER_WIDTH//2) // LANE_WIDTH
            
            # Increase score when we cross into a new lane
            if new_lane > previous_lane:
                score += 1
    
    # Increase difficulty as score increases
    if score > 0 and score % 10 == 0:
        # Increase car speed every 10 points
        car_speed_min = min(car_speed_min + 0.5, 10)
        car_speed_max = min(car_speed_max + 0.5, 15)

def handle_collision(car):
    """Handle collision between player and car"""
    global collision_state, current_player_image, menu_open, game_over, menu_elements
    
    collision_state = True  # Set collision state to True
    current_player_image = player_collision_image  # Switch to collision image
    
    if DEBUG_MODE:
        print("Collision detected! Switching to collision image.")
    
    # Clear the screen to remove the previously drawn player image
    screen.fill(WHITE)
    
    # Redraw the background
    for i in range(2):
        screen.blit(background_image, ((background_offset % SCREEN_WIDTH) - SCREEN_WIDTH * i, 0))
    
    # Redraw all cars except the one that caused the collision
    for other_car in cars:
        if other_car != car:  # Skip the car that caused the collision
            screen.blit(car_image, (other_car["x"], other_car["y"]))
    
    # Display the "How dare you!" quote
    quote_text = font.render("How dare you!", True, RED)
    screen.blit(quote_text, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 20))
    
    # Draw only the collision image
    screen.blit(current_player_image, (player_x, player_y))
    
    # Update the screen to show the changes immediately
    pygame.display.flip()
    
    # Add a delay to show the collision effect
    pygame.time.delay(2000)  # 2-second delay
    
    # Transition to game over state
    menu_open = True
    game_over = True
    menu_elements = create_menu(game_over=True)

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
        # Random chance for cars to accelerate
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
        if check_collision(player_rect, car_rect):
            handle_collision(car)
            return False  # Signal to break out of the rendering loop
    
    # Occasionally spawn car clusters
    if random.random() < 0.005 and score > 10:  # 0.5% chance each frame after score > 10
        car_cluster = create_car_cluster()
        cars.extend(car_cluster)
    
    # Inside the game loop, periodically change car speeds
    if random.random() < 0.02:  # 2% chance each frame
        for car in cars:
            # 50% chance to speed up, 50% chance to slow down
            speed_factor = 1.2 if random.random() < 0.5 else 0.8
            car["speed"] *= speed_factor
    
    # Display score and instructions
    score_text = font.render(f"Score: {score}", True, BLACK)
    screen.blit(score_text, (10, 10))
    instruction_text = instruction_font.render("Press ESC for menu", True, BLACK)
    screen.blit(instruction_text, (SCREEN_WIDTH - 160, 10))
    hold_text = instruction_font.render("Hold SPACE to move", True, BLACK)
    screen.blit(hold_text, (SCREEN_WIDTH - 160, 30))
    
    return True  # Signal to continue rendering

def draw_menu_background():
    """Draw the background when menu is open"""
    # Draw background
    draw_background()
    
    # Draw lane markers if debugging
    if DEBUG_MODE:
        draw_lane_markers()
    
    # Draw player and cars
    screen.blit(current_player_image, (player_x, player_y))
    
    # Only draw hitboxes if DEBUG_MODE is enabled
    if DEBUG_MODE:
        pygame.draw.rect(screen, BLACK, pygame.Rect(player_x, player_y, PLAYER_WIDTH, PLAYER_HEIGHT), 2)
    
    for car in cars:
        screen.blit(car_image, (car["x"], car["y"]))
        
        # Only draw hitboxes if DEBUG_MODE is enabled
        if DEBUG_MODE:
            pygame.draw.rect(screen, RED, pygame.Rect(car["x"], car["y"], CAR_WIDTH, CAR_HEIGHT), 2)
    
    # Display score
    score_text = font.render(f"Score: {score}", True, BLACK)
    screen.blit(score_text, (10, 10))
    
    # Dim the game screen under the menu
    dim_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    dim_surface.fill((0, 0, 0, 128))  # Semi-transparent black
    screen.blit(dim_surface, (0, 0))

# Initialize game state
for _ in range(5):
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
                    menu_elements = create_menu(game_over=False)  # Regular menu
                else:
                    manager.clear_and_reset()
                    menu_elements = None
        
        # Process UI events
        if menu_open:
            if event.type == pygame.USEREVENT:
                if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                    if game_over:
                        if event.ui_element == menu_elements[1]:  # Restart button (game over menu)
                            reset_game()  # Reset the game only when "Try Again" is pressed
                            menu_open = False
                            manager.clear_and_reset()
                            menu_elements = None
                        elif event.ui_element == menu_elements[2]:  # Quit button (game over menu)
                            running = False
                    else:
                        if event.ui_element == menu_elements[1]:  # Continue button (regular menu)
                            menu_open = False
                            manager.clear_and_reset()
                            menu_elements = None
                        elif event.ui_element == menu_elements[2]:  # Restart button (regular menu)
                            reset_game()
                            menu_open = False
                            manager.clear_and_reset()
                            menu_elements = None
                        elif event.ui_element == menu_elements[3]:  # Quit button (regular menu)
                            running = False
            
            # Process all UI events
            manager.process_events(event)
    
    # Clear the screen
    screen.fill(WHITE)
    
    # Only update game state if menu is not open
    if not menu_open:
        # Get keyboard state
        keys = pygame.key.get_pressed()
        
        # Handle player movement with space key
        if keys[pygame.K_SPACE]:
            handle_player_movement()
            last_move_time = pygame.time.get_ticks() / 1000  # Update last move time
        
        # Draw all game elements
        if not draw_game_elements():
            continue  # Skip the rest of this loop iteration if collision occurred
        
        # Check AFK status
        if not game_over:
            detect_afk(last_move_time, afk_limit)
    else:
        # If menu is open, render the game in background
        draw_menu_background()
        
        # Update and draw UI
        manager.update(time_delta)
        manager.draw_ui(screen)
    
    # Only print debugging info if DEBUG_MODE is enabled
    if DEBUG_MODE:
        print(f"Current player image: {'Collision' if current_player_image == player_collision_image else 'Regular'}")
    
    # Update display
    pygame.display.flip()

pygame.quit()