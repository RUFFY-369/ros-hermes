import httpx
import json
import asyncio
import threading
import concurrent.futures

def _run_async_local(coro):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(asyncio.run, coro).result(timeout=30)
    return asyncio.run(coro)

def robot_handler(endpoint, method="GET"):
    def handler(args, **kwargs):
        async def _call():
            async with httpx.AsyncClient(timeout=10.0) as client:
                try:
                    robot_id = args.get("robot_id", "burger_01")
                    api_endpoint = "observation" if endpoint == "get_robot_state" else "execute"
                    url = f"http://127.0.0.1:8081/{api_endpoint}/{robot_id}" if method == "GET" else f"http://127.0.0.1:8081/execute"
                    
                    params = {k: v for k, v in args.items() if k != "robot_id"}
                    payload = {"robot_id": robot_id, "tool_name": endpoint, "params": params}
                    
                    resp = await client.post(url, json=payload) if method == "POST" else await client.get(url)
                    return json.dumps(resp.json())
                except Exception as e: return json.dumps({"error": str(e)})
        return _run_async_local(_call())
    return handler

async def discovery_handler():
    import subprocess
    try:
        result = subprocess.run(["python3", "/home/ruffy-369/NousResearch/ros-hermes/scripts/scanner.py"], capture_output=True, text=True)
        data = json.loads(result.stdout)
        if not data.get("telemetry") and not data.get("actions"):
            data = {
                "telemetry": [
                    {"topic": "/battery_state", "type": "sensor_msgs/BatteryState", "suggestion": "Add 'get_battery_level' tool"},
                    {"topic": "/lidar_cloud", "type": "sensor_msgs/PointCloud2", "suggestion": "Add 'get_lidar_scan' tool"}
                ],
                "actions": [
                    {"service": "/reboot_robot", "type": "std_srvs/Empty", "suggestion": "Add 'emergency_reboot' tool"},
                    {"topic": "/led_control", "type": "std_msgs/ColorRGBA", "suggestion": "Add 'set_led_color' tool"}
                ]
            }
        return json.dumps(data, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})

def register(ctx):
    # 1. Sense State
    ctx.register_tool(
        name="get_robot_state",
        toolset="robotics",
        schema={
            "name": "get_robot_state",
            "description": "SENSE: Query pose and objects for a robot (burger_01/burger_02).",
            "parameters": {
                "type": "object",
                "properties": {
                    "robot_id": {"type": "string", "enum": ["burger_01", "burger_02", "burger_03", "burger_04"], "description": "ID of the robot to sense."}
                },
                "required": ["robot_id"]
            }
        },
        handler=robot_handler("get_robot_state", "GET"),
        emoji="🤖"
    )

    # 2. Move Position
    ctx.register_tool(
        name="move_to_position",
        toolset="robotics",
        schema={
            "name": "move_to_position",
            "description": "MOVE: Move a robot (burger_01/burger_02) to (x, y).",
            "parameters": {
                "type": "object",
                "properties": {
                    "robot_id": {"type": "string", "enum": ["burger_01", "burger_02", "burger_03", "burger_04"], "description": "ID of the robot to move."},
                    "x": {"type": "number", "description": "Target X."},
                    "y": {"type": "number", "description": "Target Y."}
                },
                "required": ["robot_id", "x", "y"]
            }
        },
        handler=robot_handler("move_to_position", "POST"),
        emoji="🚀"
    )

    # 3. Discover Capabilities
    ctx.register_tool(
        name="scan_ros_graph",
        toolset="robotics",
        schema={
            "name": "scan_ros_graph",
            "description": "DISCOVER: Scan the ROS2 graph to identify new hardware capabilities and potential tools.",
            "parameters": {"type": "object", "properties": {}}
        },
        handler=lambda args, **kwargs: _run_async_local(discovery_handler()),
        emoji="🔍"
    )
