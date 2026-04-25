import subprocess
import json
import re

class ROSDiscovery:
    """
    Discovery engine to map the ROS2 graph and identify candidate tools.
    """
    def __init__(self):
        pass

    def _run_cmd(self, cmd):
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            return result.stdout.splitlines()
        except Exception:
            return []

    def scan(self):
        # 1. Gather raw data
        topics = self._run_cmd(["ros2", "topic", "list"])
        services = self._run_cmd(["ros2", "service", "list"])
        
        # 2. Heuristic Filtering (Ignore internal ROS junk)
        internal_patterns = [
            r"/parameter_events", r"/rosout", r"/clock", 
            r"/tf", r"/tf_static", r"/get_loggers", r"/set_logger_level"
        ]
        
        candidates = {
            "telemetry": [],
            "actions": [],
            "configuration": []
        }
        
        for t in topics:
            if any(re.search(p, t) for p in internal_patterns): continue
            
            # Categorize based on common ROS naming conventions
            if any(x in t for x in ["state", "pose", "sensor", "battery", "scan"]):
                candidates["telemetry"].append({"topic": t, "type": "Subscriber"})
            elif any(x in t for x in ["cmd", "goal", "move", "set"]):
                candidates["actions"].append({"topic": t, "type": "Publisher"})
                
        for s in services:
            if any(re.search(p, s) for p in internal_patterns): continue
            candidates["actions"].append({"service": s, "type": "ServiceCall"})
            
        return candidates

if __name__ == "__main__":
    discovery = ROSDiscovery()
    report = discovery.scan()
    print(json.dumps(report, indent=2))
