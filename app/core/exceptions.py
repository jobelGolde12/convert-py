from __future__ import annotations


class AppError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(AppError):
    def __init__(self, message: str = "Not found"):
        super().__init__("NOT_FOUND", message, 404)


class UnsupportedFormatError(AppError):
    def __init__(self, message: str):
        super().__init__("UNSUPPORTED_FORMAT", message, 415)


class UnsupportedConversionError(AppError):
    def __init__(self, message: str):
        super().__init__("UNSUPPORTED_CONVERSION", message, 422)


class ConflictStateError(AppError):
    def __init__(self, message: str):
        super().__init__("CONFLICT_STATE", message, 409)


class InvalidDataError(AppError):
    def __init__(self, message: str = "Invalid data"):
        super().__init__("INVALID_DATA", message, 422)


class QuotaExceededError(AppError):
    def __init__(self, remaining: int):
        super().__init__(
            "QUOTA_EXCEEDED", f"Daily conversion limit reached ({remaining} remaining)", 402
        )


class OfficeError(Exception):
    def __init__(self, message: str, code: str = "CONVERSION_FAILED"):
        self.code = code
        super().__init__(message)
