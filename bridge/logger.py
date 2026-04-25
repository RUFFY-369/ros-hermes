import json
import time
from pathlib import Path
from typing import Dict, Any

class AuditLogger:
    """
    Audit Logger (L)
    Maintains a persistent record of the reasoning-execution chain:
    ℓ_t = (t, observation, action, decision, rationale, outcome)
    """
    def __init__(self, log_dir: str = None):
        if log_dir is None:
            base_dir = Path(__file__).parent
            log_dir = base_dir / "logs" / "audit"
        self.log_path = Path(log_dir) / f"audit_{int(time.time())}.jsonl"
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        
    def log_event(self, observation: Dict, action: str, params: Dict, decision: str, rationale: str, outcome: str = "PENDING"):
        log_entry = {
            "timestamp": time.time(),
            "observation": observation,
            "action": action,
            "parameters": params,
            "decision": decision,
            "rationale": rationale,
            "outcome": outcome
        }
        
        with open(self.log_path, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
            
        return log_entry
