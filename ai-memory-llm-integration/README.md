# AI Memory LLM Integration

## Overview
The AI Memory LLM Integration project provides a comprehensive system for managing persistent AI memory, designed to work seamlessly with various large language models (LLMs). This system allows for efficient storage, retrieval, and management of conversational data, insights, and memories, enhancing the capabilities of AI assistants.

## Features
- **Persistent Memory Management**: Store and retrieve memories with importance levels and tags.
- **Conversation Handling**: Automatically manage conversations and sessions.
- **Integration with LLMs**: Easily integrate with any LLM for enhanced functionality.
- **Advanced Search Capabilities**: Utilize vector-based semantic search for efficient data retrieval.
- **Real-time Monitoring**: Monitor conversation files and manage data in real-time.

## Installation
To install the AI Memory LLM Integration system, follow these steps:

1. Clone the repository:
   ```
   git clone <repository-url>
   cd ai-memory-llm-integration
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the setup script:
   ```
   python setup.py install
   ```

## Usage
After installation, you can start using the AI Memory system by importing the necessary classes from the `src` package. Here’s a quick example:

```python
from src.ai_memory_core import PersistentAIMemorySystem

# Initialize the memory system
memory_system = PersistentAIMemorySystem()

# Create a new memory
memory_id = await memory_system.create_memory("This is a test memory.")
print(f"Memory created with ID: {memory_id}")
```

## Documentation
For detailed instructions on integrating the AI memory system with various LLMs, please refer to the [Integration Guide](docs/integration_guide.md). 

## Contributing
Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.

## License
This project is licensed under the MIT License. See the LICENSE file for more details.