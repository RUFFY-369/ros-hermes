import asyncio
import time
import logging
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import httpx

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ExecutionBridge")

app = FastAPI(title="ROS-Hermes Execution Bridge")

# Global State
class GlobalState:
    last_heartbeat = time.time()
    robot_pose = {"x": 0.0, "y": 0.0, "theta": 0.0}
    detections: List[Dict[str, Any]] = []
    is_emergency_stop = False
    
state = GlobalState()

# Pydantic Schemas
class MoveCommand(BaseModel):
    x: float
    y: float
    theta: float

class Heartbeat(BaseModel):
    agent_id: str

# --- Safety Watchdog ---
async def safety_watchdog():
    """Background task to enforce safety on disconnect."""
    while True:
        await asyncio.sleep(0.5)
        if time.time() - state.last_heartbeat > 2.0:  # 2-second timeout
            if not state.is_emergency_stop:
                logger.warning("SAFETY ALERT: Heartbeat lost! Triggering E-Stop.")
                await trigger_estop()

async def trigger_estop():
    state.is_emergency_stop = True
    # In a real implementation, this would call the ROS2 CMD_VEL publisher directly
    logger.info("ROBOT HALTED (Hard Safety Clamping)")

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(safety_watchdog())

# --- API Endpoints ---

@app.post("/heartbeat")
async def post_heartbeat(hb: Heartbeat):
    state.last_heartbeat = time.time()
    state.is_emergency_stop = False
    return {"status": "alive", "timestamp": state.last_heartbeat}

@app.post("/move_to_position")
async def move_to_position(cmd: MoveCommand):
    if state.is_emergency_stop:
        raise HTTPException(status_code=403, detail="Emergency Stop Active")
    
    logger.info(f"Moving to: x={cmd.x}, y={cmd.y}, theta={cmd.theta}")
    # Integration point for ROS2 Service Call
    return {"status": "command_dispatched", "target": cmd.dict()}

@app.post("/stop")
async def stop_robot():
    await trigger_estop()
    return {"status": "emergency_stop_triggered"}

@app.get("/get_robot_pose")
async def get_robot_pose():
    return state.robot_pose

@app.get("/get_detected_objects")
async def get_detected_objects():
    return {"objects": state.detections}

# --- Mock Data Ingestion (Internal) ---
@app.post("/internal/update_pose")
async def update_pose(pose: Dict[str, float]):
    state.robot_pose = pose
    return {"status": "ok"}

@app.post("/internal/update_detections")
async def update_detections(detections: List[Dict[str, Any]]):
    state.detections = detections
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
