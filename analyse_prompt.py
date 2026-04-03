# analyze_prompts.py
import json

with open("captured_prompts.json") as f:
    calls = json.load(f)

print(f"Total LLM calls in one task: {len(calls)}")
print(f"\nCall breakdown:")

for i, call in enumerate(calls):
    print(f"\n── Call #{i} ──────────────────────────")
    print(f"  Prompt length: {call['prompt_length']} chars")

    # Identify which agent made this call
    prompt = call['prompt_full']
    if 'manager' in prompt.lower() or 'subtask' in prompt.lower():
        print(f"  Type: MANAGER (planning) call")
    elif 'reflect' in prompt.lower() or 'trajectory' in prompt.lower():
        print(f"  Type: REFLECTION call")
    elif 'action' in prompt.lower():
        print(f"  Type: ACTION GENERATION call")

    # Check what memory was injected
    if 'episodic' in prompt.lower():
        print(f"  ✅ Episodic memory injected")
    if 'narrative' in prompt.lower():
        print(f"  ✅ Narrative memory injected")
    if 'web knowledge' in prompt.lower():
        print(f"  ✅ Web knowledge injected")

    print(f"  Preview: {prompt[:200]}")