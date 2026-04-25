import logging
from typing import Tuple, Dict, Any

class SafetyValidator:
    """
    Validator Module (V)
    Enforces the Safety Layer Contract: Input -> (ALLOW | BLOCK, rationale)
    """
    def __init__(self, limits: Dict[str, float] = None):
        self.limits = limits or {
            "max_linear_vel": 0.5,    # m/s
            "max_angular_vel": 1.0,   # rad/s
            "geofence_radius": 10.0   # meters from origin
        }
        self.logger = logging.getLogger("validator")

    def validate_action(self, tool_name: str, params: Dict[str, Any], robot_state: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Main entry point for pre-execution validation.
        """
        # 1. Action Allowlist
        if tool_name not in ["move_to_position", "stop_motion", "search_for_object", "get_robot_state", "robot_heartbeat"]:
             return False, f"Unauthorized tool call: {tool_name}"

        # 2. Velocity Limit Validation
        if tool_name == "move_to_position":
            return self._validate_movement(params, robot_state)

        # 3. Parameter Integrity
        if tool_name == "search_for_object" and "label" not in params:
            return False, "Missing required parameter 'label'"

        return True, "Validated"

    def _validate_movement(self, params: Dict[str, Any], robot_state: Dict[str, Any]) -> Tuple[bool, str]:
        # Simple Geofencing
        target_x = params.get("x", 0)
        target_y = params.get("y", 0)
        
        dist_from_origin = (target_x**2 + target_y**2)**0.5
        if dist_from_origin > self.limits["geofence_radius"]:
            return False, f"Geofence Violation: Target {dist_from_origin:.2f}m exceeds limit of {self.limits['geofence_radius']}m"

        return True, "Validated"
