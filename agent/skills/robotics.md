# Skill: Autonomous Search and Stop (ROS2)
# Category: Robotics
# Description: Procedure for searching, identifying, and reaching a target object using a perception-action loop.

## Pre-conditions
- Execution Bridge is live (`/pose` and `/perception` endpoints active).
- Safety watchdog is satisfied (Heartbeat > 1Hz required).
- Robot is in a clear workspace (Check `get_robot_state`).

## Workflow
1. **Initial Scan**: Call `get_robot_state()` to analyze the current field of view.
2. **Detection Logic**: 
   - If target is found: Extract (x, y) coordinates from the perception JSON.
   - If target is NOT found: Call `move_to_position` to rotate the robot 30 degrees (theta change) to scan a new sector.
3. **Planning Step**:
   - Calculate the distance to the object.
   - Respect "Hard Safety" velocity clamping (do not expect speeds > 0.5m/s).
4. **Execution**:
   - Issue `move_to_position` towards the object coordinates.
   - Call `robot_heartbeat` at every reasoning step to prevent E-Stop.
5. **Finalization**:
   - Once within detection proximity (e.g., confidence high and size large), call `stop_motion`.

## Fail-safe / Troubleshooting
- **Heartbeat Lost**: If you see "Bridge Connection Failed", stop all reasoning and notify the user to check the local Execution Bridge status.
- **Geofence Hit**: If a movement command returns a 403 error, the robot has hit a "Hard Geofence". Do not retry the same coordinate; request a new path or manual steering.
- **Occlusion**: If the object was seen but lost, return to the last known "seen" position and perform a slow rotation scan.
