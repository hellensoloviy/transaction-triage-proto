"""
Shared Agent Loop — agents/loop.py
====================================
ReAct tool-use loop written directly against the Anthropic SDK.
NO LangChain, NO LlamaIndex, NO frameworks in this file.

Both Day Agent and Night Agent use this loop.
The loop handles:
- Sending messages to Claude
- Receiving tool call requests
- Executing tools via MCP server
- Sending tool results back
- Structured JSON logging of every step
- Retry with exponential backoff on API failures
- Prompt caching on system prompt (cached tokens don't count toward ITPM)
"""
import json
import asyncio
import os
import sys
import uuid
from datetime import datetime, timezone
from typing import Optional

import anthropic
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv

load_dotenv()

# ── Configuration ──────────────────────────────────────────────────────────

MODEL = os.getenv("MODEL_NAME", "claude-sonnet-4-6")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "4096"))
MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "80"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "5"))

# ── Logging ────────────────────────────────────────────────────────────────

os.makedirs("logs", exist_ok=True)
LOG_FILE = "logs/agent_run.jsonl"


def log_event(event: dict):
    """
    Write a structured JSON log entry.
    make verify reads this file to check for failure events.
    Each entry is one JSON object per line (JSONL format).
    """
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **event
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")


def log_tool_call(run_id: str, tool_name: str, arguments: dict):
    log_event({
        "event": "tool_call",
        "run_id": run_id,
        "tool": tool_name,
        "arguments": arguments,
    })


def log_tool_result(run_id: str, tool_name: str, result: str):
    log_event({
        "event": "tool_result",
        "run_id": run_id,
        "tool": tool_name,
        "result_preview": result[:200],
    })


def log_tool_failure(run_id: str, tool_name: str, error: str, transaction_id: str = None):
    """
    Log a tool call failure.
    make verify asserts at least one of these exists after Night Agent run.
    """
    log_event({
        "event": "tool_call_failure",
        "run_id": run_id,
        "tool": tool_name,
        "error": error,
        "transaction_id": transaction_id,
        "action": "skipping item, continuing",
    })


def log_skip(run_id: str, transaction_id: str, reason: str):
    """
    Log that an item was skipped.
    make verify asserts at least one of these exists after Night Agent run.
    """
    log_event({
        "event": "skip_item",
        "run_id": run_id,
        "transaction_id": transaction_id,
        "reason": reason,
        "action": "skipping item, continuing",
    })


def log_agent_start(run_id: str, agent_name: str):
    log_event({
        "event": "agent_start",
        "run_id": run_id,
        "agent": agent_name,
    })


def log_agent_complete(run_id: str, agent_name: str, summary: str):
    log_event({
        "event": "agent_complete",
        "run_id": run_id,
        "agent": agent_name,
        "summary": summary,
    })


def log_sub_agent_spawn(run_id: str, parent_agent: str, sub_agent_purpose: str):
    """
    Log when an agent spawns a sub-agent.
    Task requires this to be visible in logs.
    """
    log_event({
        "event": "sub_agent_spawn",
        "run_id": run_id,
        "parent_agent": parent_agent,
        "sub_agent_purpose": sub_agent_purpose,
    })


# ── MCP tool helpers ───────────────────────────────────────────────────────

def get_mcp_server_params() -> StdioServerParameters:
    """Return parameters to start the MCP server as a subprocess."""
    return StdioServerParameters(
        command=sys.executable,
        args=[os.path.join(os.path.dirname(os.path.dirname(__file__)), "mcp_server", "server.py")],
    )


async def get_mcp_tools(session: ClientSession) -> list:
    """
    Fetch tool definitions from MCP server and convert to
    Anthropic SDK tool format.
    """
    mcp_tools = await session.list_tools()
    anthropic_tools = []

    for tool in mcp_tools.tools:
        anthropic_tools.append({
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.inputSchema,
        })

    return anthropic_tools


async def execute_mcp_tool(
    session: ClientSession,
    tool_name: str,
    tool_input: dict,
    run_id: str,
) -> str:
    """
    Execute a tool via MCP and return the result as a string.
    Logs the call and result.
    """
    log_tool_call(run_id, tool_name, tool_input)

    try:
        result = await session.call_tool(tool_name, tool_input)
        result_text = result.content[0].text if result.content else ""
        log_tool_result(run_id, tool_name, result_text)
        return result_text

    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        log_tool_failure(run_id, tool_name, error_msg)
        raise


# ── Core ReAct loop ────────────────────────────────────────────────────────

async def run_agent_loop(
    session: ClientSession,
    system_prompt: str,
    initial_message: str,
    agent_name: str,
    run_id: Optional[str] = None,
    max_tokens_override: Optional[int] = None,
) -> str:
    """
    Core ReAct loop — reason, act, observe, repeat.

    Uses Anthropic SDK directly:
    1. Send messages to Claude with available tools
    2. Claude returns either a tool_use block or a text response
    3. If tool_use: execute via MCP, append result, continue
    4. If text: we're done, return the response
    5. Retry API calls with exponential backoff

    Returns the final text response from Claude.
    """
    if run_id is None:
        run_id = str(uuid.uuid4())[:8]

    # Clear log at start of each primary agent run
    # so verify.py reads only current run events.
    # Sub-agents must use a different name (e.g. "report-sub-agent")
    # to avoid wiping the log mid-run.
    if agent_name in ("day-agent", "night-agent"):
        open(LOG_FILE, "w").close()

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    tools = await get_mcp_tools(session)

    # per-agent max_tokens: Day Agent passes a lower ceiling
    # since its responses are short. Night Agent uses the global default.
    effective_max_tokens = max_tokens_override if max_tokens_override else MAX_TOKENS

    messages = [
        {"role": "user", "content": initial_message}
    ]

    log_event({
        "event": "loop_start",
        "run_id": run_id,
        "agent": agent_name,
        "model": MODEL,
    })

    # Prompt caching on system prompt.
    # The system prompt is sent on every iteration of the loop — by marking
    # it ephemeral, Anthropic caches it and cached tokens do NOT count toward
    # your ITPM rate limit. On a 200-transaction run with 80+ iterations this
    # is the single biggest lever for staying under Tier 1 limits.
    cached_system = [
        {
            "type": "text",
            "text": system_prompt,
            "cache_control": {"type": "ephemeral"},
        }
    ]

    for iteration in range(MAX_ITERATIONS):
        # ── Call Claude with retry and backoff ─────────────────────────────
        response = None
        last_error = None

        for attempt in range(MAX_RETRIES):
            try:
                response = client.messages.create(
                    model=MODEL,
                    max_tokens=effective_max_tokens,
                    system=cached_system,          # cached system prompt
                    tools=tools,
                    messages=messages,
                )
                break  # success

            except anthropic.RateLimitError as e:
                # read the actual retry-after from response headers
                retry_after = 60  # safe fallback
                if hasattr(e, "response") and e.response is not None:
                    retry_after = int(e.response.headers.get("retry-after", 60))

                log_event({
                    "event": "api_rate_limit",
                    "run_id": run_id,
                    "attempt": attempt + 1,
                    "wait_seconds": retry_after,
                })
                
                await asyncio.sleep(retry_after)
                last_error = e

            except anthropic.APIError as e:
                wait = 30 * (attempt + 1)
                log_event({
                    "event": "api_error",
                    "run_id": run_id,
                    "attempt": attempt + 1,
                    "error": str(e),
                    "wait_seconds": wait,
                })
                # await asyncio.sleep — not time.sleep
                await asyncio.sleep(wait)
                last_error = e

        if response is None:
            raise Exception(f"Claude API failed after {MAX_RETRIES} attempts: {last_error}")

        # ── Check stop reason ──────────────────────────────────────────────
        if response.stop_reason == "end_turn":
            # Claude is done — extract final text response
            final_text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    final_text += block.text

            log_event({
                "event": "loop_complete",
                "run_id": run_id,
                "agent": agent_name,
                "iterations": iteration + 1,
            })
            return final_text

        elif response.stop_reason == "tool_use":
            # Claude wants to call one or more tools
            # Add Claude's response to message history
            messages.append({
                "role": "assistant",
                "content": response.content
            })

            # Collect ALL tool_use blocks first before executing any.
            # The Anthropic API requires every tool_use block to have a matching
            # tool_result in the very next user message. If we iterate response.content
            # directly (which mixes text + tool_use blocks) and anything raises mid-loop,
            # we can end up sending fewer results than tool calls — causing the 400 error:
            # "tool_use ids were found without tool_result blocks immediately after".
            tool_use_blocks = [b for b in response.content if b.type == "tool_use"]
            tool_results = []

            for block in tool_use_blocks:
                tool_name = block.name
                tool_input = block.input

                log_event({
                    "event": "tool_dispatch",
                    "run_id": run_id,
                    "tool": tool_name,
                    "iteration": iteration,
                })

                try:
                    result_text = await execute_mcp_tool(
                        session, tool_name, tool_input, run_id
                    )
                    # await asyncio.sleep between tool calls
                    await asyncio.sleep(0.5)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result_text,
                    })

                except Exception as e:
                    # Tool failed — return error to Claude so it can decide.
                    # We MUST still append a result for this block_id or the
                    # API will reject the next request with a 400.
                    error_text = f"ERROR: Tool {tool_name} failed: {str(e)}"
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": error_text,
                        "is_error": True,
                    })

            # Sanity check — guarantee every tool_use_id has a result.
            # This is a safety net; the loop above should already cover all cases.
            result_ids = {r["tool_use_id"] for r in tool_results}
            for block in tool_use_blocks:
                if block.id not in result_ids:
                    log_event({
                        "event": "missing_tool_result_patched",
                        "run_id": run_id,
                        "tool_use_id": block.id,
                        "tool": block.name,
                    })
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": "ERROR: result missing — patched as fallback",
                        "is_error": True,
                    })

            # Add tool results to message history
            messages.append({
                "role": "user",
                "content": tool_results
            })

        elif response.stop_reason == "max_tokens":
            # Hit token limit mid-response.
            # CRITICAL: if Claude was mid-tool-call when it hit the limit,
            # response.content contains tool_use blocks. We MUST send matching
            # tool_result blocks in the next message or the API returns 400.
            # Sending a plain "continue" text message with dangling tool_use
            # blocks in history is what was causing the repeated 400 errors.
            log_event({
                "event": "max_tokens_hit",
                "run_id": run_id,
                "iteration": iteration,
            })

            tool_use_blocks = [b for b in response.content if b.type == "tool_use"]

            if tool_use_blocks:
                # Claude was mid-tool-call — execute the tools and respond properly
                messages.append({
                    "role": "assistant",
                    "content": response.content
                })
                tool_results = []
                for block in tool_use_blocks:
                    try:
                        result_text = await execute_mcp_tool(
                            session, block.name, block.input, run_id
                        )
                        await asyncio.sleep(0.5)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result_text,
                        })
                    except Exception as e:
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": f"ERROR: {str(e)}",
                            "is_error": True,
                        })
                messages.append({
                    "role": "user",
                    "content": tool_results
                })
            else:
                # Pure text truncation — safe to just ask Claude to continue
                messages.append({
                    "role": "assistant",
                    "content": response.content
                })
                messages.append({
                    "role": "user",
                    "content": [{"type": "text", "text": "Please continue where you left off."}]
                })

        else:
            log_event({
                "event": "unexpected_stop_reason",
                "run_id": run_id,
                "stop_reason": response.stop_reason,
            })
            break

    # Hit max iterations without finishing
    log_event({
        "event": "max_iterations_reached",
        "run_id": run_id,
        "agent": agent_name,
        "max": MAX_ITERATIONS,
    })
    return f"Agent reached maximum iterations ({MAX_ITERATIONS}) without completing."