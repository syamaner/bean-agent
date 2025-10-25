"""Custom exceptions for roaster control."""


class RoasterError(Exception):
    """Base exception for roaster control."""
    
    def __init__(self, message: str, error_code: str):
        super().__init__(message)
        self.error_code = error_code


class RoasterNotConnectedError(RoasterError):
    """Raised when roaster is not connected."""
    
    def __init__(self):
        super().__init__(
            "Roaster not connected",
            "ROASTER_NOT_CONNECTED"
        )


class RoasterConnectionError(RoasterError):
    """Raised when connection to roaster fails."""
    
    def __init__(self, details: str):
        super().__init__(
            f"Connection failed: {details}",
            "CONNECTION_ERROR"
        )


class InvalidCommandError(RoasterError):
    """Raised when invalid command issued."""
    
    def __init__(self, command: str, reason: str):
        super().__init__(
            f"Invalid command '{command}': {reason}",
            "INVALID_COMMAND"
        )


class NoActiveRoastError(RoasterError):
    """Raised when operation requires active roast but none exists."""
    
    def __init__(self):
        super().__init__(
            "No active roast session",
            "NO_ACTIVE_ROAST"
        )


class BeansNotAddedError(RoasterError):
    """Raised when operation requires beans added but T0 not detected."""
    
    def __init__(self):
        super().__init__(
            "Beans not yet added (T0 not detected)",
            "BEANS_NOT_ADDED"
        )