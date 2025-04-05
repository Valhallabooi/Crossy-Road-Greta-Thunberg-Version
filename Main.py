import pygame
import random
import sys
import os

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

# Game constants
STEP_SIZE = 40
SCALE_FACTOR = 2
SAFE_DISTANCE = STEP_SIZE * 4
LANE_WIDTH = STEP_SIZE * 2

# Player settings
PLAYER_WIDTH = 40
PLAYER_HEIGHT = 40
player_x = 0  # Start near the left edge
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

# Load and scale images
try:
    player_image = pygame.image.load(os.path.join(base_path, "Greta_Thunberg.png"))
    car_image = pygame.image.load(os.path.join(base_path, "car.png"))
    background_image = pygame.image.load(os.path.join(base_path, "background.png"))
    
    # Scale images
    player_image = pygame.transform.scale(player_image, 
                                          (PLAYER_WIDTH * SCALE_FACTOR, PLAYER_HEIGHT * SCALE_FACTOR))
    car_image = pygame.transform.scale(car_image, 
                                      (CAR_WIDTH * SCALE_FACTOR, CAR_HEIGHT * SCALE_FACTOR))
    background_image = pygame.transform.scale(background_image, 
                                              (SCREEN_WIDTH, SCREEN_HEIGHT))
except pygame.error as e:
    print(f"Error loading image: {e}")
    pygame.quit()
    sys.exit()

# Update dimensions to match scaled images
PLAYER_WIDTH *= SCALE_FACTOR
PLAYER_HEIGHT *= SCALE_FACTOR
CAR_WIDTH *= SCALE_FACTOR
CAR_HEIGHT *= SCALE_FACTOR

def create_car():
    """Create a new car with proper lane positioning and safe distance from other cars"""
    num_lanes = SCREEN_WIDTH // LANE_WIDTH
    attempts = 0
    max_attempts = 10
    
    lane_number = random.randint(0, num_lanes - 1)
    lane_x = lane_number * LANE_WIDTH + LANE_WIDTH // 2  # Center of lane
    
    while attempts < max_attempts:
        # Decide car spawning position and direction
        car_y = random.choice([-CAR_HEIGHT, SCREEN_HEIGHT])
        car_direction = 1 if car_y == -CAR_HEIGHT else -1
        car_speed = random.randint(car_speed_min, car_speed_max) * car_direction
        
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
        lane_number = (lane_number + 1) % num_lanes
        lane_x = lane_number * LANE_WIDTH + LANE_WIDTH // 2
    
    # Fall back to last attempted position
    return {"x": lane_x - CAR_WIDTH // 2, "y": car_y, "speed": car_speed, "lane": lane_number}

def draw_lane_markers():
    """Draw lane markers for debugging"""
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

def handle_player_movement(key):
    """Handle player movement and score update"""
    global player_x, score, background_offset
    
    if player_x < SCREEN_WIDTH // 2 - PLAYER_WIDTH // 2:  # Move player until center
        player_x += STEP_SIZE
        score += 1
    else:  # Move background and obstacles instead
        background_offset -= STEP_SIZE
        score += 1
        for car in cars:
            car["x"] -= STEP_SIZE

# Add initial cars
for _ in range(5):
    cars.append(create_car())

# Background scrolling offset
background_offset = 0

# Game loop
running = True
while running:
    screen.fill(WHITE)

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:  # Space to move player
                handle_player_movement(event.key)

    # Draw background (looping)
    for i in range(2):
        screen.blit(background_image, ((background_offset % SCREEN_WIDTH) - SCREEN_WIDTH * i, 0))
        
    # Draw lane markers for debugging
    draw_lane_markers()
    
    # Draw player
    screen.blit(player_image, (player_x, player_y))
    player_rect = pygame.Rect(player_x, player_y, PLAYER_WIDTH, PLAYER_HEIGHT)
    pygame.draw.rect(screen, BLACK, player_rect, 2)  # Player hitbox

    # Update and draw cars
    for car in cars[:]:  # Use a copy to safely modify the list
        car["y"] += car["speed"]
        
        # Remove cars that go off screen and add new ones
        if car["y"] < -CAR_HEIGHT or car["y"] > SCREEN_HEIGHT:
            cars.remove(car)
            cars.append(create_car())
            continue
        
        # Draw car and hitbox
        screen.blit(car_image, (car["x"], car["y"]))
        car_rect = pygame.Rect(car["x"], car["y"], CAR_WIDTH, CAR_HEIGHT)
        pygame.draw.rect(screen, RED, car_rect, 2)
        
        # Collision detection
        if check_collision(player_rect, car_rect):
            print("Game Over!")
            print(f"Your final score: {score}")
            pygame.quit()
            sys.exit()

    # Display score
    score_text = font.render(f"Score: {score}", True, BLACK)
    screen.blit(score_text, (10, 10))

    # Update display and control frame rate
    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()