# accounts/exceptions.py
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger('accounts.errors')

def custom_exception_handler(exc, context):
    """
    Custom exception handler with enhanced error logging and user-friendly responses
    """
    response = exception_handler(exc, context)
    
    if response is not None:
        # Log the error
        request = context.get('request')
        user_info = 'Anonymous'
        
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            user_info = f"{request.user.email} ({request.user.role})"
        
        logger.error(
            f"API_ERROR: {exc.__class__.__name__} | "
            f"Status: {response.status_code} | "
            f"User: {user_info} | "
            f"Path: {request.path if request else 'Unknown'} | "
            f"Error: {str(exc)}"
        )
        
        # Customize error response format
        custom_response_data = {
            'success': False,
            'error': {
                'code': response.status_code,
                'message': get_user_friendly_message(exc, response.status_code),
                'details': response.data if isinstance(response.data, dict) else {'detail': response.data},
                'timestamp': context.get('request').META.get('HTTP_X_REQUEST_ID') if context.get('request') else None
            }
        }
        
        response.data = custom_response_data
    
    return response


def get_user_friendly_message(exc, status_code):
    """
    Generate user-friendly error messages
    """
    error_messages = {
        400: "The request contains invalid data. Please check your input and try again.",
        401: "Authentication required. Please log in to access this resource.",
        403: "You don't have permission to perform this action.",
        404: "The requested resource was not found.",
        405: "This action is not allowed for this resource.",
        409: "This request conflicts with current resource state.",
        422: "The request data is invalid or incomplete.",
        429: "Too many requests. Please wait before trying again.",
        500: "An internal error occurred. Our team has been notified.",
        502: "Service temporarily unavailable. Please try again later.",
        503: "Service temporarily unavailable due to maintenance."
    }
    
    # Check for specific exception types
    if hasattr(exc, 'detail'):
        if 'already exists' in str(exc.detail).lower():
            return "This information already exists in our system."
        elif 'not found' in str(exc.detail).lower():
            return "The requested information was not found."
        elif 'invalid' in str(exc.detail).lower():
            return "The provided information is invalid."
    
    return error_messages.get(status_code, "An error occurred while processing your request.")


class AccountsAPIException(Exception):
    """
    Base exception class for accounts app
    """
    default_message = "An error occurred"
    status_code = status.HTTP_400_BAD_REQUEST
    
    def __init__(self, message=None, status_code=None):
        self.message = message or self.default_message
        self.status_code = status_code or self.status_code
        super().__init__(self.message)


class InvalidCredentialsException(AccountsAPIException):
    default_message = "Invalid email or password"
    status_code = status.HTTP_401_UNAUTHORIZED


class EmailNotVerifiedException(AccountsAPIException):
    default_message = "Email address is not verified"
    status_code = status.HTTP_403_FORBIDDEN


class OTPExpiredException(AccountsAPIException):
    default_message = "OTP has expired. Please request a new one"
    status_code = status.HTTP_400_BAD_REQUEST


class OTPMaxAttemptsException(AccountsAPIException):
    default_message = "Maximum OTP verification attempts exceeded"
    status_code = status.HTTP_429_TOO_MANY_REQUESTS


class UserAlreadyExistsException(AccountsAPIException):
    default_message = "User with this email already exists"
    status_code = status.HTTP_409_CONFLICT


class SupplierRequestException(AccountsAPIException):
    default_message = "Error processing supplier request"
    status_code = status.HTTP_400_BAD_REQUEST


class SocialAuthException(AccountsAPIException):
    default_message = "Social authentication failed"
    status_code = status.HTTP_400_BAD_REQUEST