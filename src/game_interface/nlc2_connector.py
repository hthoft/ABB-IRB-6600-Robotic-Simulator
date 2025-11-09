"""
NoLimits Coaster 2 Connector - UDP Telemetry Interface.

This module handles the network connection to NoLimits 2 and manages
the telemetry data stream.
"""

import socket
import logging
import time
import threading
from typing import Optional, Callable
from queue import Queue, Empty

from .telemetry_parser import TelemetryParser
from .data_structures import CoasterState, TelemetryMessage

logger = logging.getLogger(__name__)


class NLC2Connector:
    """
    Manages UDP connection to NoLimits Coaster 2 for telemetry data.
    
    NoLimits 2 telemetry works as follows:
    1. Client sends request packets to NoLimits 2
    2. NoLimits 2 responds with telemetry data
    3. Data is sent continuously while simulation is running
    """
    
    def __init__(
        self,
        host: str = "127.0.0.1",
        send_port: int = 15151,
        receive_port: int = 15152,
        buffer_size: int = 1024,
        timeout: float = 5.0
    ):
        """
        Initialize NoLimits 2 connector.
        
        Args:
            host: IP address of NoLimits 2 instance (usually localhost)
            send_port: Port to send requests to NoLimits 2
            receive_port: Port to receive telemetry data on
            buffer_size: UDP receive buffer size
            timeout: Connection timeout in seconds
        """
        self.host = host
        self.send_port = send_port
        self.receive_port = receive_port
        self.buffer_size = buffer_size
        self.timeout = timeout
        
        self.parser = TelemetryParser()
        self.socket: Optional[socket.socket] = None
        self.is_connected = False
        self.is_running = False
        
        # Threading
        self._receive_thread: Optional[threading.Thread] = None
        self._request_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        # Data queue for received states
        self.state_queue: Queue[CoasterState] = Queue(maxsize=100)
        
        # Callback for real-time processing
        self.state_callback: Optional[Callable[[CoasterState], None]] = None
        
        # Statistics
        self.packets_received = 0
        self.packets_sent = 0
        self.last_state_time = 0.0
        
    def connect(self) -> bool:
        """
        Establish connection to NoLimits 2.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Create UDP socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Bind to receive port
            self.socket.bind(('0.0.0.0', self.receive_port))
            self.socket.settimeout(1.0)  # 1 second timeout for receive
            
            logger.info(f"UDP socket bound to port {self.receive_port}")
            
            # Send version request to check connection
            version_packet = self.parser.create_version_request_packet()
            self.socket.sendto(version_packet, (self.host, self.send_port))
            
            # Wait for response
            try:
                data, addr = self.socket.recvfrom(self.buffer_size)
                logger.info(f"Received response from {addr}")
                self.is_connected = True
                return True
            except socket.timeout:
                logger.warning("No response from NoLimits 2 - connection may be unavailable")
                # Don't fail completely - might just be waiting for game to start
                self.is_connected = True
                return True
                
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            self.is_connected = False
            return False
    
    def disconnect(self) -> None:
        """Close connection to NoLimits 2."""
        self.stop()
        
        if self.socket:
            try:
                self.socket.close()
            except Exception as e:
                logger.error(f"Error closing socket: {e}")
            self.socket = None
        
        self.is_connected = False
        logger.info("Disconnected from NoLimits 2")
    
    def start(self) -> bool:
        """
        Start receiving telemetry data.
        
        Returns:
            True if started successfully, False otherwise
        """
        if not self.is_connected:
            logger.error("Not connected - call connect() first")
            return False
        
        if self.is_running:
            logger.warning("Already running")
            return True
        
        self.is_running = True
        self._stop_event.clear()
        
        # Start receive thread
        self._receive_thread = threading.Thread(
            target=self._receive_loop,
            name="NLC2-Receive",
            daemon=True
        )
        self._receive_thread.start()
        
        # Start request thread
        self._request_thread = threading.Thread(
            target=self._request_loop,
            name="NLC2-Request",
            daemon=True
        )
        self._request_thread.start()
        
        logger.info("Started telemetry reception")
        return True
    
    def stop(self) -> None:
        """Stop receiving telemetry data."""
        if not self.is_running:
            return
        
        self.is_running = False
        self._stop_event.set()
        
        # Wait for threads to finish
        if self._receive_thread:
            self._receive_thread.join(timeout=2.0)
        if self._request_thread:
            self._request_thread.join(timeout=2.0)
        
        logger.info("Stopped telemetry reception")
    
    def _receive_loop(self) -> None:
        """Background thread to receive telemetry data."""
        logger.info("Receive loop started")
        
        while self.is_running and not self._stop_event.is_set():
            try:
                if not self.socket:
                    break
                
                # Receive data
                data, addr = self.socket.recvfrom(self.buffer_size)
                self.packets_received += 1
                
                # Parse packet
                message = self.parser.parse_packet(data)
                
                if message and message.is_state_message() and message.state:
                    state = message.state
                    self.last_state_time = time.time()
                    
                    # Add to queue (non-blocking)
                    try:
                        self.state_queue.put_nowait(state)
                    except:
                        # Queue full - drop oldest
                        try:
                            self.state_queue.get_nowait()
                            self.state_queue.put_nowait(state)
                        except:
                            pass
                    
                    # Call callback if set
                    if self.state_callback:
                        try:
                            self.state_callback(state)
                        except Exception as e:
                            logger.error(f"Error in state callback: {e}")
                            
            except socket.timeout:
                # Normal timeout - continue
                continue
            except Exception as e:
                if self.is_running:
                    logger.error(f"Error in receive loop: {e}")
                break
        
        logger.info("Receive loop stopped")
    
    def _request_loop(self) -> None:
        """Background thread to periodically request telemetry."""
        logger.info("Request loop started")
        
        request_interval = 0.1  # Request every 100ms
        
        while self.is_running and not self._stop_event.is_set():
            try:
                if not self.socket:
                    break
                
                # Send telemetry request
                packet = self.parser.create_request_telemetry_packet()
                self.socket.sendto(packet, (self.host, self.send_port))
                self.packets_sent += 1
                
                # Wait before next request
                self._stop_event.wait(request_interval)
                
            except Exception as e:
                if self.is_running:
                    logger.error(f"Error in request loop: {e}")
                break
        
        logger.info("Request loop stopped")
    
    def get_latest_state(self, timeout: float = 0.1) -> Optional[CoasterState]:
        """
        Get the most recent coaster state.
        
        Args:
            timeout: Maximum time to wait for data (seconds)
            
        Returns:
            Latest CoasterState or None if no data available
        """
        try:
            return self.state_queue.get(timeout=timeout)
        except Empty:
            return None
    
    def clear_queue(self) -> None:
        """Clear all pending states from queue."""
        while not self.state_queue.empty():
            try:
                self.state_queue.get_nowait()
            except Empty:
                break
    
    def set_callback(self, callback: Callable[[CoasterState], None]) -> None:
        """
        Set callback function to be called for each received state.
        
        Args:
            callback: Function that takes a CoasterState parameter
        """
        self.state_callback = callback
    
    def get_connection_status(self) -> dict:
        """
        Get connection status and statistics.
        
        Returns:
            Dictionary with connection information
        """
        age = time.time() - self.last_state_time if self.last_state_time > 0 else None
        
        parser_stats = self.parser.get_stats()
        
        return {
            'connected': self.is_connected,
            'running': self.is_running,
            'packets_received': self.packets_received,
            'packets_sent': self.packets_sent,
            'last_state_age': age,
            'queue_size': self.state_queue.qsize(),
            'dropped_frames': parser_stats['dropped_frames'],
            'drop_rate': parser_stats['drop_rate']
        }
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
