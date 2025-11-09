"""
NoLimits 2 Connector using TCP protocol (adapted from py_nl2telemetry).

This replaces our UDP implementation with a working TCP-based approach.
"""

import socket
import struct
import logging
from typing import Optional
from .data_structures import CoasterState, Vector3D, Quaternion

logger = logging.getLogger(__name__)


class NL2TelemetryClient:
    """
    TCP-based telemetry client for NoLimits 2.
    
    Based on the py_nl2telemetry library by bestdani.
    Uses TCP protocol instead of UDP for reliable communication.
    """
    
    # Message magic bytes
    MAGIC_START = b'N'
    MAGIC_END = b'L'
    
    # Message type IDs
    MSG_IDLE = 0
    MSG_GET_VERSION = 3
    MSG_GET_TELEMETRY = 5
    
    # Reply type IDs
    REPLY_OK = 1
    REPLY_ERROR = 2
    REPLY_VERSION = 4
    REPLY_TELEMETRY = 6
    
    def __init__(self, host: str = '127.0.0.1', port: int = 15151, timeout: float = 3.0):
        """
        Initialize NoLimits 2 telemetry client.
        
        Args:
            host: IP address of NoLimits 2 (usually localhost)
            port: TCP port (default: 15151)
            timeout: Socket timeout in seconds
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self.socket: Optional[socket.socket] = None
        self.is_connected = False
        
    def connect(self) -> bool:
        """
        Connect to NoLimits 2 telemetry server.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            logger.info(f"Connecting to NoLimits 2 at {self.host}:{self.port}")
            
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(self.timeout)
            self.socket.connect((self.host, self.port))
            
            self.is_connected = True
            logger.info("Connected successfully!")
            return True
            
        except socket.timeout:
            logger.error("Connection timed out - is NoLimits 2 running with --telemetry?")
            return False
        except ConnectionRefusedError:
            logger.error("Connection refused - make sure NoLimits 2 is running with --telemetry option")
            return False
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            return False
    
    def disconnect(self) -> None:
        """Close connection to NoLimits 2."""
        if self.socket:
            try:
                self.socket.close()
            except Exception as e:
                logger.error(f"Error closing socket: {e}")
            self.socket = None
        
        self.is_connected = False
        logger.info("Disconnected from NoLimits 2")
    
    def _build_message(self, type_id: int, request_id: int = 0, data: bytes = b'') -> bytes:
        """
        Build a message in NoLimits 2 telemetry protocol format.
        
        Format:
        - Magic start (1 byte): 'N'
        - Type ID (2 bytes, uint16, big-endian)
        - Request ID (4 bytes, uint32, big-endian)
        - Data size (2 bytes, uint16, big-endian)
        - Data (variable)
        - Magic end (1 byte): 'L'
        
        Args:
            type_id: Message type ID
            request_id: Request ID for tracking
            data: Optional data payload
            
        Returns:
            Complete message as bytes
        """
        data_size = len(data)
        
        # Build header: N + type_id + request_id + data_size
        header = struct.pack('!cHIH', self.MAGIC_START, type_id, request_id, data_size)
        
        # Complete message
        message = header + data + self.MAGIC_END
        
        return message
    
    def _parse_message(self, data: bytes) -> Optional[dict]:
        """
        Parse a message from NoLimits 2.
        
        Args:
            data: Raw bytes received
            
        Returns:
            Dictionary with message fields or None if invalid
        """
        if len(data) < 10:  # Minimum size
            logger.warning(f"Message too small: {len(data)} bytes")
            return None
        
        # Check magic bytes
        if data[0:1] != self.MAGIC_START or data[-1:] != self.MAGIC_END:
            logger.warning("Invalid magic bytes")
            return None
        
        # Parse header
        try:
            type_id, request_id, data_size = struct.unpack('!HIH', data[1:9])
            
            # Extract data payload
            payload = data[9:9+data_size]
            
            return {
                'type_id': type_id,
                'request_id': request_id,
                'data_size': data_size,
                'data': payload
            }
        except struct.error as e:
            logger.error(f"Failed to parse message header: {e}")
            return None
    
    def _parse_telemetry_data(self, data: bytes) -> Optional[CoasterState]:
        """
        Parse telemetry data payload into CoasterState.
        
        Telemetry format (big-endian):
        - state flags (4 bytes, int32)
        - rendered_frame (4 bytes, int32)
        - view_mode (4 bytes, int32)
        - current_coaster (4 bytes, int32)
        - coaster_style_id (4 bytes, int32)
        - current_train (4 bytes, int32)
        - current_car (4 bytes, int32)
        - current_seat (4 bytes, int32)
        - speed (4 bytes, float32)
        - position x, y, z (12 bytes, 3× float32)
        - quaternion x, y, z, w (16 bytes, 4× float32)
        - g-force x, y, z (12 bytes, 3× float32)
        Total: 76 bytes (from py_nl2telemetry)
        
        Args:
            data: Telemetry data payload
            
        Returns:
            CoasterState object or None if parsing failed
        """
        # Log actual size for debugging
        if len(data) != 76:
            logger.debug(f"Telemetry data size: {len(data)} bytes (expected 76)")
        
        # Accept 76 or more bytes (newer versions might have extra data)
        if len(data) < 76:
            logger.warning(f"Telemetry data too small: {len(data)} bytes")
            return None
        
        try:
            # Unpack exactly 76 bytes (the known format)
            # Format: 8 ints + 1 float (speed) + 3 floats (pos) + 4 floats (quat) + 3 floats (g)
            # = 8i + 11f = !iiiiiiiifffffffffff (19 values)
            unpacked = struct.unpack('!iiiiiiiifffffffffff', data[:76])
            
            # Extract fields
            state_flags = unpacked[0]
            rendered_frame = unpacked[1]
            view_mode = unpacked[2]
            current_coaster = unpacked[3]
            coaster_style_id = unpacked[4]
            current_train = unpacked[5]
            current_car = unpacked[6]
            current_seat = unpacked[7]
            speed = unpacked[8]
            pos_x, pos_y, pos_z = unpacked[9:12]
            quat_x, quat_y, quat_z, quat_w = unpacked[12:16]
            g_x, g_y, g_z = unpacked[16:19]
            
            # Parse state flags
            in_play_mode = (state_flags >> 0) & 1
            is_braking = (state_flags >> 1) & 1
            is_paused = (state_flags >> 2) & 1
            
            # Calculate velocity from speed (approximation - we don't have direction)
            # In a real scenario, this should be derived from position changes
            velocity = Vector3D(0.0, 0.0, speed)
            
            # Calculate acceleration from g-forces
            # Convert G to m/s² (1G = 9.81 m/s²)
            acceleration = Vector3D(g_x * 9.81, g_y * 9.81, g_z * 9.81)
            
            # Build CoasterState
            state = CoasterState(
                timestamp=float(rendered_frame) / 60.0,  # Assume 60 FPS
                position=Vector3D(pos_x, pos_y, pos_z),
                velocity=velocity,
                acceleration=acceleration,
                orientation=Quaternion(quat_w, quat_x, quat_y, quat_z),
                g_force=Vector3D(g_x, g_y, g_z),
                speed=speed,
                view_mode=view_mode,
                train_index=current_train
            )
            
            return state if state.is_valid() else None
            
        except struct.error as e:
            logger.error(f"Failed to parse telemetry data: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error parsing telemetry: {e}")
            return None
    
    def get_telemetry(self, request_id: int = 0) -> Optional[CoasterState]:
        """
        Request and receive telemetry data from NoLimits 2.
        
        Args:
            request_id: Request ID for tracking
            
        Returns:
            CoasterState object or None if failed
        """
        if not self.is_connected or not self.socket:
            logger.error("Not connected")
            return None
        
        try:
            # Build and send telemetry request
            message = self._build_message(self.MSG_GET_TELEMETRY, request_id)
            self.socket.send(message)
            
            # Receive response
            response = self.socket.recv(1024)
            
            # Parse response
            parsed = self._parse_message(response)
            if not parsed:
                return None
            
            # Check if it's telemetry data
            if parsed['type_id'] != self.REPLY_TELEMETRY:
                if parsed['type_id'] == self.REPLY_ERROR:
                    error_msg = parsed['data'].decode('utf-8', errors='ignore')
                    logger.error(f"Server error: {error_msg}")
                else:
                    logger.warning(f"Unexpected reply type: {parsed['type_id']}")
                return None
            
            # Parse telemetry data
            return self._parse_telemetry_data(parsed['data'])
            
        except socket.timeout:
            logger.warning("Telemetry request timed out")
            return None
        except Exception as e:
            logger.error(f"Error getting telemetry: {e}")
            return None
    
    def get_version(self) -> Optional[str]:
        """
        Get NoLimits 2 version.
        
        Returns:
            Version string or None if failed
        """
        if not self.is_connected or not self.socket:
            logger.error("Not connected")
            return None
        
        try:
            # Build and send version request
            message = self._build_message(self.MSG_GET_VERSION, 0)
            self.socket.send(message)
            
            # Receive response
            response = self.socket.recv(1024)
            
            # Parse response
            parsed = self._parse_message(response)
            if not parsed or parsed['type_id'] != self.REPLY_VERSION:
                return None
            
            # Parse version data (4 bytes: major, minor, revision, build)
            if len(parsed['data']) >= 4:
                version_bytes = struct.unpack('!bbbb', parsed['data'][:4])
                version = f"{version_bytes[0]}.{version_bytes[1]}.{version_bytes[2]}.{version_bytes[3]}"
                return version
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting version: {e}")
            return None
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
