# ABB-IRB-6600-Robotic-Simulator

A project to transform an ABB IRB-6600 industrial robotic manipulator into a motion simulator synchronized with NoLimits Coaster 2.

Special thanks to https://github.com/bestdani/py_nl2telemetry/tree/public for the NL2 data. 

## Project Overview

This project extracts real-time motion data from NoLimits Coaster 2 (Steam) and translates it into robotic coordinates for the ABB IRB-6600 manipulator. The system simulates a coaster seat mounted to the robot's TCP (Tool Center Point), providing a physical motion experience synchronized with the virtual roller coaster.

<img width="1695" height="905" alt="image" src="https://github.com/user-attachments/assets/49047968-2853-4378-82df-677828dab8fa" />

Ideally we want in the end to mount a "fictive" seat to the robotic tool center point (TCP). Thus a conversion between actual movements in the game and the seat will be transformed. Seat goes backwards when coast goes uphill, etc etc. 

## Project Checklist

### Phase 1: Game Data Extraction
- [x] Research NoLimits Coaster 2 API/SDK documentation
- [x] Identify available data streams (position, velocity, acceleration, orientation)
- [x] Implement Steam API integration (if required)
- [x] Create game data capture module
- [x] Parse coaster track metadata (G-forces, banking, pitch)
- [x] Implement real-time data streaming pipeline
- [x] Add data validation and error handling
- [x] Create data logging system for debugging
- [ ] Test with multiple coaster designs

Phase 1 is complete with data extraction:
<img width="408" height="134" alt="image" src="https://github.com/user-attachments/assets/47121083-3a14-419b-9f03-4d0936c18374" />


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

### NoLimits 2 Telemetry (Ready to Use!)

The NoLimits Coaster 2 data extraction module is now complete and ready to test!

**5-Minute Quick Start:**

1. Install dependencies:
   ```powershell
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Start NoLimits Coaster 2 and ride a coaster

3. Run the test:
   ```powershell
   python tools\test_nlc2_telemetry.py
   ```

**Documentation:**
- 📖 [Quick Start Guide](docs/QUICKSTART.md) - Get running in 5 minutes
- 📚 [Integration Guide](docs/NOLIMITS2_INTEGRATION.md) - Complete documentation
- 🧪 [Test Script](tools/test_nlc2_telemetry.py) - Interactive testing tool

**What's Working:**
- ✅ UDP telemetry connection to NoLimits 2
- ✅ Real-time data parsing (position, velocity, acceleration, G-forces)
- ✅ Data validation and error handling
- ✅ Recording to CSV files
- ✅ Callback-based processing
- ✅ Comprehensive test suite

**Next Steps:**
- Coordinate transformation (game → robot workspace)
- Motion scaling and filtering
- Safety validation
- Robot integration

## Safety Notice

⚠️ **WARNING**: This system controls an industrial robot capable of causing serious injury or death. Always follow proper safety procedures, maintain emergency stop accessibility, and never operate without appropriate safety barriers and personnel training.

## License

*(To be determined)*
