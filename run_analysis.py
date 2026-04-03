# run_analysis.py  ← put this in your Agent-S root

import sys

sys.path.insert(0, '.')

from mock_llm import MockLLMEngine
from mock_screen import create_fake_screenshot, create_fake_accessibility_tree
from trace_agent import install_traces

# Install tracing first
install_traces()

# Import after tracing is set up
from gui_agents.s3.agents.agent_s import AgentS3
from gui_agents.s3.agents.grounding import OSWorldACI

# Create mock engines
mock_llm = MockLLMEngine()

# Create engine params pointing to mock
engine_params = {
    "engine_type": "mock",
    "model": "mock-model",
    "_mock_instance": mock_llm  # inject our mock
}

# Try to instantiate — observe what __init__ requires
# This will fail informatively if params are wrong,
# telling you exactly what the real system expects
try:
    # Adjust these based on what you find in the source
    agent = AgentS3(
        engine_params=engine_params,
        grounding_agent=None,  # start with None, add mock later
        platform="linux",
        max_trajectory_length=8,
        enable_reflection=True
    )
    print("✅ Agent instantiated successfully")
    print(f"Agent attributes: {[k for k in agent.__dict__.keys()]}")

except Exception as e:
    print(f"❌ Instantiation failed: {e}")
    print("→ This tells you what's required. Read the error and fix.")

# Attempt a predict() call
fake_obs = {
    "screenshot": create_fake_screenshot(),
    "accessibility_tree": create_fake_accessibility_tree()
}

try:
    info, action = agent.predict(
        instruction="Open Notepad and type Hello World",
        observation=fake_obs
    )
    print(f"\n✅ predict() returned:")
    print(f"  info: {info}")
    print(f"  action: {action}")

except Exception as e:
    print(f"predict() error: {e}")
    import traceback

    traceback.print_exc()  # full stack trace shows exact failure point

# Save all captured LLM calls
mock_llm.save_log("captured_prompts.json")