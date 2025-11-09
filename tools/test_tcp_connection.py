"""
Test NoLimits 2 TCP telemetry connection.

This uses the TCP-based protocol (port 15151) instead of UDP.

IMPORTANT: Start NoLimits 2 with the --telemetry command line option!

Usage:
    python tools\test_tcp_connection.py
"""

import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.game_interface import NL2TelemetryClient


def main():
    """Test TCP connection to NoLimits 2."""
    print("="*80)
    print("NoLimits 2 TCP Telemetry Connection Test")
    print("="*80)
    print("\n⚠️  IMPORTANT: NoLimits 2 must be started with --telemetry option!")
    print("   Example: NoLimits2.exe --telemetry\n")
    
    # Create client
    client = NL2TelemetryClient(host='127.0.0.1', port=15151)
    
    # Connect
    print("Connecting to NoLimits 2...")
    if not client.connect():
        print("\n❌ Connection failed!")
        print("   Make sure:")
        print("   1. NoLimits 2 is running")
        print("   2. Started with --telemetry command line option")
        print("   3. No firewall blocking port 15151")
        return 1
    
    print("✅ Connected!\n")
    
    # Get version
    print("Getting NoLimits 2 version...")
    version = client.get_version()
    if version:
        print(f"✅ NoLimits 2 version: {version}\n")
    else:
        print("⚠️  Could not get version\n")
    
    # Get telemetry
    print("="*80)
    print("Getting telemetry data...")
    print("💡 Start riding a coaster in NoLimits 2 to see data!")
    print("   Press Ctrl+C to stop.\n")
    print("="*80)
    
    try:
        sample_count = 0
        max_speed = 0.0
        max_g = 0.0
        
        while True:
            # Request telemetry
            state = client.get_telemetry(request_id=sample_count)
            
            if state:
                sample_count += 1
                
                # Track maximums
                max_speed = max(max_speed, state.speed)
                max_g = max(max_g, state.get_total_g_force())
                
                # Display every 10th sample
                if sample_count % 10 == 0:
                    print(f"\n📊 Sample #{sample_count}")
                    print(f"   Position:    ({state.position.x:.1f}, "
                          f"{state.position.y:.1f}, {state.position.z:.1f}) m")
                    print(f"   Speed:       {state.speed:.1f} m/s "
                          f"({state.speed * 3.6:.1f} km/h)")
                    print(f"   G-Force:     {state.get_total_g_force():.2f}G")
                    
                    # Show orientation
                    euler = state.orientation.to_euler()
                    print(f"   Orientation: Roll: {euler.x*57.3:.1f}° "
                          f"Pitch: {euler.y*57.3:.1f}° "
                          f"Yaw: {euler.z*57.3:.1f}°")
                    
                    print(f"   Max Speed:   {max_speed * 3.6:.1f} km/h")
                    print(f"   Max G-Force: {max_g:.2f}G")
            else:
                if sample_count == 0:
                    print("⏳ Waiting for data... (Is a coaster running?)", end='\r')
                time.sleep(0.1)
    
    except KeyboardInterrupt:
        print("\n\n⏹️  Stopping...")
    
    finally:
        # Cleanup
        client.disconnect()
        
        print(f"\n📈 Session Summary:")
        print(f"   Samples received: {sample_count}")
        if sample_count > 0:
            print(f"   Maximum speed:    {max_speed * 3.6:.1f} km/h")
            print(f"   Maximum G-force:  {max_g:.2f}G")
        print("\n✅ Done!")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
