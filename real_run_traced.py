# real_run_traced.py
import logging
import os

# Enable maximum logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler('real_run.log'),
        logging.StreamHandler()
    ]
)

os.environ["OPENAI_API_KEY"] = "your-key"

# Monkey-patch the LLM engine to log all calls
from gui_agents.s3 import engine_module   # adjust to real module name

original_generate = engine_module.LLMEngine.generate

def logged_generate(self, prompt, **kwargs):
    logging.info(f"LLM_INPUT: {str(prompt)[:1000]}")
    result = original_generate(self, prompt, **kwargs)
    logging.info(f"LLM_OUTPUT: {str(result)[:500]}")
    return result

engine_module.LLMEngine.generate = logged_generate
