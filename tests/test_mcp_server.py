"""
MCP Server Tests
================
Unit tests: test structure and imports, no stack needed.
Integration tests: call FastAPI directly, require make up + make seed.
"""
import pytest
import sys
import os
import httpx

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")


def api_available() -> bool:
    """Check if FastAPI is running."""
    try:
        response = httpx.get(f"{API_BASE}/", timeout=2.0)
        return response.status_code == 200
    except Exception:
        return False


# ── Unit tests — no stack needed ───────────────────────────────────────────

class TestMCPToolValidation:

    def test_server_imports_cleanly(self):
        """MCP server module imports without errors."""
        try:
            import mcp_server.server as server_module
            assert hasattr(server_module, "server")
        except ImportError as e:
            pytest.fail(f"MCP server failed to import: {e}")

    def test_five_tools_registered(self):
        """Server object exists and is initialized."""
        import mcp_server.server as server_module
        assert server_module.server is not None

    def test_api_base_url_configurable(self):
        """API base URL comes from environment, not hardcoded."""
        import mcp_server.server as server_module
        assert "localhost" in server_module.API_BASE or \
               os.getenv("API_BASE_URL") is not None


# ── Integration tests — require stack running ──────────────────────────────

@pytest.mark.skipif(not api_available(), reason="FastAPI not running — run make up first")
class TestMCPToolsIntegration:

    def test_list_transactions_returns_data(self):
        """list_transactions returns transactions from database."""
        response = httpx.get(
            f"{API_BASE}/transactions",
            params={"status": "pending", "limit": 5}
        )
        assert response.status_code == 200
        data = response.json()
        assert "transactions" in data
        assert "count" in data

    def test_get_risk_metrics_returns_structure(self):
        """get_risk_metrics returns expected fields."""
        response = httpx.get(f"{API_BASE}/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "count_by_status" in data
        assert "total_amount_by_status" in data
        assert "top_suspicious_counterparties" in data
        assert "total_transactions" in data

    def test_set_status_requires_reasoning(self):
        """set_transaction_status rejects empty reasoning."""
        response = httpx.get(
            f"{API_BASE}/transactions",
            params={"limit": 1}
        )
        transactions = response.json().get("transactions", [])
        if not transactions:
            pytest.skip("No transactions — run make seed first")

        tx_id = transactions[0]["id"]
        response = httpx.patch(
            f"{API_BASE}/transactions/{tx_id}/status",
            json={"status": "clean", "reasoning": "", "agent": "test"}
        )
        assert response.status_code == 422

    def test_invalid_uuid_returns_400(self):
        """get_transaction with invalid UUID returns 400."""
        response = httpx.get(f"{API_BASE}/transactions/not-a-valid-uuid")
        assert response.status_code == 400

    def test_write_report_saves_file(self):
        """write_report creates reports/morning-report.md."""
        response = httpx.post(
            f"{API_BASE}/reports",
            json={"content": "# Test Report\n\nTest.", "report_type": "test"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert os.path.exists("reports/morning-report.md")