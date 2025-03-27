# Foot Activated Asteroid Game for Ankle Physiotherapy
A flex sensor-enabled ankle sleeve that acts as a controller for a gamified visual interface. The aim of this device is to detect dorsiflexion, plantarflexion, eversion and inversion motions  used in physiotherapy, to provide an engaging form of exercise and increase adherence to the patient’s exercise regimen. Using this device allows the user to increase their ankle strength and range of motion, and monitor their progress through different difficulty levels. 

This repository contains the Asteroid Blaster game built using Python and the Pygame library. The game allows players to control a spaceship via ankle movements, thanks to a flexible sensor setup and calibration interface. 

## Overview

- **Single Interface for All Actions**  
  Users only need to interact with the main user interface (UI) to perform device calibration, choose difficulty levels, or restart the game. There is no need to open multiple scripts or additional software packages.
  
- **Multiple Difficulty Levels**  
  Three difficulty settings (Levels 1–3) provide progressive challenges. Speed, asteroid frequency, and game mechanics (e.g., shooting) are adjusted for each difficulty level.

- **Calibration Functionality**  
  A built-in calibration interface ensures the system adapts to each user's unique range of ankle motion. This helps to accurately map ankle movements to in-game controls.

## Features

1. **Ankle-Based Control**  
   - Uses flexible sensors to detect ankle angles and translate them into up/down/left/right game inputs.

2. **Easy Menu Navigation**  
   - Main menu allows selection of difficulty levels, calibration, and restarting the game.

3. **Game Difficulty Levels**  
   - **Level 1**: Slower and fewer asteroids—perfect for beginners.  
   - **Level 2**: Increased speed and asteroid count—an intermediate challenge.  
   - **Level 3**: Shooting mechanics and more complex asteroid behaviors—advanced play.

4. **Calibration System**  
   - Step-by-step instructions guide users to set their neutral, left-max, and right-max ankle positions.  
   - Saves calibration data so that each session tailors control sensitivity to individual user needs.

5. **User-Friendly Design**  
   - Consolidates all functionality (calibration, game launch, difficulty selection) within a single UI built in Pygame.

## Requirements

- **Python 3.7+**  
- **Pygame** (version 2.0 or later is recommended)

You can install the dependencies with: pip install pygame


## How to Run

1. **Clone the Repository**  

2. **Launch the Game**  
   ```bash
   python game.py
   ```
   ```bash
   python game_Jason.py
   ```
   - This will start the Pygame window and load the main menu.

3. **Navigation**  
   - **Select “Calibration”** to set up or adjust your ankle sensor’s calibration data.  
   - **Choose Difficulty** (Level 1, 2, or 3) to start the game.  
   - **Restart/Return** to the main menu at any time to change difficulty or re-run calibration.

## Usage Tips

- **Sensor Setup**: Ensure your flexible sensors are properly placed on the ankle and connected before running the game.  
- **Keyboard Alternative**: If sensors are not available, the game supports keyboard input for directional movement and shooting (where applicable).  
- **Recalibration**: Perform calibration whenever you notice drift or if multiple users share the same setup.

## Contributing

Contributions are welcome! Feel free to open issues for bugs or suggestions, and submit pull requests for improvements.

