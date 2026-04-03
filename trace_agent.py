# ~/agent_s_analysis/Agent-S/trace_agent.py

import functools
import time
import json
from rich import print as rprint
from rich.panel import Panel
from rich.syntax import Syntax


# ── Decorator to trace any function ──────────────────────────────────────────
def trace(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        func_name = f"{func.__module__}.{func.__qualname__}"

        rprint(Panel(
            f"[bold green]ENTER[/] {func_name}\n"
            f"args: {str(args[1:])[:200]}\n"  # skip 'self'
            f"kwargs: {str(kwargs)[:200]}",
            border_style="green"
        ))

        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start

        rprint(Panel(
            f"[bold blue]EXIT[/] {func_name} ({elapsed:.3f}s)\n"
            f"returned: {str(result)[:300]}",
            border_style="blue"
        ))
        return result

    return wrapper


# ── Patch key methods at runtime ─────────────────────────────────────────────
def install_traces():
    from gui_agents.s3.agents import agent_s

    # Patch the methods you want to trace
    agent_s.AgentS3.predict = trace(agent_s.AgentS3.predict)

    # Try to find and patch memory retrieval
    try:
        from gui_agents.s3.memory import episodic_memory
        # patch whatever retrieval method exists
    except ImportError:
        print("Memory module path differs - adjust import")

    print("✅ Traces installed")


if __name__ == "__main__":
    install_traces()
    # Now import and run agent normally