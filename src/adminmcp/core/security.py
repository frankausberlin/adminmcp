import re
from typing import List, Optional

class SecurityValidator:
    """
    Validates commands and enforces security rules.
    """
    
    # Dangerous patterns that should be blocked in restricted mode
    BLOCKED_PATTERNS = [
        r"rm\s+-[rf]+.*\/",  # Recursive delete of root or dangerous paths
        r":\(\)\s*{\s*:\s*\|\s*:\s*&\s*};\s*:",  # Fork bomb
        r"mkfs",  # Formatting filesystems
        r"dd\s+if=",  # Low-level data copying
        r">\s*/dev/sd[a-z]",  # Writing directly to devices
    ]

    def __init__(self, mode: str = "restricted"):
        self.mode = mode
        self._compiled_patterns = [re.compile(p) for p in self.BLOCKED_PATTERNS]

    def validate_command(self, command: str) -> bool:
        """
        Validate if a command is safe to execute.
        Returns True if safe, False otherwise.
        """
        if self.mode == "autonomous":
            return True
            
        # Check against blocked patterns
        for pattern in self._compiled_patterns:
            if pattern.search(command):
                return False
                
        return True

    def check_permissions(self, tool_name: str) -> bool:
        """
        Check if the current mode allows execution of the given tool.
        """
        # For now, all tools are allowed in all modes, 
        # but this is where we'd restrict specific tools.
        return True