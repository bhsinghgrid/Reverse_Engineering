# Test grounding in isolation
from gui_agents.s3.agents.grounding import OSWorldACI
from mock_screen import create_fake_accessibility_tree

# Instantiate grounding agent alone
grounding = OSWorldACI(
    platform="linux",
    engine_params_for_generation={"engine_type": "mock", "model": "mock"},
    engine_params_for_grounding={"engine_type": "mock", "model": "mock",
                                  "grounding_width": 1920, "grounding_height": 1080}
)

# Test valid element access
valid_action = {"type": "click", "element_id": 2}
result = grounding.execute(valid_action, create_fake_accessibility_tree())
print(f"Valid action result: {result}")

# Test OUT-OF-RANGE element (trigger the fallback)
invalid_action = {"type": "click", "element_id": 9999}   # doesn't exist
result = grounding.execute(invalid_action, create_fake_accessibility_tree())
print(f"Invalid action result (should be 'wait'): {result}")
# ↑ This confirms the fallback mechanism