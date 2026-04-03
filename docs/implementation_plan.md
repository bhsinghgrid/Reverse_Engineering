# Implementation Plan: Environment Execution Demo

To demonstrate Agent-S's real-world capabilities, we'll create a script that performs a multi-step task on the user's macOS system.

## Proposed Changes

### [Demo Script]
#### [NEW] [complex_task_demo.py](file:///Users/bhsingh/Documents/Project4/agent_s_analysis/Agent-S/complex_task_demo.py)
Creates a script that uses Agent-S to:
1. Open the **TextEdit** application.
2. Type a message.
3. Save the file manually.

## Verification Plan
1. **User Execution**: The user will run `python complex_task_demo.py` in their terminal.
2. **Visual Feedback**: The user will observe the agent autonomously opening the app, typing, and saving.
