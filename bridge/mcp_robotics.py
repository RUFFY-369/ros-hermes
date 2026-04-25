import asyncio
import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("robotics")
BRIDGE_URL = "http://localhost:8080"

@mcp.tool()
async def get_robot_state():
    """Retrieve the current robot pose and vision observations (O) from the Executive Layer."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(f"{BRIDGE_URL}/observation")
        return resp.json()

@mcp.tool()
async def move_to_position(x: float, y: float, theta: float = 0.0):
    """Instruct the robot to navigate to (x, y). Subject to Validator (V) safety checks."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        payload = {"tool_name": "move_to_position", "params": {"x": x, "y": y, "theta": theta}}
        resp = await client.post(f"{BRIDGE_URL}/execute", json=payload)
        return resp.json()

if __name__ == "__main__":
    mcp.run()
