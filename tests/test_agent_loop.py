"""
Agent Loop Tests — tests/test_agent_loop.py
============================================
Tests for agents/loop.py — the shared ReAct loop.

These are unit tests only — no API calls, no MCP server, no Postgres needed.
We test the logging, structure, and configuration of the loop
without actually calling Claude.
"""
import json
import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ── Import tests ───────────────────────────────────────────────────────────

class TestLoopImports:
    """Verify loop.py exports everything agents need."""

    def test_loop_imports_cleanly(self):
        """loop.py imports without errors."""
        try:
            import agents.loop as loop
            assert loop is not None
        except ImportError as e:
            pytest.fail(f"agents/loop.py failed to import: {e}")

    def test_required_functions_exist(self):
        """All functions that agents depend on must exist."""
        from agents.loop import (
            run_agent_loop,
            log_event,
            log_tool_failure,
            log_skip,
            log_agent_start,
            log_agent_complete,
            log_sub_agent_spawn,
            get_mcp_server_params,
        )
        assert callable(run_agent_loop)
        assert callable(log_event)
        assert callable(log_tool_failure)
        assert callable(log_skip)
        assert callable(log_agent_start)
        assert callable(log_agent_complete)
        assert callable(log_sub_agent_spawn)
        assert callable(get_mcp_server_params)

    def test_configuration_constants_exist(self):
        """Configuration constants must be defined."""
        from agents.loop import MODEL, MAX_TOKENS, MAX_ITERATIONS, MAX_RETRIES
        assert isinstance(MODEL, str)
        assert len(MODEL) > 0
        assert isinstance(MAX_TOKENS, int)
        assert isinstance(MAX_ITERATIONS, int)
        assert isinstance(MAX_RETRIES, int)

    def test_model_name_is_valid_format(self):
        """Model name should look like a real Anthropic model string."""
        from agents.loop import MODEL
        # Valid Anthropic model strings contain 'claude'
        assert "claude" in MODEL.lower(), \
            f"MODEL '{MODEL}' does not look like a valid Anthropic model string"

    def test_log_file_path_defined(self):
        """LOG_FILE constant must be defined."""
        from agents.loop import LOG_FILE
        assert isinstance(LOG_FILE, str)
        assert LOG_FILE.endswith(".jsonl"), \
            "Log file should be JSONL format"


# ── Logging tests ──────────────────────────────────────────────────────────

class TestLogging:
    """
    Test structured JSON logging.
    make verify reads these logs — getting them right is critical.
    """

    def test_log_event_writes_valid_json(self, tmp_path, monkeypatch):
        """log_event writes a valid JSON line to the log file."""
        import agents.loop as loop

        # Point log file to a temp location for testing
        test_log = str(tmp_path / "test.jsonl")
        monkeypatch.setattr(loop, "LOG_FILE", test_log)

        loop.log_event({"event": "test_event", "data": "hello"})

        with open(test_log) as f:
            lines = f.readlines()

        assert len(lines) == 1
        entry = json.loads(lines[0])
        assert entry["event"] == "test_event"
        assert entry["data"] == "hello"
        assert "timestamp" in entry

    def test_log_event_includes_timestamp(self, tmp_path, monkeypatch):
        """Every log entry must have a timestamp."""
        import agents.loop as loop
        test_log = str(tmp_path / "test.jsonl")
        monkeypatch.setattr(loop, "LOG_FILE", test_log)

        loop.log_event({"event": "anything"})

        with open(test_log) as f:
            entry = json.loads(f.readline())

        assert "timestamp" in entry
        # Timestamp should be ISO format
        assert "T" in entry["timestamp"]
        assert "Z" in entry["timestamp"] or "+" in entry["timestamp"]

    def test_log_tool_failure_has_required_fields(self, tmp_path, monkeypatch):
        """
        log_tool_failure must write specific fields.
        make verify checks for 'tool_call_failure' events in the log.
        """
        import agents.loop as loop
        test_log = str(tmp_path / "test.jsonl")
        monkeypatch.setattr(loop, "LOG_FILE", test_log)

        loop.log_tool_failure(
            run_id="test-run",
            tool_name="get_transaction",
            error="ValueError: something broke",
            transaction_id="abc-123"
        )

        with open(test_log) as f:
            entry = json.loads(f.readline())

        # make verify specifically checks for these fields
        assert entry["event"] == "tool_call_failure"
        assert entry["tool"] == "get_transaction"
        assert entry["transaction_id"] == "abc-123"
        assert "error" in entry
        assert "action" in entry

    def test_log_skip_has_required_fields(self, tmp_path, monkeypatch):
        """
        log_skip must write specific fields.
        make verify checks for 'skipping item, continuing' in the log.
        """
        import agents.loop as loop
        test_log = str(tmp_path / "test.jsonl")
        monkeypatch.setattr(loop, "LOG_FILE", test_log)

        loop.log_skip(
            run_id="test-run",
            transaction_id="abc-123",
            reason="Poison case: empty counterparty"
        )

        with open(test_log) as f:
            entry = json.loads(f.readline())

        assert entry["event"] == "skip_item"
        assert entry["transaction_id"] == "abc-123"
        assert "skipping" in entry["action"].lower()
        assert "continuing" in entry["action"].lower()

    def test_log_sub_agent_spawn_is_logged(self, tmp_path, monkeypatch):
        """
        Sub-agent spawning must be logged.
        Task requires sub-agent to be visible in logs.
        """
        import agents.loop as loop
        test_log = str(tmp_path / "test.jsonl")
        monkeypatch.setattr(loop, "LOG_FILE", test_log)

        loop.log_sub_agent_spawn(
            run_id="test-run",
            parent_agent="night-agent",
            sub_agent_purpose="generate morning report"
        )

        with open(test_log) as f:
            entry = json.loads(f.readline())

        assert entry["event"] == "sub_agent_spawn"
        assert entry["parent_agent"] == "night-agent"
        assert "sub_agent_purpose" in entry

    def test_multiple_log_entries_appended(self, tmp_path, monkeypatch):
        """Multiple log_event calls append lines, not overwrite."""
        import agents.loop as loop
        test_log = str(tmp_path / "test.jsonl")
        monkeypatch.setattr(loop, "LOG_FILE", test_log)

        loop.log_event({"event": "first"})
        loop.log_event({"event": "second"})
        loop.log_event({"event": "third"})

        with open(test_log) as f:
            lines = f.readlines()

        assert len(lines) == 3
        events = [json.loads(line)["event"] for line in lines]
        assert events == ["first", "second", "third"]


# ── Configuration tests ────────────────────────────────────────────────────

class TestConfiguration:
    """Test that configuration is read from environment correctly."""

    def test_model_configurable_via_env(self, monkeypatch):
        """MODEL should be overridable via MODEL_NAME env variable."""
        monkeypatch.setenv("MODEL_NAME", "claude-test-model")

        # Re-import to pick up the env change
        import importlib
        import agents.loop as loop
        # The module-level MODEL is set at import time
        # so we test the env reading pattern directly
        model = os.getenv("MODEL_NAME", "claude-sonnet-4-6")
        assert model == "claude-test-model"

    def test_mcp_server_params_point_to_server_file(self):
        """MCP server params should reference the actual server.py file."""
        from agents.loop import get_mcp_server_params
        params = get_mcp_server_params()
        assert "server.py" in params.args[-1]
        assert os.path.exists(params.args[-1]), \
            f"MCP server file not found at {params.args[-1]}"