# Game Interface Module

This module handles all communication with NoLimits Coaster 2 and extracts real-time simulation data.

## Responsibilities

- Connect to NoLimits Coaster 2 via available APIs
- Extract position, velocity, acceleration, and orientation data
- Parse coaster metadata (track layout, G-force limits, etc.)
- Stream data to coordinate transformation module
- Handle connection errors and reconnection logic

## Key Components

- `nlc2_connector.py`: Main connection handler
- `data_parser.py`: Parse and validate incoming data
- `stream_manager.py`: Manage real-time data streaming
- `metadata_extractor.py`: Extract track and coaster information

## Data Format

All output data should use the standard game state format defined in `config/data_schema.json`.
