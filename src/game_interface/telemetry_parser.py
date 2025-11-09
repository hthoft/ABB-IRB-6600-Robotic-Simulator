"""
NoLimits Coaster 2 Telemetry Parser.

This module handles parsing of binary telemetry data sent by NoLimits 2 via UDP.

NoLimits 2 Telemetry Protocol:
- Data is sent via UDP on port 15151 (configurable)
- Messages are in little-endian binary format
- Message structure:
  - Message ID (4 bytes, int32)
  - Frame number (4 bytes, int32)
  - State data (variable length depending on message type)
"""

import struct
import logging
from typing import Optional, Tuple
from .data_structures import CoasterState, Vector3D, Quaternion, TelemetryMessage

logger = logging.getLogger(__name__)


class TelemetryParser:
    """Parse NoLimits 2 telemetry data from UDP packets."""
    
    # Message type constants
    MSG_GET_VERSION = 1
    MSG_VERSION = 2
    MSG_GET_TELEMETRY = 3
    MSG_TELEMETRY = 4
    MSG_SET_MANUAL_MODE = 5
    MSG_DISPATCH_TRAIN = 6
    MSG_STATION_STATE = 7
    MSG_RECENTER_VR = 8
    
    # Minimum packet sizes
    MIN_HEADER_SIZE = 8  # message_id (4) + frame_number (4)
    MIN_TELEMETRY_SIZE = 88  # Header + basic telemetry data
    
    def __init__(self):
        """Initialize the telemetry parser."""
        self.last_frame_number = -1
        self.dropped_frames = 0
        
    def parse_packet(self, data: bytes) -> Optional[TelemetryMessage]:
        """
        Parse a raw UDP packet from NoLimits 2.
        
        Args:
            data: Raw bytes from UDP packet
            
        Returns:
            TelemetryMessage if successfully parsed, None otherwise
        """
        if len(data) < self.MIN_HEADER_SIZE:
            logger.warning(f"Packet too small: {len(data)} bytes")
            return None
        
        try:
            # Parse header (message ID and frame number)
            message_id, frame_number = struct.unpack('<II', data[0:8])
            
            # Check for dropped frames
            if self.last_frame_number >= 0:
                expected = self.last_frame_number + 1
                if frame_number != expected and frame_number > expected:
                    dropped = frame_number - expected
                    self.dropped_frames += dropped
                    logger.debug(f"Dropped {dropped} frames (total: {self.dropped_frames})")
            
            self.last_frame_number = frame_number
            
            # Parse based on message type
            if message_id == self.MSG_TELEMETRY:
                state = self._parse_telemetry_data(data[8:])
                return TelemetryMessage(
                    message_type=message_id,
                    frame_number=frame_number,
                    state=state
                )
            elif message_id == self.MSG_VERSION:
                version = self._parse_version_data(data[8:])
                logger.info(f"NoLimits 2 version: {version}")
                return TelemetryMessage(
                    message_type=message_id,
                    frame_number=frame_number
                )
            else:
                logger.debug(f"Unhandled message type: {message_id}")
                return TelemetryMessage(
                    message_type=message_id,
                    frame_number=frame_number
                )
                
        except struct.error as e:
            logger.error(f"Failed to parse packet: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error parsing packet: {e}")
            return None
    
    def _parse_telemetry_data(self, data: bytes) -> Optional[CoasterState]:
        """
        Parse telemetry state data.
        
        Expected format (all floats are 32-bit little-endian):
        - Position: x, y, z (3 floats, 12 bytes)
        - Velocity: x, y, z (3 floats, 12 bytes)
        - Acceleration: x, y, z (3 floats, 12 bytes)
        - Quaternion: w, x, y, z (4 floats, 16 bytes)
        - G-Force: x, y, z (3 floats, 12 bytes)
        - View mode (1 int, 4 bytes)
        - Timestamp (1 float, 4 bytes)
        Total: 72 bytes minimum
        
        Args:
            data: Telemetry data portion of packet
            
        Returns:
            CoasterState if successfully parsed, None otherwise
        """
        if len(data) < 72:
            logger.warning(f"Telemetry data too small: {len(data)} bytes")
            return None
        
        try:
            # Unpack all fields at once for efficiency
            # Format: 16 floats + 1 int = 17 values
            unpacked = struct.unpack('<16fI', data[0:68])
            
            # Extract position (indices 0-2)
            position = Vector3D(unpacked[0], unpacked[1], unpacked[2])
            
            # Extract velocity (indices 3-5)
            velocity = Vector3D(unpacked[3], unpacked[4], unpacked[5])
            
            # Extract acceleration (indices 6-8)
            acceleration = Vector3D(unpacked[6], unpacked[7], unpacked[8])
            
            # Extract quaternion (indices 9-12)
            orientation = Quaternion(unpacked[9], unpacked[10], unpacked[11], unpacked[12])
            
            # Extract G-force (indices 13-15)
            g_force = Vector3D(unpacked[13], unpacked[14], unpacked[15])
            
            # Extract view mode (index 16)
            view_mode = unpacked[16]
            
            # Calculate speed from velocity magnitude
            speed = velocity.magnitude()
            
            # Extract timestamp if available (some versions send it)
            timestamp = 0.0
            if len(data) >= 72:
                timestamp = struct.unpack('<f', data[68:72])[0]
            
            # Create coaster state
            state = CoasterState(
                timestamp=timestamp,
                position=position,
                velocity=velocity,
                acceleration=acceleration,
                orientation=orientation.normalize(),
                g_force=g_force,
                speed=speed,
                view_mode=view_mode
            )
            
            # Validate the state
            if not state.is_valid():
                logger.warning("Parsed state contains invalid values")
                return None
            
            return state
            
        except struct.error as e:
            logger.error(f"Failed to unpack telemetry data: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error parsing telemetry: {e}")
            return None
    
    def _parse_version_data(self, data: bytes) -> str:
        """
        Parse version message.
        
        Args:
            data: Version data portion of packet
            
        Returns:
            Version string
        """
        try:
            if len(data) >= 4:
                version = struct.unpack('<I', data[0:4])[0]
                return f"{version >> 16}.{version & 0xFFFF}"
            return "Unknown"
        except Exception as e:
            logger.error(f"Failed to parse version: {e}")
            return "Unknown"
    
    def create_request_telemetry_packet(self) -> bytes:
        """
        Create a request packet to ask NoLimits 2 to send telemetry.
        
        Returns:
            Binary packet ready to send via UDP
        """
        # Message: MSG_GET_TELEMETRY with frame number 0
        return struct.pack('<II', self.MSG_GET_TELEMETRY, 0)
    
    def create_version_request_packet(self) -> bytes:
        """
        Create a version request packet.
        
        Returns:
            Binary packet ready to send via UDP
        """
        return struct.pack('<II', self.MSG_GET_VERSION, 0)
    
    def get_stats(self) -> dict:
        """
        Get parser statistics.
        
        Returns:
            Dictionary with parser stats
        """
        return {
            'last_frame_number': self.last_frame_number,
            'dropped_frames': self.dropped_frames,
            'drop_rate': self.dropped_frames / max(1, self.last_frame_number) if self.last_frame_number > 0 else 0
        }
