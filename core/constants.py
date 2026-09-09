"""EduTrack Enterprise System Constants and Enumerations."""
from django.db import models
from django.utils.translation import gettext_lazy as _

class AcademicStatus(models.TextChoices):
    ACTIVE = "ACTIVE", _("Active Enrolled")
    PROBATION = "PROBATION", _("Academic Probation")
    SUSPENDED = "SUSPENDED", _("Suspended")
    GRADUATED = "GRADUATED", _("Graduated")
    WITHDRAWN = "WITHDRAWN", _("Withdrawn")
    EXPELLED = "EXPELLED", _("Expelled")

class Gender(models.TextChoices):
    MALE = "MALE", _("Male")
    FEMALE = "FEMALE", _("Female")
    NON_BINARY = "NON_BINARY", _("Non-Binary")
    OTHER = "OTHER", _("Other")
    PREFER_NOT_TO_SAY = "PREFER_NOT_TO_SAY", _("Prefer Not To Say")

class BloodGroup(models.TextChoices):
    A_POSITIVE = "A+", _("A Positive")
    A_NEGATIVE = "A-", _("A Negative")
    B_POSITIVE = "B+", _("B Positive")
    B_NEGATIVE = "B-", _("B Negative")
    O_POSITIVE = "O+", _("O Positive")
    O_NEGATIVE = "O-", _("O Negative")
    AB_POSITIVE = "AB+", _("AB Positive")
    AB_NEGATIVE = "AB-", _("AB Negative")
    UNKNOWN = "UNKNOWN", _("Unknown")

class DegreeLevel(models.TextChoices):
    CERTIFICATE = "CERTIFICATE", _("Certificate")
    DIPLOMA = "DIPLOMA", _("Diploma")
    ASSOCIATE = "ASSOCIATE", _("Associate Degree")
    BACHELOR = "BACHELOR", _("Bachelor Degree")
    MASTER = "MASTER", _("Master Degree")
    DOCTORATE = "DOCTORATE", _("Doctorate / Ph.D.")
    POST_DOCTORAL = "POST_DOCTORAL", _("Post-Doctoral")

class AttendanceStatus(models.TextChoices):
    PRESENT = "PRESENT", _("Present")
    ABSENT = "ABSENT", _("Absent")
    LATE = "LATE", _("Late Arrival")
    HALF_DAY = "HALF_DAY", _("Half Day")
    EXCUSED = "EXCUSED", _("Excused Absence")
    MEDICAL = "MEDICAL", _("Medical Leave")

class InvoiceStatus(models.TextChoices):
    DRAFT = "DRAFT", _("Draft")
    ISSUED = "ISSUED", _("Issued / Pending Payment")
    PARTIALLY_PAID = "PARTIALLY_PAID", _("Partially Paid")
    PAID = "PAID", _("Paid in Full")
    OVERDUE = "OVERDUE", _("Overdue")
    CANCELLED = "CANCELLED", _("Cancelled")
    REFUNDED = "REFUNDED", _("Refunded")

class PaymentMethod(models.TextChoices):
    CASH = "CASH", _("Cash")
    CARD = "CARD", _("Credit / Debit Card")
    BANK_TRANSFER = "BANK_TRANSFER", _("Bank Transfer / Wire")
    ONLINE_PORTAL = "ONLINE_PORTAL", _("Online Payment Gateway")
    CHEQUE = "CHEQUE", _("Cheque")
    SCHOLARSHIP = "SCHOLARSHIP", _("Scholarship / Financial Aid")

class ExamType(models.TextChoices):
    QUIZ = "QUIZ", _("Pop Quiz")
    ASSIGNMENT = "ASSIGNMENT", _("Continuous Assessment")
    MID_TERM = "MID_TERM", _("Mid-Term Examination")
    FINAL_EXAM = "FINAL_EXAM", _("Final Semester Examination")
    PRACTICAL = "PRACTICAL", _("Laboratory / Practical Exam")
    SUPPLEMENTARY = "SUPPLEMENTARY", _("Supplementary / Retake")

class UserRoleEnum(models.TextChoices):
    SUPER_ADMIN = "SUPER_ADMIN", _("Super Administrator")
    PRINCIPAL = "PRINCIPAL", _("Principal / Executive Dean")
    DEAN = "DEAN", _("Academic Dean")
    HOD = "HOD", _("Head of Department")
    TEACHER = "TEACHER", _("Faculty Instructor / Teacher")
    STAFF = "STAFF", _("Administrative Staff")
    BURSAR = "BURSAR", _("Bursar / Financial Officer")
    LIBRARIAN = "LIBRARIAN", _("Librarian")
    STUDENT = "STUDENT", _("Enrolled Student")
    PARENT = "PARENT", _("Guardian / Parent")
