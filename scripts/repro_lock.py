import tempfile, shutil
from pathlib import Path
from ai_memory_core import PersistentAIMemorySystem

d = Path(tempfile.mkdtemp(prefix='ai_mem_test_'))
print('tmp', d)
ms = PersistentAIMemorySystem(data_dir=str(d/'memory_data'), enable_file_monitoring=False)
print('created')
try:
    shutil.rmtree(d)
    print('removed ok')
except Exception as e:
    print('remove failed', e)
    import traceback
    traceback.print_exc()
