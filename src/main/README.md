# Main Application

This is the main controller that orchestrates all modules.

## Responsibilities

- Initialize all subsystems
- Manage application lifecycle
- Coordinate data flow between modules
- Provide operator interface
- Handle configuration loading
- Implement main control loop

## Key Components

- `app.py`: Main application entry point
- `controller.py`: System orchestration
- `config_manager.py`: Configuration management
- `ui.py`: Operator interface/dashboard

## Startup Sequence

1. Load configuration
2. Initialize safety systems
3. Connect to robot
4. Connect to game
5. Run self-tests
6. Enter ready state
7. Wait for operator start command
