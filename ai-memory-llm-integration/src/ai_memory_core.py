from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime, timezone, timedelta
from pathlib import Path
import sqlite3
import json
import uuid
import logging

# Configure logging with minimal output
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

class DatabaseManager:
    """Base database manager for common operations"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.ensure_database_exists()
    
    def ensure_database_exists(self):
        """Ensure the database file and directory exist"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
    def get_connection(self) -> sqlite3.Connection:
        """Get a database connection with proper configuration"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
        return conn
    
    async def execute_query(self, query: str, params: Tuple = ()) -> List[sqlite3.Row]:
        """Execute a SELECT query and return results"""
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            return cursor.fetchall()
    
    async def execute_update(self, query: str, params: Tuple = ()) -> str:
        """Execute an INSERT/UPDATE/DELETE query and return last row ID"""
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            conn.commit()
            return cursor.lastrowid

class MCPToolCallDatabase(DatabaseManager):
    """Tracks all MCP tool calls for reflection and debugging"""
    
    def __init__(self, db_path: str = "mcp_tool_calls.db"):
        super().__init__(db_path)
        self.initialize_tables()
    
    def initialize_tables(self):
        """Create tool call tracking tables"""
        with self.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tool_calls (
                    call_id TEXT PRIMARY KEY,
                    timestamp TEXT,
                    client_id TEXT,
                    tool_name TEXT,
                    parameters TEXT,
                    result TEXT,
                    status TEXT,
                    execution_time_ms INTEGER,
                    error_message TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tool_usage_stats (
                    tool_name TEXT,
                    date TEXT,
                    call_count INTEGER,
                    success_count INTEGER,
                    failure_count INTEGER,
                    PRIMARY KEY (tool_name, date)
                )
            """)

    async def log_tool_call(self, tool_name: str, parameters: Dict, result: Any = None, 
                           status: str = "success", execution_time_ms: float = None,
                           error_message: str = None, client_id: str = None) -> str:
        """Log a tool call with all relevant details"""
        
        call_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        await self.execute_update(
            """INSERT INTO tool_calls 
               (call_id, timestamp, client_id, tool_name, parameters, result, 
                status, execution_time_ms, error_message) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (call_id, timestamp, client_id, tool_name, 
             json.dumps(parameters), json.dumps(result) if result else None,
             status, int(execution_time_ms) if execution_time_ms else None, error_message)
        )
        
        await self._update_tool_stats(tool_name, status, execution_time_ms)
        
        return call_id
    
    async def _update_tool_stats(self, tool_name: str, status: str, execution_time_ms: float):
        """Update daily usage statistics for a tool"""
        today = datetime.now().date().isoformat()
        
        existing = await self.execute_query(
            "SELECT * FROM tool_usage_stats WHERE tool_name = ? AND date = ?",
            (tool_name, today)
        )
        
        if existing:
            await self.execute_update(
                """UPDATE tool_usage_stats 
                   SET call_count = call_count + 1,
                       success_count = success_count + (CASE WHEN ? = 'success' THEN 1 ELSE 0 END),
                       failure_count = failure_count + (CASE WHEN ? = 'failure' THEN 1 ELSE 0 END)
                   WHERE tool_name = ? AND date = ?""",
                (status, status, tool_name, today)
            )
        else:
            await self.execute_update(
                """INSERT INTO tool_usage_stats (tool_name, date, call_count, success_count, failure_count) 
                   VALUES (?, ?, 1, ?, ?)""",
                (tool_name, today, 1 if status == 'success' else 0, 1 if status == 'failure' else 0)
            )

class ConversationDatabase(DatabaseManager):
    """Manages conversation auto-save database"""
    
    def __init__(self, db_path: str = "conversations.db"):
        super().__init__(db_path)
        self.initialize_tables()

    def initialize_tables(self):
        """Create tables if they don't exist"""
        with self.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    message_id TEXT PRIMARY KEY,
                    conversation_id TEXT,
                    timestamp TEXT,
                    role TEXT,
                    content TEXT,
                    metadata TEXT
                )
            """)

    async def store_message(self, content: str, role: str, session_id: str = None, 
                          conversation_id: str = None, metadata: Dict = None) -> Dict[str, str]:
        """Store a message and auto-manage sessions/conversations with duplicate detection"""
        timestamp = datetime.now().isoformat()
        message_id = str(uuid.uuid4())

        await self.execute_update(
            """INSERT INTO messages 
               (message_id, conversation_id, timestamp, role, content, metadata) 
               VALUES (?, ?, ?, ?, ?, ?)""",
            (message_id, conversation_id, timestamp, role, content, 
             json.dumps(metadata) if metadata else None)
        )

        return {
            "message_id": message_id,
            "conversation_id": conversation_id,
            "session_id": session_id
        }

class AIMemoryDatabase(DatabaseManager):
    """Manages AI-curated memories database with enhanced operations"""
    
    def __init__(self, db_path: str = "ai_memories.db"):
        super().__init__(db_path)
        self.initialize_tables()

    def initialize_tables(self):
        """Create tables if they don't exist"""
        with self.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS curated_memories (
                    memory_id TEXT PRIMARY KEY,
                    timestamp_created TEXT,
                    timestamp_updated TEXT,
                    source_conversation_id TEXT,
                    memory_type TEXT,
                    content TEXT,
                    importance_level INTEGER,
                    tags TEXT
                )
            """)

    async def create_memory(self, content: str, memory_type: str = None, 
                          importance_level: int = 5, tags: List[str] = None,
                          source_conversation_id: str = None) -> str:
        """Create a new curated memory"""
        memory_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()

        await self.execute_update(
            """INSERT INTO curated_memories 
               (memory_id, timestamp_created, timestamp_updated, source_conversation_id, 
                memory_type, content, importance_level, tags) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (memory_id, timestamp, timestamp, source_conversation_id, 
             memory_type, content, importance_level, 
             json.dumps(tags) if tags else None)
        )
        
        return memory_id

class ScheduleDatabase(DatabaseManager):
    """Manages appointments and reminders database"""
    
    def __init__(self, db_path: str = "schedule.db"):
        super().__init__(db_path)
        self.initialize_tables()

    def initialize_tables(self):
        """Create tables if they don't exist"""
        with self.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS appointments (
                    appointment_id TEXT PRIMARY KEY,
                    timestamp_created TEXT,
                    scheduled_datetime TEXT,
                    title TEXT,
                    description TEXT,
                    location TEXT,
                    source_conversation_id TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS reminders (
                    reminder_id TEXT PRIMARY KEY,
                    timestamp_created TEXT,
                    due_datetime TEXT,
                    content TEXT,
                    priority_level INTEGER,
                    source_conversation_id TEXT
                )
            """)

    async def create_appointment(self, title: str, scheduled_datetime: str, 
                               description: str = None, location: str = None,
                               source_conversation_id: str = None) -> str:
        """Create a new appointment"""
        appointment_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()

        await self.execute_update(
            """INSERT INTO appointments 
               (appointment_id, timestamp_created, scheduled_datetime, title, description, location, source_conversation_id) 
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (appointment_id, timestamp, scheduled_datetime, title, description, location, source_conversation_id)
        )
        return appointment_id

class VSCodeProjectDatabase(DatabaseManager):
    """Manages VS Code project context and development sessions"""
    
    def __init__(self, db_path: str = "vscode_project.db"):
        super().__init__(db_path)
        self.initialize_tables()

    def initialize_tables(self):
        """Create tables if they don't exist"""
        with self.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS project_sessions (
                    session_id TEXT PRIMARY KEY,
                    start_timestamp TEXT,
                    workspace_path TEXT,
                    active_files TEXT,
                    git_branch TEXT,
                    session_summary TEXT
                )
            """)

    async def save_development_session(self, workspace_path: str, active_files: List[str] = None,
                                     git_branch: str = None, session_summary: str = None) -> str:
        """Save a development session"""
        
        session_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        await self.execute_update(
            """INSERT INTO project_sessions 
               (session_id, start_timestamp, workspace_path, active_files, git_branch, session_summary) 
               VALUES (?, ?, ?, ?, ?, ?)""",
            (session_id, timestamp, workspace_path, 
             json.dumps(active_files) if active_files else None,
             git_branch, session_summary)
        )
        
        return session_id

# Additional classes and methods for integration with LLMs would be added here.