# ABB IRB-6600 Robotic Simulator - Requirements

## Python Version

- Python 3.10 or higher

## System Requirements

### Hardware
- Windows 10/11 (for NoLimits Coaster 2 compatibility)
- Minimum 8GB RAM
- Multi-core processor (4+ cores recommended)
- Network connection to ABB robot controller

### ABB Robot
- ABB IRB-6600 series robot
- IRC5 controller with network connectivity
- RobotWare 6.0 or higher
- Optional: Externally Guided Motion (EGM) option for low-latency control

### Software
- NoLimits Coaster 2 (Steam version)
- ABB RobotStudio (for simulation and testing)
- Git for version control

## Installation

1. Clone the repository:
```bash
git clone https://github.com/hthoft/ABB-IRB-6600-Robotic-Simulator.git
cd ABB-IRB-6600-Robotic-Simulator
```

2. Create a virtual environment:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Copy configuration templates:
```bash
copy config\robot_config.template.yaml config\robot_config.yaml
copy config\game_config.template.yaml config\game_config.yaml
```

5. Edit configuration files with your specific settings

## Development Setup

For development, install additional tools:

```bash
pip install black flake8 mypy pylint isort
```

Configure your IDE to use these tools for code formatting and linting.

## Testing

Run tests with:
```bash
pytest tests/
```

Run tests with coverage:
```bash
pytest --cov=src tests/
```

## Safety Considerations

⚠️ **Read before operating:**

1. Always test in simulation mode first
2. Ensure emergency stop button is accessible
3. Maintain safety barriers around robot
4. Never disable safety features
5. Follow all ABB safety guidelines
6. Have trained personnel present during operation

## License

(To be determined)
