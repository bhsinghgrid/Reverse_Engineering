# Q4: Why Does Full Conversation Context Eventually Fail?

---

## 📋 Summary

**Question**: Modern LLMs have 100k–200k token context windows. Why does Agent-S still aggressively prune screenshots from older turns instead of keeping everything?

**One-Line Answer**: The problem is not token capacity — it's semantic staleness. A screenshot from Turn 3 shows a UI state that no longer exists by Turn 10, causing the model to hallucinate actions on vanished elements.

**Key Insight**: Agent-S implements a "Sliding Window" strategy — keep full text history (cheap, always valid) but prune old images (expensive, temporally invalid). This mirrors how humans remember *what they did* but not *exactly what the screen looked like*.

---

## 🔬 Reverse Engineering Technique Used

| Technique | Description | Applied Here |
|---|---|---|
| **Static Code Inspection** | Read `flush_messages()` to understand the pruning algorithm | Found targeted deletion: only `"image"` content deleted, text always preserved |
| **Runtime Log Analysis** | Read `mock_llm.py` logs to trace message history growth across turns | Confirmed messages accumulate while images are removed after `max_trajectory_length` |
| **Two-Tier Strategy Identification** | Identify different code paths for different model types | Long-context models (OpenAI/Anthropic): image-only pruning. Short-context (vLLM): full message-pair deletion |

**Evidence Chain**: `Worker.generate_next_action()` → `self.flush_messages()` → `for i in range(len(messages)-1, -1, -1)` → `del agent.messages[i]["content"][j]` (image only).

---

## 🔹 Phase 2: Mechanism Extraction


Modern LMMs (Claude, GPT-4o) have 100k–200k token windows. But Agent-S aggressively prunes old screenshots. The reason isn't token capacity — it's **semantic staleness**.

Every turn produces a new screenshot. An old screenshot from Turn 3 shows a menu in a specific state. By Turn 10, that menu may be closed, different data may be shown, or the app may have navigated to another page. Keeping old screenshots causes the model to hallucinate actions on **no-longer-existing UI elements**.

---

## 🔹 Phase 3: Component Analysis

**File**: `https://github.com/simular-ai/Agent-S/blob/main/gui_agents/s3/agents/worker.py` — `flush_messages` (L90–123)
```python
def flush_messages(self):
    engine_type = self.engine_params.get("engine_type", "")
    # Long-context strategy: keep all text, delete old images
    if engine_type in ["anthropic", "openai", "gemini"]:
        max_images = self.max_trajectory_length
        for agent in [self.generator_agent, self.reflection_agent]:
            img_count = 0
            for i in range(len(agent.messages) - 1, -1, -1):
                for j in range(len(agent.messages[i]["content"])):
                    if "image" in agent.messages[i]["content"][j].get("type", ""):
                        img_count += 1
                        if img_count > max_images:
                            del agent.messages[i]["content"][j]
    # Short-context strategy: drop entire old turn pairs
    else:
        if len(self.generator_agent.messages) > 2 * self.max_trajectory_length + 1:
            self.generator_agent.messages.pop(1)
            self.generator_agent.messages.pop(1)
```

---

## 🔹 Phase 4: Code Evidence

**Two-tier pruning strategy explained**:

| Model Type | Pruning Strategy | Rationale |
|---|---|---|
| OpenAI / Anthropic / Gemini | Delete old images only | Text history is cheap and useful; images are semantically stale |
| Small models (vLLM, HuggingFace) | Drop full turn pairs | Cannot afford long history; must delete both text and images |

**File**: `https://github.com/simular-ai/Agent-S/blob/main/gui_agents/s1/utils/common_utils.py` — ID invalidation comment
```python
def parse_action_from_fixed_code(action_string, linearized_accessibility_tree):
    # element_id is an integer index into the AX tree
    element = linearized_accessibility_tree[element_id]
```
This code shows that in S1, element IDs were positional indices in the AX tree — these IDs would become **completely meaningless** after each UI state change, further proving that old context is unreliable.

---

## 🔹 Phase 5: Architecture Diagram

```
Message History After 10 Turns:
  Turn 1:  [Text Action] + [Image 1 — DELETED]
  Turn 2:  [Text Action] + [Image 2 — DELETED]
  Turn 3:  [Text Action] + [Image 3 — DELETED]
  Turn 7:  [Text Action] + [Image 7 — KEPT]
  Turn 8:  [Text Action] + [Image 8 — KEPT]
  Turn 9:  [Text Action] + [Image 9 — KEPT]
  Turn 10: [Text Action] + [Image 10 — KEPT (most recent)]

Model sees:
  ✅ Full text history (all 10 turns)
  ✅ Only most recent 4 screenshots (max_trajectory_length=4 in example)
```

---

## 🔹 Phase 6: Comparative Reasoning

| Context Management | Token Use | Visual Accuracy | Risk |
|---|---|---|---|
| Keep everything | Very high | Degrades (stale images) | High — model confusion |
| Drop everything (reset) | Low | Resets on each turn | High — loses task history |
| Keep text, prune images (Agent-S) | Moderate | High (recent only) | Low — best balance |

---

## ✅ Phase 7: Proof of Correctness

- **Code Evidence**: `del agent.messages[i]["content"][j]` is targeted specifically at `"image"` type content — text is never deleted in long-context mode
- **Execution Evidence**: After 8+ turns with `max_trajectory_length=8`, only the last 8 screenshots remain visible to the model
- **Theoretical Justification**: "Sliding Window Attention" — the principle that recent events are more predictive of current state than distant history, used in temporal sequence models

---
