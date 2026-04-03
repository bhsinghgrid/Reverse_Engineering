# Agent S — Complete Guide
> Reverse Engineering · Architecture · Testing · API Keys · Ollama

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture Deep Dive](#2-architecture-deep-dive)
3. [Environment Setup](#3-environment-setup)
4. [Reverse Engineering Workflow](#4-reverse-engineering-workflow)
5. [Testing with OpenAI API Key](#5-testing-with-openai-api-key)
6. [Testing with Anthropic API Key](#6-testing-with-anthropic-api-key)
7. [Testing with Ollama (Local, Free)](#7-testing-with-ollama-local-free)
8. [Mock LLM Testing (Zero Cost)](#8-mock-llm-testing-zero-cost)
9. [Terminal Command Reference](#9-terminal-command-reference)
10. [Instrumentation and Tracing](#10-instrumentation-and-tracing)
11. [Profiling and Performance Analysis](#11-profiling-and-performance-analysis)
12. [Findings Documentation Template](#12-findings-documentation-template)
13. [Troubleshooting](#13-troubleshooting)

---

## 1. Project Overview

**Agent S** is an open-source agentic framework that controls computers through a GUI using Multimodal Large Language Models (MLLMs). It was built by Simular AI and achieved 72.60% on the OSWorld benchmark — surpassing human-level performance (~72%) for the first time.

### What it does

Agent S takes a plain-English instruction like `"Open VS Code and create a Python file called hello.py"` and executes it by controlling the mouse and keyboard on a real desktop, just as a human would.

### Three generations

| Version | Paper | Benchmark Score | Key Innovation |
|---------|-------|----------------|----------------|
| S1 | arXiv:2410.08164 (ICLR 2025) | ~20% OSWorld | Hierarchical planning + ACI |
| S2 | arXiv:2504.00906 (COLM 2025) | ~40% OSWorld | Generalist-Specialist split |
| S3 | arXiv:2510.02250 | 72.60% OSWorld | Scaling + Behavior Best-of-N |

### Repository layout

```
Agent-S/
├── gui_agents/
│   ├── s1/                  # Agent S1 implementation
│   ├── s2/                  # Agent S2 implementation
│   └── s3/                  # Agent S3 (current, production)
│       ├── agents/
│       │   ├── agent_s.py   ← MAIN AGENT LOOP (start here)
│       │   └── grounding.py ← ACI + UI-TARS grounding
│       ├── memory/          ← Episodic, Narrative, Procedural
│       ├── engine/          ← LLM engine adapters
│       └── cli_app.py       ← CLI entry point
├── evaluation_sets/         # OSWorld / WindowsAgentArena tasks
├── osworld_setup/           # Deployment configs
├── requirements.txt
└── setup.py
```

---

## 2. Architecture Deep Dive

### 2.1 The five-layer stack

```
┌─────────────────────────────────────────────────┐
│                USER INSTRUCTION                 │
│        "Send an email to Alice about X"         │
└────────────────────┬────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────┐
│              MANAGER AGENT                      │
│  • Queries web for domain knowledge             │
│  • Retrieves narrative memory (past tasks)      │
│  • Decomposes task → subtask list               │
│  Output: [s0, s1, s2, ... sN]                   │
└────────────────────┬────────────────────────────┘
                     │  one subtask at a time
┌────────────────────▼────────────────────────────┐
│              WORKER AGENT                       │
│  • Retrieves episodic memory (Turn 0 only)      │
│  • Reflects on trajectory before each action   │
│  • Generates primitive actions                  │
│  Output: click(id) / type(text) / scroll(dir)   │
└────────────────────┬────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────┐
│         ACI / GROUNDING MODULE                  │
│  • Validates element_id exists in ACI tree      │
│  • If out of range → returns wait command       │
│  • Calls UI-TARS to convert action → px coords  │
│  Output: pyautogui.click(940, 621)              │
└────────────────────┬────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────┐
│           OPERATING SYSTEM / SCREEN             │
│  Screenshot + Accessibility Tree + Execution    │
└─────────────────────────────────────────────────┘
```

### 2.2 Memory system

```
MEMORY SYSTEM
├── Episodic Memory
│   ├── Stores: successful subtask step-by-step patterns
│   ├── Format: text summary (e.g. "To rename in Finder: right-click → Rename → type → Enter")
│   ├── Retrieval: embedding similarity search, TURN 0 ONLY
│   └── Update: after each successful subtask (via Self-Evaluator)
│
├── Narrative Memory
│   ├── Stores: full task experience summaries
│   ├── Format: abstractive textual reward (high-level story of what happened)
│   ├── Retrieval: by Manager at planning time
│   └── Update: after each completed task
│
└── Procedural Memory
    ├── Stores: Python/Bash scripts for mechanical tasks
    ├── Format: executable code
    ├── Retrieval: when local_env is enabled (--enable_local_env)
    └── Update: when agent successfully writes and runs code
```

### 2.3 Dual-model design

```
Instruction + Screenshot + ACI Tree
         │
         ├──► PRIMARY LLM (GPT-5, Claude, Gemini)
         │    Role: reasoning, planning, memory, reflection
         │    Output: symbolic action  e.g. click(element_id=42)
         │
         └──► GROUNDING MODEL (UI-TARS-1.5-7B)
              Role: pixel-level localization
              Input: screenshot + element description
              Output: (x=940, y=621) coordinates
              Native resolution: 1920×1080 for UI-TARS-1.5-7B
                                 1000×1000 for UI-TARS-72B
```

### 2.4 The predict() loop (one turn)

```python
# Simplified pseudocode of agent_s.py predict()

def predict(instruction, observation):

    # ── Turn 0: retrieve episodic memory ──────────────
    if self.turn == 0:
        memory = self.episodic_memory.retrieve(current_subtask)
    
    # ── Every turn: reflect on trajectory ─────────────
    reflection = self.llm.generate(
        prompt=build_reflection_prompt(self.trajectory_history)
    )
    
    # ── Generate action ────────────────────────────────
    action_str = self.llm.generate(
        prompt=build_action_prompt(
            instruction,
            observation,       # screenshot + ACI tree
            reflection,
            memory,
            self.done_tasks,   # what subtasks are complete
            self.future_tasks  # what subtasks remain
        )
    )
    
    # ── Ground and execute ─────────────────────────────
    action_code = self.grounding_agent.execute(
        parse(action_str),
        observation['accessibility_tree']
    )
    
    # ── Update trajectory ──────────────────────────────
    self.trajectory_history.append((observation, action_str))
    if len(self.trajectory_history) > self.max_trajectory_length:
        self.trajectory_history.pop(0)   # sliding window
    
    return action_code   # e.g. "pyautogui.click(940, 621)"
```

### 2.5 Fallback mechanism

```python
# In grounding.py (simplified)

def execute(action, accessibility_tree):
    element_id = action.get('element_id')
    max_id = len(accessibility_tree['elements']) - 1
    
    if element_id > max_id:
        # HALLUCINATED element → safe fallback
        return "import time; time.sleep(1)"   # wait command
    else:
        # Valid element → convert to coordinates
        element = accessibility_tree['elements'][element_id]
        coords = self.ui_tars.ground(element, screenshot)
        return f"pyautogui.click({coords[0]}, {coords[1]})"
```

---

## 3. Environment Setup

### 3.1 System requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| Python | 3.10 | 3.11 |
| RAM | 8 GB | 16 GB |
| Disk | 5 GB | 20 GB (for Ollama models) |
| OS | Linux / macOS | Ubuntu 22.04 / macOS 14 |

### 3.2 Step-by-step setup

```bash
# ── 1. Clone the repository ────────────────────────────────
git clone https://github.com/simular-ai/Agent-S.git
cd Agent-S

# ── 2. Create isolated virtual environment ─────────────────
python3 -m venv venv_analysis
source venv_analysis/bin/activate          # Linux / macOS
# venv_analysis\Scripts\activate           # Windows

# ── 3. Verify you are inside the venv ─────────────────────
which python
# Should print: .../Agent-S/venv_analysis/bin/python

# ── 4. Install in editable mode (critical for analysis) ────
pip install -e .

# ── 5. Install Tesseract OCR (required by pytesseract) ─────
sudo apt install tesseract-ocr             # Ubuntu / Debian
brew install tesseract                     # macOS

# ── 6. Install analysis tools ──────────────────────────────
pip install ipython jupyter objgraph memory_profiler \
            line_profiler py-spy viztracer pydeps \
            rich icecream python-dotenv

# ── 7. Verify installation ─────────────────────────────────
python -c "import gui_agents; print('OK')"
```

### 3.3 Create a .env file for API keys

```bash
# Create the env file (never commit this to git)
cat > .env << 'EOF'
OPENAI_API_KEY=sk-...your-key-here...
ANTHROPIC_API_KEY=sk-ant-...your-key-here...
HF_TOKEN=hf_...your-token-here...
EOF

# Make it readable only by you
chmod 600 .env

# Verify .env is in .gitignore
grep ".env" .gitignore || echo ".env" >> .gitignore
```

---

## 4. Reverse Engineering Workflow

### 4.1 Map the codebase (do this first)

```bash
# Generate full file list
find . -name "*.py" | sort > file_map.txt

# Find the heaviest files (most likely to contain core logic)
find . -name "*.py" -exec wc -l {} + | sort -n | tail -20

# Find all function definitions in the main agent
grep -n "def " gui_agents/s3/agents/agent_s.py

# Find all LLM call sites
grep -rn "generate\|completion\|llm\|engine" \
    gui_agents/s3/ --include="*.py" -i | grep -v "#"

# Find all prompt templates
grep -rn '"""' gui_agents/s3/ --include="*.py" -l

# Find memory access points
grep -rn "episodic\|narrative\|memory" \
    gui_agents/s3/ --include="*.py"

# Find cost tracking
grep -rn "cost\|token\|price" \
    gui_agents/s3/ --include="*.py" -i

# Find fallback / error handling
grep -rn "out_of_range\|fallback\|wait\|element_id" \
    gui_agents/s3/ --include="*.py"
```

### 4.2 Generate dependency graph

```bash
# Install graphviz
sudo apt install graphviz           # Ubuntu
brew install graphviz               # macOS

# Generate call graph
pip install pydeps
pydeps gui_agents/s3/agents/agent_s --max-bacon 3 \
        --output agent_s_deps.svg

open agent_s_deps.svg               # macOS
xdg-open agent_s_deps.svg          # Linux

# Generate class diagram
pip install pyreverse
pyreverse -o png -p AgentS gui_agents/s3/agents/
# Creates: classes.png and packages.png
```

### 4.3 Extract all prompts

```bash
# Find all multi-line strings (likely prompts)
python3 << 'EOF'
import ast, os, textwrap

for root, dirs, files in os.walk('gui_agents/s3'):
    for f in files:
        if not f.endswith('.py'): continue
        path = os.path.join(root, f)
        try:
            tree = ast.parse(open(path).read())
        except:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.s, str):
                if len(node.s) > 200 and '\n' in node.s:
                    print(f"\n{'='*60}")
                    print(f"FILE: {path}  LINE: {node.lineno}")
                    print(textwrap.shorten(node.s, 400))
EOF
```

---

## 5. Testing with OpenAI API Key

### 5.1 Quick test — single instruction

```bash
# Activate venv first
source venv_analysis/bin/activate

# Load env vars
export $(cat .env | xargs)

# Run Agent S3 — minimal single task test
agent_s \
    --provider openai \
    --model gpt-4o \
    --ground_provider huggingface \
    --ground_url http://localhost:8080 \
    --ground_model ui-tars-1.5-7b \
    --grounding_width 1920 \
    --grounding_height 1080
```

### 5.2 Python SDK test with OpenAI

```python
# test_openai.py
import os, io, pyautogui
from dotenv import load_dotenv
from gui_agents.s3.agents.agent_s import AgentS3
from gui_agents.s3.agents.grounding import OSWorldACI

load_dotenv()

# Engine config — primary reasoning model
engine_params = {
    "engine_type": "openai",
    "model": "gpt-4o",                 # or "gpt-4o-mini" for cheaper tests
    "api_key": os.environ["OPENAI_API_KEY"],
    "temperature": 0.0,                 # deterministic for analysis
}

# Grounding engine config (needs UI-TARS running)
engine_params_grounding = {
    "engine_type": "huggingface",
    "model": "ui-tars-1.5-7b",
    "base_url": "http://localhost:8080",
    "grounding_width": 1920,
    "grounding_height": 1080,
}

# Build the agent
grounding_agent = OSWorldACI(
    platform="linux",                   # "darwin" for Mac, "windows" for Windows
    engine_params_for_generation=engine_params,
    engine_params_for_grounding=engine_params_grounding,
)

agent = AgentS3(
    engine_params,
    grounding_agent,
    platform="linux",
    max_trajectory_length=8,
    enable_reflection=True,
)

# Take screenshot and run one prediction
screenshot = pyautogui.screenshot()
buf = io.BytesIO()
screenshot.save(buf, format="PNG")

obs = {"screenshot": buf.getvalue()}
instruction = "Open a terminal window"

info, action = agent.predict(instruction=instruction, observation=obs)
print("Action returned:", action)

# Execute the action
if action:
    exec(action[0])
```

```bash
# Run it
python test_openai.py
```

### 5.3 Cost-monitored test (logs token usage per turn)

```python
# test_openai_with_cost.py
import os, io, time, pyautogui
from dotenv import load_dotenv
from gui_agents.s3.agents.agent_s import AgentS3
from gui_agents.s3.agents.grounding import OSWorldACI

load_dotenv()

engine_params = {
    "engine_type": "openai",
    "model": "gpt-4o",
    "api_key": os.environ["OPENAI_API_KEY"],
}

# GPT-4o pricing (as of 2025)
INPUT_COST_PER_1K  = 0.0025   # USD per 1K input tokens
OUTPUT_COST_PER_1K = 0.010    # USD per 1K output tokens

total_input_tokens  = 0
total_output_tokens = 0

# Patch the engine to log token usage
original_generate = None

def logged_generate(self, messages, **kwargs):
    global total_input_tokens, total_output_tokens
    result = original_generate(self, messages, **kwargs)
    # Try to extract usage if exposed
    print(f"[TURN] Tokens approx — total so far: {total_input_tokens + total_output_tokens}")
    return result

grounding_agent = OSWorldACI(
    platform="linux",
    engine_params_for_generation=engine_params,
    engine_params_for_grounding={
        "engine_type": "huggingface",
        "model": "ui-tars-1.5-7b",
        "base_url": "http://localhost:8080",
        "grounding_width": 1920,
        "grounding_height": 1080,
    },
)

agent = AgentS3(engine_params, grounding_agent, platform="linux")

for turn in range(5):
    screenshot = pyautogui.screenshot()
    buf = io.BytesIO()
    screenshot.save(buf, format="PNG")
    obs = {"screenshot": buf.getvalue()}

    start = time.time()
    info, action = agent.predict(
        instruction="Open Notepad and type Hello World",
        observation=obs
    )
    elapsed = time.time() - start

    print(f"\nTurn {turn}: {elapsed:.2f}s")
    print(f"Action: {action}")

    if action:
        exec(action[0])

    if info.get("done"):
        print("Task complete!")
        break
    time.sleep(1)
```

---

## 6. Testing with Anthropic API Key

### 6.1 CLI with Claude

```bash
export $(cat .env | xargs)

agent_s \
    --provider anthropic \
    --model claude-sonnet-4-6 \
    --ground_provider huggingface \
    --ground_url http://localhost:8080 \
    --ground_model ui-tars-1.5-7b \
    --grounding_width 1920 \
    --grounding_height 1080 \
    --enable_reflection
```

### 6.2 Python SDK test with Claude

```python
# test_anthropic.py
import os, io, pyautogui
from dotenv import load_dotenv
from gui_agents.s3.agents.agent_s import AgentS3
from gui_agents.s3.agents.grounding import OSWorldACI

load_dotenv()

engine_params = {
    "engine_type": "anthropic",
    "model": "claude-sonnet-4-6",         # or claude-opus-4-6 for best quality
    "api_key": os.environ["ANTHROPIC_API_KEY"],
}

engine_params_grounding = {
    "engine_type": "huggingface",
    "model": "ui-tars-1.5-7b",
    "base_url": "http://localhost:8080",
    "grounding_width": 1920,
    "grounding_height": 1080,
}

grounding_agent = OSWorldACI(
    platform="linux",
    engine_params_for_generation=engine_params,
    engine_params_for_grounding=engine_params_grounding,
)

agent = AgentS3(
    engine_params,
    grounding_agent,
    platform="linux",
    max_trajectory_length=8,
    enable_reflection=True,
)

screenshot = pyautogui.screenshot()
buf = io.BytesIO()
screenshot.save(buf, format="PNG")

info, action = agent.predict(
    instruction="Take a screenshot and save it to the Desktop",
    observation={"screenshot": buf.getvalue()}
)

print("Action:", action)
if action:
    exec(action[0])
```

---

## 7. Testing with Ollama (Local, Free)

Ollama lets you run LLMs entirely on your laptop with zero API costs.

### 7.1 Install Ollama

```bash
# Linux / macOS
curl -fsSL https://ollama.com/install.sh | sh

# Verify install
ollama --version

# Start the Ollama server
ollama serve &
# Server runs on http://localhost:11434
```

### 7.2 Pull models for Agent S

```bash
# Recommended models (choose based on your RAM)

# ── 8 GB RAM ──────────────────────────────────────────────
ollama pull llama3.1:8b          # Meta's Llama 3.1 8B
ollama pull qwen2.5:7b           # Alibaba Qwen 2.5 7B (strong at coding)
ollama pull mistral:7b           # Mistral 7B

# ── 16 GB RAM ─────────────────────────────────────────────
ollama pull llama3.1:70b         # Llama 3.1 70B (much better reasoning)
ollama pull qwen2.5:32b          # Qwen 2.5 32B
ollama pull deepseek-r1:32b      # DeepSeek R1 32B (strong reasoning)

# ── 32 GB RAM ─────────────────────────────────────────────
ollama pull llama3.1:70b         # Full quality
ollama pull qwen2.5:72b

# List installed models
ollama list

# Test a model works
ollama run llama3.1:8b "What is 2 + 2?"
```

### 7.3 Run Agent S with Ollama (CLI)

```bash
# Ollama exposes an OpenAI-compatible API at localhost:11434

agent_s \
    --provider openai \
    --model llama3.1:8b \
    --model_url http://localhost:11434/v1 \
    --model_api_key ollama \
    --ground_provider huggingface \
    --ground_url http://localhost:8080 \
    --ground_model ui-tars-1.5-7b \
    --grounding_width 1920 \
    --grounding_height 1080
```

### 7.4 Python SDK test with Ollama

```python
# test_ollama.py
import os, io, pyautogui

# Ollama is OpenAI-compatible so we use engine_type "openai"
# with a custom base_url pointing to localhost
engine_params = {
    "engine_type": "openai",
    "model": "llama3.1:8b",                    # must match what you pulled
    "base_url": "http://localhost:11434/v1",    # Ollama OpenAI-compat endpoint
    "api_key": "ollama",                        # any non-empty string works
}

engine_params_grounding = {
    "engine_type": "openai",
    "model": "llama3.1:8b",                    # also use ollama for grounding
    "base_url": "http://localhost:11434/v1",
    "api_key": "ollama",
    "grounding_width": 1920,
    "grounding_height": 1080,
}

from gui_agents.s3.agents.agent_s import AgentS3
from gui_agents.s3.agents.grounding import OSWorldACI

grounding_agent = OSWorldACI(
    platform="linux",
    engine_params_for_generation=engine_params,
    engine_params_for_grounding=engine_params_grounding,
)

agent = AgentS3(
    engine_params,
    grounding_agent,
    platform="linux",
    max_trajectory_length=6,      # smaller window for local models
    enable_reflection=False,       # disable reflection to save tokens on small models
)

screenshot = pyautogui.screenshot()
buf = io.BytesIO()
screenshot.save(buf, format="PNG")

info, action = agent.predict(
    instruction="Open a text editor",
    observation={"screenshot": buf.getvalue()}
)
print("Ollama action:", action)
```

### 7.5 Verify Ollama is responding

```bash
# Direct API test (no Agent S involved)
curl http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.1:8b",
    "messages": [
      {"role": "system", "content": "You are a GUI agent. Reply with a single action."},
      {"role": "user", "content": "How do I open a terminal on Linux?"}
    ]
  }'

# Check available models via API
curl http://localhost:11434/api/tags | python3 -m json.tool
```

### 7.6 Ollama model comparison for Agent S

| Model | RAM needed | Reasoning | GUI understanding | Speed |
|-------|-----------|-----------|-------------------|-------|
| llama3.1:8b | 6 GB | Basic | Weak | Fast |
| qwen2.5:7b | 6 GB | Good | Moderate | Fast |
| mistral:7b | 5 GB | Basic | Weak | Fast |
| llama3.1:70b | 48 GB | Strong | Good | Slow |
| qwen2.5:32b | 20 GB | Strong | Good | Medium |
| deepseek-r1:32b | 20 GB | Very strong | Good | Medium |

**Best for Agent S on Ollama:** `qwen2.5:32b` if you have 20 GB RAM, otherwise `qwen2.5:7b`.

---

## 8. Mock LLM Testing (Zero Cost)

This approach requires no API keys and lets you trace every internal state.

### 8.1 The mock LLM engine

```python
# mock_llm.py  — save this in your Agent-S root

import json, time

class MockLLMEngine:
    """
    Drop-in replacement for any real LLM engine.
    Records every prompt and returns scripted responses.
    Use this to analyze data flow without API costs.
    """

    def __init__(self):
        self.call_log    = []
        self.call_count  = 0
        self.responses   = self._build_responses()

    def _build_responses(self):
        """
        Script responses to simulate a real agent run.
        call 0 = Manager planning call
        call 1 = Worker reflection call
        call 2 = Worker action generation call
        ...repeat pattern
        """
        return {
            0: json.dumps({
                "subtasks": [
                    {"id": 0, "description": "Open text editor",
                     "completion": "Text editor window is visible"},
                    {"id": 1, "description": "Type the content",
                     "completion": "Content appears in editor"},
                ]
            }),
            1: "Trajectory analysis: No prior actions. Starting fresh. "
               "Next I should look for a text editor icon on the desktop.",
            2: '{"action": "click", "element_id": 2, '
               '"reasoning": "Clicking the text editor element"}',
            3: "Trajectory analysis: Clicked element 2. "
               "Editor appears to be opening. Waiting for window.",
            4: '{"action": "wait", "duration": 1, '
               '"reasoning": "Waiting for editor to fully load"}',
        }

    def generate(self, messages, **kwargs):
        """Called by Agent S every time it needs an LLM response."""

        # Build log entry
        prompt_text = str(messages)
        entry = {
            "call_number"    : self.call_count,
            "timestamp"      : time.time(),
            "prompt_chars"   : len(prompt_text),
            "prompt_full"    : prompt_text,
            "kwargs"         : str(kwargs),
        }
        self.call_log.append(entry)

        # Classify the call type from prompt content
        lower = prompt_text.lower()
        if "subtask" in lower and "plan" in lower:
            call_type = "MANAGER/PLANNING"
        elif "reflect" in lower or "trajectory" in lower:
            call_type = "WORKER/REFLECTION"
        elif "action" in lower:
            call_type = "WORKER/ACTION"
        else:
            call_type = "UNKNOWN"

        print(f"\n{'─'*55}")
        print(f"  LLM call #{self.call_count}  [{call_type}]")
        print(f"  Prompt length: {len(prompt_text):,} chars")
        print(f"  Preview: {prompt_text[:180]!r}")
        print(f"{'─'*55}")

        # Return scripted response
        response = self.responses.get(
            self.call_count,
            '{"action": "wait", "reasoning": "default mock response"}'
        )
        self.call_count += 1
        return response

    def save_log(self, path="llm_call_log.json"):
        with open(path, "w") as f:
            json.dump(self.call_log, f, indent=2)
        print(f"\nSaved {len(self.call_log)} LLM calls → {path}")
```

### 8.2 The mock screen

```python
# mock_screen.py  — save this in your Agent-S root

import io
from PIL import Image, ImageDraw, ImageFont

def make_screenshot(label="Mock Desktop"):
    img = Image.new("RGB", (1920, 1080), color=(230, 230, 230))
    d   = ImageDraw.Draw(img)
    # Taskbar
    d.rectangle([0, 1040, 1920, 1080], fill=(50, 50, 50))
    # App icons
    d.rectangle([10, 1042, 50, 1078], fill=(0, 120, 212), outline="white")
    d.text((15, 1050), "Files", fill="white")
    # Window
    d.rectangle([200, 100, 1200, 800], fill="white", outline=(100,100,100), width=2)
    d.rectangle([200, 100, 1200, 130], fill=(0, 120, 212))
    d.text((210, 108), label, fill="white")
    d.text((600, 450), "Desktop area", fill=(150, 150, 150))

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def make_aci_tree():
    return {
        "active_app": "MockDesktop",
        "elements": [
            {"id": 0, "type": "desktop",    "name": "Desktop",      "bounds": [0,0,1920,1080]},
            {"id": 1, "type": "taskbar",    "name": "Taskbar",      "bounds": [0,1040,1920,1080]},
            {"id": 2, "type": "button",     "name": "Files",        "bounds": [10,1042,50,1078]},
            {"id": 3, "type": "window",     "name": "MainWindow",   "bounds": [200,100,1200,800]},
            {"id": 4, "type": "titlebar",   "name": "Window title", "bounds": [200,100,1200,130]},
            {"id": 5, "type": "textfield",  "name": "Content area", "bounds": [200,130,1200,800]},
        ]
    }
```

### 8.3 Run the full mock analysis

```python
# run_mock_analysis.py

import sys
sys.path.insert(0, ".")

from mock_llm    import MockLLMEngine
from mock_screen import make_screenshot, make_aci_tree

mock_llm = MockLLMEngine()

# Try to instantiate the agent
try:
    from gui_agents.s3.agents.agent_s import AgentS3

    # Build minimal engine params
    engine_params = {
        "engine_type" : "openai",
        "model"       : "mock",
        "_mock"       : mock_llm,   # inject our mock
    }

    agent = AgentS3(
        engine_params,
        grounding_agent    = None,
        platform           = "linux",
        max_trajectory_length = 4,
        enable_reflection  = True,
    )
    print("Agent instantiated. Attributes:", list(agent.__dict__.keys()))

except Exception as e:
    print(f"Instantiation error: {e}")
    import traceback; traceback.print_exc()

# Run predict() with fake observation
obs = {
    "screenshot"         : make_screenshot("Mock Desktop"),
    "accessibility_tree" : make_aci_tree(),
}

try:
    info, action = agent.predict(
        instruction = "Open a text editor and type Hello World",
        observation = obs,
    )
    print("\npredict() returned:")
    print("  info  :", info)
    print("  action:", action)

except Exception as e:
    print(f"predict() error: {e}")
    import traceback; traceback.print_exc()

# Save all captured prompts for analysis
mock_llm.save_log("llm_call_log.json")
print("\nAnalyze captured prompts:")
print("  python3 analyze_prompts.py")
```

```bash
python run_mock_analysis.py
```

### 8.4 Analyze the captured prompts

```python
# analyze_prompts.py

import json

with open("llm_call_log.json") as f:
    calls = json.load(f)

print(f"Total LLM calls in this run: {len(calls)}")
print(f"{'─'*60}")

for c in calls:
    p = c["prompt_full"].lower()
    print(f"\nCall #{c['call_number']}  ({c['prompt_chars']:,} chars)")

    # Identify what memory was injected
    if "episodic" in p:  print("  ✓ Episodic memory injected")
    if "narrative" in p: print("  ✓ Narrative memory injected")
    if "web"       in p: print("  ✓ Web knowledge injected")
    if "reflect"   in p: print("  ✓ Reflection section present")
    if "subtask"   in p: print("  → Manager planning call")
    else:                print("  → Worker execution call")

    # Check future/done task context
    if "future_tasks" in p: print("  ✓ future_tasks present in prompt")
    if "done_task"    in p: print("  ✓ done_tasks present in prompt")
```

---

## 9. Terminal Command Reference

### 9.1 Setup commands

```bash
# Clone
git clone https://github.com/simular-ai/Agent-S.git && cd Agent-S

# Env
python3 -m venv venv_analysis && source venv_analysis/bin/activate

# Install
pip install -e .
pip install ipython jupyter py-spy line_profiler rich icecream python-dotenv

# Tesseract
sudo apt install tesseract-ocr    # Ubuntu
brew install tesseract             # macOS
```

### 9.2 Run commands

```bash
# Run with OpenAI
agent_s --provider openai --model gpt-4o \
        --ground_provider huggingface \
        --ground_url http://localhost:8080 \
        --ground_model ui-tars-1.5-7b \
        --grounding_width 1920 --grounding_height 1080

# Run with Anthropic Claude
agent_s --provider anthropic --model claude-sonnet-4-6 \
        --ground_provider huggingface \
        --ground_url http://localhost:8080 \
        --ground_model ui-tars-1.5-7b \
        --grounding_width 1920 --grounding_height 1080

# Run with Ollama (local, free)
agent_s --provider openai --model llama3.1:8b \
        --model_url http://localhost:11434/v1 \
        --model_api_key ollama \
        --ground_provider openai \
        --ground_url http://localhost:11434/v1 \
        --ground_model llama3.1:8b \
        --grounding_width 1920 --grounding_height 1080

# Run with local coding env enabled
agent_s --provider openai --model gpt-4o \
        --ground_provider huggingface \
        --ground_url http://localhost:8080 \
        --ground_model ui-tars-1.5-7b \
        --grounding_width 1920 --grounding_height 1080 \
        --enable_local_env

# Disable reflection (faster, cheaper)
agent_s --provider openai --model gpt-4o \
        --ground_provider huggingface \
        --ground_url http://localhost:8080 \
        --ground_model ui-tars-1.5-7b \
        --grounding_width 1920 --grounding_height 1080 \
        --enable_reflection False

# Limit trajectory (smaller context window)
agent_s --provider openai --model gpt-4o \
        --ground_provider huggingface \
        --ground_url http://localhost:8080 \
        --ground_model ui-tars-1.5-7b \
        --grounding_width 1920 --grounding_height 1080 \
        --max_trajectory_length 4
```

### 9.3 Analysis commands

```bash
# Find all function definitions
grep -n "def " gui_agents/s3/agents/agent_s.py

# Find all LLM call sites
grep -rn "\.generate\(" gui_agents/s3/ --include="*.py"

# Find all memory access
grep -rn "episodic\|narrative" gui_agents/s3/ --include="*.py"

# Count lines per file
find . -name "*.py" -exec wc -l {} + | sort -n | tail -20

# Search for a specific string across all files
grep -rn "future_tasks" gui_agents/ --include="*.py"

# Watch log file in real time
tail -f real_run.log

# Check what packages are installed
pip list | grep -i gui

# Verify editable install
pip show gui-agents | grep Location
```

### 9.4 Ollama commands

```bash
# Start server
ollama serve

# Pull a model
ollama pull llama3.1:8b
ollama pull qwen2.5:7b

# List models
ollama list

# Run interactive chat
ollama run llama3.1:8b

# Remove a model
ollama rm llama3.1:8b

# Check server health
curl http://localhost:11434/

# List models via API
curl http://localhost:11434/api/tags

# Test completion via API
curl http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"llama3.1:8b","messages":[{"role":"user","content":"Hello"}]}'

# Monitor GPU usage while running
watch -n 1 nvidia-smi         # NVIDIA GPU
watch -n 1 ollama ps          # Ollama process status
```

### 9.5 Profiling commands

```bash
# Attach py-spy to a running agent (no code changes needed)
py-spy record -o profile.svg --pid $(pgrep -f agent_s)
open profile.svg

# Profile a specific script
py-spy record -o profile.svg -- python run_mock_analysis.py

# Line-by-line timing
pip install line_profiler
# Add @profile decorator to the function you want
kernprof -l -v run_mock_analysis.py

# Memory profiling
pip install memory_profiler
# Add @profile decorator
python -m memory_profiler run_mock_analysis.py

# Execution timeline (visual)
viztracer run_mock_analysis.py
vizviewer result.json
```

---

## 10. Instrumentation and Tracing

### 10.1 Universal trace decorator

```python
# trace_utils.py

import functools, time, json
from rich.console import Console
from rich.panel   import Panel

console = Console()

def trace(func):
    """Wrap any method to log its inputs and outputs."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        name = f"{func.__module__}.{func.__qualname__}"
        console.print(Panel(
            f"[green]ENTER[/] {name}\n"
            f"args   = {str(args[1:])[:300]}\n"
            f"kwargs = {str(kwargs)[:200]}",
            border_style="green", expand=False
        ))
        t0 = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            elapsed = time.perf_counter() - t0
            console.print(Panel(
                f"[blue]EXIT[/] {name}  ({elapsed*1000:.1f} ms)\n"
                f"return = {str(result)[:400]}",
                border_style="blue", expand=False
            ))
            return result
        except Exception as e:
            console.print(f"[red]ERROR in {name}: {e}[/]")
            raise
    return wrapper


def patch_agent():
    """Monkey-patch key Agent S methods with tracing."""
    from gui_agents.s3.agents import agent_s, grounding

    agent_s.AgentS3.predict   = trace(agent_s.AgentS3.predict)

    if hasattr(grounding, 'OSWorldACI'):
        grounding.OSWorldACI.execute = trace(grounding.OSWorldACI.execute)

    print("Traces installed on: AgentS3.predict, OSWorldACI.execute")
```

### 10.2 Full run logging

```python
# log_full_run.py
import logging, os

logging.basicConfig(
    level   = logging.DEBUG,
    format  = "%(asctime)s | %(name)-30s | %(levelname)s | %(message)s",
    handlers = [
        logging.FileHandler("full_run.log"),
        logging.StreamHandler(),
    ]
)

os.environ["OPENAI_API_KEY"] = open(".env").read().split("OPENAI_API_KEY=")[1].split()[0]

# Patch LLM engine to log all calls
from gui_agents.s3.engine import base_engine   # adjust path

_orig = base_engine.BaseEngine.generate

def _logged(self, messages, **kw):
    logging.info(f"LLM_INPUT ({len(str(messages))} chars): {str(messages)[:500]}")
    r = _orig(self, messages, **kw)
    logging.info(f"LLM_OUTPUT: {str(r)[:300]}")
    return r

base_engine.BaseEngine.generate = _logged

# Now run your task
# ...
```

---

## 11. Profiling and Performance Analysis

### 11.1 Find hot functions

```bash
# Run agent and profile simultaneously
python run_mock_analysis.py &
PID=$!
sleep 2
py-spy record -d 10 -o flame.svg --pid $PID
wait
open flame.svg
```

### 11.2 Memory usage per function

```python
# Add to the top of any function you want to profile:
from memory_profiler import profile

@profile
def predict(self, instruction, observation):
    ...

# Then run:
# python -m memory_profiler your_script.py
```

### 11.3 Object graph analysis

```python
# Run this after a full predict() call to see what objects were created
import objgraph

objgraph.show_most_common_types(limit=15)

# Visualize what's keeping a specific object alive
objgraph.show_backrefs(
    objgraph.by_type('dict')[0],
    max_depth=3,
    filename='obj_graph.png'
)
```

---

## 12. Findings Documentation Template

Use this Jupyter notebook structure to document your analysis:

```markdown
# Agent S — Reverse Engineering Findings

## Section 1: Architecture Map
- [ ] Module dependency graph (image)
- [ ] Call hierarchy from predict()
- [ ] Data flow: instruction → action

## Section 2: Entry Points
- cli_app.py — what it creates, what loop it runs
- predict() — full call sequence

## Section 3: Memory System
| Memory Type | Storage | Retrieval | Update Trigger |
|-------------|---------|-----------|----------------|
| Episodic    | ?       | ?         | ?              |
| Narrative   | ?       | ?         | ?              |
| Procedural  | ?       | ?         | ?              |

## Section 4: Prompts Catalogue
- Manager planning prompt — variables injected
- Worker reflection prompt — variables injected
- Worker action prompt — expected output format

## Section 5: Grounding Pipeline
- ACI tree structure (from mock_screen.py)
- Element ID assignment logic
- Fallback tested: out-of-range → wait ✓

## Section 6: Open Questions
- How exactly is episodic memory indexed?
- What embedding model is used for retrieval?
- How does the self-evaluator decide success?
```

---

## 13. Troubleshooting

### `ModuleNotFoundError: No module named 'gui_agents'`

```bash
# You are not in the venv or the editable install failed
source venv_analysis/bin/activate
pip install -e .
python -c "import gui_agents; print(gui_agents.__file__)"
```

### `tesseract is not installed or it's not in your PATH`

```bash
sudo apt install tesseract-ocr    # Ubuntu
brew install tesseract             # macOS
which tesseract                    # verify
```

### `Connection refused` when using Ollama

```bash
# Ollama server is not running
ollama serve &

# Verify it is up
curl http://localhost:11434/
```

### `model not found` with Ollama

```bash
# Pull the model first
ollama pull llama3.1:8b

# Check model name matches exactly
ollama list
```

### `AuthenticationError` with OpenAI or Anthropic

```bash
# Check your key is loaded
echo $OPENAI_API_KEY
echo $ANTHROPIC_API_KEY

# Reload from .env
export $(cat .env | xargs)
```

### Agent loops forever / does not complete

```bash
# Reduce trajectory length to prevent context bloat
--max_trajectory_length 4

# Disable reflection to simplify
--enable_reflection False

# Check the task is achievable on your screen resolution
# Agent S is designed for single-monitor setups
```

### Out of memory with large model on Ollama

```bash
# Check how much RAM your model needs
ollama show llama3.1:70b   # shows model info including size

# Use a smaller model
ollama pull qwen2.5:7b

# Or increase swap space temporarily (Linux)
sudo fallocate -l 16G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

---

## Quick Reference Card

```
SETUP              git clone → venv → pip install -e . → pip install tools
OPENAI             export OPENAI_API_KEY=sk-... then use --provider openai
ANTHROPIC          export ANTHROPIC_API_KEY=sk-ant-... then use --provider anthropic
OLLAMA             ollama serve → ollama pull model → --provider openai --model_url localhost:11434/v1
MOCK               python run_mock_analysis.py → analyze llm_call_log.json
PROFILE            py-spy record -o profile.svg --pid $(pgrep -f agent_s)
DEBUG              grep -rn "def " gui_agents/s3/agents/agent_s.py
```

---

*Agent S is licensed under Apache 2.0. This guide is for educational analysis only.*
