# Motion Control Module

This module plans and executes robot motion trajectories.

## Responsibilities

- Generate smooth robot trajectories from target positions
- Implement inverse kinematics for ABB IRB-6600
- Apply velocity and acceleration limits
- Queue and buffer motion commands
- Interface with ABB robot controller (RAPID/EGM)
- Minimize motion latency

## Key Components

- `trajectory_planner.py`: Generate smooth motion paths
- `inverse_kinematics.py`: IK solver for ABB IRB-6600
- `motion_buffer.py`: Queue management and buffering
- `robot_interface.py`: Communication with ABB controller
- `latency_optimizer.py`: Minimize end-to-end delay

## Performance Targets

- Latency: <50ms game-to-robot
- Update rate: 100Hz minimum
- Trajectory smoothness: Jerk-limited profiles
