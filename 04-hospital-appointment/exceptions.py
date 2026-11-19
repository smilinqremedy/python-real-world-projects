"""
Custom Domain Exceptions for Hospital Appointment Management System
"""

class ClinicError(Exception):
    """Base exception for clinic domain errors."""
    pass

class ValidationError(ClinicError):
    """Raised when an input value fails validation rules."""
    pass

class NotFoundError(ClinicError):
    """Raised when a requested resource (patient, doctor, appointment) is not found."""
    pass

class DoctorUnavailableError(ClinicError):
    """Raised when attempting to book an appointment slot that is already booked."""
    pass

class PatientConflictError(ClinicError):
    """Raised when a patient already has a scheduled appointment at the same date and time."""
    pass

class InvalidStatusTransitionError(ClinicError):
    """Raised when attempting an invalid status transition (e.g. rescheduling cancelled appointment)."""
    pass
