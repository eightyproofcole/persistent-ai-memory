import asyncio
import sys
import os

# Ensure repository root is on sys.path for local imports
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from mcp_server_clean import PersistentAIMemoryMCPServer


async def run():
    server = PersistentAIMemoryMCPServer()

    # Create a memory via the shim
    req = {"tool": "create_memory", "parameters": {"content": "Test memory from shim", "memory_type": "note"}}
    res = await server.handle_mcp_request(req, client_id="test-client")
    print("create_memory ->", res)

    # Query tool call history
    req2 = {"tool": "get_tool_call_history", "parameters": {"limit": 10}}
    res2 = await server.handle_mcp_request(req2, client_id="test-client")
    print("get_tool_call_history ->", res2)


if __name__ == "__main__":
    asyncio.run(run())
