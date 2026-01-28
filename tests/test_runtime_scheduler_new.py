"""
Tests for runtime/scheduler.py (NexusPipeline)
"""

import pytest
from runtime.scheduler import NexusPipeline, Phase

@pytest.fixture
def pipeline():
    return NexusPipeline()

def test_pipeline_initialization(pipeline):
    state = pipeline.create_instance("Test task")
    assert state["current_phase"] == Phase.LOOK
    assert state["status"] == "running"
    assert "id" in state
    assert state["context"]["user_prompt"] == "Test task"

def test_linear_transitions(pipeline):
    state = pipeline.create_instance("Test task")
    
    # LOOK -> PLAN
    state = pipeline.next_phase(state, {"summary": "Found files"})
    assert state["current_phase"] == Phase.PLAN
    assert len(state["history"]) == 1
    
    # PLAN -> EXECUTE
    state = pipeline.next_phase(state, {"summary": "Designed architecture"})
    assert state["current_phase"] == Phase.EXECUTE
    
    # EXECUTE -> VERIFY
    state = pipeline.next_phase(state, {"summary": "Implemented code"})
    assert state["current_phase"] == Phase.VERIFY
    
    # VERIFY -> COMPLETE
    state = pipeline.next_phase(state, {"summary": "Tests passed"})
    assert state["current_phase"] == Phase.COMPLETE
    assert state["status"] == "completed"

def test_loopback_logic(pipeline):
    state = pipeline.create_instance("Test task")
    
    # Go to EXECUTE
    state = pipeline.next_phase(state) # to PLAN
    state = pipeline.next_phase(state) # to EXECUTE
    assert state["current_phase"] == Phase.EXECUTE
    
    # Simulation: Execution failed, loop back to PLAN
    state = pipeline.request_loopback(state, Phase.PLAN, "Implementation conflict")
    assert state["current_phase"] == Phase.PLAN
    assert state["status"] == "running"
    assert any(h.get("event") == "loopback" for h in state["history"])

def test_role_mapping(pipeline):
    state = pipeline.create_instance("Test")
    assert pipeline.get_active_role(state) == "nexus-eye"
    
    state["current_phase"] = Phase.PLAN
    assert pipeline.get_active_role(state) == "nexus-core"
    
    state["current_phase"] = Phase.EXECUTE
    assert pipeline.get_active_role(state) == "nexus-coder"
