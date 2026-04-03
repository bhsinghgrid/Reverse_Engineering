# Q10: Why Does the System Enable Both Procedural and Episodic Memory Simultaneously?

---

## 📋 Summary

**Question**: Agent-S loads both a static action API prompt (procedural) and a dynamically retrieved past trajectory (episodic) at Turn 0. Why not just use one?

**One-Line Answer**: Procedural memory defines *how to operate the system correctly* (grammar, constraints, tool API). Episodic memory provides *what worked before in a similar situation* (adaptive strategy). Neither can substitute for the other.

**Key Insight**: This architecture directly mirrors ACT-R cognitive theory (Anderson, 1983) — procedural memory = production rules (how to act), episodic memory = autobiographical experience (what worked when). Expert humans use both simultaneously; so does Agent-S.

---

## 🔬 Reverse Engineering Technique Used

| Technique | Description | Applied Here |
|---|---|---|
| **Class Hierarchy Inspection** | Trace `construct_simple_worker_procedural_memory()` to understand what it builds | Found Python `inspect.signature()` call — proves procedural memory is dynamically built from the live ACI class, not hardcoded |
| **Import Analysis** | Follow `knowledge.py` imports and function calls | Confirmed `retrieve_episodic_experience()` uses embedding cosine similarity (dense retrieval) against a flat JSON store |
| **Temporal Load Analysis** | Identify when each memory type is loaded relative to task execution | Procedural: every session start. Episodic: Turn 0 only. Live observation: Turn 1+. Three distinct phases. |

**Evidence Chain**: `Worker.__init__()` → `PROCEDURAL_MEMORY.construct_simple_worker_procedural_memory(type(self.grounding_agent))` (always) + `knowledge_base.retrieve_episodic_experience(...)` (Turn 0 only).

---

## 🔹 Phase 2: Mechanism Extraction


Agent-S uses two orthogonal, non-competing knowledge systems:

| Memory Type | What it Stores | When Loaded | How Updated |
|---|---|---|---|
| **Procedural** | Action grammar, completion rules, tool API | Every session — hardcoded | Never (static) |
| **Episodic** | Past successful task trajectories | Turn 0 only — RAG retrieval | After each successful task |

Procedural memory provides stable behavioral rails (the rules of engagement). Episodic memory provides adaptive strategy hints (what has worked before). Neither can replace the other.

---

## 🔹 Phase 3: Component Analysis

**Procedural Memory** (`procedural_memory.py:14–123`):
```python
@staticmethod
def construct_simple_worker_procedural_memory(agent_class, skipped_actions):
    procedural_memory = "You are an expert in graphical user interfaces...\n"
    # Dynamically introspect the ACI class for valid actions
    for attr_name in dir(agent_class):
        attr = getattr(agent_class, attr_name)
        if callable(attr) and hasattr(attr, "is_agent_action"):
            signature = inspect.signature(attr)
            procedural_memory += f"\n    def {attr_name}{signature}:\n"
            procedural_memory += f"    '''{attr.__doc__}'''\n"
    return procedural_memory.strip()
```
- Uses Python `inspect` module to extract real function signatures from the deployed `OSWorldACI` class
- Result: The model only knows about actions that physically exist at runtime — no hallucinated API calls

**Episodic Memory** (`knowledge.py:262–282`):
```python
def save_episodic_memory(self, subtask_key: str, subtask_traj: str) -> None:
    """Save episodic memory (subtask level knowledge)."""
    kb = load_knowledge_base(self.episodic_memory_path)
    kb[subtask_key] = subtask_traj
    os.makedirs(os.path.dirname(self.episodic_memory_path), exist_ok=True)
    with open(self.episodic_memory_path, "w") as fout:
        json.dump(kb, fout)
```
- A flat JSON dictionary maps task descriptions → successful trajectory strings
- Retrieval uses embedding cosine similarity (dense vector search)

---

## 🔹 Phase 4: Code Evidence

**Turn 0 integration of both memory types** (`worker.py:65–146`):
```python
# STEP 1: Load Procedural Memory (always)
sys_prompt = PROCEDURAL_MEMORY.construct_simple_worker_procedural_memory(
    type(self.grounding_agent), skipped_actions=skipped_actions
).replace("CURRENT_OS", self.platform)
self.generator_agent = self._create_agent(sys_prompt)

# STEP 2: Load Episodic Memory (Turn 0 only)
if self.turn_count == 0 and self.use_subtask_experience:
    retrieved_similar_subtask, retrieved_subtask_experience = (
        self.knowledge_base.retrieve_episodic_experience(subtask_query_key)
    )
    instruction += "\nYou may refer to some similar subtask experience: {}".format(
        retrieved_similar_subtask + "\n" + retrieved_subtask_experience
    )
```

**Line-by-Line**:
| Line | Behavior |
|---|---|
| `construct_simple_worker_procedural_memory(...)` | Injects static action API into system prompt |
| `.replace("CURRENT_OS", self.platform)` | Tailors procedural rules for macOS vs Linux vs Windows |
| `retrieve_episodic_experience(...)` | Dynamic RAG retrieval from past successful trajectories |
| `instruction += "...{experience}"` | Appends retrieved experience as a hint to the task instruction |

---

## 🔹 Phase 5: Architecture Diagram

```
Agent Session Starts:
         │
         ├──► Procedural Memory (static)
         │         "Rules, API, Action Grammar"
         │         Loaded once into system_prompt
         │         Valid for entire session
         │
         └──► Episodic Memory (dynamic)
                   "Past successful trajectories"
                   Retrieved once at Turn 0 via embedding search
                   Valid as a hint for this task

Turn 1+:
         │
         ▼
  Live screen observation only
  (Procedural memory stays active in system prompt)
  (Episodic memory fades — no re-injection)
```

---

## 🔹 Phase 6: Comparative Reasoning

| Memory Architecture | Stability | Adaptability | Hallucination Risk |
|---|---|---|---|
| Procedural only | Very High | Very Low | High (no learned patterns) |
| Episodic only | Very Low | High | Very High (grammar undefined) |
| Both (Agent-S) | High | High | Low (grammar fixed, strategy adaptive) |
| Fine-tuned LLM | High | Very High | Low (baked in) | Very High cost |

---

## ✅ Phase 7: Proof of Correctness

- **Procedural Evidence**: `inspect.signature(attr)` generates the action API from the live `OSWorldACI` class — the model cannot call a function that doesn't exist
- **Episodic Evidence**: `save_episodic_memory()` + `retrieve_episodic_experience()` form a write-read lifecycle that accumulates task knowledge across evaluations
- **Execution Pattern**: On first run (empty episodic store), the system gracefully returns `("", "")` and proceeds with procedural memory alone
- **Theoretical Justification**: Directly maps to **ACT-R Cognitive Architecture** (Anderson, 1983):
  - Procedural memory = production rules (IF condition THEN action)
  - Episodic memory = autobiographical experience (what worked in specific past situations)
  - Combined, they enable "expert-level adaptive behavior" — the same dual system used in human skill acquisition

---
