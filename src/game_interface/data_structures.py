"""
Data structures for NoLimits Coaster 2 telemetry data.

This module defines the data classes used to represent coaster state information
extracted from the game.
"""

from dataclasses import dataclass
from typing import Optional
import numpy as np
from numpy.typing import NDArray


@dataclass
class Vector3D:
    """3D vector representation."""
    x: float
    y: float
    z: float
    
    def to_array(self) -> NDArray[np.float64]:
        """Convert to numpy array."""
        return np.array([self.x, self.y, self.z], dtype=np.float64)
    
    def magnitude(self) -> float:
        """Calculate vector magnitude."""
        return float(np.sqrt(self.x**2 + self.y**2 + self.z**2))
    
    def __str__(self) -> str:
        return f"({self.x:.3f}, {self.y:.3f}, {self.z:.3f})"


@dataclass
class Quaternion:
    """Quaternion for representing orientation."""
    w: float
    x: float
    y: float
    z: float
    
    def to_array(self) -> NDArray[np.float64]:
        """Convert to numpy array [w, x, y, z]."""
        return np.array([self.w, self.x, self.y, self.z], dtype=np.float64)
    
    def normalize(self) -> 'Quaternion':
        """Return normalized quaternion."""
        mag = np.sqrt(self.w**2 + self.x**2 + self.y**2 + self.z**2)
        if mag < 1e-10:
            return Quaternion(1.0, 0.0, 0.0, 0.0)
        return Quaternion(
            self.w / mag,
            self.x / mag,
            self.y / mag,
            self.z / mag
        )
    
    def to_euler(self) -> Vector3D:
        """
        Convert quaternion to Euler angles (roll, pitch, yaw) in radians.
        
        Returns:
            Vector3D with (roll, pitch, yaw) in radians
        """
        # Roll (x-axis rotation)
        sinr_cosp = 2 * (self.w * self.x + self.y * self.z)
        cosr_cosp = 1 - 2 * (self.x * self.x + self.y * self.y)
        roll = np.arctan2(sinr_cosp, cosr_cosp)
        
        # Pitch (y-axis rotation)
        sinp = 2 * (self.w * self.y - self.z * self.x)
        if abs(sinp) >= 1:
            pitch = np.copysign(np.pi / 2, sinp)
        else:
            pitch = np.arcsin(sinp)
        
        # Yaw (z-axis rotation)
        siny_cosp = 2 * (self.w * self.z + self.x * self.y)
        cosy_cosp = 1 - 2 * (self.y * self.y + self.z * self.z)
        yaw = np.arctan2(siny_cosp, cosy_cosp)
        
        return Vector3D(roll, pitch, yaw)


@dataclass
class CoasterState:
    """
    Complete state information for a coaster train at a specific moment.
    
    Attributes:
        timestamp: Time in seconds since simulation start
        position: Position in world space (meters)
        velocity: Velocity vector (m/s)
        acceleration: Acceleration vector (m/s²)
        orientation: Orientation as quaternion
        g_force: G-force vector (in G units, 1.0 = 9.81 m/s²)
        speed: Scalar speed (m/s)
        view_mode: Current camera view mode
        coaster_name: Name of the coaster
        train_index: Index of the train (for multi-train coasters)
    """
    timestamp: float
    position: Vector3D
    velocity: Vector3D
    acceleration: Vector3D
    orientation: Quaternion
    g_force: Vector3D
    speed: float
    view_mode: int = 0
    coaster_name: str = ""
    train_index: int = 0
    
    def is_valid(self) -> bool:
        """
        Check if the state data is valid.
        
        Returns:
            True if all values are finite and reasonable
        """
        # Check for NaN or infinite values
        values = [
            self.timestamp,
            self.position.x, self.position.y, self.position.z,
            self.velocity.x, self.velocity.y, self.velocity.z,
            self.acceleration.x, self.acceleration.y, self.acceleration.z,
            self.orientation.w, self.orientation.x, self.orientation.y, self.orientation.z,
            self.g_force.x, self.g_force.y, self.g_force.z,
            self.speed
        ]
        
        if not all(np.isfinite(values)):
            return False
        
        # Check reasonable bounds
        if abs(self.position.x) > 10000 or abs(self.position.y) > 10000 or abs(self.position.z) > 10000:
            return False
        
        if self.speed > 200:  # Over 200 m/s (720 km/h) is unrealistic
            return False
        
        if self.g_force.magnitude() > 50:  # Over 50G is unrealistic
            return False
        
        return True
    
    def get_total_g_force(self) -> float:
        """Get total G-force magnitude."""
        return self.g_force.magnitude()
    
    def to_dict(self) -> dict:
        """Convert to dictionary for logging/serialization."""
        return {
            'timestamp': self.timestamp,
            'position': {'x': self.position.x, 'y': self.position.y, 'z': self.position.z},
            'velocity': {'x': self.velocity.x, 'y': self.velocity.y, 'z': self.velocity.z},
            'acceleration': {'x': self.acceleration.x, 'y': self.acceleration.y, 'z': self.acceleration.z},
            'orientation': {'w': self.orientation.w, 'x': self.orientation.x, 
                           'y': self.orientation.y, 'z': self.orientation.z},
            'g_force': {'x': self.g_force.x, 'y': self.g_force.y, 'z': self.g_force.z},
            'speed': self.speed,
            'view_mode': self.view_mode,
            'coaster_name': self.coaster_name,
            'train_index': self.train_index
        }


@dataclass
class TelemetryMessage:
    """
    Raw telemetry message from NoLimits 2.
    
    NoLimits 2 sends UDP telemetry data in a specific binary format.
    This class represents the parsed message.
    """
    message_type: int
    frame_number: int
    state: Optional[CoasterState] = None
    
    def is_state_message(self) -> bool:
        """Check if this is a state update message (vs control message)."""
        return self.message_type == 1 and self.state is not None
