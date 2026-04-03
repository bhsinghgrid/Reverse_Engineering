import os
import sys
import time
import logging
from PIL import ImageGrab
import base64
from io import BytesIO

# Configure relative imports for gui_agents
sys.path.append(os.path.join(os.getcwd()))

from gui_agents.s3.agents.agent_s import AgentS3
from gui_agents.s3.agents.grounding import OSWorldACI

# 1. Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("agent_s_demo")

# 2. Mock Environment for macOS local execution
class LocalDesktopEnv:
    def __init__(self):
        self.controller = None 

def get_screenshot():
    """Captures the actual local screen and returns b64 data."""
    screenshot = ImageGrab.grab()
    buffered = BytesIO()
    screenshot.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

# 3. Configure Models (Ollama local endpoint)
# NOTE: Ensure 'llama3.2-vision' is pulled in Ollama before running.
engine_params = {
    "engine_type": "openai", # Ollama's OpenAI compatible API
    "model": "llama3.2-vision",
    "api_base": "http://localhost:11434/v1",
    "api_key": "ollama", # Dummy key
    "grounding_width": 1000,   # Model internal coordinate space
    "grounding_height": 1000 
}

# 4. Initialize Agent-S components
env = LocalDesktopEnv()
platform = "darwin" # macOS

grounding_agent = OSWorldACI(
    env=env,
    platform=platform,
    engine_params_for_generation=engine_params,
    engine_params_for_grounding=engine_params,
)

agent = AgentS3(
    worker_engine_params=engine_params,
    grounding_agent=grounding_agent,
    platform=platform,
    enable_reflection=True
)

# 5. Define the Task
task = "Open TextEdit, type 'Agent-S is successfully running on my Mac!', and then save it to the desktop as 'agent_s_test.txt'."

print(f"\n🚀 STARTING COMPLEX TASK DEMO")
print(f"TASK: {task}")
print("=" * 60)

# 6. Execution Loop (Simulated)
try:
    for step in range(15): # Max 15 steps
        print(f"\n--- STEP {step + 1} ---")
        
        # Take real screenshot
        screenshot_b64 = get_screenshot()
        obs = {"screenshot": screenshot_b64}
        
        # Predict action
        info, actions = agent.predict(task, obs)
        
        # Execute action locally
        for action_code in actions:
            if action_code == "DONE":
                print("\n✅ TASK COMPLETE!")
                sys.exit(0)
            elif action_code == "FAIL":
                print("\n❌ AGENT SIGNALED FAILURE")
                sys.exit(1)
            
            print(f"Executing: {action_code}")
            # DANGER: Only use this in controlled scenarios.
            exec(action_code)
            
        time.sleep(2) # Wait for UI to update

except KeyboardInterrupt:
    print("\n🛑 Stopped by user.")
except Exception as e:
    print(f"\n💥 ERROR: {e}")
