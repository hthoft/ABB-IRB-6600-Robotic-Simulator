"""
Simple example: Connect to NoLimits 2 and display live telemetry data.

This is the simplest possible example to get started.

Requirements:
- NoLimits Coaster 2 running with an active coaster
- Python dependencies installed (pip install -r requirements.txt)

Usage:
    python example_simple.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.game_interface import NLC2Connector


def main():
    """Main function - connect and display data."""
    print("="*80)
    print("NoLimits Coaster 2 - Simple Telemetry Example")
    print("="*80)
    print("\nConnecting to NoLimits 2...")
    
    # Create and configure connector
    connector = NLC2Connector(
        host="127.0.0.1",      # Localhost
        send_port=15151,       # NoLimits 2 receive port
        receive_port=15152     # Our receive port
    )
    
    # Connect
    if not connector.connect():
        print("\n❌ Failed to connect!")
        print("   Make sure NoLimits 2 is running.")
        return
    
    print("✅ Connected!")
    
    # Start receiving data
    if not connector.start():
        print("\n❌ Failed to start telemetry reception!")
        connector.disconnect()
        return
    
    print("✅ Receiving data...")
    print("\n💡 Start riding a coaster in NoLimits 2!")
    print("   Press Ctrl+C to stop.\n")
    
    try:
        sample_count = 0
        max_speed = 0.0
        max_g = 0.0
        
        while True:
            # Get latest coaster state
            state = connector.get_latest_state(timeout=1.0)
            
            if state:
                sample_count += 1
                
                # Track maximums
                max_speed = max(max_speed, state.speed)
                max_g = max(max_g, state.get_total_g_force())
                
                # Display every 10th sample to avoid spam
                if sample_count % 10 == 0:
                    print(f"\n📊 Sample #{sample_count}")
                    print(f"   Position:    ({state.position.x:.1f}, "
                          f"{state.position.y:.1f}, {state.position.z:.1f}) m")
                    print(f"   Speed:       {state.speed:.1f} m/s "
                          f"({state.speed * 3.6:.1f} km/h)")
                    print(f"   G-Force:     {state.get_total_g_force():.2f}G")
                    print(f"   Max Speed:   {max_speed * 3.6:.1f} km/h")
                    print(f"   Max G-Force: {max_g:.2f}G")
            else:
                if sample_count == 0:
                    print("⏳ Waiting for data... (Is a coaster running?)")
    
    except KeyboardInterrupt:
        print("\n\n⏹️  Stopping...")
    
    finally:
        # Cleanup
        connector.disconnect()
        
        print(f"\n📈 Session Summary:")
        print(f"   Samples received: {sample_count}")
        print(f"   Maximum speed:    {max_speed * 3.6:.1f} km/h")
        print(f"   Maximum G-force:  {max_g:.2f}G")
        print("\n✅ Done!")


if __name__ == "__main__":
    main()
