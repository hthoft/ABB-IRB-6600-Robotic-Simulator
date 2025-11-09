# NoLimits Coaster 2 Integration Guide

This guide explains how to extract telemetry data from NoLimits Coaster 2 for use with the ABB IRB-6600 robotic simulator.

## Table of Contents

1. [Overview](#overview)
2. [How It Works](#how-it-works)
3. [Setup Instructions](#setup-instructions)
4. [Usage Examples](#usage-examples)
5. [Data Format](#data-format)
6. [Troubleshooting](#troubleshooting)

---

## Overview

NoLimits Coaster 2 provides a built-in telemetry system that can export real-time simulation data via UDP network protocol. This allows external applications to receive:

- Position (x, y, z coordinates)
- Velocity vectors
- Acceleration vectors
- Orientation (quaternion)
- G-forces
- Speed
- Camera view mode

Our implementation provides a complete Python interface to capture, parse, and process this telemetry data.

---

## How It Works

### Communication Protocol

NoLimits 2 uses a **UDP-based request/response protocol**:

1. **Client** (our code) sends periodic requests to NoLimits 2
2. **NoLimits 2** responds with telemetry data packets
3. Data is sent in **binary format** (little-endian)
4. Update rate: ~100 Hz when simulation is running

### Network Configuration

- **Default Send Port**: 15151 (where we send requests)
- **Default Receive Port**: 15152 (where we receive data)
- **Protocol**: UDP (connectionless)
- **Host**: 127.0.0.1 (localhost)

### Data Flow

```
┌─────────────────┐         Request Packet         ┌──────────────────┐
│                 │ ──────────────────────────────> │                  │
│   Our Code      │         (UDP:15151)             │  NoLimits 2      │
│   (Python)      │                                 │   (Game)         │
│                 │ <────────────────────────────── │                  │
└─────────────────┘      Telemetry Response         └──────────────────┘
                         (UDP:15152)
```

---

## Setup Instructions

### 1. Enable Telemetry in NoLimits 2

**Important**: NoLimits Coaster 2 has telemetry enabled by default, but you may need to configure it.

1. Start NoLimits Coaster 2
2. Go to **Options** → **Settings**
3. Look for **Telemetry** or **Network** settings
4. Ensure telemetry is enabled
5. Note the port numbers (default: 15151/15152)

### 2. Configure Firewall

If you're having connection issues:

1. Open Windows Firewall settings
2. Allow UDP traffic on ports 15151 and 15152
3. Allow `nolimits2.exe` through the firewall

### 3. Install Python Dependencies

```bash
# Activate your virtual environment
venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

### 4. Test the Connection

Run the test script to verify everything works:

```bash
python tools\test_nlc2_telemetry.py
```

Choose option 1 for basic connection test.

---

## Usage Examples

### Basic Usage - Get Latest State

```python
from src.game_interface import NLC2Connector

# Create connector
connector = NLC2Connector(
    host="127.0.0.1",
    send_port=15151,
    receive_port=15152
)

# Connect and start receiving
connector.connect()
connector.start()

try:
    while True:
        # Get latest coaster state
        state = connector.get_latest_state(timeout=1.0)
        
        if state:
            print(f"Position: {state.position}")
            print(f"Speed: {state.speed:.2f} m/s")
            print(f"G-Force: {state.get_total_g_force():.2f}G")
        
except KeyboardInterrupt:
    pass
finally:
    connector.disconnect()
```

### Using Context Manager

```python
from src.game_interface import NLC2Connector

# Automatically handles connection/disconnection
with NLC2Connector() as connector:
    while True:
        state = connector.get_latest_state()
        if state:
            # Process state
            print(f"Speed: {state.speed:.1f} m/s")
```

### Using Callbacks for Real-Time Processing

```python
from src.game_interface import NLC2Connector

def process_telemetry(state):
    """Called for every received state."""
    print(f"Position: ({state.position.x:.1f}, "
          f"{state.position.y:.1f}, {state.position.z:.1f})")

connector = NLC2Connector()
connector.set_callback(process_telemetry)
connector.connect()
connector.start()

# Callbacks run automatically in background
try:
    while True:
        time.sleep(0.1)
except KeyboardInterrupt:
    connector.disconnect()
```

### Recording Data to File

```python
from src.game_interface import NLC2Connector
import csv

with NLC2Connector() as connector:
    with open('coaster_data.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['time', 'pos_x', 'pos_y', 'pos_z', 'speed', 'g_force'])
        
        for _ in range(1000):  # Record 1000 samples
            state = connector.get_latest_state()
            if state:
                writer.writerow([
                    state.timestamp,
                    state.position.x,
                    state.position.y,
                    state.position.z,
                    state.speed,
                    state.get_total_g_force()
                ])
```

---

## Data Format

### CoasterState Object

All telemetry data is provided as a `CoasterState` object with the following attributes:

| Attribute | Type | Units | Description |
|-----------|------|-------|-------------|
| `timestamp` | float | seconds | Time since simulation start |
| `position` | Vector3D | meters | Position in world space |
| `velocity` | Vector3D | m/s | Velocity vector |
| `acceleration` | Vector3D | m/s² | Acceleration vector |
| `orientation` | Quaternion | - | Orientation (rotation) |
| `g_force` | Vector3D | G | G-force vector (1G = 9.81m/s²) |
| `speed` | float | m/s | Scalar speed magnitude |
| `view_mode` | int | - | Camera view mode |

### Vector3D

3D vector with `x`, `y`, `z` components:

```python
pos = state.position
print(f"X: {pos.x}, Y: {pos.y}, Z: {pos.z}")

# Convert to numpy array
arr = pos.to_array()  # Returns np.array([x, y, z])

# Get magnitude
mag = pos.magnitude()
```

### Quaternion

Rotation represented as quaternion (`w`, `x`, `y`, `z`):

```python
orientation = state.orientation

# Convert to Euler angles (roll, pitch, yaw in radians)
euler = orientation.to_euler()
print(f"Roll: {euler.x}, Pitch: {euler.y}, Yaw: {euler.z}")

# Convert to degrees
roll_deg = euler.x * 57.2958
```

### Coordinate System

NoLimits 2 uses a **right-handed coordinate system** with:
- **X**: Left/Right
- **Y**: Up/Down
- **Z**: Forward/Backward

---

## Troubleshooting

### No Data Received

**Problem**: Connection succeeds but no telemetry data arrives.

**Solutions**:
1. Make sure a coaster is **actively running** (not paused)
2. Check that you're in **ride mode** (not editor mode)
3. Verify ports in NoLimits 2 settings match your code
4. Restart NoLimits 2 and try again

### Connection Timeout

**Problem**: `connect()` fails or times out.

**Solutions**:
1. Ensure NoLimits 2 is running
2. Check firewall settings
3. Verify port numbers are correct
4. Try running both NoLimits 2 and your code as administrator

### High Packet Loss

**Problem**: Many dropped frames reported.

**Solutions**:
1. Close other network-intensive applications
2. Increase receive buffer size:
   ```python
   connector = NLC2Connector(buffer_size=2048)
   ```
3. Process data faster (use callbacks instead of polling)
4. Check CPU usage - game or code may be overloaded

### Invalid Data Values

**Problem**: `state.is_valid()` returns False.

**Solutions**:
1. Check for NaN or Inf values in logs
2. Verify NoLimits 2 version compatibility
3. Try a different coaster design
4. Report issue with sample data

### Port Already in Use

**Problem**: Error binding to port 15152.

**Solutions**:
1. Close other instances of the application
2. Check for other programs using the port:
   ```powershell
   netstat -ano | findstr 15152
   ```
3. Use a different port:
   ```python
   connector = NLC2Connector(receive_port=15153)
   ```

---

## Advanced Topics

### Performance Optimization

For minimum latency:

```python
# Use callbacks instead of polling
connector.set_callback(process_state)

# Increase priority of receive thread (Windows)
import win32process, win32api
handle = win32api.GetCurrentProcess()
win32process.SetPriorityClass(handle, win32process.HIGH_PRIORITY_CLASS)
```

### Filtering Noisy Data

Apply low-pass filter to smooth data:

```python
from scipy.signal import butter, filtfilt

def lowpass_filter(data, cutoff=10.0, fs=100.0):
    """Apply low-pass filter to data."""
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(4, normal_cutoff, btype='low', analog=False)
    return filtfilt(b, a, data)
```

### Multi-Train Support

If your coaster has multiple trains:

```python
# Track states by train index
train_states = {}

def handle_state(state):
    train_id = state.train_index
    train_states[train_id] = state
```

---

## API Reference

See module docstrings for complete API documentation:
- `src/game_interface/data_structures.py` - Data classes
- `src/game_interface/telemetry_parser.py` - Binary protocol parsing
- `src/game_interface/nlc2_connector.py` - Network connection manager

---

## Example Output

When running the test script with a coaster in motion:

```
================================================================================
Timestamp: 15.234s
Position:  (125.450, 45.200, 210.350)
Velocity:  (15.234, -2.145, 8.456) | Speed: 17.45 m/s (62.8 km/h)
Accel:     (2.145, -9.810, 1.234)
Rotation:  Roll: 15.3° Pitch: -8.5° Yaw: 45.2°
G-Force:   (0.215, -1.234, 0.125) | Total: 1.25G
View Mode: 0
================================================================================
```

---

## Next Steps

Once you have telemetry data working:

1. **Coordinate Transformation**: Convert game coordinates to robot workspace
2. **Motion Scaling**: Scale motion to fit robot capabilities
3. **Safety Validation**: Ensure all motions are within safe limits
4. **Integration**: Connect to robot control system

See the coordinate transformation module documentation for the next phase.
