"""Tests for workspace state machine."""
import pytest
from pyworkspace.core.workspace_engine import WorkspaceStateMachine, InvalidTransitionError

class TestWorkspaceStateMachine:
    def test_valid_transition_provisioning_to_running(self):
        sm = WorkspaceStateMachine("ws-1", "provisioning")
        result = sm.transition("running")
        assert result == "running"
        assert sm.status == "running"

    def test_valid_transition_running_to_paused(self):
        sm = WorkspaceStateMachine("ws-1", "running")
        result = sm.transition("paused")
        assert result == "paused"

    def test_invalid_transition_paused_to_running(self):
        sm = WorkspaceStateMachine("ws-1", "paused")
        with pytest.raises(InvalidTransitionError):
            sm.transition("running")

    def test_valid_transition_paused_to_resuming(self):
        sm = WorkspaceStateMachine("ws-1", "paused")
        sm.transition("resuming")
        assert sm.status == "resuming"

    def test_can_transition(self):
        sm = WorkspaceStateMachine("ws-1", "running")
        assert sm.can_transition("paused") is True
        assert sm.can_transition("running") is False

    def test_error_from_any_state(self):
        for status in ["provisioning", "running", "paused", "resuming", "destroying"]:
            sm = WorkspaceStateMachine("ws-1", status)
            sm.transition("error")
            assert sm.status == "error"
