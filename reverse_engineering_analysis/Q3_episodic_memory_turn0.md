# Q3: Why Is Episodic Memory Retrieval Limited to Turn 0?

---

## 📋 Summary

**Question**: Agent-S stores successful past trajectories as episodic memory. Why is retrieval only performed at Turn 0 and never again during a task?

**One-Line Answer**: After Turn 0, the live GUI state diverges from any past episode — old coordinates, element IDs, and screen layouts are invalid by Turn 1, making re-retrieval actively harmful.

**Key Insight**: Episodic memory acts as an "initialization prior" — it biases intent at the start, then yields to live observation. Just as a human recalls "how I did this last time" before starting, then adapts based on what they actually see.

---

## 🔬 Reverse Engineering Technique Used

| Technique | Description | Applied Here |
|---|---|---|
| **Control Flow Analysis** | Trace all conditional branches in a function | Found `if self.turn_count == 0:` as the sole gate for episodic retrieval in `generate_next_action()` |
| **Assertion Tracing** | Identify what the code validates before acting | Found `re.sub(r"\(\d+", "(element_description", ...)` — proves retrieved IDs are pre-sanitized as invalid |
| **Temporal Invariant Detection** | Identify which system properties are time-dependent | Confirmed: GUI element IDs are session-specific and reset between tasks |

**Evidence Chain**: `Worker.generate_next_action()` → `if self.turn_count == 0:` → `knowledge_base.retrieve_episodic_experience()` → `re.sub()` ID sanitization → injected into `instruction`.

---

## 🔹 Phase 2: Mechanism Extraction


Episodic memory stores successful past task/subtask trajectories as a flat JSON file indexed by task description. When a new task begins, the system retrieves the most semantically similar past trajectory via **embedding cosine similarity**.

However, this retrieval is **strictly gated to `turn_count == 0`**. After the first turn, the agent relies exclusively on live screen observations. This is because GUI state changes every turn — coordinates, menus, and layouts shift — making old trajectories progressively misleading.

---

## 🔹 Phase 3: Component Analysis

**File**: `gui_agents/s2/agents/worker.py` — `generate_next_action` (L115–146)
```python
if self.turn_count == 0:
    if self.use_subtask_experience:
        subtask_query_key = (
            "Task:\n" + search_query + "\n\nSubtask: " + subtask
            + "\nSubtask Instruction: " + subtask_info
        )
        retrieved_similar_subtask, retrieved_subtask_experience = (
            self.knowledge_base.retrieve_episodic_experience(subtask_query_key)
        )
        # Strip numeric element IDs — they are invalid in the current session
        retrieved_subtask_experience = re.sub(
            r"\(\d+", "(element_description", retrieved_subtask_experience
        )
```

**File**: `gui_agents/s2/core/knowledge.py` — `retrieve_episodic_experience` (L198–210)
```python
def retrieve_episodic_experience(self, instruction: str) -> Tuple[str, str]:
    knowledge_base = load_knowledge_base(self.episodic_memory_path)
    if not knowledge_base:
        return "", ""
    most_similar_key, most_similar_experience = \
        get_most_similar(instruction, knowledge_base, self.embedding_engine)
    return most_similar_key, most_similar_experience
```

---

## 🔹 Phase 4: Code Evidence

**File**: `gui_agents/s2/core/knowledge.py` — `save_episodic_memory` (L262–282)
```python
def save_episodic_memory(self, subtask_key: str, subtask_traj: str) -> None:
    """Save episodic memory (subtask level knowledge)."""
    if not subtask_traj:
        return
    try:
        kb = load_knowledge_base(self.episodic_memory_path)
        kb[subtask_key] = subtask_traj
        os.makedirs(os.path.dirname(self.episodic_memory_path), exist_ok=True)
        with open(self.episodic_memory_path, "w") as fout:
            json.dump(kb, fout)
    except Exception:
        pass
```

**Line-by-Line**:
| Line | Behavior |
|---|---|
| `kb = load_knowledge_base(...)` | Reads existing JSON dictionary |
| `kb[subtask_key] = subtask_traj` | Overwrites or inserts the trajectory for this key |
| `json.dump(kb, fout)` | Writes the updated knowledge base back to disk |

---

## 🔹 Phase 5: Architecture Diagram

```
Task Starts (turn_count = 0)
         │
         ▼
  EmbeddingEngine.embed(subtask_query_key)
         │
         ▼
  cosine_similarity(query, all_stored_keys)
         │
         ▼
  Most Similar Past Trajectory → Injected into system prompt

Turn 1+:
         │
         ▼
  NO RETRIEVAL — live screenshot + ACI tree only

After Task:
         │
         ▼
  save_episodic_memory(subtask_key, trajectory) → episodic_memory.json
```

---

## 🔹 Phase 6: Comparative Reasoning

| Strategy | Initial Boost | Staleness Risk | Implementation Cost |
|---|---|---|---|
| Turn 0 only (Agent-S) | High | Low — overridden quickly | Low |
| Every turn | High | Very High — stale coords | Medium |
| Never | None | None | Zero |

---

## ✅ Phase 7: Proof of Correctness

- **Code Evidence**: `if self.turn_count == 0` gate is the first condition in `generate_next_action`
- **ID Sanitization**: `re.sub(r"\(\d+", "(element_description", ...)` proves the system knows past element IDs are invalid in the current session
- **Theoretical Justification**: "Context-Sensitive Priming" — retrieved memory primes intent but must not constrain dynamic visual grounding after the first observation


---
