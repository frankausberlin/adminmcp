import pytest
from adminmcp.core.security import SecurityValidator

def test_security_validator_autonomous():
    validator = SecurityValidator(mode="autonomous")
    assert validator.validate_command("rm -rf /") is True

def test_security_validator_restricted():
    validator = SecurityValidator(mode="restricted")
    assert validator.validate_command("ls -la") is True
    assert validator.validate_command("echo hello") is True
    
    # Test blocked commands
    assert validator.validate_command("rm -rf /") is False
    assert validator.validate_command("rm -r /etc") is False
    assert validator.validate_command("mkfs.ext4 /dev/sda") is False
    assert validator.validate_command(":(){ :|:& };:") is False

def test_check_permissions():
    validator = SecurityValidator()
    assert validator.check_permissions("execute_command") is True