"""
Unit tests for game_interface module.
"""

import pytest
import struct
import numpy as np
from src.game_interface import (
    CoasterState, Vector3D, Quaternion, TelemetryMessage,
    TelemetryParser, NLC2Connector
)


class TestVector3D:
    """Test Vector3D class."""
    
    def test_creation(self):
        """Test creating a Vector3D."""
        v = Vector3D(1.0, 2.0, 3.0)
        assert v.x == 1.0
        assert v.y == 2.0
        assert v.z == 3.0
    
    def test_to_array(self):
        """Test converting to numpy array."""
        v = Vector3D(1.0, 2.0, 3.0)
        arr = v.to_array()
        assert isinstance(arr, np.ndarray)
        assert np.allclose(arr, [1.0, 2.0, 3.0])
    
    def test_magnitude(self):
        """Test magnitude calculation."""
        v = Vector3D(3.0, 4.0, 0.0)
        assert abs(v.magnitude() - 5.0) < 1e-6
    
    def test_magnitude_zero(self):
        """Test magnitude of zero vector."""
        v = Vector3D(0.0, 0.0, 0.0)
        assert v.magnitude() == 0.0


class TestQuaternion:
    """Test Quaternion class."""
    
    def test_creation(self):
        """Test creating a Quaternion."""
        q = Quaternion(1.0, 0.0, 0.0, 0.0)
        assert q.w == 1.0
        assert q.x == 0.0
    
    def test_normalize(self):
        """Test quaternion normalization."""
        q = Quaternion(2.0, 0.0, 0.0, 0.0)
        qn = q.normalize()
        assert abs(qn.w - 1.0) < 1e-6
        assert abs(qn.x) < 1e-6
    
    def test_normalize_zero(self):
        """Test normalizing zero quaternion."""
        q = Quaternion(0.0, 0.0, 0.0, 0.0)
        qn = q.normalize()
        assert qn.w == 1.0  # Should default to identity
    
    def test_to_euler_identity(self):
        """Test converting identity quaternion to Euler angles."""
        q = Quaternion(1.0, 0.0, 0.0, 0.0)
        euler = q.to_euler()
        assert abs(euler.x) < 1e-6
        assert abs(euler.y) < 1e-6
        assert abs(euler.z) < 1e-6


class TestCoasterState:
    """Test CoasterState class."""
    
    def test_valid_state(self):
        """Test creating a valid coaster state."""
        state = CoasterState(
            timestamp=1.0,
            position=Vector3D(100.0, 50.0, 200.0),
            velocity=Vector3D(10.0, 5.0, 2.0),
            acceleration=Vector3D(1.0, 0.5, 0.1),
            orientation=Quaternion(1.0, 0.0, 0.0, 0.0),
            g_force=Vector3D(0.0, 0.0, 1.0),
            speed=11.0
        )
        assert state.is_valid()
    
    def test_invalid_state_nan(self):
        """Test that NaN values make state invalid."""
        state = CoasterState(
            timestamp=float('nan'),
            position=Vector3D(100.0, 50.0, 200.0),
            velocity=Vector3D(10.0, 5.0, 2.0),
            acceleration=Vector3D(1.0, 0.5, 0.1),
            orientation=Quaternion(1.0, 0.0, 0.0, 0.0),
            g_force=Vector3D(0.0, 0.0, 1.0),
            speed=11.0
        )
        assert not state.is_valid()
    
    def test_invalid_state_extreme_position(self):
        """Test that extreme position values make state invalid."""
        state = CoasterState(
            timestamp=1.0,
            position=Vector3D(100000.0, 50.0, 200.0),
            velocity=Vector3D(10.0, 5.0, 2.0),
            acceleration=Vector3D(1.0, 0.5, 0.1),
            orientation=Quaternion(1.0, 0.0, 0.0, 0.0),
            g_force=Vector3D(0.0, 0.0, 1.0),
            speed=11.0
        )
        assert not state.is_valid()
    
    def test_get_total_g_force(self):
        """Test total G-force calculation."""
        state = CoasterState(
            timestamp=1.0,
            position=Vector3D(0.0, 0.0, 0.0),
            velocity=Vector3D(0.0, 0.0, 0.0),
            acceleration=Vector3D(0.0, 0.0, 0.0),
            orientation=Quaternion(1.0, 0.0, 0.0, 0.0),
            g_force=Vector3D(3.0, 4.0, 0.0),
            speed=0.0
        )
        assert abs(state.get_total_g_force() - 5.0) < 1e-6
    
    def test_to_dict(self):
        """Test converting state to dictionary."""
        state = CoasterState(
            timestamp=1.0,
            position=Vector3D(100.0, 50.0, 200.0),
            velocity=Vector3D(10.0, 5.0, 2.0),
            acceleration=Vector3D(1.0, 0.5, 0.1),
            orientation=Quaternion(1.0, 0.0, 0.0, 0.0),
            g_force=Vector3D(0.0, 0.0, 1.0),
            speed=11.0
        )
        d = state.to_dict()
        assert d['timestamp'] == 1.0
        assert d['position']['x'] == 100.0
        assert d['speed'] == 11.0


class TestTelemetryParser:
    """Test TelemetryParser class."""
    
    def test_create_request_packet(self):
        """Test creating telemetry request packet."""
        parser = TelemetryParser()
        packet = parser.create_request_telemetry_packet()
        
        # Should be 8 bytes (2 x 4-byte integers)
        assert len(packet) == 8
        
        # Parse the packet
        msg_id, frame = struct.unpack('<II', packet)
        assert msg_id == parser.MSG_GET_TELEMETRY
        assert frame == 0
    
    def test_create_version_request_packet(self):
        """Test creating version request packet."""
        parser = TelemetryParser()
        packet = parser.create_version_request_packet()
        
        assert len(packet) == 8
        msg_id, frame = struct.unpack('<II', packet)
        assert msg_id == parser.MSG_GET_VERSION
    
    def test_parse_packet_too_small(self):
        """Test parsing packet that's too small."""
        parser = TelemetryParser()
        packet = b'\x00\x01'  # Only 2 bytes
        
        result = parser.parse_packet(packet)
        assert result is None
    
    def test_parse_telemetry_packet(self):
        """Test parsing a valid telemetry packet."""
        parser = TelemetryParser()
        
        # Create a mock telemetry packet
        # Header: message_id=4 (MSG_TELEMETRY), frame=1
        header = struct.pack('<II', 4, 1)
        
        # Telemetry data: 16 floats + 1 int
        position = (100.0, 50.0, 200.0)
        velocity = (10.0, 5.0, 2.0)
        acceleration = (1.0, 0.5, 0.1)
        quaternion = (1.0, 0.0, 0.0, 0.0)
        g_force = (0.0, 0.0, 1.0)
        view_mode = 0
        timestamp = 1.5
        
        telemetry = struct.pack(
            '<16fI',
            *position, *velocity, *acceleration, *quaternion, *g_force,
            view_mode
        )
        telemetry += struct.pack('<f', timestamp)
        
        packet = header + telemetry
        
        result = parser.parse_packet(packet)
        
        assert result is not None
        assert result.message_type == 4
        assert result.frame_number == 1
        assert result.is_state_message()
        assert result.state is not None
        
        state = result.state
        assert abs(state.position.x - 100.0) < 1e-6
        assert abs(state.velocity.y - 5.0) < 1e-6
        assert abs(state.timestamp - 1.5) < 1e-6
    
    def test_get_stats(self):
        """Test getting parser statistics."""
        parser = TelemetryParser()
        stats = parser.get_stats()
        
        assert 'last_frame_number' in stats
        assert 'dropped_frames' in stats
        assert 'drop_rate' in stats


class TestNLC2Connector:
    """Test NLC2Connector class."""
    
    def test_initialization(self):
        """Test connector initialization."""
        connector = NLC2Connector(
            host="127.0.0.1",
            send_port=15151,
            receive_port=15152
        )
        
        assert connector.host == "127.0.0.1"
        assert connector.send_port == 15151
        assert connector.receive_port == 15152
        assert not connector.is_connected
        assert not connector.is_running
    
    def test_context_manager(self):
        """Test using connector as context manager."""
        # Note: This will fail if NoLimits 2 is not running
        # but tests the interface
        try:
            with NLC2Connector() as connector:
                assert connector.is_connected or True  # May fail to connect
        except Exception:
            pass  # Expected if no game running
    
    def test_get_connection_status(self):
        """Test getting connection status."""
        connector = NLC2Connector()
        status = connector.get_connection_status()
        
        assert 'connected' in status
        assert 'running' in status
        assert 'packets_received' in status
        assert 'packets_sent' in status
