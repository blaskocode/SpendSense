"""Custom error classes for SpendSense"""


class SpendSenseError(Exception):
    """Base exception for SpendSense"""
    pass


class ValidationError(SpendSenseError):
    """Raised when data validation fails"""
    pass


class ConsentError(SpendSenseError):
    """Raised when user consent is required but not present"""
    pass


class DataError(SpendSenseError):
    """Raised when data operations fail"""
    pass


class PersonaError(SpendSenseError):
    """Raised when persona assignment fails"""
    pass

