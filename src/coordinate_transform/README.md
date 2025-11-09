# Coordinate Transformation Module

This module converts game world coordinates into robot workspace coordinates.

## Responsibilities

- Transform NoLimits Coaster 2 coordinates to robot base frame
- Scale motion to fit within robot workspace
- Apply seat mounting offset (TCP transformation)
- Perform coordinate system conversions (orientation, rotation)
- Validate transformed coordinates are within safe limits

## Key Components

- `transform_engine.py`: Main coordinate transformation logic
- `scaling.py`: Motion scaling algorithms
- `tcp_calculator.py`: Calculate TCP position from game data
- `workspace_validator.py`: Ensure coordinates are safe and reachable

## Coordinate Systems

- **Game World**: NoLimits Coaster 2 world space (right-handed, Z-up)
- **Robot Base**: ABB IRB-6600 base frame (right-handed, Z-up)
- **TCP**: Tool Center Point (seat mounting point)
