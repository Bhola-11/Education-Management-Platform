"""EduTrack Enterprise Core Exception Hierarchy."""

class EduTrackException(Exception):
    """Root exception for all domain business errors in EduTrack."""
    def __init__(self, message: str = "An institutional error occurred.", code: str = "EDUTRACK_ERROR"):
        self.message = message
        self.code = code
        super().__init__(f"[{code}] {message}")

class CapacityExceededException(EduTrackException):
    def __init__(self, message: str = "Resource capacity limit reached."):
        super().__init__(message, code="CAPACITY_EXCEEDED")

class AcademicPolicyViolation(EduTrackException):
    def __init__(self, message: str = "Action violates an institutional academic policy."):
        super().__init__(message, code="POLICY_VIOLATION")

class PrerequisiteUnfulfilledException(EduTrackException):
    def __init__(self, message: str = "Course prerequisites have not been satisfied."):
        super().__init__(message, code="PREREQUISITE_MISSING")

class FinancialHoldException(EduTrackException):
    def __init__(self, message: str = "Action blocked due to an outstanding financial hold."):
        super().__init__(message, code="FINANCIAL_HOLD")

class DuplicateEnrollmentException(EduTrackException):
    def __init__(self, message: str = "Student is already enrolled in this course session."):
        super().__init__(message, code="DUPLICATE_ENROLLMENT")

class ScheduleConflictException(EduTrackException):
    def __init__(self, message: str = "Time slot clashes with an existing room or instructor booking."):
        super().__init__(message, code="SCHEDULE_CONFLICT")

class GradeLockedException(EduTrackException):
    def __init__(self, message: str = "Finalized grades have been moderated and locked against edits."):
        super().__init__(message, code="GRADE_LOCKED")

class CertificateRevokedException(EduTrackException):
    def __init__(self, message: str = "This certificate token has been revoked."):
        super().__init__(message, code="CERTIFICATE_REVOKED")
