# Q7: How Does the System Maintain `future_tasks` and `done_task` Context?

---

## 📋 Summary

**Question**: The Worker only handles one subtask at a time, but it needs to know what has already been done and what comes next. How does Agent-S pass this global coordination state to an isolated Worker?

**One-Line Answer**: The Manager injects `DONE_TASKS` and `FUTURE_TASKS` as plain string template substitutions into the Worker's system prompt at Turn 0 — no shared memory, no APIs, just text.

**Key Insight**: This is the Blackboard Architecture pattern — a coordinator writes shared state (Manager → task lists), isolated workers read it (Worker → system prompt). The coupling is minimal: only strings cross the boundary.

---

## 🔬 Reverse Engineering Technique Used

| Technique | Description | Applied Here |
|---|---|---|
| **Data Flow Tracing** | Follow global state from where it is written to where it is consumed | Traced `agent_s2.subtasks` → `.replace("FUTURE_TASKS", ...)` → Worker system prompt |
| **Template Analysis** | Search for placeholder strings in prompt templates | Found `FUTURE_TASKS`, `DONE_TASKS`, `SUBTASK_DESCRIPTION` in `PROCEDURAL_MEMORY` base prompt |
| **Coordination Pattern Recognition** | Identify how components share state without tight coupling | Identified Blackboard pattern — Manager writes, Worker reads, no direct object references shared |

**Evidence Chain**: `AgentS2.run()` → `worker.generate_next_action(future_tasks=..., done_task=...)` → `system_prompt.replace("FUTURE_TASKS", ...)` → Worker knows global task state.

---

## 🔹 Phase 2: Mechanism Extraction


The top-level `AgentS2` maintains a live DAG queue. As subtasks are completed or failed, it updates two lists:

- `self.completed_tasks` — finished subtasks (DONE)
- `self.subtasks` — remaining pending subtasks

These lists are passed **by reference** to every `Worker.generate_next_action()` call. The Worker injects them into its system prompt via template replacement, giving the Worker **global task awareness** without owning the DAG logic itself.

---

## 🔹 Phase 3: Component Analysis

**File**: `gui_agents/s2/agents/worker.py` — `generate_next_action` (L148–155)
```python
# Inject global DAG state into the Worker's system prompt at Turn 0
if self.turn_count == 0:
    self.generator_agent.add_system_prompt(
        self.generator_agent.system_prompt
            .replace("SUBTASK_DESCRIPTION", subtask)
            .replace("TASK_DESCRIPTION", instruction)
            .replace("FUTURE_TASKS", ", ".join([f.name for f in future_tasks]))
            .replace("DONE_TASKS", ",".join(d.name for d in done_task))
    )
```

**File**: `gui_agents/s2/agents/worker.py` — subtask constraints (L199–201)
```python
if self.turn_count == 0:
    generator_message += f"Remember only complete the subtask: {subtask}\n"
    generator_message += f"You can use this extra information: {subtask_info}.\n"
```

---

## 🔹 Phase 4: Code Evidence

**File**: `gui_agents/s2/agents/agent_s.py` — DAG queue management (conceptual)
```python
# AgentS2 maintains the task queue
self.subtasks = action_queue           # Pending tasks
self.completed_tasks = []              # Finished tasks

# For each turn:
current_subtask = self.subtasks[0]

# After Worker returns DONE:
self.completed_tasks.append(current_subtask)
self.subtasks.pop(0)

# After Worker returns FAIL:
# Trigger re-planning
self.subtasks = manager.get_action_queue(
    failed_subtask=current_subtask,
    completed_subtasks_list=self.completed_tasks,
    remaining_subtasks_list=self.subtasks[1:])
```

**Line-by-Line**:
| Line | Behavior |
|---|---|
| `FUTURE_TASKS` | Tells the Worker what NOT to do yet ("Book ticket" should wait until flight is selected) |
| `DONE_TASKS` | Tells the Worker what NOT to repeat ("Browser is already open, skip that step") |
| `SUBTASK_DESCRIPTION` | Constrains the Worker to only its assigned unit of work |

---

## 🔹 Phase 5: Architecture Diagram

```
Manager generates: [Open Browser, Search, Filter, Select, Book]

Turn 1: Worker executing "Open Browser"
  System Prompt:
    DONE_TASKS     = ""
    SUBTASK        = "Open Browser"
    FUTURE_TASKS   = "Search, Filter, Select, Book"

Worker returns: DONE
Manager updates: completed=["Open Browser"], remaining=["Search", "Filter", "Select", "Book"]

Turn 2: Worker executing "Search Flights"
  System Prompt:
    DONE_TASKS     = "Open Browser"
    SUBTASK        = "Search Flights"
    FUTURE_TASKS   = "Filter, Select, Book"

    Worker knows: browser is open, don't re-open it
    Worker knows: don't book yet — that's a future task
```

---

## 🔹 Phase 6: Comparative Reasoning

| Coordination Method | Global Awareness | Complexity |
|---|---|---|
| None (Monolithic) | None — agent must infer from context | Low |
| DONE/FUTURE lists (Agent-S) | High — each turn is globally aware | Low — just string replacement |
| Shared memory / blackboard | Very High | High — requires synchronization |

---

## ✅ Phase 7: Proof of Correctness

- **Code Evidence**: `FUTURE_TASKS` and `DONE_TASKS` are template placeholders in `PROCEDURAL_MEMORY` — no custom logic is needed by the Worker itself
- **Execution Pattern**: The Worker's `turn_count == 0` gate ensures global state is injected exactly once per subtask, preventing repeated overwrites
- **Theoretical Justification**: "Blackboard Architecture" — a classical AI coordination pattern where shared state is written by a coordinator (Manager) and read by isolated workers (Worker), without tight coupling
