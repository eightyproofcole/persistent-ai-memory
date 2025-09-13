import asyncio
from pathlib import Path
import sys

# Make the package importable when running this example directly
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

try:
    from src.llama_integration import LlamaIntegration
except Exception:
    # If running from repo root, import from the package path
    from llama_ai_memory.src.llama_integration import LlamaIntegration

# ...existing code... replace with real imports when integrating

async def main():
    print("Example integration for Persistent AI Memory with an LLM")
    print("1) Install requirements from `llama-ai-memory/requirements.txt`")
    print("2) Replace this example with your LLM client code and import `PersistentAIMemorySystem` from the main repo.")

if __name__ == '__main__':
    asyncio.run(main())
