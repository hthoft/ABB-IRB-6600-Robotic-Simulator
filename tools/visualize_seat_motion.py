"""
Live 3D Visualization of Simulator Seat Motion.

This tool connects to NoLimits 2 telemetry and displays real-time
visualization of how a simulator seat would move, including:
- 3D position trajectory
- Orientation (roll, pitch, yaw)
- G-force magnitude
- Speed

Usage:
    python tools/visualize_seat_motion.py
"""

import sys
import os
import time
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from mpl_toolkits.mplot3d import Axes3D
from collections import deque

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.game_interface import NL2TelemetryClient, CoasterState


class SeatMotionVisualizer:
    """Real-time visualization of simulator seat motion from NoLimits 2 telemetry."""
    
    def __init__(self, max_history: int = 500):
        """
        Initialize the visualizer.
        
        Args:
            max_history: Maximum number of historical points to display
        """
        self.max_history = max_history
        self.client = NL2TelemetryClient()
        
        # Data storage (raw game positions)
        self.positions = deque(maxlen=max_history)
        self.timestamps = deque(maxlen=max_history)
        self.speeds = deque(maxlen=max_history)
        self.g_forces = deque(maxlen=max_history)
        self.rolls = deque(maxlen=max_history)
        self.pitches = deque(maxlen=max_history)
        self.yaws = deque(maxlen=max_history)
        
        # Robot-mapped values (small TCP motions derived from game data)
        self.robot_positions = deque(maxlen=max_history)
        self.robot_rolls = deque(maxlen=max_history)
        self.robot_pitches = deque(maxlen=max_history)
        self.robot_yaws = deque(maxlen=max_history)
        
        # Acceleration-based orientation (for seat tilt)
        self.accel_rolls = deque(maxlen=max_history)
        self.accel_pitches = deque(maxlen=max_history)
        
        # Statistics
        self.max_speed = 0.0
        self.max_g_force = 0.0
        self.sample_count = 0
        
        # Create figure with single 3D plot
        self.fig = plt.figure(figsize=(10, 10))
        self.fig.suptitle('Robot TCP Frame - Seat Motion', fontsize=16, fontweight='bold')
        
        # 3D robot TCP frame (full window)
        self.ax_3d = self.fig.add_subplot(111, projection='3d')
        self.ax_3d.set_title('Real-time TCP Position and Orientation')
        self.ax_3d.set_xlabel('X (m)')
        self.ax_3d.set_ylabel('Y (m)')
        self.ax_3d.set_zlabel('Z (m)')
        
        # Initialize plot elements for TCP frame
        # We do not plot the world trajectory here; focus on TCP around origin
        self.robot_point_3d, = self.ax_3d.plot([0], [0], [0], 'ko', markersize=10)
        # quiver will be created on first update
        self.robot_quiver = None
        
        # Status text
        self.status_text = self.fig.text(0.02, 0.02, '', fontsize=11, family='monospace')
        
        plt.tight_layout(rect=[0, 0.05, 1, 0.98])
        
        # --- Filtering / mapping parameters ---
        self.anchor_pos = None  # reference position to compute small deltas
        # Low-pass filter for signal smoothing (0..1, higher = smoother/more damped)
        self.lp_alpha = 0.95  # Increased for more damping
        # Very slow low-frequency estimate for washout (remove DC)
        self.low_freq_alpha = 0.998  # Even slower washout
        # Scales to map game meters/accelerations into robot meters/angles
        self.translation_scale = 0.04  # game meters -> robot meters
        # Direct G-force to roll angle mapping
        self.g_force_limit = 0.3  # ±0.3G is maximum
        self.max_roll_deg = 40.0  # ±40° at max G-force
        # Hard limits for robot travel and angles
        self.max_travel_m = 0.25  # max translation magnitude (m)
        self.max_tilt_rate_deg_per_sec = 20.0  # REDUCED rate limit for more damping
        # Internal filter state
        self._prev_filtered_pos = np.zeros(3, dtype=np.float64)
        self._low_freq_pos = np.zeros(3, dtype=np.float64)
        self._prev_filtered_gx = 0.0  # Filtered lateral G-force
        self._low_freq_gx = 0.0  # Low frequency component for washout
        # Previous tilt angles for rate limiting
        self._prev_roll = 0.0
        self._last_update_time = None
    
    def connect(self) -> bool:
        """
        Connect to NoLimits 2 telemetry server.
        
        Returns:
            True if connection successful
        """
        try:
            if self.client.connect():
                version = self.client.get_version()
                print(f"✅ Connected to NoLimits 2 version: {version}")
                return True
            else:
                print("❌ Failed to connect to NoLimits 2")
                return False
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
    
    def update_data(self):
        """Fetch latest telemetry data and update buffers."""
        try:
            state = self.client.get_telemetry()
            
            if state and state.is_valid():
                self.sample_count += 1
                
                # Store position
                self.positions.append([state.position.x, state.position.y, state.position.z])
                self.timestamps.append(state.timestamp)

                # Store speed (convert to km/h)
                speed_kmh = state.speed * 3.6
                self.speeds.append(speed_kmh)
                self.max_speed = max(self.max_speed, speed_kmh)

                # Store G-force
                g_force = state.get_total_g_force()
                self.g_forces.append(g_force)
                self.max_g_force = max(self.max_g_force, g_force)

                # Store raw orientation (convert to degrees) - NOT USED FOR ROBOT
                euler = state.orientation.to_euler()
                euler_deg = np.array([np.degrees(euler.x), np.degrees(euler.y), np.degrees(euler.z)])
                self.rolls.append(euler_deg[0])
                self.pitches.append(euler_deg[1])
                self.yaws.append(euler_deg[2])

                # --- Map to robot TCP (small motions based on G-forces and acceleration) ---
                raw_pos = np.array([state.position.x, state.position.y, state.position.z], dtype=np.float64)
                if self.anchor_pos is None:
                    # set initial anchor to current game position
                    self.anchor_pos = raw_pos.copy()

                # compute delta relative to anchor (we only care about small deltas)
                delta = (raw_pos - self.anchor_pos) * self.translation_scale

                # low-pass filter for smoothness
                filtered = self.lp_alpha * self._prev_filtered_pos + (1.0 - self.lp_alpha) * delta
                self._prev_filtered_pos = filtered

                # slow low-frequency estimate for washout (remove sustained offsets)
                self._low_freq_pos = self.low_freq_alpha * self._low_freq_pos + (1.0 - self.low_freq_alpha) * filtered

                # high-passed (washout) robot command
                robot_cmd = filtered - self._low_freq_pos

                # clamp to max travel
                norm = np.linalg.norm(robot_cmd)
                if norm > self.max_travel_m and norm > 1e-12:
                    robot_cmd = robot_cmd * (self.max_travel_m / norm)

                # push to robot position history
                self.robot_positions.append(robot_cmd.tolist())

                # --- Direct mapping: Lateral G-force -> Roll angle ---
                # Simple linear relationship: ±3G -> ±50°
                # Lateral G-force (X axis) directly controls roll
                
                lateral_g = state.g_force.x  # Positive = right, Negative = left
                
                # Filter lateral G-force for smoothness
                filtered_gx = self.lp_alpha * self._prev_filtered_gx + (1.0 - self.lp_alpha) * lateral_g
                self._prev_filtered_gx = filtered_gx
                
                # Apply washout to prevent sustained tilts
                self._low_freq_gx = self.low_freq_alpha * self._low_freq_gx + (1.0 - self.low_freq_alpha) * filtered_gx
                washout_gx = filtered_gx - self._low_freq_gx
                
                # Direct linear mapping: G-force to degrees
                # roll_angle = (lateral_g / 3.0) * 50.0
                roll_target = (washout_gx / self.g_force_limit) * self.max_roll_deg
                
                # Clamp to max roll angle
                roll_target = np.clip(roll_target, -self.max_roll_deg, self.max_roll_deg)
                
                # No pitch - keep seat level in forward/back direction
                pitch_target = 0.0
                
                # Rate limiting to prevent sudden jumps (slew rate limiter)
                current_time = state.timestamp
                if self._last_update_time is not None:
                    dt = current_time - self._last_update_time
                    if dt > 0 and dt < 1.0:  # Sanity check on time delta
                        max_change = self.max_tilt_rate_deg_per_sec * dt
                        
                        # Limit roll change
                        roll_delta = roll_target - self._prev_roll
                        if abs(roll_delta) > max_change:
                            roll_target = self._prev_roll + np.sign(roll_delta) * max_change
                
                self._last_update_time = current_time
                self._prev_roll = roll_target
                
                self.robot_rolls.append(roll_target)
                self.robot_pitches.append(pitch_target)
                self.robot_yaws.append(0.0)  # No yaw
                
                # Store G-force components for plotting
                self.accel_rolls.append(washout_gx)  # Store in G units for display
                self.accel_pitches.append(0.0)

                return True
            return False
            
        except Exception as e:
            print(f"Error fetching telemetry: {e}")
            return False
    
    def update_plot(self, frame):
        """Update all plot elements (called by animation)."""
        # Fetch new data
        self.update_data()
        
        # allow plotting even if world positions are not yet present; focus on robot TCP
        
        # Convert to numpy arrays
        positions = np.array(list(self.positions))
        timestamps = np.array(list(self.timestamps))
        speeds = np.array(list(self.speeds))
        g_forces = np.array(list(self.g_forces))
        rolls = np.array(list(self.rolls))
        pitches = np.array(list(self.pitches))
        yaws = np.array(list(self.yaws))
        
        # Robot-mapped arrays
        robot_positions = np.array(list(self.robot_positions)) if len(self.robot_positions) > 0 else np.zeros((0, 3))
        robot_rolls = np.array(list(self.robot_rolls)) if len(self.robot_rolls) > 0 else np.zeros(0)
        robot_pitches = np.array(list(self.robot_pitches)) if len(self.robot_pitches) > 0 else np.zeros(0)
        robot_yaws = np.array(list(self.robot_yaws)) if len(self.robot_yaws) > 0 else np.zeros(0)
        accel_rolls = np.array(list(self.accel_rolls)) if len(self.accel_rolls) > 0 else np.zeros(0)
        accel_pitches = np.array(list(self.accel_pitches)) if len(self.accel_pitches) > 0 else np.zeros(0)
        
    # Update 3D robot TCP frame
        
        # Update robot TCP marker (in separate coordinate system centered at origin)
        if robot_positions.shape[0] > 0:
            rp = robot_positions[-1]
            # robot TCP represented near origin
            self.robot_point_3d.set_data([rp[0]], [rp[1]])
            self.robot_point_3d.set_3d_properties([rp[2]])
            
            # Draw seat frame based on acceleration-derived tilt angles
            yaw = 0.0  # No yaw from acceleration
            pitch = np.deg2rad(robot_pitches[-1]) if robot_pitches.size else 0.0
            roll = np.deg2rad(robot_rolls[-1]) if robot_rolls.size else 0.0
            
            # Rotation matrix from ZYX (yaw, pitch, roll)
            cy, sy = np.cos(yaw), np.sin(yaw)
            cp, sp = np.cos(pitch), np.sin(pitch)
            cr, sr = np.cos(roll), np.sin(roll)
            Rz = np.array([[cy, -sy, 0],[sy, cy, 0],[0,0,1]])
            Ry = np.array([[cp,0,sp],[0,1,0],[-sp,0,cp]])
            Rx = np.array([[1,0,0],[0,cr,-sr],[0,sr,cr]])
            R = Rz @ Ry @ Rx
            
            # Seat frame axes (RGB = XYZ)
            axis_len = 0.08
            x_axis = R @ np.array([axis_len, 0, 0])
            y_axis = R @ np.array([0, axis_len, 0])
            z_axis = R @ np.array([0, 0, axis_len])
            
            # Remove previous quiver
            if self.robot_quiver is not None:
                try:
                    for coll in self.robot_quiver:
                        coll.remove()
                except Exception:
                    pass
                self.robot_quiver = None
            
            # Draw new seat frame
            self.robot_quiver = []
            origin = rp
            # X (red) - forward
            self.robot_quiver.append(self.ax_3d.quiver(origin[0], origin[1], origin[2], x_axis[0], x_axis[1], x_axis[2], color='r', length=1.0, normalize=False, arrow_length_ratio=0.3, linewidth=2))
            # Y (green) - lateral
            self.robot_quiver.append(self.ax_3d.quiver(origin[0], origin[1], origin[2], y_axis[0], y_axis[1], y_axis[2], color='g', length=1.0, normalize=False, arrow_length_ratio=0.3, linewidth=2))
            # Z (blue) - vertical (up)
            self.robot_quiver.append(self.ax_3d.quiver(origin[0], origin[1], origin[2], z_axis[0], z_axis[1], z_axis[2], color='b', length=1.0, normalize=False, arrow_length_ratio=0.3, linewidth=2))
        
        # Fixed small frame around origin for robot TCP (centered)
        m = self.max_travel_m + 0.05
        self.ax_3d.set_xlim3d(-m, m)
        self.ax_3d.set_ylim3d(-m, m)
        self.ax_3d.set_zlim3d(-m, m)
        
        # Draw reference axes at origin (world frame)
        self.ax_3d.plot([0, 0.15], [0, 0], [0, 0], color='darkred', linewidth=2, alpha=0.3, label='World X')
        self.ax_3d.plot([0, 0], [0, 0.15], [0, 0], color='darkgreen', linewidth=2, alpha=0.3, label='World Y')
        self.ax_3d.plot([0, 0], [0, 0], [0, 0.15], color='darkblue', linewidth=2, alpha=0.3, label='World Z')
        
        # Update time-based plots - REMOVED, only show 3D frame
        
        # Update status text with robot TCP info
        current_speed = speeds[-1] if len(speeds) > 0 else 0
        current_g = g_forces[-1] if len(g_forces) > 0 else 0
        robot_disp = robot_positions[-1] if robot_positions.shape[0] > 0 else [0, 0, 0]
        robot_angles = [robot_rolls[-1] if robot_rolls.size else 0.0,
                        robot_pitches[-1] if robot_pitches.size else 0.0,
                        robot_yaws[-1] if robot_yaws.size else 0.0]

        status = (
            f"Samples: {self.sample_count:,}  |  "
            f"Speed: {current_speed:.1f} km/h (max: {self.max_speed:.1f})  |  "
            f"Total G-Force: {current_g:.2f}G (max: {self.max_g_force:.2f}G)\n"
            f"Robot TCP: ({robot_disp[0]:+.3f}, {robot_disp[1]:+.3f}, {robot_disp[2]:+.3f}) m  |  "
            f"Lateral G: {accel_rolls[-1] if accel_rolls.size > 0 else 0.0:+.2f}G → Roll: {robot_angles[0]:+.1f}°"
        )
        self.status_text.set_text(status)
        
        handles = [self.status_text, self.robot_point_3d]
        # include quiver handles if present
        if self.robot_quiver:
            handles.extend(self.robot_quiver)
        return handles
    
    def run(self):
        """Start the visualization."""
        if not self.connect():
            print("Cannot start visualization without connection.")
            return
        
        print("\n🎢 Starting live visualization...")
        print("📊 Waiting for telemetry data...")
        print("💡 Start a ride in NoLimits 2 to see the motion!")
        print("\nPress Ctrl+C to stop.\n")
        
        # Create animation with 60 FPS update rate
        anim = FuncAnimation(
            self.fig,
            self.update_plot,
            interval=16,  # ~60 FPS
            blit=False,
            cache_frame_data=False
        )
        
        try:
            plt.show()
        except KeyboardInterrupt:
            print("\n\n⏹️  Visualization stopped")
        finally:
            self.client.disconnect()
            print(f"\n📈 Session Summary:")
            print(f"   Total samples: {self.sample_count:,}")
            print(f"   Maximum speed: {self.max_speed:.1f} km/h")
            print(f"   Maximum G-force: {self.max_g_force:.2f}G")


def main():
    """Main entry point."""
    print("=" * 70)
    print("NoLimits 2 - Simulator Seat Motion Visualization")
    print("=" * 70)
    print()
    
    visualizer = SeatMotionVisualizer(max_history=500)
    visualizer.run()


if __name__ == '__main__':
    main()
