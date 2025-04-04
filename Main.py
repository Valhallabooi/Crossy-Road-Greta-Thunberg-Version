import pygame
import random
import sys
import os

# Get the base directory of the script
base_path = os.path.dirname(os.path.abspath(__file__))

# Initialize pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Crossy Road")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)

# Clock for controlling frame rate
clock = pygame.time.Clock()

# Player settings
PLAYER_WIDTH = 40
PLAYER_HEIGHT = 40
player_x = 10  # Start near the left edge
player_y = SCREEN_HEIGHT // 2 - PLAYER_HEIGHT // 2  # Center vertically
STEP_SIZE = 40  # Movement step size

# Car settings
CAR_WIDTH = 60
CAR_HEIGHT = 40
car_speed_min = 3  # Minimum car speed
car_speed_max = 7  # Maximum car speed
cars = []

# Score system
score = 0
font = pygame.font.Font(None, 36)  # Font for displaying the score

# Load images using relative paths
try:
    player_image = pygame.image.load(os.path.join(base_path, "Greta_Thunberg.png"))
    car_image = pygame.image.load(os.path.join(base_path, "car.png"))
    background_image = pygame.image.load(os.path.join(base_path, "background.png"))  # Background
except pygame.error as e:
    print(f"Error loading image: {e}")
    pygame.quit()
    sys.exit()

# Scale up the images
SCALE_FACTOR = 2
player_image = pygame.transform.scale(player_image, (PLAYER_WIDTH * SCALE_FACTOR, PLAYER_HEIGHT * SCALE_FACTOR))
car_image = pygame.transform.scale(car_image, (CAR_WIDTH * SCALE_FACTOR, CAR_HEIGHT * SCALE_FACTOR))
background_image = pygame.transform.scale(background_image, (SCREEN_WIDTH, SCREEN_HEIGHT))

# Update player and car dimensions to match the scaled images
PLAYER_WIDTH *= SCALE_FACTOR
PLAYER_HEIGHT *= SCALE_FACTOR
CAR_WIDTH *= SCALE_FACTOR
CAR_HEIGHT *= SCALE_FACTOR

# Function to create a new car
def create_car():
    # Align car spawn positions to every other column based on STEP_SIZE * 2
    lane_x = random.randint(0, SCREEN_WIDTH // (STEP_SIZE * 2) - 1) * (STEP_SIZE * 2)
    car_y = random.choice([-CAR_HEIGHT, SCREEN_HEIGHT])  # Cars start off-screen vertically
    car_direction = 1 if car_y == -CAR_HEIGHT else -1  # Direction is now vertical
    car_speed = random.randint(car_speed_min, car_speed_max) * car_direction

    # Ensure there is a gap between cars for the player to pass through
    for existing_car in cars:
        if abs(existing_car["x"] - lane_x) < PLAYER_WIDTH + STEP_SIZE:
            # If the gap is too small, adjust the lane_x to create a larger gap
            lane_x += STEP_SIZE * 2
            lane_x %= SCREEN_WIDTH  # Wrap around to stay within screen bounds

    return {"x": lane_x, "y": car_y, "speed": car_speed}

# Add initial cars to the list
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
            if event.key == pygame.K_SPACE:  # Space key to move player
                if player_x < SCREEN_WIDTH // 2 - PLAYER_WIDTH // 2:  # Move player until center
                    player_x += STEP_SIZE
                    score += 1  # Increase score when moving right
                else:  # Move background and obstacles instead of the player
                    background_offset -= STEP_SIZE
                    score += 1
                    for car in cars:
                        car["x"] -= STEP_SIZE

    # Draw background (looping)
    for i in range(2):  # Simplify background drawing
        screen.blit(background_image, ((background_offset % SCREEN_WIDTH) - SCREEN_WIDTH * i, 0))

    # Draw player
    screen.blit(player_image, (player_x, player_y))

    # Update and draw cars
    for car in cars:
        car["y"] += car["speed"]
        if car["y"] < -CAR_HEIGHT or car["y"] > SCREEN_HEIGHT:
            cars.remove(car)
            cars.append(create_car())
        screen.blit(car_image, (car["x"], car["y"]))

        # Debugging: Draw car hitboxes
        pygame.draw.rect(screen, RED, (car["x"], car["y"], CAR_WIDTH, CAR_HEIGHT), 2)

        # Collision detection
        if (player_x < car["x"] + CAR_WIDTH and
            player_x + PLAYER_WIDTH > car["x"] and
            player_y < car["y"] + CAR_HEIGHT and
            player_y + PLAYER_HEIGHT > car["y"]):
            print("Game Over!")
            print(f"Your final score: {score}")
            pygame.quit()
            sys.exit()

    # Debugging: Draw player hitbox
    pygame.draw.rect(screen, BLACK, (player_x, player_y, PLAYER_WIDTH, PLAYER_HEIGHT), 2)

    # Display score
    score_text = font.render(f"Score: {score}", True, BLACK)
    screen.blit(score_text, (10, 10))

    # Update display
    pygame.display.flip()

    # Control frame rate
    clock.tick(30)

pygame.quit()