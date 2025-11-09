# Coding Conventions

This document defines the coding standards for the ABB IRB-6600 Robotic Simulator project.

## Table of Contents

1. [General Principles](#general-principles)
2. [Python Style Guide](#python-style-guide)
3. [Safety-Critical Code](#safety-critical-code)
4. [Documentation](#documentation)
5. [Testing](#testing)
6. [Version Control](#version-control)
7. [Dependencies](#dependencies)

---

## General Principles

### Safety First
- **All code must prioritize safety over performance or features**
- Safety-critical modules require peer review before merge
- Emergency stop functionality must never be disabled
- Always fail to a safe state

### Code Quality
- Write clear, maintainable, self-documenting code
- Prefer readability over cleverness
- Use meaningful variable and function names
- Keep functions focused and small (<50 lines when possible)

### Performance
- Target <50ms latency for game-to-robot pipeline
- Profile before optimizing
- Document performance-critical sections

---

## Python Style Guide

### General Style

Follow **PEP 8** with the following project-specific rules:

- **Line Length**: 100 characters (not 79)
- **Indentation**: 4 spaces (no tabs)
- **Quotes**: Double quotes `"` for strings, single quotes `'` for dict keys when appropriate
- **Type Hints**: Required for all function signatures

### Naming Conventions

```python
# Classes: PascalCase
class MotionController:
    pass

# Functions and methods: snake_case
def calculate_tcp_position():
    pass

# Variables: snake_case
robot_position = [0, 0, 0]
tcp_offset = [0, 0, 100]

# Constants: UPPER_SNAKE_CASE
MAX_VELOCITY = 1000  # mm/s
SAFETY_TIMEOUT = 5.0  # seconds

# Private methods/attributes: leading underscore
def _internal_helper():
    pass

# Protected (subclass use): single leading underscore
_protected_value = 42

# Module-level "private": single leading underscore
_internal_cache = {}
```

### Type Hints

All functions must include type hints:

```python
from typing import List, Tuple, Optional, Dict
import numpy as np
from numpy.typing import NDArray

def transform_coordinates(
    position: NDArray[np.float64],
    rotation: NDArray[np.float64],
    scale: float = 1.0
) -> Tuple[NDArray[np.float64], NDArray[np.float64]]:
    """
    Transform coordinates from game space to robot space.
    
    Args:
        position: 3D position vector [x, y, z]
        rotation: 3x3 rotation matrix
        scale: Scaling factor for motion
        
    Returns:
        Tuple of (transformed_position, transformed_rotation)
    """
    # Implementation
    pass
```

### Imports

Organize imports in three groups (separated by blank lines):

```python
# 1. Standard library
import time
from typing import List, Optional

# 2. Third-party packages
import numpy as np
import pytest

# 3. Local modules
from src.safety import watchdog
from src.motion_control.inverse_kinematics import solve_ik
```

### Error Handling

Be explicit about exceptions:

```python
# Good
try:
    robot.move_to(target)
except ConnectionError as e:
    logger.error(f"Robot connection lost: {e}")
    trigger_emergency_stop()
except ValueError as e:
    logger.warning(f"Invalid target position: {e}")
    return False

# Bad - too broad
try:
    robot.move_to(target)
except Exception:
    pass
```

### Logging

Use structured logging with appropriate levels:

```python
import logging

logger = logging.getLogger(__name__)

# Levels
logger.debug("Detailed diagnostic information")
logger.info("Normal operation milestone")
logger.warning("Unexpected but handled situation")
logger.error("Error that prevents operation")
logger.critical("System-critical failure - immediate attention required")

# Include context
logger.error(
    "Failed to transform coordinates",
    extra={
        "position": position,
        "rotation": rotation,
        "module": "coordinate_transform"
    }
)
```

---

## Safety-Critical Code

### Designation

Mark safety-critical files with a header:

```python
"""
SAFETY-CRITICAL MODULE

This module implements emergency stop functionality.
All changes require:
1. Peer review by 2+ developers
2. Complete test coverage
3. Manual safety validation
4. Safety audit approval

Reviewer: ________________  Date: ________
Reviewer: ________________  Date: ________
"""
```

### Requirements for Safety Code

1. **No Complex Logic**: Keep safety code simple and obvious
2. **Defensive Programming**: Check all inputs, assume nothing
3. **Fail-Safe Defaults**: Always default to safe states
4. **No External Dependencies**: Minimize reliance on external libraries
5. **Comprehensive Testing**: 100% code coverage + manual validation
6. **Timeout Everything**: All operations must have timeouts

### Example: Safety-Critical Function

```python
def check_workspace_limits(position: NDArray[np.float64]) -> bool:
    """
    SAFETY-CRITICAL: Verify position is within safe workspace.
    
    Args:
        position: Target position in robot base frame [x, y, z] in mm
        
    Returns:
        True if position is safe, False otherwise
        
    Safety:
        - Returns False for any invalid input
        - Uses conservative workspace limits
        - No exceptions raised (fail-safe return)
    """
    # Validate input
    if position is None or len(position) != 3:
        logger.critical("Invalid position input to workspace check")
        return False
    
    if not all(np.isfinite(position)):
        logger.critical("Non-finite values in position")
        return False
    
    # Conservative workspace limits (mm)
    X_MIN, X_MAX = -2000, 2000
    Y_MIN, Y_MAX = -2000, 2000
    Z_MIN, Z_MAX = 0, 2500
    
    # Check boundaries
    x, y, z = position
    if not (X_MIN <= x <= X_MAX):
        logger.warning(f"X position {x} outside limits [{X_MIN}, {X_MAX}]")
        return False
    if not (Y_MIN <= y <= Y_MAX):
        logger.warning(f"Y position {y} outside limits [{Y_MIN}, {Y_MAX}]")
        return False
    if not (Z_MIN <= z <= Z_MAX):
        logger.warning(f"Z position {z} outside limits [{Z_MIN}, {Z_MAX}]")
        return False
    
    return True
```

### Watchdog Pattern

All critical loops must include watchdog monitoring:

```python
from src.safety.watchdog import Watchdog

def main_control_loop():
    """Main control loop with watchdog protection."""
    watchdog = Watchdog(timeout=1.0)  # 1 second timeout
    
    try:
        while True:
            watchdog.kick()  # Reset watchdog timer
            
            # Do work
            process_data()
            update_robot()
            
            time.sleep(0.01)  # 100 Hz
    except Exception as e:
        logger.critical(f"Control loop exception: {e}")
        trigger_emergency_stop()
```

---

## Documentation

### Docstrings

Use Google-style docstrings for all public functions and classes:

```python
def calculate_inverse_kinematics(
    tcp_position: NDArray[np.float64],
    tcp_orientation: NDArray[np.float64],
    current_joints: Optional[NDArray[np.float64]] = None
) -> Optional[NDArray[np.float64]]:
    """
    Calculate joint angles for desired TCP pose.
    
    Solves inverse kinematics for ABB IRB-6600 manipulator.
    Uses analytical solution when possible, numerical otherwise.
    
    Args:
        tcp_position: Target TCP position [x, y, z] in mm
        tcp_orientation: Target orientation as quaternion [w, x, y, z]
        current_joints: Current joint angles in radians (for continuity)
        
    Returns:
        Joint angles [j1, j2, j3, j4, j5, j6] in radians, or None if unreachable
        
    Raises:
        ValueError: If input dimensions are incorrect
        
    Example:
        >>> position = np.array([500, 0, 1000])
        >>> orientation = np.array([1, 0, 0, 0])
        >>> joints = calculate_inverse_kinematics(position, orientation)
        >>> print(joints)
        [0.0, -0.785, 1.57, 0.0, 0.785, 0.0]
    """
    # Implementation
    pass
```

### Code Comments

- Explain **why**, not **what**
- Comment complex algorithms
- Reference external resources (papers, standards)

```python
# Good
# Using Denavit-Hartenberg convention from ABB IRB-6600 manual (3HAC 12345-1)
dh_params = get_dh_parameters()

# Bad
# Get DH parameters
dh_params = get_dh_parameters()
```

### README Files

Each module should have a README.md explaining:
- Purpose
- Key components
- Usage examples
- Dependencies

---

## Testing

### Test Coverage

- **Safety modules**: 100% coverage required
- **Other modules**: 80% minimum coverage
- All public APIs must have tests

### Test Organization

```
tests/
├── unit/                  # Fast, isolated tests
│   ├── test_game_interface.py
│   ├── test_coordinate_transform.py
│   ├── test_motion_control.py
│   └── test_safety.py
└── integration/           # Multi-module tests
    ├── test_end_to_end.py
    └── test_safety_scenarios.py
```

### Test Naming

```python
def test_transform_coordinates_with_valid_input():
    """Test coordinate transformation with standard input."""
    pass

def test_transform_coordinates_with_invalid_input_raises_error():
    """Test that invalid input raises ValueError."""
    pass

def test_emergency_stop_halts_robot_within_timeout():
    """SAFETY: Verify E-stop stops motion within 100ms."""
    pass
```

### Fixtures and Mocks

Use pytest fixtures for common setup:

```python
import pytest
from unittest.mock import Mock

@pytest.fixture
def mock_robot():
    """Provide mock robot for testing."""
    robot = Mock()
    robot.is_connected.return_value = True
    robot.get_position.return_value = [0, 0, 0, 0, 0, 0]
    return robot

def test_motion_planning_with_mock_robot(mock_robot):
    """Test motion planning without real robot."""
    planner = MotionPlanner(mock_robot)
    assert planner.plan_trajectory([1000, 0, 1000]) is not None
```

### Safety Tests

Safety-critical code requires additional validation:

```python
@pytest.mark.safety_critical
def test_emergency_stop_all_failure_modes():
    """
    SAFETY TEST: E-stop must work in all scenarios.
    
    Tests:
    - Normal operation
    - During motion
    - Communication failure
    - Power loss simulation
    - Repeated activations
    """
    # Comprehensive test implementation
    pass
```

---

## Version Control

### Branch Naming

```
main                    # Production-ready code
develop                 # Integration branch
feature/game-data-extraction
feature/ik-solver
bugfix/watchdog-timeout
hotfix/emergency-stop-critical
safety/workspace-limits-review
```

### Commit Messages

Follow conventional commits:

```
feat: add inverse kinematics solver for IRB-6600
fix: correct workspace boundary check in safety module
docs: update API documentation for motion controller
test: add integration tests for game interface
refactor: simplify coordinate transformation logic
perf: optimize trajectory planning algorithm
safety: add redundant E-stop validation

BREAKING CHANGE: coordinate system changed to right-handed Z-up
```

### Pull Requests

All PRs must:
- Pass all tests (CI/CD)
- Maintain or improve code coverage
- Include documentation updates
- Be reviewed by at least one other developer

**Safety-critical PRs** require:
- Two reviewer approvals
- Manual safety validation
- Updated safety audit log

---

## Dependencies

### Allowed Dependencies

**Core Libraries**:
- `numpy`: Numerical computing
- `scipy`: Scientific computing
- `pytest`: Testing framework

**Communication**:
- `pyserial`: Serial communication
- `socket` (stdlib): Network communication

**Logging/Monitoring**:
- `logging` (stdlib): Standard logging
- `structlog`: Structured logging (optional)

**Configuration**:
- `pyyaml`: YAML config files
- `pydantic`: Config validation

### Dependency Rules

1. **Minimize dependencies**: Each dependency is a potential failure point
2. **Pin versions**: Use exact versions in `requirements.txt`
3. **Review licenses**: Ensure compatibility
4. **Safety-critical code**: Avoid external dependencies when possible
5. **Regular updates**: Review and update quarterly

### requirements.txt

```
# Numerical computing
numpy==1.24.0
scipy==1.10.0

# Testing
pytest==7.4.0
pytest-cov==4.1.0
pytest-mock==3.11.1

# Communication
pyserial==3.5

# Configuration
pyyaml==6.0
pydantic==2.0.0

# Logging
structlog==23.1.0
```

---

## Code Review Checklist

Before submitting code for review, verify:

- [ ] Code follows PEP 8 and project conventions
- [ ] All functions have type hints and docstrings
- [ ] Tests are included and passing
- [ ] Code coverage meets requirements
- [ ] No hardcoded values (use config files)
- [ ] Error handling is comprehensive
- [ ] Logging is appropriate
- [ ] Documentation is updated
- [ ] Safety implications considered
- [ ] Performance impact evaluated

For safety-critical code, additionally verify:

- [ ] Code is simple and obvious
- [ ] All inputs are validated
- [ ] Fail-safe defaults are used
- [ ] Timeouts are implemented
- [ ] Manual safety validation completed
- [ ] Two reviewers assigned
- [ ] Safety audit log updated

---

## Questions?

For clarification on coding standards, contact the project maintainers or open an issue for discussion.
