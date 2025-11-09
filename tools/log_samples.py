"""
Simple script to log 10 samples of telemetry data from NoLimits 2.

Usage:
    python tools/log_samples.py
"""

import sys
import os
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.game_interface import NL2TelemetryClient


def main():
    """Capture and log 10 samples of telemetry data."""
    print("=" * 70)
    print("NoLimits 2 - Sample Data Logger")
    print("=" * 70)
    print()
    
    # Connect to NoLimits 2
    client = NL2TelemetryClient()
    
    print("Connecting to NoLimits 2...")
    if not client.connect():
        print("❌ Failed to connect to NoLimits 2")
        print("   Make sure NoLimits 2 is running with --telemetry flag")
        return
    
    version = client.get_version()
    print(f"✅ Connected to NoLimits 2 version: {version}")
    print()
    print("Collecting 10 samples...")
    print()
    
    samples = []
    sample_count = 0
    
    while sample_count < 10:
        state = client.get_telemetry()
        
        if state and state.is_valid():
            sample_count += 1
            samples.append(state)
            
            # Log the sample
            euler = state.orientation.to_euler()
            print(f"Sample #{sample_count}:")
            print(f"  Timestamp:    {state.timestamp:.3f} s")
            print(f"  Position:     ({state.position.x:.3f}, {state.position.y:.3f}, {state.position.z:.3f}) m")
            print(f"  Velocity:     ({state.velocity.x:.3f}, {state.velocity.y:.3f}, {state.velocity.z:.3f}) m/s")
            print(f"  Speed:        {state.speed:.3f} m/s ({state.speed * 3.6:.1f} km/h)")
            print(f"  Acceleration: ({state.acceleration.x:.3f}, {state.acceleration.y:.3f}, {state.acceleration.z:.3f}) m/s²")
            print(f"  G-Force:      ({state.g_force.x:.3f}, {state.g_force.y:.3f}, {state.g_force.z:.3f}) G")
            print(f"  Total G:      {state.get_total_g_force():.3f} G")
            print(f"  Orientation:  Roll: {euler.x * 57.2958:.1f}° Pitch: {euler.y * 57.2958:.1f}° Yaw: {euler.z * 57.2958:.1f}°")
            print(f"  Quaternion:   ({state.orientation.w:.4f}, {state.orientation.x:.4f}, {state.orientation.y:.4f}, {state.orientation.z:.4f})")
            print()
        
        time.sleep(0.1)  # Small delay between samples
    
    client.disconnect()
    
    print("=" * 70)
    print("✅ Completed - 10 samples collected")
    print("=" * 70)


if __name__ == '__main__':
    main()
