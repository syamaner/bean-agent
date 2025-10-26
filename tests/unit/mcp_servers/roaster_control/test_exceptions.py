"""Tests for custom exceptions."""
import pytest

from src.mcp_servers.roaster_control.exceptions import (
    RoasterError,
    RoasterNotConnectedError,
    RoasterConnectionError,
    InvalidCommandError,
    NoActiveRoastError,
    BeansNotAddedError,
)


class TestRoasterError:
    """Test base RoasterError."""
    
    def test_base_exception(self):
        """Test base RoasterError creation."""
        error = RoasterError("Test error", "TEST_ERROR")
        assert str(error) == "Test error"
        assert error.error_code == "TEST_ERROR"
    
    def test_is_exception(self):
        """Test RoasterError is an Exception."""
        error = RoasterError("Test", "TEST")
        assert isinstance(error, Exception)


class TestRoasterNotConnectedError:
    """Test RoasterNotConnectedError."""
    
    def test_not_connected_error(self):
        """Test RoasterNotConnectedError."""
        error = RoasterNotConnectedError()
        assert "not connected" in str(error).lower()
        assert error.error_code == "ROASTER_NOT_CONNECTED"
    
    def test_is_roaster_error(self):
        """Test inheritance from RoasterError."""
        error = RoasterNotConnectedError()
        assert isinstance(error, RoasterError)


class TestRoasterConnectionError:
    """Test RoasterConnectionError."""
    
    def test_connection_error_with_details(self):
        """Test connection error with details."""
        error = RoasterConnectionError("USB port not found")
        assert "USB port not found" in str(error)
        assert error.error_code == "CONNECTION_ERROR"
    
    def test_is_roaster_error(self):
        """Test inheritance from RoasterError."""
        error = RoasterConnectionError("test")
        assert isinstance(error, RoasterError)


class TestInvalidCommandError:
    """Test InvalidCommandError."""
    
    def test_invalid_command_with_reason(self):
        """Test invalid command error with reason."""
        error = InvalidCommandError("set_heat", "Value must be 0-100")
        assert "set_heat" in str(error)
        assert "Value must be 0-100" in str(error)
        assert error.error_code == "INVALID_COMMAND"
    
    def test_is_roaster_error(self):
        """Test inheritance from RoasterError."""
        error = InvalidCommandError("cmd", "reason")
        assert isinstance(error, RoasterError)


class TestNoActiveRoastError:
    """Test NoActiveRoastError."""
    
    def test_no_active_roast(self):
        """Test no active roast error."""
        error = NoActiveRoastError()
        assert "no active roast" in str(error).lower()
        assert error.error_code == "NO_ACTIVE_ROAST"
    
    def test_is_roaster_error(self):
        """Test inheritance from RoasterError."""
        error = NoActiveRoastError()
        assert isinstance(error, RoasterError)


class TestBeansNotAddedError:
    """Test BeansNotAddedError."""
    
    def test_beans_not_added(self):
        """Test beans not added error."""
        error = BeansNotAddedError()
        assert "beans not" in str(error).lower() or "t0" in str(error).lower()
        assert error.error_code == "BEANS_NOT_ADDED"
    
    def test_is_roaster_error(self):
        """Test inheritance from RoasterError."""
        error = BeansNotAddedError()
        assert isinstance(error, RoasterError)