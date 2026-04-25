# 🛸 ROS-Hermes Swarm Production Framework

A production-grade bridge connecting the **Hermes AI Agent** with a **ROS2-compatible robotics swarm**. This framework enables high-level agentic coordination, real-time tactical sensing, and automated hardware discovery.

## 🏛️ The Five-Pillar Architecture
1.  **The Plugin**: Native Hermes integration for "Sense, Act, Discover" toolsets.
2.  **The Bridge**: A high-performance FastAPI server (HAL) translating AI intent to ROS2 execution.
3.  **The Docker Stack**: Fully containerized ROS2 Humble environment for "One-Click" deployment.
4.  **The SDK**: Manual CLI (`hermes-robotics`) for human-in-the-loop control.
5.  **Discovery Engine**: Automated ROS graph mapping for self-auditing AI capabilities.

## 🚀 One-Click Installation
To install the swarm capabilities into your Hermes agent:

```bash
# 1. Symlink the plugin to your Hermes installation
ln -s $(pwd)/plugin ~/.hermes/plugins/ros-hermes

# 2. Launch the Swarm Infrastructure
docker-compose up -d
```

## 🕹️ Usage
### 1. Simulation Mode (Default)
Run the tactical dashboard at: `http://localhost:8081/video_feed`

**Demo Prompt:**
> "Hermes, initiate a full 4-unit tactical formation. Encircle the target at (1.2, -0.3) and perform a synchronized clockwise orbit."

### 2. Real Hardware Mode
To deploy on physical robots, update the `SyntheticRobot` class in `bridge/api.py` to use `rclpy` (ROS2 Python Client) for publishing to `/cmd_vel` and subscribing to `/odom`.

## 📂 Repository Structure
```text
ros-hermes/
├── bridge/
│   └── api.py          # The core HAL (Hardware Abstraction Layer)
├── plugin/
│   └── __init__.py     # The Hermes-side connector
├── scripts/
│   ├── scanner.py      # ROS2 Discovery Engine
│   └── hermes-robotics # Manual CLI SDK
├── Dockerfile          # ROS2 Humble + Python Base
└── docker-compose.yaml # Orchestration
```

## 🔗 Connect with the Commander
If you like this framework or want to collaborate, reach out:

*   **Twitter**: [@ruffy0369](https://x.com/ruffy0369)
*   **GitHub**: [RUFFY-369](https://github.com/RUFFY-369/)

---
**Maintained by: @ruffy0369 (RUFFY-369) | Swarm Commander**
