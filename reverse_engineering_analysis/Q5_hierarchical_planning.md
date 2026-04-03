# Q5: How Does the Hierarchical Planning System Decompose Complex Tasks?

---

## 📋 Summary

**Question**: The S2 Manager converts a user goal into a DAG of subtasks. What is this 3-stage process and why is topological sorting necessary?

**One-Line Answer**: The Manager runs: (1) generate text plan → (2) convert to dependency DAG → (3) topological sort into a linear execution queue — because subtasks often have dependencies (open browser before navigating).

**Key Insight**: This is Hierarchical Task Network (HTN) Planning — a classical AI technique from industrial robotics, applied to GUI automation. The DAG ensures dependency order is always respected, and failed subtasks can trigger partial re-planning without restarting from scratch.

---

## 🔬 Reverse Engineering Technique Used

| Technique | Description | Applied Here |
|---|---|---|
| **Algorithm Tracing** | Step through `_topological_sort()` with a sample DAG | Confirmed DFS-based topological sort — nodes with no dependencies execute first |
| **Class Hierarchy Inspection** | Trace `Manager.get_action_queue()` call chain | Found: `_generate_step_by_step_plan()` → `_generate_dag()` → `_topological_sort()` — 3 separate LLM calls |
| **Failure Recovery Analysis** | Find what triggers re-planning and what state it preserves | Found `get_action_queue(failed_subtask=...)` re-invokes Manager with `completed_subtasks_list` to avoid repeating done work |

**Evidence Chain**: `AgentS2.run()` → `manager.get_action_queue()` → `_generate_step_by_step_plan()` → `_generate_dag(plan)` → `_topological_sort(dag)` → `action_queue`.

---

## 🔹 Phase 2: Mechanism Extraction


In Agent-S S2, the `Manager` runs a **three-stage planning pipeline** before the Worker takes a single action:

1. **Step-by-Step Plan** — The Manager generates a human-readable outline of the full task
2. **DAG Translation** — A second LLM call converts the plan into a structured Directed Acyclic Graph (DAG) of nodes and edges
3. **Topological Sort** — The Manager sorts the DAG into a linear execution queue

The Worker then executes its assigned subtask **step-by-step**, returning `DONE` or `FAIL` to advance or replan the DAG.

---

## 🔹 Phase 3: Component Analysis

**File**: `https://github.com/simular-ai/Agent-S/blob/main/gui_agents/s2/agents/manager.py` — `get_action_queue` (L305–321)
```python
def get_action_queue(self, instruction, observation,
                     failed_subtask=None,
                     completed_subtasks_list=[], remaining_subtasks_list=[]):
    # Stage 1: Generate a text plan
    planner_info, plan = self._generate_step_by_step_plan(
        observation, instruction, failed_subtask,
        completed_subtasks_list, remaining_subtasks_list)
    # Stage 2: Convert text plan to a structured DAG
    dag_info, dag = self._generate_dag(instruction, plan)
    # Stage 3: Topological sort for ordered execution
    action_queue = self._topological_sort(dag)
    planner_info.update(dag_info)
    return planner_info, action_queue
```

**Topological Sort** (`manager.py:263–291`):
```python
def _topological_sort(self, dag: Dag) -> List[Node]:
    def dfs(node_name, visited, stack):
        visited[node_name] = True
        for neighbor in adj_list[node_name]:
            if not visited[neighbor]:
                dfs(neighbor, visited, stack)
        stack.append(node_name)
    adj_list = defaultdict(list)
    for u, v in dag.edges:
        adj_list[u.name].append(v.name)
    visited = {node.name: False for node in dag.nodes}
    stack = []
    for node in dag.nodes:
        if not visited[node.name]:
            dfs(node.name, visited, stack)
    return [next(n for n in dag.nodes if n.name == name) for name in stack[::-1]]
```

---

## 🔹 Phase 4: Code Evidence

**Failure Recovery** (`manager.py:172–184`):
```python
# Re-plan triggered by a failed subtask
if failed_subtask:
    generator_message = (
        f"The subtask {failed_subtask} cannot be completed. "
        "Please generate a new plan for the remainder of the trajectory.\n\n"
        f"Successfully Completed Subtasks:\n{format_subtask_list(completed_subtasks_list)}\n"
    )
```

**Line-by-Line**:
| Line | Behavior |
|---|---|
| `if failed_subtask` | Detects that a Worker returned FAIL |
| `"generate a new plan..."` | Instructs Manager to produce a new plan from the current state |
| `format_subtask_list(completed_subtasks_list)` | Provides "what's already done" so Manager doesn't re-plan completed work |

---

## 🔹 Phase 5: Architecture Diagram

```
User Goal: "Search for flights and book the cheapest"
              │
              ▼
Manager: Stage 1 — Step-by-Step Plan
  1. Open Chrome
  2. Navigate to Google Flights
  3. Search "NYC" from "LAX"
  4. Filter by lowest price
  5. Select cheapest flight
  6. Enter passenger info
  7. Confirm booking
              │
              ▼
Manager: Stage 2 — DAG
  [Open Chrome] → [Navigate] → [Search] → [Filter] → [Select] → [Enter Info] → [Confirm]
              │
              ▼
Manager: Stage 3 — Topological Queue
  [Open Chrome, Navigate, Search, Filter, Select, Enter Info, Confirm]
              │
              ▼
Worker: Executes "Open Chrome" → Returns DONE
              │
              ▼
Worker: Executes "Navigate to Google Flights" → Returns DONE
              │
              ... (continues)
```

---

## 🔹 Phase 6: Comparative Reasoning

| Architecture | Complex Task Performance | Re-planning | Inference Cost |
|---|---|---|---|
| Single LLM (S3) | Lower on >5-step tasks | Full restart | Low |
| Hierarchical DAG (S2) | High — steps are isolated | Partial re-plan from fail point | High |
| Three-level | Very high | Very flexible | Very high |

---
## 🧩 CLAIM: DAG-Based Task Decomposition
Agent-S employs a **three-stage hierarchy** to decompose high-level user instructions into a linear execution queue, using a **Directed Acyclic Graph (DAG)** to manage subtask dependencies.

### 🔬 EVIDENCE
1.  **Stage 1: Step-by-Step Generation**
    *   `Manager._generate_step_by_step_plan` ([Manager.py:L86](https://github.com/simular-ai/Agent-S/blob/main/gui_agents/s1/core/Manager.py#L86))
    *   Uses the `MANAGER_PROMPT` to produce a natural language outline of required steps.
2.  **Stage 2: Graph Translation**
    *   `Manager._generate_dag` ([Manager.py:L193](https://github.com/simular-ai/Agent-S/blob/main/gui_agents/s1/core/Manager.py#L193))
    *   Invokes a second LLM pass (`DAG_TRANSLATOR_PROMPT`) to convert the text plan into a structured `Dag` object.
3.  **Stage 3: Topological Ordering**
    *   `Manager._topological_sort` ([Manager.py:L228](https://github.com/simular-ai/Agent-S/blob/main/gui_agents/s1/core/Manager.py#L228))
    *   Implements a standard **Depth-First Search (DFS)** algorithm ([Line 233](https://github.com/simular-ai/Agent-S/blob/main/gui_agents/s1/core/Manager.py#L233)) to order nodes such that all dependencies are satisfied before execution.

### 🧠 INFERENCE
By separating strategy (plan generation) from structure (DAG translation), Agent-S ensures that complex multi-step workflows (e.g., "Install app then configure settings") are executed in the correct causal order. The use of a DAG rather than a linear list allows the system to model parallel subtasks that eventually converge on a bottleneck step.

---

## 🧪 Counterfactual Reasoning & Alternative Designs

### Why not use a simple Linear List?
While simpler to implement, a linear list lacks **dependency awareness**. If a subtask fails, a linear agent must either skip it blindly or restart the entire task.
*   **Agent-S Advantage**: The DAG structure allows the `Manager` to receive `failure_feedback` ([Manager.py:L151](https://github.com/simular-ai/Agent-S/blob/main/gui_agents/s1/core/Manager.py#L151)) and perform a **partial re-plan** while maintaining the state of independent, successful nodes.

### Why not hit the LLM with a single prompt?
Generating both the logic AND the grounding IDs in one pass often leads to "hallucinated" element IDs. Agent-S isolates the planning logic to the `Manager`, leaving the pixel-level execution to the `Worker`.

## ✅ Phase 7: Proof of Correctness

- **Code Evidence**: `_topological_sort` implements a standard DFS-based algorithm — nodes with no dependencies execute first
- **Failure Recovery**: `get_action_queue(failed_subtask=...)` is called by `AgentS2` whenever Worker returns `FAIL`, triggering a partial replan
- **Theoretical Justification**: "Hierarchical Task Network (HTN) Planning" — a classical AI planning paradigm used in industrial robotics and game AI for multi-step goal decomposition

---
## 📊 Confidence Level
**High** — The 3-stage pipeline and DFS-based topological sort are explicitly documented and implemented in `gui_agents/s1/core/Manager.py`.

