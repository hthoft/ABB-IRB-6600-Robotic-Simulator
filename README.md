# ABB-IRB-6600-Robotic-Simulator

A project to transform an ABB IRB-6600 industrial robotic manipulator into a motion simulator synchronized with NoLimits Coaster 2.

## Project Overview

This project extracts real-time motion data from NoLimits Coaster 2 (Steam) and translates it into robotic coordinates for the ABB IRB-6600 manipulator. The system simulates a coaster seat mounted to the robot's TCP (Tool Center Point), providing a physical motion experience synchronized with the virtual roller coaster.

## Project Checklist

### Phase 1: Game Data Extraction
- [ ] Research NoLimits Coaster 2 API/SDK documentation
- [ ] Identify available data streams (position, velocity, acceleration, orientation)
- [ ] Implement Steam API integration (if required)
- [ ] Create game data capture module
- [ ] Parse coaster track metadata (G-forces, banking, pitch)
- [ ] Implement real-time data streaming pipeline
- [ ] Add data validation and error handling
- [ ] Create data logging system for debugging
- [ ] Test with multiple coaster designs

### Phase 2: Coordinate Interpolation & Motion Planning
- [ ] Define coordinate transformation (game world → robot workspace)
- [ ] Implement inverse kinematics for ABB IRB-6600
- [ ] Create motion scaling algorithms (coaster motion → robot motion)
- [ ] Develop trajectory smoothing and filtering
- [ ] Implement real-time interpolation engine
- [ ] Add workspace boundary checking
- [ ] Create motion preview/visualization tool
- [ ] Test motion profiles against robot specifications
- [ ] Optimize for minimal latency (<50ms target)
- [ ] Implement motion queuing and buffering

### Phase 3: Safety & Security Systems
- [ ] Define safety zones and workspace limits
- [ ] Implement emergency stop (E-stop) handler
- [ ] Create watchdog timer for connection monitoring
- [ ] Add heartbeat system between game and robot
- [ ] Implement velocity limiting
- [ ] Add acceleration limiting
- [ ] Create fault detection system
- [ ] Implement safe state recovery procedures
- [ ] Add motion range validation
- [ ] Create operator override controls
- [ ] Implement safety interlocks
- [ ] Add collision detection (virtual)
- [ ] Create safety audit logging
- [ ] Test all emergency scenarios
- [ ] Document safety procedures

### Phase 4: Robot Integration
- [ ] Set up ABB Robot Studio environment
- [ ] Configure RAPID programming interface
- [ ] Implement TCP/IP communication protocol
- [ ] Create robot control module
- [ ] Test basic movement commands
- [ ] Calibrate robot workspace
- [ ] Mount seat fixture to robot flange
- [ ] Calculate TCP offset for seat
- [ ] Test low-speed movements
- [ ] Gradually increase motion complexity

### Phase 5: System Integration & Testing
- [ ] Integrate all modules into main controller
- [ ] Create configuration management system
- [ ] Implement comprehensive logging
- [ ] Build operator interface/dashboard
- [ ] Perform end-to-end testing
- [ ] Conduct safety validation tests
- [ ] Optimize performance
- [ ] Create user documentation
- [ ] Create maintenance documentation

### Phase 6: Polish & Deployment
- [ ] Fine-tune motion feel
- [ ] Add customization options
- [ ] Create installation guide
- [ ] Perform final safety audit
- [ ] Create demo scenarios
- [ ] Document known limitations

## Project Structure

```
ABB-IRB-6600-Robotic-Simulator/
├── src/                          # Source code
│   ├── game_interface/          # NoLimits Coaster 2 data extraction
│   ├── coordinate_transform/    # Game to robot coordinate conversion
│   ├── motion_control/          # Robot motion planning & control
│   ├── safety/                  # Safety systems & watchdogs
│   └── main/                    # Main application controller
├── config/                       # Configuration files
├── docs/                         # Documentation
├── tests/                        # Unit and integration tests
├── data/                         # Sample data & logs
├── tools/                        # Utility scripts
└── extern/                       # External dependencies

```

## Quick Start

*(Coming soon)*

## Safety Notice

⚠️ **WARNING**: This system controls an industrial robot capable of causing serious injury or death. Always follow proper safety procedures, maintain emergency stop accessibility, and never operate without appropriate safety barriers and personnel training.

## License

*(To be determined)*
