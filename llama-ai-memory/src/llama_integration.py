from typing import Any, Dict, List

class LlamaIntegration:
    """Integrates the Persistent AI Memory System with the Llama language model."""

    def __init__(self, memory_system: Any):
        """
        Initialize the LlamaIntegration with a reference to the memory system.

        Args:
            memory_system: An instance of the Persistent AI Memory System.
        """
        self.memory_system = memory_system

    async def retrieve_memory(self, query: str) -> List[Dict]:
        """
        Retrieve memories from the AI memory system based on a query.

        Args:
            query: The query string to search for relevant memories.

        Returns:
            A list of memories that match the query.
        """
        return await self.memory_system.search_memories(query)

    async def store_memory(self, content: str, memory_type: str = None, 
                           importance_level: int = 5, tags: List[str] = None) -> str:
        """
        Store a new memory in the AI memory system.

        Args:
            content: The content of the memory to store.
            memory_type: Optional type of the memory.
            importance_level: Importance level of the memory (default is 5).
            tags: Optional list of tags associated with the memory.

        Returns:
            The ID of the created memory.
        """
        return await self.memory_system.create_memory(content, memory_type, importance_level, tags)

    async def log_tool_call(self, tool_name: str, parameters: Dict, result: Any = None) -> str:
        """
        Log a tool call to the memory system.

        Args:
            tool_name: The name of the tool being called.
            parameters: The parameters used in the tool call.
            result: The result returned from the tool call.

        Returns:
            The ID of the logged tool call.
        """
        return await self.memory_system.log_tool_call(tool_name, parameters, result)

    async def get_tool_usage_summary(self, days: int = 7) -> Dict:
        """
        Get a summary of tool usage over a specified number of days.

        Args:
            days: The number of days to summarize tool usage for.

        Returns:
            A summary of tool usage statistics.
        """
        return await self.memory_system.get_tool_usage_summary(days)