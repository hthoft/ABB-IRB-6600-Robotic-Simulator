"""
Test script for NoLimits Coaster 2 telemetry data extraction.

This script demonstrates how to connect to NoLimits 2 and receive telemetry data.

Usage:
    1. Start NoLimits Coaster 2
    2. Load a coaster and start the simulation
    3. Run this script: python test_nlc2_telemetry.py
    4. Watch the live telemetry data stream

Press Ctrl+C to stop.
"""

import sys
import time
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.game_interface import NLC2Connector, CoasterState

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_state(state: CoasterState) -> None:
    """
    Print coaster state in a readable format.
    
    Args:
        state: CoasterState to display
    """
    print(f"\n{'='*80}")
    print(f"Timestamp: {state.timestamp:.3f}s")
    print(f"Position:  {state.position}")
    print(f"Velocity:  {state.velocity} | Speed: {state.speed:.2f} m/s ({state.speed * 3.6:.1f} km/h)")
    print(f"Accel:     {state.acceleration}")
    
    # Convert orientation to Euler angles for readability
    euler = state.orientation.to_euler()
    print(f"Rotation:  Roll: {euler.x*57.3:.1f}° Pitch: {euler.y*57.3:.1f}° Yaw: {euler.z*57.3:.1f}°")
    
    g_total = state.get_total_g_force()
    print(f"G-Force:   {state.g_force} | Total: {g_total:.2f}G")
    print(f"View Mode: {state.view_mode}")
    print(f"{'='*80}")


def test_basic_connection():
    """Test basic connection to NoLimits 2."""
    logger.info("Testing basic connection to NoLimits 2...")
    
    connector = NLC2Connector(
        host="127.0.0.1",
        send_port=15151,
        receive_port=15152
    )
    
    # Connect
    if not connector.connect():
        logger.error("Failed to connect to NoLimits 2")
        logger.info("Make sure NoLimits 2 is running!")
        return False
    
    logger.info("Connected successfully!")
    
    # Start receiving
    if not connector.start():
        logger.error("Failed to start telemetry reception")
        connector.disconnect()
        return False
    
    logger.info("Receiving telemetry data...")
    logger.info("Start a coaster simulation in NoLimits 2 to see data")
    logger.info("Press Ctrl+C to stop\n")
    
    try:
        count = 0
        last_print_time = 0
        
        while True:
            # Get latest state
            state = connector.get_latest_state(timeout=1.0)
            
            if state:
                count += 1
                current_time = time.time()
                
                # Print every 0.5 seconds to avoid spam
                if current_time - last_print_time >= 0.5:
                    print_state(state)
                    last_print_time = current_time
                    
                    # Print statistics every 10 states
                    if count % 20 == 0:
                        status = connector.get_connection_status()
                        logger.info(
                            f"Stats - Packets RX: {status['packets_received']}, "
                            f"TX: {status['packets_sent']}, "
                            f"Dropped: {status['dropped_frames']}, "
                            f"Queue: {status['queue_size']}"
                        )
            else:
                # No data received
                if count == 0:
                    print("Waiting for data... (Make sure a coaster is running in NoLimits 2)")
                
    except KeyboardInterrupt:
        logger.info("\nStopping...")
    finally:
        connector.disconnect()
        logger.info(f"Received {count} telemetry updates")
    
    return True


def test_data_recording():
    """Test recording telemetry data to a file."""
    logger.info("Testing data recording...")
    
    output_file = Path(__file__).parent.parent.parent / "data" / "samples" / "nlc2_recording.csv"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    connector = NLC2Connector()
    
    if not connector.connect() or not connector.start():
        logger.error("Failed to connect")
        return False
    
    logger.info(f"Recording to: {output_file}")
    logger.info("Run a coaster for a few seconds...")
    logger.info("Press Ctrl+C to stop recording\n")
    
    try:
        with open(output_file, 'w') as f:
            # Write CSV header
            f.write("timestamp,pos_x,pos_y,pos_z,vel_x,vel_y,vel_z,speed,")
            f.write("accel_x,accel_y,accel_z,quat_w,quat_x,quat_y,quat_z,")
            f.write("g_x,g_y,g_z,g_total\n")
            
            count = 0
            while True:
                state = connector.get_latest_state(timeout=1.0)
                
                if state:
                    # Write CSV row
                    f.write(f"{state.timestamp:.4f},")
                    f.write(f"{state.position.x:.4f},{state.position.y:.4f},{state.position.z:.4f},")
                    f.write(f"{state.velocity.x:.4f},{state.velocity.y:.4f},{state.velocity.z:.4f},")
                    f.write(f"{state.speed:.4f},")
                    f.write(f"{state.acceleration.x:.4f},{state.acceleration.y:.4f},{state.acceleration.z:.4f},")
                    f.write(f"{state.orientation.w:.4f},{state.orientation.x:.4f},")
                    f.write(f"{state.orientation.y:.4f},{state.orientation.z:.4f},")
                    f.write(f"{state.g_force.x:.4f},{state.g_force.y:.4f},{state.g_force.z:.4f},")
                    f.write(f"{state.get_total_g_force():.4f}\n")
                    
                    count += 1
                    if count % 100 == 0:
                        logger.info(f"Recorded {count} samples...")
                        
    except KeyboardInterrupt:
        logger.info("\nStopping recording...")
    finally:
        connector.disconnect()
        logger.info(f"Recorded {count} samples to {output_file}")
    
    return True


def test_callback_mode():
    """Test using callback for real-time processing."""
    logger.info("Testing callback mode...")
    
    max_speed = 0.0
    max_g = 0.0
    sample_count = 0
    
    def process_state(state: CoasterState) -> None:
        """Callback function to process each state."""
        nonlocal max_speed, max_g, sample_count
        
        sample_count += 1
        max_speed = max(max_speed, state.speed)
        max_g = max(max_g, state.get_total_g_force())
        
        if sample_count % 100 == 0:
            logger.info(
                f"Samples: {sample_count}, "
                f"Max Speed: {max_speed:.1f} m/s ({max_speed*3.6:.1f} km/h), "
                f"Max G: {max_g:.2f}G"
            )
    
    connector = NLC2Connector()
    connector.set_callback(process_state)
    
    if not connector.connect() or not connector.start():
        logger.error("Failed to connect")
        return False
    
    logger.info("Processing telemetry with callback...")
    logger.info("Press Ctrl+C to stop\n")
    
    try:
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        logger.info("\nStopping...")
    finally:
        connector.disconnect()
        logger.info(f"Final stats - Samples: {sample_count}, Max Speed: {max_speed:.1f} m/s, Max G: {max_g:.2f}G")
    
    return True


def main():
    """Main test runner."""
    print("\n" + "="*80)
    print("NoLimits Coaster 2 Telemetry Test Suite")
    print("="*80 + "\n")
    
    print("Available tests:")
    print("1. Basic connection and data display")
    print("2. Record data to CSV file")
    print("3. Callback mode (real-time processing)")
    print("0. Run all tests")
    
    choice = input("\nSelect test (0-3): ").strip()
    
    if choice == "1":
        test_basic_connection()
    elif choice == "2":
        test_data_recording()
    elif choice == "3":
        test_callback_mode()
    elif choice == "0":
        logger.info("Running all tests sequentially...")
        test_basic_connection()
        input("\nPress Enter to continue to recording test...")
        test_data_recording()
        input("\nPress Enter to continue to callback test...")
        test_callback_mode()
    else:
        print("Invalid choice")
        return
    
    print("\nTest complete!")


if __name__ == "__main__":
    main()
