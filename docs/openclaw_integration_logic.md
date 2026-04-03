# Integration: Agent-S as an OpenClaw Skill

The `integrations/openclaw` folder contains the "glue code" required to run Agent-S as a specialized skill within the **OpenClaw** autonomous agent framework.

## 1. How it Works (The Bridge)

The integration relies on a **Wrapper Pattern**. Instead of OpenClaw needing to understand the internal Python classes of Agent-S, it interacts with a simplified CLI interface.

### The Execution Flow:
1.  **Invocation**: OpenClaw decides it needs to perform a GUI task and calls the `agent_s_task` bash script with a task description.
2.  **Translation**: The bash script triggers `agent_s_wrapper.py`.
3.  **Command Building**: The wrapper reads your environment variables (like `ANTHROPIC_API_KEY`) and constructs a complete CLI command for the `agent_s` engine.
4.  **Process Management**: The wrapper starts Agent-S as a subprocess.
5.  **Real-time Streaming**: Crucially, it sets `capture_output=False`. This allows the agent's thoughts and action logs to stream directly to the terminal, allowing you to watch the GUI automation live.

---

## 2. Key Components

### A. `agent_s_wrapper.py`
This is the "Brain" of the integration. It:
- **Auto-detects**: Finds where the `agent_s` library is installed.
- **Configures**: Sets the default reasoning model (e.g., Claude 3.7/4.5) and the grounding model (UI-TARS 7B).
- **Timeouts**: Implements a 10-minute "safety" timeout so the agent doesn't run indefinitely if it gets stuck.

### B. `SKILL.md`
This is the **OpenClaw Manifest**. It tells the OpenClaw framework:
- **What** the skill is capable of (GUI control, form filling, etc.).
- **How** to call it (parameters like `max_steps`).
- **Examples**: Provides few-shot examples that OpenClaw uses to understand when to invoke Agent-S.

---

## 3. Why use this Integration?

By using Agent-S as an OpenClaw skill, you combine two strengths:
1.  **OpenClaw**: Great at high-level reasoning, web searching, and managing project-wide files.
2.  **Agent-S**: Great at the "last mile" of GUI interaction (clicking buttons, moving sliders, interacting with legacy desktop apps).

This allows you to have a "Headless" agent (OpenClaw) that can "take control of the mouse" (Agent-S) whenever it encounters a task that doesn't have an API or a CLI.

---

## 4. Configuration Requirements
To use this integration, you must have these variables set in your environment:
- `ANTHROPIC_API_KEY`: For the reasoning planner.
- `AGENT_S_GROUND_URL`: The endpoint for your UI-TARS grounding model.
- `AGENT_S_PATH`: (Optional) The path to your virtualenv's `agent_s` binary.
