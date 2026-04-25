import httpx
import json
from typing import Dict, Any, List
from tools.registry import registry

BRIDGE_URL = "http://localhost:8000"

async def _call_bridge(endpoint: str, method: str = "GET", data: Dict = None):
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            if method == "POST":
                resp = await client.post(f"{BRIDGE_URL}/{endpoint}", json=data)
            else:
                resp = await client.get(f"{BRIDGE_URL}/{endpoint}")
            
            if resp.status_code == 403:
                return {"error": f"Safety Blocked: {resp.json().get('detail')}"}
            
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"error": f"Bridge Connection Failed: {e}"}

# --- Hermes Tools ---

async def get_robot_state():
    """Retrieve full Observation (O) and Affordance (A) manifests from the robot."""
    affordance = await _call_bridge("affordance")
    observation = await _call_bridge("observation")
    return {
        "affordance": affordance,
        "observation": observation
    }

async def move_to_position(x: float, y: float, theta: float = 0.0):
    """Navigate the robot to a target (x, y) coordinate. Subject to Validator (V)."""
    return await _call_bridge("execute", "POST", {
        "tool_name": "move_to_position",
        "params": {"x": x, "y": y, "theta": theta}
    })

async def search_for_object(label: str):
    """Scan the current vision buffer for a specific YOLO object label."""
    state = await get_robot_state()
    vision = state.get("observation", {}).get("vision", {})
    objects = vision.get("objects", [])
    matches = [obj for obj in objects if obj['label'] == label]
    return {"found": True, "details": matches[0]} if matches else {"found": False, "message": f"No {label} detected."}

async def stop_motion():
    """Emergency stop command. Immediate execution."""
    return await _call_bridge("execute", "POST", {
        "tool_name": "stop_motion",
        "params": {}
    })

# --- Registration ---

registry.register(
    handler=get_robot_state,
    schema={"name": "get_robot_state", "description": "Get current sensors and robot capabilities."}
)

registry.register(
    handler=move_to_position,
    schema={
        "name": "move_to_position",
        "description": "Send navigation goal to the robot.",
        "parameters": {
            "type": "object",
            "properties": {
                "x": {"type": "number"},
                "y": {"type": "number"},
                "theta": {"type": "number"}
            },
            "required": ["x", "y"]
        }
    }
)

registry.register(
    handler=search_for_object,
    schema={
        "name": "search_for_object",
        "parameters": {"type": "object", "properties": {"label": {"type": "string"}}, "required": ["label"]}
    }
)

registry.register(
    handler=stop_motion,
    schema={"name": "stop_motion", "description": "Halt all robot movement."}
)
