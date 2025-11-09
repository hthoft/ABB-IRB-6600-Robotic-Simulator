"""
Game Interface Module - NoLimits Coaster 2 Integration.

This module provides the interface to extract data from NoLimits Coaster 2.
"""

from .data_structures import CoasterState, Vector3D, Quaternion, TelemetryMessage
from .telemetry_parser import TelemetryParser
from .nlc2_connector import NLC2Connector
from .nl2_tcp_client import NL2TelemetryClient

__all__ = [
    'CoasterState',
    'Vector3D',
    'Quaternion',
    'TelemetryMessage',
    'TelemetryParser',
    'NLC2Connector',
    'NL2TelemetryClient',  # TCP-based client (recommended)
]
