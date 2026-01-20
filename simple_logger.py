"""Simple logger replacement for loguru using print statements."""

class SimpleLogger:
    """A simple logger class that mimics loguru API."""
    
    def info(self, message):
        print(f"INFO: {message}")
    
    def error(self, message):
        print(f"ERROR: {message}")
    
    def warning(self, message):
        print(f"WARNING: {message}")
    
    def debug(self, message):
        print(f"DEBUG: {message}")
    
    def success(self, message):
        print(f"SUCCESS: {message}")
    
    def exception(self, message):
        print(f"EXCEPTION: {message}")
    
    def critical(self, message):
        print(f"CRITICAL: {message}")
    
    def trace(self, message):
        print(f"TRACE: {message}")

# Create a global logger instance
logger = SimpleLogger()
