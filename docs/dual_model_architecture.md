# Dual-Model Architecture: Reasoning vs. Perceiving

Agent-S employs a sophisticated **Dual-Model Architecture** that separates high-level strategic reasoning from low-level visual grounding. This separation is critical for achieving human-level precision in graphical user interfaces.

## 1. The Strategic Rationale: Why Two Models?

### A. Specialization vs. Generality
*   **Reasoning Agent (The Brain)**: Focuses on understanding complex requests, maintaining long-term memory, and generating logical sequences of actions. It is usually a large model (e.g., Claude 3.7, GPT-4o, or a 70B+ Llama model).
*   **Grounding Agent (The Eyes)**: Focuses exclusively on pixel-level accuracy. It is often a smaller, specialized model (like UI-TARS or specialized VLM) trained specifically on screenshot-to-coordinate mapping.

### B. Contextual Focus (Noise Reduction)
If a single model handles both reasoning and grounding, it can become "blinded" by the noise of its own past thoughts and history. By isolating the grounding task, the Grounding Agent only sees the *current* screenshot and a single, isolated description (e.g., "Find the red login button"). This drastically reduces hallucinations and pixel-misses.

### C. Resource Efficiency
For local deployments (like Ollama), running a massive Reasoning model for every coordinate check is slow. A dual-model approach allows for:
- One **High-Intelligence** model for planning (infrequent calls).
- One **High-Speed Vision** model for coordinate grounding (frequent calls).

---

## 2. Implementation: The `OSWorldACI` Bridge

The logic is implemented via the **Agent-Computer Interface (ACI)** in `gui_agents/s3/agents/grounding.py`.

### The Core Loop
1.  **Request**: The **Worker** outputs a high-level command like `agent.click("The settings icon in the top right")`.
2.  **Intercept**: The `OSWorldACI`'s `click` method catches this command.
3.  **Grounding Call**: It calls `self.generate_coords()`, which isolates the description and sends it to the **Grounding VLM**.
4.  **Translation**: The VLM returns raw coordinates (e.g., `[960, 40]`), which the ACI then translates into standard PyAutoGUI code for the operating system.

```mermaid
graph LR
    A[Worker / Reasoning] -->| "agent.click('Search')" | B[OSWorldACI / Bridge]
    B -->| Screenshot + 'Search' | C[Grounding Model / Perception]
    C -->| [x, y] Coordinates | B
    B -->| "pyautogui.click(x, y)" | D[Operating System]
```

---

## 3. Benefits for Local Models (Ollama)
When running locally, this architecture allows you to use a model like `llama3.2-vision` primarily for grounding while using a more capable text-based model for planning, or even mixing a local grounding model with a cloud-based reasoning model for the best of both worlds.
