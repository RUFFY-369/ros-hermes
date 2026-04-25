import os
import cv2
import numpy as np
import time
import httpx
import logging
import json
import asyncio
from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel
from typing import Dict, List, Optional
from pathlib import Path

# =============================================================================
# Configuration
# =============================================================================
PORT = int(os.getenv("PORT", 8081))
HOST = os.getenv("HOST", "0.0.0.0")
SWARM_SIZE = 4
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger("ros-hermes-bridge")

# =============================================================================
# Swarm Intelligence (Synthetic Engine)
# =============================================================================
class SyntheticRobot:
    def __init__(self, id, color, start_pos=(0, 0)):
        self.id = id
        self.color = color
        self.x, self.y = start_pos
        self.target_x, self.target_y = start_pos
        self.moving = False
        self.speed = 0.12
        self.history = []
        self.scan_angle = 0 # For Cinematic Radar
        
    def step(self):
        self.history.append((self.x, self.y))
        if len(self.history) > 30: self.history.pop(0)
        self.scan_angle = (self.scan_angle + 10) % 360
        
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        dist = (dx**2 + dy**2)**0.5
        if dist > 0.01:
            self.moving = True
            step_size = min(self.speed, dist)
            self.x += (dx/dist) * step_size
            self.y += (dy/dist) * step_size
        else:
            self.moving = False
            
    def get_observation(self, other_robots: List['SyntheticRobot']):
        target = {"label": "red_sphere", "x": 1.2, "y": -0.3}
        rel_x = target["x"] - self.x
        rel_y = target["y"] - self.y
        dist = (rel_x**2 + rel_y**2)**0.5
        
        objects = []
        if dist < 5.0:
            objects.append({"label": "red_sphere", "confidence": 0.98, "x": round(rel_x, 2), "y": round(rel_y, 2)})
            
        for other in other_robots:
            if other.id == self.id: continue
            rdx, rdy = other.x - self.x, other.y - self.y
            rdist = (rdx**2 + rdy**2)**0.5
            if rdist < 5.0:
                objects.append({"label": other.id, "confidence": 0.95, "x": round(rdx, 2), "y": round(rdy, 2)})
                
        return {
            "pose": {"x": round(self.x, 2), "y": round(self.y, 2)},
            "battery": 88.5,
            "vision": {"objects": objects}
        }

class SwarmManager:
    def __init__(self, size):
        colors = [(0, 255, 0), (0, 255, 255), (255, 255, 0), (255, 0, 255)]
        starts = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
        self.robots = {
            f"burger_{i+1:02d}": SyntheticRobot(
                f"burger_{i+1:02d}", 
                colors[i % len(colors)],
                starts[i % len(starts)]
            ) for i in range(size)
        }

swarm = SwarmManager(SWARM_SIZE)

# =============================================================================
# API Layer
# =============================================================================
app = FastAPI(title="ROS-Hermes Swarm Bridge")

class ActionRequest(BaseModel):
    robot_id: str
    tool_name: str
    params: dict

@app.get("/")
async def root():
    return {"status": "online", "swarm_size": len(swarm.robots), "robots": list(swarm.robots.keys())}

@app.get("/observation/{robot_id}")
async def get_observation(robot_id: str):
    if robot_id not in swarm.robots:
        raise HTTPException(status_code=404, detail=f"Robot {robot_id} not found")
    robot = swarm.robots[robot_id]
    return robot.get_observation(list(swarm.robots.values()))

@app.post("/execute")
async def execute_command(req: ActionRequest):
    if req.robot_id not in swarm.robots:
        return {"error": f"Robot {req.robot_id} not found"}
    
    robot = swarm.robots[req.robot_id]
    if req.tool_name == "move_to_position":
        try:
            robot.target_x = float(req.params["x"])
            robot.target_y = float(req.params["y"])
            return {"status": "moving", "target": {"x": robot.target_x, "y": robot.target_y}}
        except (ValueError, KeyError):
            return {"status": "error", "message": "Invalid coordinates"}
    return {"error": "Unknown tool"}

# =============================================================================
# Visual Engine (Cinematic Upgrade)
# =============================================================================
def get_frame():
    for r in swarm.robots.values(): r.step()
    
    # Base Canvas
    radar = np.zeros((640, 640, 3), dtype=np.uint8) + 15
    center = (320, 320)
    scale = 100 
    
    # Grid Arcs (Concentric Circles)
    for r in [100, 200, 300]:
        cv2.circle(radar, center, r, (30, 30, 30), 1)

    # Draw Target (Pulsing Red)
    pulse = int(abs(np.sin(time.time() * 3) * 5))
    tx, ty = int(center[0] + 1.2*scale), int(center[1] - (-0.3)*scale)
    cv2.circle(radar, (tx, ty), 10 + pulse, (0, 0, 150), -1)
    cv2.circle(radar, (tx, ty), 5, (0, 0, 255), -1)

    # Draw Data Links (Inter-robot lines)
    robot_list = list(swarm.robots.values())
    for i in range(len(robot_list)):
        for j in range(i + 1, len(robot_list)):
            p1 = (int(center[0] + robot_list[i].x*scale), int(center[1] - robot_list[i].y*scale))
            p2 = (int(center[0] + robot_list[j].x*scale), int(center[1] - robot_list[j].y*scale))
            cv2.line(radar, p1, p2, (30, 30, 30), 1)

    # Draw Robots
    for r in swarm.robots.values():
        rx, ry = int(center[0] + r.x*scale), int(center[1] - r.y*scale)
        
        # Radar Cone (Semi-transparent)
        overlay = radar.copy()
        cv2.ellipse(overlay, (rx, ry), (80, 80), r.scan_angle, 0, 45, r.color, -1)
        cv2.addWeighted(overlay, 0.2, radar, 0.8, 0, radar)

        # History Trail
        if len(r.history) > 1:
            for i in range(len(r.history)-1):
                h1 = (int(center[0] + r.history[i][0]*scale), int(center[1] - r.history[i][1]*scale))
                h2 = (int(center[0] + r.history[i+1][0]*scale), int(center[1] - r.history[i+1][1]*scale))
                cv2.line(radar, h1, h2, r.color, 1)

        cv2.circle(radar, (rx, ry), 7, r.color, -1)
        cv2.circle(radar, (rx, ry), 12, (255, 255, 255), 1)
        cv2.putText(radar, r.id, (rx+15, ry-15), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)

    cv2.putText(radar, "SWARM TACTICAL HUD V4 [CINEMATIC]", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    cv2.putText(radar, f"SYSTEM: {SWARM_SIZE} AGENTS ACTIVE", (20, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)

    _, buffer = cv2.imencode('.jpg', radar)
    return buffer.tobytes()

@app.get("/video_feed")
async def video_feed():
    async def generate():
        while True:
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + get_frame() + b'\r\n')
            await asyncio.sleep(0.04)
    return StreamingResponse(generate(), media_type="multipart/x-mixed-replace; boundary=frame")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)
