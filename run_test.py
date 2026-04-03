import pyautogui
import io
import os
import time
from gui_agents.s3.agents.agent_s import AgentS3
from gui_agents.s3.agents.grounding import OSWorldACI

# 1. Configuration for Ollama
# We use llama3.2-vision for both the Worker and the Grounding model
engine_params = {
    "engine_type": "openai",
    "model": "llama3.2-vision",
    "base_url": "http://localhost:11434/v1",
    "api_key": "ollama", # Placeholder for local
    "temperature": 0.0,
}

# Grounding width/height for llama3.2-vision
# Since it's not fine-tuned for UI-TARS, we'll try standard resolution
grounding_width = 1920
grounding_height = 1080

engine_params_for_grounding = {
    "engine_type": "openai",
    "model": "llama3.2-vision",
    "base_url": "http://localhost:11434/v1",
    "api_key": "ollama",
    "grounding_width": grounding_width,
    "grounding_height": grounding_height,
}

# 2. Initialize Grounding Agent and Agent-S
print("Initializing Agent-S with Ollama...")
grounding_agent = OSWorldACI(
    env=None, # Run on real OS
    platform="darwin",
    engine_params_for_generation=engine_params,
    engine_params_for_grounding=engine_params_for_grounding,
)

agent = AgentS3(
    engine_params, 
    grounding_agent, 
    platform="darwin",
    enable_reflection=True
)

# 3. Perform a simple task
instruction = "Open the Calculator app"
print(f"Task: {instruction}")

# Capture initial screenshot
screenshot = pyautogui.screenshot()
buffered = io.BytesIO()
screenshot.save(buffered, format="PNG")
screenshot_bytes = buffered.getvalue()

obs = {
    "screenshot": screenshot_bytes,
}

# 4. Step through the agent (1 step for demonstration)
print("Predicting next action...")
info, actions = agent.predict(instruction=instruction, observation=obs)

print("-" * 30)
print("AGENT PLAN:", info.get("plan"))
print("AGENT ACTIONS:", actions)
print("-" * 30)

if actions and "DONE" not in actions[0] and "FAIL" not in actions[0]:
    print("Executing action...")
    # WARNING: This will actually move your mouse and type!
    # exec(actions[0])
    print(f"To execute, you would run: {actions[0]}")
else:
    print("No executable action returned or task already completed/failed.")
