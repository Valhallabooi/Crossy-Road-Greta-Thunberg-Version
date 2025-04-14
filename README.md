# Crossy Road - Greta Thunberg Edition

A fun and challenging adaptation of the classic Crossy Road game featuring Greta Thunberg as the main character. Navigate through traffic and avoid collisions while increasing your score!

## Installation

### Required Software:
1. **Python 3.7+** - Download from [python.org](https://www.python.org/downloads/)
2. **Required Python packages**:
python -m pip install pygame pygame_gui

### Running the Game:
1. Make sure all game files are in the same directory
2. Run the launcher to start:
python Launcher.py

## Game Files
Make sure you have the following files in your game directory:
- `Launcher.py` - Game launcher with mode selection
- `Regular_Mode.py` - Standard difficulty game mode
- `Hard_Mode.py` - More challenging game mode
- Image files:
  - `background.png` - Game background
  - `car.png` - Car obstacles
  - `Greta_Thunberg.png` - Player character
  - `How_dare_you.png` - Collision animation

## How to Play

### Controls:
- **SPACE**: Hold to move forward
- **ESC**: Open/close menu

### Gameplay:
- Hold SPACE to advance forward through traffic
- Avoid colliding with cars
- Your score increases as you move forward
- Beware of being idle too long - the game will end if you're AFK!

### Game Modes:
- **Regular Mode**: Standard gameplay experience
- **Hard Mode**: Faster cars, more obstacles, and less forgiving gameplay

## Features
- Smooth, lane-based movement system
- Dynamic car obstacles that move vertically
- Collision detection with "How dare you!" animation
- AFK detection with warning system
- Background scrolling to simulate continuous movement
- Score tracking
- Pause menu with continue, restart, and quit options
- Game over screen with final score

## Development Notes
- Debug mode can be enabled by setting `DEBUG_MODE = True` at the top of the game files
- Lane markers and hitboxes are displayed when debug mode is active

---

Developed by: Martin Kleppa  
Project for: YFF uke 3 2025  
Version: 1.0