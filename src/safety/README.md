# Safety Module

**CRITICAL**: This module implements all safety systems. Changes require thorough review and testing.

## Responsibilities

- Monitor all system states continuously
- Implement emergency stop functionality
- Enforce workspace limits
- Apply velocity and acceleration limits
- Detect communication failures (watchdogs)
- Manage safe state recovery
- Log all safety events

## Key Components

- `watchdog.py`: Connection monitoring and heartbeat
- `emergency_stop.py`: E-stop handler and safe shutdown
- `limit_enforcer.py`: Velocity, acceleration, workspace limits
- `fault_detector.py`: Detect and classify system faults
- `recovery_manager.py`: Safe state recovery procedures
- `safety_logger.py`: Comprehensive safety event logging

## Safety Hierarchy

1. **Hardware E-stop**: Physical emergency stop button (highest priority)
2. **Software E-stop**: Triggered by safety violations
3. **Limit Enforcement**: Prevent exceeding safe parameters
4. **Watchdog**: Detect communication/system failures
5. **Fault Recovery**: Return to safe state after faults

## Testing Requirements

All safety functions must have:
- Unit tests with 100% coverage
- Integration tests for all fault scenarios
- Manual validation procedures
- Regular safety audits
