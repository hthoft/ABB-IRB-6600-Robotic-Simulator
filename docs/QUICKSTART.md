# Quick Start - NoLimits Coaster 2 Telemetry

Get up and running with NoLimits 2 telemetry in 5 minutes!

## Prerequisites

- NoLimits Coaster 2 installed and running
- Python 3.10+ installed
- This repository cloned

## Step 1: Install Dependencies

```powershell
# Navigate to project directory
cd ABB-IRB-6600-Robotic-Simulator

# Create virtual environment
python -m venv venv

# Activate it
venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

## Step 2: Start NoLimits 2

1. Launch NoLimits Coaster 2
2. Load any coaster
3. Start riding (press Play or F9)

## Step 3: Run Test Script

```powershell
python tools\test_nlc2_telemetry.py
```

Select option `1` for basic connection test.

## What You Should See

If everything works, you'll see live telemetry data:

```
================================================================================
Timestamp: 5.234s
Position:  (125.450, 45.200, 210.350)
Velocity:  (15.234, -2.145, 8.456) | Speed: 17.45 m/s (62.8 km/h)
Accel:     (2.145, -9.810, 1.234)
Rotation:  Roll: 15.3° Pitch: -8.5° Yaw: 45.2°
G-Force:   (0.215, -1.234, 0.125) | Total: 1.25G
================================================================================
```

Press `Ctrl+C` to stop.

## Troubleshooting

### "Waiting for data..."

- Make sure the coaster is **actively running** (not paused!)
- Verify you're in **ride mode** (not editor)

### "Failed to connect"

- Check NoLimits 2 is running
- Verify firewall allows UDP on ports 15151-15152
- Try running as administrator

### "Connection timeout"

- Close and restart NoLimits 2
- Check Windows Firewall settings
- Verify no other program is using port 15152

## Next Steps

1. **Try option 2**: Record data to CSV file
2. **Try option 3**: Use callback mode for real-time processing
3. **Read the docs**: `docs/NOLIMITS2_INTEGRATION.md` for detailed guide
4. **Write your own**: Use the examples to create custom processing

## Simple Example

Create `my_test.py`:

```python
from src.game_interface import NLC2Connector
import time

# Connect to NoLimits 2
with NLC2Connector() as connector:
    print("Connected! Ride a coaster now...")
    
    for i in range(100):  # Get 100 samples
        state = connector.get_latest_state(timeout=1.0)
        
        if state:
            print(f"Sample {i}: Speed = {state.speed:.1f} m/s, "
                  f"G-Force = {state.get_total_g_force():.2f}G")
        
        time.sleep(0.1)
    
    print("Done!")
```

Run it:
```powershell
python my_test.py
```

## Happy Testing! 🎢
