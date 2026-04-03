# Setup & Execution Guide: Agent-S

This guide provides instructions on how to set up and run Agent-S on your laptop, including using local models with Ollama.

## Prerequisites

1.  **Python 3.10+**: Ensure you have Python 3.10 or higher.
2.  **Tesseract OCR**: Required for text-based grounding. (Already installed: `brew install tesseract`)
3.  **Single Monitor**: The agent is designed for single-monitor setups.
4.  **Ollama**: For running local models. (Already installed)

## 1. Environment Setup

I have already initialized a virtual environment and installed the dependencies for you. To activate it in your terminal, run:

```bash
source .venv/bin/activate
```

## 2. Using Ollama for Local Models

Agent-S can use Ollama as a local model provider by leveraging its OpenAI-compatible API.

### Pull a Vision Model
The agent requires a vision model to analyze screenshots. We recommend `llama3.2-vision`:

```bash
ollama pull llama3.2-vision
```

### Running Agent-S with Ollama

You can run the agent from the CLI using the following configuration. Replace `YOUR_GROUNDING_MODEL_URL` with your grounding endpoint (see below).

```bash
agent_s \
    --provider openai \
    --model llama3.2-vision \
    --model_url http://localhost:11434/v1 \
    --ground_provider huggingface \
    --ground_url <YOUR_GROUNDING_MODEL_URL> \
    --ground_model ui-tars-1.5-7b \
    --grounding_width 1920 \
    --grounding_height 1080
```

## 3. Grounding Model (Critical)

Agent-S relies on a specialized model for **Grounding** (mapping descriptions to screen coordinates). The researchers recommend **UI-TARS-1.5-7B**.

- **Option A (HuggingFace)**: Use a HuggingFace Inference Endpoint. This is the easiest way to get high performance.
- **Option B (Local)**: If you have enough VRAM (at least 16GB), you can run UI-TARS locally via a framework like `vLLM`.

## 4. Example Usage (Python SDK)

You can also use Agent-S within a Python script:

```python
from gui_agents.s3.agents.agent_s import AgentS3
from gui_agents.s3.agents.grounding import OSWorldACI

# 1. Define Engine Parameters for Ollama
engine_params = {
    "engine_type": "openai",
    "model": "llama3.2-vision",
    "base_url": "http://localhost:11434/v1",
    "api_key": "ollama", # Placeholder for local
}

# 2. Define Grounding Parameters
engine_params_for_grounding = {
    "engine_type": "huggingface",
    "model": "ui-tars-1.5-7b",
    "base_url": "YOUR_HF_ENDPOINT_URL",
    "api_key": "YOUR_HF_TOKEN",
    "grounding_width": 1920,
    "grounding_height": 1080,
}

# 3. Initialize Agent
grounding_agent = OSWorldACI(
    env=None,
    platform="darwin",
    engine_params_for_generation=engine_params,
    engine_params_for_grounding=engine_params_for_grounding,
)

agent = AgentS3(engine_params, grounding_agent, platform="darwin")

# 4. Predict Action
## 5. Troubleshooting (macOS)

If you see an error like `could not create image from display` or `UnidentifiedImageError`:

1.  **Grant Permissions**: Go to `System Settings` > `Privacy & Security` > `Screen Recording`. Ensure your terminal (e.g., Terminal, iTerm2) or IDE (e.g., VS Code) is enabled.
2.  **Accessibility**: Ensure the same application is enabled under `System Settings` > `Privacy & Security` > `Accessibility`.
3.  **Run from Terminal**: If you are running the script from a background process or a restricted shell, it will fail. Always run from a primary terminal window.

## 6. How to Run the Test Script

I've created a test script called `run_test.py` in the root directory. To run it:

```bash
source .venv/bin/activate
python3 run_test.py
```

This will attempt to open the Calculator app using your local Ollama model.
