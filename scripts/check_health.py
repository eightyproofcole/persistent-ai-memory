import sys, pathlib, asyncio
sys.path.insert(0, str(pathlib.Path('.').resolve()))
from ai_memory_core import PersistentAIMemorySystem

async def main():
    ms = PersistentAIMemorySystem(enable_file_monitoring=False)
    health = await ms.get_system_health()
    print('embedding endpoint:', health.get('embedding_service', {}).get('endpoint'))

if __name__ == '__main__':
    asyncio.run(main())
