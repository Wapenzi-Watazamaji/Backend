"""
Custom exceptions and standard response models for the BintiCare project.
"""
from typing import Any, Dict, Generic, Optional, TypeVar
from pydantic import BaseModel

T = TypeVar("T")

class ErrorDetail(BaseModel):
    code: str
    message: str
    fields: Optional[Dict[str, str]] = None

class APIResponse(BaseModel, Generic[T]):
    success: bool
    message: Optional[str] = None
    data: Optional[T] = None
    meta: Optional[Dict[str, Any]] = None
    error: Optional[ErrorDetail] = None

def create_success_response(message:Optional[str] = None, data: Any = None, meta: Optional[Dict[str, Any]] = None) -> dict:
    """Helper to generate a successful response dictionary following the standard structure."""
    return APIResponse(
        success=True,
        message=message if message is not None else "Operation successful",
        data=data if data is not None else {},
        meta=meta if meta is not None else {},
    )

class BaseAppException(Exception):
    """Base exception for all custom API exceptions"""
    def __init__(
        self, 
        status_code: int, 
        code: str, 
        message: str, 
        fields: Optional[Dict[str, str]] = None, 
        meta: Optional[Dict[str, Any]] = None
    ):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.fields = fields
        self.meta = meta
        
        self.error_dict = {
            "code": self.code,
            "message": self.message,
        }
        if self.fields:
            self.error_dict["fields"] = self.fields
            
        super().__init__(self.message)

    def to_response_dict(self) -> dict:
        return {
            "success": False,
            "data": None,
            "meta": self.meta,
            "error": self.error_dict
        }

#400 Bad Request

class ValidationError(BaseAppException):
    def __init__(self, message: str, fields: Optional[Dict[str, str]] = None, meta: Optional[Dict[str, Any]] = None):
        super().__init__(status_code=400, code="VALIDATION_ERROR", message=message, fields=fields, meta=meta)

class TemplateValidationError(BaseAppException):
    def __init__(self, message: str, fields: Optional[Dict[str, str]] = None, meta: Optional[Dict[str, Any]] = None):
        super().__init__(status_code=400, code="TEMPLATE_VALIDATION_ERROR", message=message, fields=fields, meta=meta)

class NoPreferredFacilityError(BaseAppException):
    def __init__(self, message: str, meta: Optional[Dict[str, Any]] = None):
        super().__init__(status_code=400, code="NO_PREFERRED_FACILITY", message=message, meta=meta)

#401 Unauthorized

class UnauthorizedError(BaseAppException):
    def __init__(self, message: str, meta: Optional[Dict[str, Any]] = None):
        super().__init__(status_code=401, code="UNAUTHORIZED", message=message, meta=meta)

class InvalidCredentialsError(BaseAppException):
    def __init__(self, message: str, meta: Optional[Dict[str, Any]] = None):
        super().__init__(status_code=401, code="INVALID_CREDENTIALS", message=message, meta=meta)

class InvalidRefreshTokenError(BaseAppException):
    def __init__(self, message: str, meta: Optional[Dict[str, Any]] = None):
        super().__init__(status_code=401, code="INVALID_REFRESH_TOKEN", message=message, meta=meta)

class RefreshTokenExpiredError(BaseAppException):
    def __init__(self, message: str, meta: Optional[Dict[str, Any]] = None):
        super().__init__(status_code=401, code="REFRESH_TOKEN_EXPIRED", message=message, meta=meta)

#403 Forbidden

class ForbiddenError(BaseAppException):
    def __init__(self, message: str, meta: Optional[Dict[str, Any]] = None):
        super().__init__(status_code=403, code="FORBIDDEN", message=message, meta=meta)

class ConsentRequiredError(BaseAppException):
    def __init__(self, message: str, meta: Optional[Dict[str, Any]] = None):
        super().__init__(status_code=403, code="CONSENT_REQUIRED", message=message, meta=meta)

#404 Not Found

class NotFoundError(BaseAppException):
    def __init__(self, message: str, meta: Optional[Dict[str, Any]] = None):
        super().__init__(status_code=404, code="NOT_FOUND", message=message, meta=meta)

class NoActivePregnancyError(BaseAppException):
    def __init__(self, message: str, meta: Optional[Dict[str, Any]] = None):
        super().__init__(status_code=404, code="NO_ACTIVE_PREGNANCY", message=message, meta=meta)

class QrTokenNotFoundError(BaseAppException):
    def __init__(self, message: str, meta: Optional[Dict[str, Any]] = None):
        super().__init__(status_code=404, code="QR_TOKEN_NOT_FOUND", message=message, meta=meta)

#409 Conflict

class PhoneAlreadyRegisteredError(BaseAppException):
    def __init__(self, message: str, fields: Optional[Dict[str, str]] = None, meta: Optional[Dict[str, Any]] = None):
        super().__init__(status_code=409, code="PHONE_ALREADY_REGISTERED", message=message, fields=fields, meta=meta)

class ActivePregnancyExistsError(BaseAppException):
    def __init__(self, message: str, meta: Optional[Dict[str, Any]] = None):
        super().__init__(status_code=409, code="ACTIVE_PREGNANCY_EXISTS", message=message, meta=meta)

#410 Gone

class QrTokenExpiredError(BaseAppException):
    def __init__(self, message: str, meta: Optional[Dict[str, Any]] = None):
        super().__init__(status_code=410, code="QR_TOKEN_EXPIRED", message=message, meta=meta)

class OtpExpiredError(BaseAppException):
    def __init__(self, message: str, meta: Optional[Dict[str, Any]] = None):
        super().__init__(status_code=410, code="OTP_EXPIRED", message=message, meta=meta)

#423 Locked

class AccountLockedError(BaseAppException):
    def __init__(self, message: str, meta: Optional[Dict[str, Any]] = None):
        super().__init__(status_code=423, code="ACCOUNT_LOCKED", message=message, meta=meta)

#429 Too Many Requests

class RateLimitedError(BaseAppException):
    def __init__(self, message: str, meta: Optional[Dict[str, Any]] = None):
        super().__init__(status_code=429, code="RATE_LIMITED", message=message, meta=meta)

#500 Internal Server Error

class InternalServerError(BaseAppException):
    def __init__(self, message: str, meta: Optional[Dict[str, Any]] = None):
        super().__init__(status_code=500, code="INTERNAL_ERROR", message=message, meta=meta)

class DuplicateResourceError(BaseAppException):
    def __init__(self, message: str, meta: Optional[Dict[str, Any]] = None):
        super().__init__(status_code=409, code="DUPLICATE_RESOURCE", message=message, meta=meta)