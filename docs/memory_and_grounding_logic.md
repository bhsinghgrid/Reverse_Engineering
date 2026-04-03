# Agent-S: Memory and Grounding Logic

This document details the implementation and rationale behind two core technical concepts in Agent-S: the **ACI Tree** and **Episodic Memory Retrieval**.

## 1. The ACI Tree (Agent-Computer Interface)
The ACI Tree is how the agent "perceives" the operating system.

### A. Evolutionary Shift: From Structure to Vision
In the current version (S3), Agent-S has shifted away from a rigid, OS-specific tree hierarchy.
*   **Older Versions (S1/S2)**: Used OS APIs (e.g., Apple's `AXUIElement`) to recursively traverse the system's accessibility tree. This was then "linearized" into a text table.
*   **Current Version (S3)**: Uses **Visual Grounding (UI-TARS)**. Instead of parsing a complex tree of thousands of nodes, the agent "looks" at the screen and maps natural language to pixels directly. This is much more robust for non-standard applications (like Spotify or Slack) that don't correctly report their internal "tree" to the OS.

### B. OCR-Enhanced Grounding
For text-heavy tasks, the ACI creates a **Flat OCR Table**:
1.  Captures a screenshot.
2.  Runs **Tesseract OCR** to identify every word and its bounding box.
3.  Assigns each word a unique **Word ID**.
4.  The agent can then say `agent.click("The login button")`, and the grounding layer finds the ID associated with that text and clicks its center.

---

## 2. Episodic Memory Retrieval (Turn-0 Logic)
One of the most debated design choices in Agent-S is why it only retrieves past experiences at **Turn 0**.

### A. The Challenge: Divergence
Episodic memory helps the agent by retrieving a successful "narrative experience" (a past run of a similar task).
*   **Why only Turn 0?** After the very first action is taken, the real-world environment starts to **diverge** from even the most similar past example. Window positions, browser tabs, and network lag mean the environment is never quite the same twice.

### B. Strategy Prior vs. Live Controller
The system treats episodic memory as a **Strategy Prior**, not a continuous controller.
- **At Turn 0**: The history tells the agent "Usually, we start by opening the browser and going to Google."
- **At Turn 1+**: If the agent kept following the old history, it might click where a button *used* to be instead of where it is *now*. By "disabling" retrieval after Turn 0, the agent is forced to rely on **live screenshot evidence**, which is a far more reliable source of truth during the middle of a task.

### C. Summary of Retrieval Benefits
| Phase | Source of Truth | Rationale |
|---|---|---|
| **Turn 0** | **Retrieved Experience** | Setting a broad strategy and high-level plan. |
| **Turns 1+** | **Live Vision + Reflection** | Reacting to immediate environmental feedback and avoiding stale guidance. |
