def get_current_timestamp() -> str:
    """Get current timestamp in ISO format."""
    return datetime.now().isoformat()

def parse_timestamp(timestamp: Union[str, int, float, None], fallback: Optional[datetime] = None) -> str:
    """Parse various timestamp formats into ISO format string."""
    if not timestamp:
        return fallback.isoformat() if fallback else get_current_timestamp()

    if isinstance(timestamp, (int, float)):
        return datetime.fromtimestamp(timestamp).isoformat()

    try:
        return datetime.fromisoformat(timestamp).isoformat()
    except ValueError:
        return fallback.isoformat() if fallback else get_current_timestamp()

def log_message(message: str, level: str = "INFO") -> None:
    """Log a message with a specified log level."""
    timestamp = get_current_timestamp()
    print(f"[{timestamp}] [{level}] {message}")

def generate_uuid() -> str:
    """Generate a unique identifier."""
    return str(uuid.uuid4())