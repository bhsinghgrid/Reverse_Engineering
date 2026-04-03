# Agent-S Prompt Analysis & Optimization Report

This report analyzes the core prompts used in the Agent-S framework and suggests improvements for better performance, especially when using local models like Ollama.

## 1. Core Prompt Analysis

### A. Worker Prompt (`construct_simple_worker_procedural_memory`)
**Strengths**:
- **Role Definition**: Clear persona as an expert in GUI and Python.
- **Agent Selection**: Distinct rules for when to use the GUI Agent vs. the Code Agent.
- **Strict Formatting**: Enforces `<thoughts>` and `<answer>` tags which helps with parsing stability.

**Opportunities**:
- **Few-Shot Examples**: Adding a single "Gold Standard" example of a multi-step trajectory would help smaller models (Ollama) follow the reasoning format more strictly.
- **Mac-Specific Nuance**: While it mentions not using `cmd+tab`, it could explicitly suggest using `cmd+space` (Spotlight) as the primary way to switch apps on macOS to avoid focus issues.

### B. Code Agent Prompt (`CODE_AGENT_PROMPT`)
**Strengths**:
- **Incrementalism**: Excellent emphasis on small, standalone steps.
- **Self-Verification**: Explicitly instructs the agent to verify changes after each step.
- **Library Recommendations**: Suggests using `openpyxl` or `python-docx` for in-place edits.

**Opportunities**:
- **Error Recovery**: Could include a section on how to handle common bash/python errors (e.g., "If a package is missing, install it using `pip` in the same step").
- **Output Verbosity**: For local models, the prompt could request more print statements within the code to provide better "visibility" for the `Worker` agent.

### C. Grounding Prompt (`generate_coords`)
**Strengths**:
- **Conciseness**: Very simple "Query: {expr}" format.

**Opportunities**:
- **Format Enforcement**: Since this model is often a standalone VLM (like UI-TARS), adding a requirement for a specific coordinate format (e.g., `[x, y]`) in the prompt itself can prevent prose-style responses that break the regex parser.

---

## 2. Proposed Optimizations

### Optimization 1: Few-Shot Injector
**Insight**: Models under 70B parameters significantly benefit from seeing the desired format in action.
**Change**: Modify `procedural_memory.py` to include a `FEW_SHOT_EXAMPLE` block in the system prompt.

### Optimization 2: Vision-Model Specificity
**Insight**: Models like `Llama 3.2 Vision` are good at describing scenes but struggle with precise pixel coordinates unless told how to look for them.
**Change**: Update the `BEHAVIOR_NARRATOR_SYSTEM_PROMPT` to ask the model to look for "high-contrast edges" when identifying UI element bounds.

### Optimization 3: macOS Focus Strategy
**Insight**: On macOS, clicking can sometimes fail to focus a window.
**Change**: Update the `Worker` prompt to recommend a "Click-to-Focus" strategy (first click a neutral area like the title bar, then click the target element).

---

## 3. Recommended Prompt Refactor (Example)

Instead of:
> "Translate the next action into code using the provided API methods."

Try:
> "Translate the next action into a **single, valid Python function call** using the API methods above. 
> **NEVER** use `import` statements or multi-line code here. 
> **EXAMPLE**: `agent.click(\"The search bar\", 1)`"

---

## 4. Next Steps
- [ ] Implement a `few_shot_enabled` flag in the `Worker` initialization.
- [ ] Create a library of "Common GUI Pitfalls" to inject into the `Worker` prompt based on the detected OS.
- [ ] Update the `CodeAgent` to always verify file existence before modification.
