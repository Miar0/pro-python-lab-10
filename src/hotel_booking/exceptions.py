"""Domain exception classes for the Hotel Booking system."""


class HotelBookingException(Exception):
    """Base exception for hotel booking domain errors."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class EntityNotFoundException(HotelBookingException):
    """Raised when a requested resource was not found."""

    def __init__(self, entity_name: str, identifier: str | int) -> None:
        super().__init__(
            f"{entity_name} with identifier '{identifier}' was not found.",
            status_code=404,
        )


class ConflictException(HotelBookingException):
    """Raised when an operation encounters a business conflict (e.g. double booking)."""

    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=409)


class ValidationException(HotelBookingException):
    """Raised when domain constraints or input validation rules are violated."""

    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=400)
