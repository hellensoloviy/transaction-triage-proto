"""
Custom MCP Server — the tool layer between agents and FastAPI.

Agents never call FastAPI directly.
They call MCP tools, which call FastAPI, which talks to Postgres.

Run with: python mcp_server/server.py
The agent loop starts this as a subprocess and communicates via stdio.
"""
import asyncio
import os
import sys
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types
from dotenv import load_dotenv

load_dotenv()

# FastAPI base URL — all tool calls go through here
API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")

# Initialize the MCP server
server = Server("transaction-triage-mcp")


# ── HTTP helper ────────────────────────────────────────────────────────────

async def api_get(path: str, params: dict = None) -> dict:
    """Make a GET request to FastAPI."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{API_BASE}{path}", params=params)
        response.raise_for_status()
        return response.json()


async def api_patch(path: str, data: dict) -> dict:
    """Make a PATCH request to FastAPI."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.patch(f"{API_BASE}{path}", json=data)
        response.raise_for_status()
        return response.json()


async def api_post(path: str, data: dict) -> dict:
    """Make a POST request to FastAPI."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(f"{API_BASE}{path}", json=data)
        response.raise_for_status()
        return response.json()


# ── Tool definitions ───────────────────────────────────────────────────────

@server.list_tools()
async def list_tools() -> list[types.Tool]:
    """Register all tools the agents can call."""
    return [
        types.Tool(
            name="list_transactions",
            description=(
                "List transactions filtered by status and optional time window. "
                "Returns a list of transactions with all fields. "
                "Use status='pending' for Day Agent, status='suspicious' for Night Agent."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "description": "Filter by status: pending, clean, suspicious, blocked, needs-human-review",
                        "enum": ["pending", "clean", "suspicious", "blocked", "needs-human-review"]
                    },
                    "since": {
                        "type": "string",
                        "description": "ISO 8601 timestamp — only return transactions created after this time"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of transactions to return (default 100)",
                        "default": 100
                    }
                },
                "required": []
            }
        ),

        types.Tool(
            name="get_transaction",
            description=(
                "Fetch a single transaction by ID. "
                "Returns all fields including prior agent notes. "
                "Use this before classifying to see full context."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "transaction_id": {
                        "type": "string",
                        "description": "UUID of the transaction to fetch"
                    }
                },
                "required": ["transaction_id"]
            }
        ),

        types.Tool(
            name="set_transaction_status",
            description=(
                "Update a transaction's status with a required reasoning note. "
                "Always provide a clear reasoning note explaining the classification decision. "
                "Valid statuses: clean, suspicious, blocked, needs-human-review."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "transaction_id": {
                        "type": "string",
                        "description": "UUID of the transaction to update"
                    },
                    "status": {
                        "type": "string",
                        "description": "New status for the transaction",
                        "enum": ["clean", "suspicious", "blocked", "needs-human-review"]
                    },
                    "reasoning": {
                        "type": "string",
                        "description": "Required explanation for this classification decision"
                    },
                    "agent": {
                        "type": "string",
                        "description": "Name of the agent making this decision (e.g. day-agent, night-agent)"
                    }
                },
                "required": ["transaction_id", "status", "reasoning", "agent"]
            }
        ),

        types.Tool(
            name="get_risk_metrics",
            description=(
                "Aggregate risk metrics over a time window. "
                "Returns count by status, total amount by status, "
                "and top counterparties by suspicious transaction count. "
                "Use this for the Night Agent morning report summary."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "since": {
                        "type": "string",
                        "description": "ISO 8601 timestamp — aggregate only transactions after this time"
                    },
                    "top_n": {
                        "type": "integer",
                        "description": "Number of top counterparties to return (default 5)",
                        "default": 5
                    }
                },
                "required": []
            }
        ),

        types.Tool(
            name="write_report",
            description=(
                "Save a structured markdown report and return its identifier. "
                "The report is saved to reports/morning-report.md and persisted in the database. "
                "Use this as the final step of the Night Agent run."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "Full markdown content of the report"
                    },
                    "report_type": {
                        "type": "string",
                        "description": "Type of report (default: morning_report)",
                        "default": "morning_report"
                    }
                },
                "required": ["content"]
            }
        ),
    ]


# ── Tool implementations ───────────────────────────────────────────────────

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """
    Route tool calls to the appropriate FastAPI endpoint.
    All errors are caught and returned as text so the agent can handle them.
    """
    try:
        if name == "list_transactions":
            params = {}
            if arguments.get("status"):
                params["status"] = arguments["status"]
            if arguments.get("since"):
                params["since"] = arguments["since"]
            if arguments.get("limit"):
                params["limit"] = arguments["limit"]

            result = await api_get("/transactions", params=params)
            return [types.TextContent(
                type="text",
                text=str(result)
            )]

        elif name == "get_transaction":
            transaction_id = arguments.get("transaction_id", "").strip()
            if not transaction_id:
                raise ValueError("transaction_id is required and cannot be empty")

            result = await api_get(f"/transactions/{transaction_id}")
            return [types.TextContent(
                type="text",
                text=str(result)
            )]

        elif name == "set_transaction_status":
            transaction_id = arguments.get("transaction_id", "").strip()
            status = arguments.get("status", "").strip()
            reasoning = arguments.get("reasoning", "").strip()
            agent = arguments.get("agent", "unknown").strip()

            if not transaction_id:
                raise ValueError("transaction_id is required")
            if not status:
                raise ValueError("status is required")
            if not reasoning:
                raise ValueError("reasoning note is required — cannot classify without explanation")

            result = await api_patch(
                f"/transactions/{transaction_id}/status",
                {
                    "status": status,
                    "reasoning": reasoning,
                    "agent": agent
                }
            )
            return [types.TextContent(
                type="text",
                text=str(result)
            )]

        elif name == "get_risk_metrics":
            params = {}
            if arguments.get("since"):
                params["since"] = arguments["since"]
            if arguments.get("top_n"):
                params["top_n"] = arguments["top_n"]

            result = await api_get("/metrics", params=params)
            return [types.TextContent(
                type="text",
                text=str(result)
            )]

        elif name == "write_report":
            content = arguments.get("content", "").strip()
            if not content:
                raise ValueError("Report content cannot be empty")

            result = await api_post(
                "/reports",
                {
                    "content": content,
                    "report_type": arguments.get("report_type", "morning_report")
                }
            )
            return [types.TextContent(
                type="text",
                text=str(result)
            )]

        else:
            raise ValueError(f"Unknown tool: {name}")

    except httpx.HTTPStatusError as e:
        # FastAPI returned an error response
        error_msg = f"API error calling {name}: {e.response.status_code} — {e.response.text}"
        return [types.TextContent(type="text", text=f"ERROR: {error_msg}")]

    except httpx.RequestError as e:
        # Network error — FastAPI might be down
        error_msg = f"Network error calling {name}: {str(e)}"
        return [types.TextContent(type="text", text=f"ERROR: {error_msg}")]

    except Exception as e:
        # Any other error
        error_msg = f"Tool {name} failed: {type(e).__name__}: {str(e)}"
        return [types.TextContent(type="text", text=f"ERROR: {error_msg}")]


# ── Entry point ────────────────────────────────────────────────────────────

async def main():
    """Run the MCP server on stdio."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())