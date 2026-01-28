"""
Nexus Pipeline Scheduler - Linear phase-based execution model.

This module replaces the complex DAG-based scheduler with a streamlined
linear pipeline: LOOK -> PLAN -> EXECUTE -> VERIFY.
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any


class Phase(str, Enum):
    LOOK = "LOOK"        # nexus-eye: Context & Exploration
    PLAN = "PLAN"        # nexus-core: Strategy & Architecture
    EXECUTE = "EXECUTE"  # nexus-coder: Implementation
    VERIFY = "VERIFY"    # nexus-eye/coder: Final verification
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"


class NexusPipeline:
    """
    Simplified linear pipeline for Nexus task execution.
    
    Flow: LOOK -> PLAN -> EXECUTE -> VERIFY -> COMPLETE
    Allows for loops (e.g., VERIFY -> EXECUTE) if needed.
    """

    def __init__(self):
        self.phases = [Phase.LOOK, Phase.PLAN, Phase.EXECUTE, Phase.VERIFY]
        self.role_map = {
            Phase.LOOK: "nexus-eye",
            Phase.PLAN: "nexus-core",
            Phase.EXECUTE: "nexus-coder",
            Phase.VERIFY: "nexus-coder"  # Coder usually verifies their own work
        }

    def create_instance(self, user_prompt: str) -> Dict[str, Any]:
        """Initialize a new pipeline instance."""
        now = datetime.now(timezone.utc).isoformat()
        return {
            "id": f"pipe_{uuid.uuid4().hex[:12]}",
            "title": f"Task: {user_prompt[:50]}",
            "current_phase": Phase.LOOK,
            "status": "running",
            "created_at": now,
            "updated_at": now,
            "history": [],
            "context": {
                "user_prompt": user_prompt,
                "findings": [],
                "plan": None,
                "changes": [],
                "test_results": None
            }
        }

    def next_phase(self, current_state: Dict[str, Any], result: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Transition to the next phase in the pipeline.
        
        Args:
            current_state: The current pipeline state dictionary.
            result: The output from the specialist who just finished.
        """
        current = current_state["current_phase"]
        
        # Record history
        if result:
            current_state["history"].append({
                "phase": current,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "output_summary": result.get("summary", "No summary provided")
            })

        # Transition Logic
        if current == Phase.LOOK:
            next_p = Phase.PLAN
        elif current == Phase.PLAN:
            next_p = Phase.EXECUTE
        elif current == Phase.EXECUTE:
            next_p = Phase.VERIFY
        elif current == Phase.VERIFY:
            # If verification passed, we are done. If not, logic could loop back.
            next_p = Phase.COMPLETE
        else:
            next_p = current

        current_state["current_phase"] = next_p
        current_state["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        if next_p == Phase.COMPLETE:
            current_state["status"] = "completed"
            
        return current_state

    def get_active_role(self, current_state: Dict[str, Any]) -> str:
        """Get the @specialist handle for the current phase."""
        phase = current_state.get("current_phase", Phase.LOOK)
        return self.role_map.get(phase, "nexus-core")

    def request_loopback(self, current_state: Dict[str, Any], target_phase: Phase, reason: str) -> Dict[str, Any]:
        """Force the pipeline to loop back to a previous phase (e.g., re-plan)."""
        current_state["history"].append({
            "event": "loopback",
            "from": current_state["current_phase"],
            "to": target_phase,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        current_state["current_phase"] = target_phase
        current_state["status"] = "running"
        return current_state

    def get_summary(self, state: Dict[str, Any]) -> str:
        """Return a human-readable status of the pipeline."""
        return f"Pipeline {state['id']} | Phase: {state['current_phase']} | Status: {state['status']}"
