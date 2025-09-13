"""
1, success_count = success_count + ?, failure_count = failure_count + ?
                   WHERE tool_name = ? AND date = ?""",
                (1 if status == "success" else 0, tool_name, today)
            )
        else:
            await self.execute_update(
                """INSERT INTO tool_usage_stats (tool_name, date, call_count, success_count, failure_count) 
                   VALUES (?, ?, ?, ?, ?)""",
                (tool_name, today, 1, 1 if status == "success" else 0, 0 if status == "success" else 1)
            )
    
    async def get_tool_usage_summary(self, days: int = 7) -> Dict:
        """Get tool usage summary for the last N days"""
        
        recent_calls = await self.execute_query(
            """SELECT tool_name, status, COUNT(*) as count
               FROM tool_calls 
               WHERE timestamp >= datetime('now', '-{} days')
               GROUP BY tool_name, status
               ORDER BY count DESC""".format(days)
        )
        
        daily_stats = await self.execute_query(
            """SELECT * FROM tool_usage_stats 
               WHERE date >= date('now', '-{} days')
               ORDER BY date DESC, call_count DESC""".format(days)
        )
        
        most_used = await self.execute_query(
            """SELECT tool_name, COUNT(*) as total_calls
               FROM tool_calls 
               WHERE timestamp >= datetime('now', '-{} days')
               GROUP BY tool_name
               ORDER BY total_calls DESC
               LIMIT 10""".format(days)
        )
        
        return {
            "recent_calls": [dict(row) for row in recent_calls],
            "daily_stats": [dict(row) for row in daily_stats],
            "most_used_tools": [dict(row) for row in most_used],
            "period_days": days
        }
    
    async def get_tool_call_history(self, tool_name: str = None, limit: int = 50) -> List[Dict]:
        """Get recent tool call history, optionally filtered by tool name"""
        
        if tool_name:
            query = "SELECT * FROM tool_calls WHERE tool_name = ? ORDER BY timestamp DESC LIMIT ?"
            params = (tool_name, limit)
        else:
            query = "SELECT * FROM tool_calls ORDER BY timestamp DESC LIMIT ?"
            params = (limit,)
        
        rows = await self.execute_query(query, params)
        return [dict(row) for row in rows]

class ConversationDatabase(DatabaseManager):
    """Manages conversation auto-save database"""
    
    def __init__(self, db_path: str = "conversations.db"):
        super().__init__(db_path)
        self.initialize_tables()

    def initialize_tables(self):
        """Create tables if they don't exist, and migrate schema if columns are missing"""
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
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    conversation_id TEXT PRIMARY KEY,
                    timestamp_created TEXT,
                    title TEXT
                )
            """)

    async def store_message(self, content: str, role: str, session_id: str = None, 
                          conversation_id: str = None, metadata: Dict = None) -> Dict[str, str]:
        """Store a message and auto-manage sessions/conversations with duplicate detection"""
        timestamp = get_current_timestamp()
        message_id = str(uuid.uuid4())

        # Advanced duplicate detection: check for existing message with same content, role, and session in last hour
        if session_id:
            existing = await self.execute_query(
                """SELECT message_id FROM messages 
                   WHERE content = ? AND role = ? AND session_id = ? 
                   AND timestamp >= datetime('now', '-1 hour')""",
                (content, role, session_id)
            )
            if existing:
                return {"message_id": existing[0]["message_id"], "duplicate": True}

        # Auto-create session if not provided or doesn't exist
        if not session_id:
            session_id = str(uuid.uuid4())

        # Auto-create conversation if not provided
        if not conversation_id:
            conversation_id = str(uuid.uuid4())

        # Store the message
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
            "session_id": session_id,
            "duplicate": False
        }
    
    async def get_recent_messages(self, limit: int = 10, session_id: str = None) -> List[Dict]:
        """Get recent messages, optionally filtered by session"""
        
        if session_id:
            query = "SELECT * FROM messages WHERE session_id = ? ORDER BY timestamp DESC LIMIT ?"
            params = (session_id, limit)
        else:
            query = "SELECT * FROM messages ORDER BY timestamp DESC LIMIT ?"
            params = (limit,)
        
        rows = await self.execute_query(query, params)
        return [dict(row) for row in rows]

class AIMemoryDatabase(DatabaseManager):
    """Manages AI-curated memories database with enhanced operations"""
    
    def __init__(self, db_path: str = "ai_memories.db"):
        super().__init__(db_path)
        self.initialize_tables()

    def initialize_tables(self):
        """Create tables if they don't exist, and migrate schema if columns are missing"""
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
        """Create a new curated memory with duplicate detection"""
        memory_id = str(uuid.uuid4())
        timestamp = get_current_timestamp()

        # Advanced duplicate detection: check for existing memory with same content, type, and source
        existing = await self.execute_query(
            """SELECT memory_id FROM curated_memories 
                   WHERE content = ? AND memory_type = ? AND source_conversation_id IS ?""",
            (content, memory_type, source_conversation_id)
        )
        if existing:
            return existing[0]["memory_id"]

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
        """Create tables if they don't exist, and migrate schema if columns are missing"""
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
                    source_conversation_id TEXT,
                    completed INTEGER DEFAULT 0
                )
            """)

    async def create_appointment(self, title: str, scheduled_datetime: str, 
                               description: str = None, location: str = None,
                               source_conversation_id: str = None) -> str:
        """Create a new appointment with duplicate detection"""
        appointment_id = str(uuid.uuid4())
        timestamp = get_current_timestamp()

        # Duplicate detection: check for existing appointment with same title, datetime, location, and source
        existing = await self.execute_query(
            """SELECT appointment_id FROM appointments 
                   WHERE title = ? AND scheduled_datetime = ? AND location IS ? AND source_conversation_id IS ?""",
            (title, scheduled_datetime, location, source_conversation_id)
        )
        if existing:
            return existing[0]["appointment_id"]

        await self.execute_update(
            """INSERT INTO appointments 
               (appointment_id, timestamp_created, scheduled_datetime, title, description, location, source_conversation_id) 
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (appointment_id, timestamp, scheduled_datetime, title, description, location, source_conversation_id)
        )
        return appointment_id
    
    async def create_reminder(self, content: str, due_datetime: str, 
                            priority_level: int = 5, source_conversation_id: str = None) -> str:
        """Create a new reminder with duplicate detection"""
        reminder_id = str(uuid.uuid4())
        timestamp = get_current_timestamp()

        # Duplicate detection: check for existing reminder with same content, due_datetime, and source
        existing = await self.execute_query(
            """SELECT reminder_id FROM reminders 
                   WHERE content = ? AND due_datetime = ? AND source_conversation_id IS ?""",
            (content, due_datetime, source_conversation_id)
        )
        if existing:
            return existing[0]["reminder_id"]

        await self.execute_update(
            """INSERT INTO reminders 
               (reminder_id, timestamp_created, due_datetime, content, priority_level, source_conversation_id) 
               VALUES (?, ?, ?, ?, ?, ?)""",
            (reminder_id, timestamp, due_datetime, content, priority_level, source_conversation_id)
        )
        return reminder_id
    
    async def get_upcoming_appointments(self, days_ahead: int = 7) -> List[Dict]:
        """Get upcoming appointments within specified days"""
        
        future_date = datetime.now(get_local_timezone()) + timedelta(days=days_ahead)
        
        rows = await self.execute_query(
            """SELECT * FROM appointments 
               WHERE scheduled_datetime >= ? AND scheduled_datetime <= ?
               ORDER BY scheduled_datetime ASC""",
            (get_current_timestamp(), future_date.isoformat())
        )
        
        return [dict(row) for row in rows]
    
    async def get_active_reminders(self) -> List[Dict]:
        """Get all uncompleted reminders"""
        
        rows = await self.execute_query(
            "SELECT * FROM reminders WHERE completed = 0 ORDER BY due_datetime ASC"
        )
        
        return [dict(row) for row in rows]

class VSCodeProjectDatabase(DatabaseManager):
    """Manages VS Code project context and development sessions"""
    
    def __init__(self, db_path: str = "vscode_project.db"):
        super().__init__(db_path)
        self.initialize_tables()

    def initialize_tables(self):
        """Create tables if they don't exist, and migrate schema if columns are missing"""
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
            conn.execute("""
                CREATE TABLE IF NOT EXISTS development_conversations (
                    conversation_id TEXT PRIMARY KEY,
                    session_id TEXT,
                    timestamp TEXT,
                    chat_context_id TEXT,
                    conversation_content TEXT,
                    decisions_made TEXT,
                    code_changes TEXT
                )
            """)

    async def save_development_session(self, workspace_path: str, active_files: List[str] = None,
                                     git_branch: str = None, session_summary: str = None) -> str:
        """Save a development session"""
        
        session_id = str(uuid.uuid4())
        timestamp = get_current_timestamp()
        
        await self.execute_update(
            """INSERT INTO project_sessions 
               (session_id, start_timestamp, workspace_path, active_files, git_branch, session_summary) 
               VALUES (?, ?, ?, ?, ?, ?)""",
            (session_id, timestamp, workspace_path, 
             json.dumps(active_files) if active_files else None,
             git_branch, session_summary)
        )
        
        return session_id
    
    async def store_development_conversation(self, content: str, session_id: str = None,
                                          chat_context_id: str = None, decisions_made: str = None,
                                          code_changes: Dict = None) -> str:
        """Store a development conversation from VS Code"""
        conversation_id = str(uuid.uuid4())
        timestamp = get_current_timestamp()
        
        # Create session if none provided
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Store conversation
        await self.execute_update(
            """INSERT INTO development_conversations 
               (conversation_id, session_id, timestamp, chat_context_id,
                conversation_content, decisions_made, code_changes)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (conversation_id, session_id, timestamp, chat_context_id,
             content, decisions_made, json.dumps(code_changes) if code_changes else None)
        )
        
        return conversation_id

    async def store_project_insight(self, content: str, insight_type: str = None,
                                  related_files: List[str] = None, importance_level: int = 5,
                                  source_conversation_id: str = None) -> str:
        """Store a project insight with duplicate detection"""
        insight_id = str(uuid.uuid4())
        timestamp = get_current_timestamp()

        # Duplicate detection: check for existing insight with same content, type, and source
        existing = await self.execute_query(
            """SELECT insight_id FROM project_insights 
                   WHERE content = ? AND insight_type IS ? AND source_conversation_id IS ?""",
            (content, insight_type, source_conversation_id)
        )
        if existing:
            return existing[0]["insight_id"]

        await self.execute_update(
            """INSERT INTO project_insights 
               (insight_id, timestamp_created, timestamp_updated, insight_type, content, 
                related_files, source_conversation_id, importance_level) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (insight_id, timestamp, timestamp, insight_type, content,
             json.dumps(related_files) if related_files else None,
             source_conversation_id, importance_level)
        )
        return insight_id

class ConversationFileMonitor:
    def __init__(self, memory_system, watch_directories):
        self.memory_system = memory_system
        self.watch_directories = watch_directories
        self.vscode_db = memory_system.vscode_db
        self.conversations_db = memory_system.conversations_db
        self.curated_db = memory_system.curated_db

    def _parse_character_ai_format(self, data: Dict) -> List[Dict]:
        """Parse Character.ai conversation format"""
        conversations = []
        try:
            # Parsing logic here
        except Exception as e:
            logger.error(f"Error parsing Character.ai format: {e}")
        return conversations

    def _parse_text_gen_format(self, data: Dict) -> List[Dict]:
        """Parse text-generation-webui format"""
        conversations = []
        try:
            # Parsing logic here
        except Exception as e:
            logger.error(f"Error parsing text-gen format: {e}")
        return conversations

class PersistentAIMemorySystem:
    """Main memory system that coordinates all databases and operations"""
    
    def __init__(self, data_dir: str = "memory_data", enable_file_monitoring: bool = True, 
                 watch_directories: List[str] = None):
        self.data_dir = data_dir
        self.enable_file_monitoring = enable_file_monitoring
        self.watch_directories = watch_directories or []
        self.conversations_db = ConversationDatabase(f"{data_dir}/conversations.db")
        self.ai_memory_db = AIMemoryDatabase(f"{data_dir}/ai_memories.db")
        self.schedule_db = ScheduleDatabase(f"{data_dir}/schedule.db")
        self.vscode_db = VSCodeProjectDatabase(f"{data_dir}/vscode_project.db")
        self.mcp_tool_call_db = MCPToolCallDatabase(f"{data_dir}/mcp_tool_calls.db")

    async def start_file_monitoring(self):
        """Start monitoring conversation files"""
        if not self.watch_directories:
            logger.warning("No directories to monitor.")
            return
        # Monitoring logic here

    async def stop_file_monitoring(self):
        """Stop monitoring conversation files"""
        # Stopping logic here

    async def create_memory(self, content: str, memory_type: str = None,
                          importance_level: int = 5, tags: List[str] = None,
                          source_conversation_id: str = None) -> Dict:
        """Create a new memory"""
        return await self.ai_memory_db.create_memory(content, memory_type, importance_level, tags, source_conversation_id)

    async def store_conversation(self, content: str, role: str, session_id: str = None,
                               conversation_id: str = None, metadata: Dict = None) -> Dict:
        """Store a conversation"""
        return await self.conversations_db.store_message(content, role, session_id, conversation_id, metadata)

    async def create_appointment(self, title: str, scheduled_datetime: str,
                               description: str = None, location: str = None,
                               source_conversation_id: str = None) -> Dict:
        """Create a new appointment"""
        return await self.schedule_db.create_appointment(title, scheduled_datetime, description, location, source_conversation_id)

    async def create_reminder(self, content: str, due_datetime: str,
                            priority_level: int = 5, source_conversation_id: str = None) -> Dict:
        """Create a new reminder"""
        return await self.schedule_db.create_reminder(content, due_datetime, priority_level, source_conversation_id)

async def main():
    """Main entry point for the memory system"""
    memory = PersistentAIMemorySystem()
    logger.info("Persistent AI Memory System initialized.")
    # Example usage
    health = await memory.get_system_health()
    logger.info(f"System Status: {health['status']}")
    # More example usage...

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
"""