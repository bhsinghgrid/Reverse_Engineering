# ~/agent_s_analysis/Agent-S/mock_llm.py

import json
import datetime


class MockLLMEngine:
    """
    Replaces the real LLM engine.
    Records all prompts sent to it and returns scripted responses.
    Lets you analyze data flow without spending API credits.
    """

    def __init__(self, response_script=None):
        self.call_log = []
        self.call_count = 0
        self.response_script = response_script or self._default_responses()

    @staticmethod
    def _default_responses():
        return {
            0: json.dumps({
                "subtasks": [
                    {"id": 0, "description": "Open the target application",
                     "completion_criteria": "Application window is visible"},
                    {"id": 1, "description": "Perform the action",
                     "completion_criteria": "Action result is visible"}
                ]
            }),
            # Add more scripted responses for each turn
        }

    def generate(self, prompt, **kwargs):
        """Intercepts every LLM call"""

        # Log the full prompt
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "call_number": self.call_count,
            "prompt_length": len(str(prompt)),
            "prompt_preview": str(prompt)[:500],
            "prompt_full": str(prompt),  # save full for analysis
            "kwargs": kwargs
        }
        self.call_log.append(entry)

        # Print for live observation
        print(f"\n{'=' * 60}")
        print(f"LLM CALL #{self.call_count}")
        print(f"Prompt length: {len(str(prompt))} chars")
        print(f"System message preview:")
        print(str(prompt)[:300])
        print(f"{'=' * 60}")

        # Return scripted response
        response = self.response_script.get(
            self.call_count,
            '{"action": "wait", "reasoning": "mock response"}'
        )
        self.call_count += 1
        return response

    def save_log(self, path="llm_call_log.json"):
        """Save all captured prompts for offline analysis"""
        with open(path, "w") as f:
            json.dump(self.call_log, f, indent=2)
        print(f"Saved {len(self.call_log)} LLM calls to {path}")


# Usage Example:
if __name__ == "__main__":
    mock = MockLLMEngine()
    print("Capturing prompts...")
    
    # Simulate a call
    response_data = mock.generate("What is Agent-S?")
    print(f"Agent response: {response_data}")
    
    # Save the captured log
    mock.save_log()
    print("Log saved to llm_call_log.json. You can now inspect this file to see the prompt data.")
