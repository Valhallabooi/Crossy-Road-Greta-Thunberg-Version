import pygame
import pygame_gui
import sys
import os
import subprocess

# Initialize pygame
pygame.init()

# Screen dimensions and setup
SCREEN_WIDTH = 500
SCREEN_HEIGHT = 400
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Crossy Road - Mode Selection")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)

# Clock for controlling frame rate
clock = pygame.time.Clock()
FPS = 30

# Initialize pygame_gui manager
manager = pygame_gui.UIManager((SCREEN_WIDTH, SCREEN_HEIGHT))

# Get the base directory of the script
base_path = os.path.dirname(os.path.abspath(__file__))

# Load background image for launcher
try:
    background_image = pygame.image.load(os.path.join(base_path, "background.png"))
    background_image = pygame.transform.scale(background_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
except:
    # If loading fails, use a solid color
    background_image = None

# Create title and buttons
title_font = pygame.font.Font(None, 48)
title_text = title_font.render("Crossy Road", True, BLACK)
subtitle_font = pygame.font.Font(None, 28)
subtitle_text = subtitle_font.render("Greta Thunberg Edition", True, BLACK)

# Create a panel for the menu
panel = pygame_gui.elements.UIPanel(
    relative_rect=pygame.Rect((SCREEN_WIDTH//2-150, 100), (300, 240)),
    manager=manager
)

# Mode selection text
select_label = pygame_gui.elements.UILabel(
    relative_rect=pygame.Rect((50, 20), (200, 30)),
    text="Select Game Mode:",
    manager=manager,
    container=panel
)

# Regular Mode button
regular_button = pygame_gui.elements.UIButton(
    relative_rect=pygame.Rect((30, 60), (240, 60)),
    text="Regular Mode",
    manager=manager,
    container=panel,
    object_id="regular_mode"
)

# Hard Mode button
hard_button = pygame_gui.elements.UIButton(
    relative_rect=pygame.Rect((30, 130), (240, 60)),
    text="Hard Mode",
    manager=manager,
    container=panel,
    object_id="hard_mode"
)

# Quit button
quit_button = pygame_gui.elements.UIButton(
    relative_rect=pygame.Rect((80, 200), (140, 30)),
    text="Quit Game",
    manager=manager,
    container=panel
)

def launch_game_mode(mode):
    """Launch the selected game mode"""
    python_executable = sys.executable
    
    if mode == "regular":
        game_file = os.path.join(base_path, "Regular_Mode.py")  # Changed from Main.py
    else:
        game_file = os.path.join(base_path, "Hard_Mode.py")
    
    try:
        # Close the launcher
        pygame.quit()
        # Launch the selected game file
        subprocess.run([python_executable, game_file])
        # Exit the launcher after the game exits
        sys.exit()
    except Exception as e:
        print(f"Error launching game: {e}")
        return

# Game loop
running = True
while running:
    time_delta = clock.tick(FPS)/1000.0
    
    # Process events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        # Process button clicks
        if event.type == pygame.USEREVENT:
            if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                if event.ui_element == regular_button:
                    launch_game_mode("regular")
                elif event.ui_element == hard_button:
                    launch_game_mode("hard")
                elif event.ui_element == quit_button:
                    running = False
        
        # Process all UI events
        manager.process_events(event)
    
    # Clear the screen
    screen.fill(WHITE)
    
    # Draw background image if available
    if background_image:
        screen.blit(background_image, (0, 0))
        
        # Add semi-transparent overlay for better text readability
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((255, 255, 255, 128))  # Semi-transparent white
        screen.blit(overlay, (0, 0))
    
    # Draw title
    screen.blit(title_text, (SCREEN_WIDTH//2 - title_text.get_width()//2, 30))
    screen.blit(subtitle_text, (SCREEN_WIDTH//2 - subtitle_text.get_width()//2, 70))
    
    # Update and draw UI
    manager.update(time_delta)
    manager.draw_ui(screen)
    
    # Update display
    pygame.display.flip()

# Clean up
pygame.quit()
sys.exit()