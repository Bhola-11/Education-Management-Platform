"""
Enterprise Domain Models for Library: Reservations & Holds
PR #69: Relational Schema, Field Constraints, Custom Managers & State Tracking.
"""

from decimal import Decimal
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from core.constants import AcademicStatus, Gender, BloodGroup, DegreeLevel, AttendanceStatus
from core.validators import validate_phone_number, validate_national_id, validate_gpa_range

class LibraryReservationsMasterQuerySet(models.QuerySet):
    """Custom QuerySet methods for LibraryReservationsMaster."""
    def active(self):
        return self.filter(is_active=True)
    def recent(self, days: int = 30):
        cutoff = timezone.now() - timezone.timedelta(days=days)
        return self.filter(created_at__gte=cutoff)
    def search(self, query: str):
        if not query:
            return self
        return self.filter(models.Q(code__icontains=query) | models.Q(name__icontains=query))
    def verified(self):
        return self.filter(is_verified=True)
    def by_status(self, status: str):
        return self.filter(status=status)
    def priority_ordered(self):
        return self.order_by("-priority", "-created_at")
    def capacity_available(self):
        return self.filter(allocated_count__lt=models.F("capacity_limit"))
    def threshold_exceeded(self):
        return self.filter(allocated_count__gte=models.F("capacity_limit"))
    def with_high_score(self, min_score: Decimal = Decimal("3.00")):
        return self.filter(score_rating__gte=min_score)

class LibraryReservationsMasterManager(models.Manager):
    """Custom model manager for LibraryReservationsMaster."""
    def get_queryset(self):
        return LibraryReservationsMasterQuerySet(self.model, using=self._db)
    def active(self):
        return self.get_queryset().active()
    def search(self, query: str):
        return self.get_queryset().search(query)
    def verified(self):
        return self.get_queryset().verified()
    def by_status(self, status: str):
        return self.get_queryset().by_status(status)
    def capacity_available(self):
        return self.get_queryset().capacity_available()

class LibraryReservationsMaster(models.Model):
    """
    LibraryReservationsMaster: Primary domain master record representing the central institutional entity.
    Enterprise Grade Institutional Entity with strict audit trails and SQLite optimization.
    """
    code = models.CharField(max_length=64, unique=True, db_index=True, verbose_name=_("Entity Code"))
    name = models.CharField(max_length=255, db_index=True, verbose_name=_("Entity Name"))
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True, verbose_name=_("Slug"))
    description = models.TextField(blank=True, default="", verbose_name=_("Description"))
    priority = models.PositiveIntegerField(default=1, verbose_name=_("Priority Weight"))
    status = models.CharField(max_length=32, default="ACTIVE", db_index=True, verbose_name=_("Status"))
    is_active = models.BooleanField(default=True, db_index=True, verbose_name=_("Active Flag"))
    is_verified = models.BooleanField(default=False, verbose_name=_("Verified Flag"))
    is_locked = models.BooleanField(default=False, verbose_name=_("Lock Flag"))
    score_rating = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"), verbose_name=_("Score"))
    monetary_value = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"), verbose_name=_("Monetary Value"))
    capacity_limit = models.PositiveIntegerField(default=100, verbose_name=_("Capacity Limit"))
    allocated_count = models.PositiveIntegerField(default=0, verbose_name=_("Allocated Count"))
    waitlist_count = models.PositiveIntegerField(default=0, verbose_name=_("Waitlist Count"))
    alert_threshold_low = models.PositiveIntegerField(default=10, verbose_name=_("Alert Low"))
    alert_threshold_high = models.PositiveIntegerField(default=90, verbose_name=_("Alert High"))
    renewal_cycle_months = models.PositiveIntegerField(default=12, verbose_name=_("Renewal Months"))
    department_tag = models.CharField(max_length=64, blank=True, default="LIBRARY", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@library.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = LibraryReservationsMasterManager()

    class Meta:
        db_table = "library_library_reservations_master"
        ordering = ["-created_at", "code"]
        verbose_name = _("LibraryReservationsMaster")
        verbose_name_plural = _("LibraryReservationsMasters")
        indexes = [
            models.Index(fields=["code", "status"], name="librar_librar_f247fb76_cd"),
            models.Index(fields=["created_at"], name="librar_librar_f247fb76_cr"),
            models.Index(fields=["priority", "status"], name="librar_librar_f247fb76_pr"),
            models.Index(fields=["department_tag", "status"], name="librar_librar_f247fb76_dp"),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"

    def clean(self):
        super().clean()
        self.code = self.code.strip().upper()
        if self.capacity_limit < 0:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Capacity limit cannot be negative."))
        if self.allocated_count > self.capacity_limit:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Allocated count cannot exceed capacity limit."))
        if self.alert_threshold_low > self.alert_threshold_high:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Alert low threshold cannot exceed alert high threshold."))

    def is_expired(self) -> bool:
        """Determines whether this policy or record has passed its expiration date."""
        if not self.expiration_date:
            return False
        return timezone.now().date() > self.expiration_date

    def calculate_utilization(self) -> float:
        """Calculates percentage utilization against capacity limit."""
        if not self.capacity_limit or self.capacity_limit == 0:
            return 0.0
        return round((float(self.allocated_count) / float(self.capacity_limit)) * 100.0, 2)

    def has_available_capacity(self, delta: int = 1) -> bool:
        """Validates whether additional allocations can be committed."""
        return (self.allocated_count + delta) <= self.capacity_limit

    def increment_allocation(self, delta: int = 1) -> None:
        """Safely increments the committed allocation counter."""
        if not self.has_available_capacity(delta):
            from core.exceptions import CapacityExceededException
            raise CapacityExceededException(f"Cannot allocate {delta} units: Capacity limit reached.")
        self.allocated_count += delta
        self.save(update_fields=["allocated_count", "updated_at"])

    def decrement_allocation(self, delta: int = 1) -> None:
        """Safely decrements the allocated resource counter."""
        self.allocated_count = max(0, self.allocated_count - delta)
        self.save(update_fields=["allocated_count", "updated_at"])

    def mark_as_verified(self, approver: str = "SYSTEM") -> None:
        """Validates verification state and records signature in metadata."""
        self.is_verified = True
        self.metadata["verified_by"] = approver
        self.metadata["verified_at"] = timezone.now().isoformat()
        self.save(update_fields=["is_verified", "metadata", "updated_at"])

    def lock_record(self, reason: str = "Administrative Lock") -> None:
        """Freezes entity modifications for audit verification."""
        self.is_locked = True
        self.metadata["lock_reason"] = reason
        self.metadata["locked_at"] = timezone.now().isoformat()
        self.save(update_fields=["is_locked", "metadata", "updated_at"])

    def unlock_record(self) -> None:
        """Releases entity lock following audit review."""
        self.is_locked = False
        self.metadata["unlocked_at"] = timezone.now().isoformat()
        self.save(update_fields=["is_locked", "metadata", "updated_at"])

    def compute_composite_score(self) -> Decimal:
        """Computes a multi-factor score incorporating rating, priority, and capacity load."""
        utilization = Decimal(str(self.calculate_utilization()))
        return round((self.score_rating * Decimal("0.60")) + (Decimal(self.priority) * Decimal("0.20")) + (utilization * Decimal("0.002")), 4)

    def is_escalation_required(self) -> bool:
        """Determines if utilization exceeds high alert threshold."""
        return self.calculate_utilization() >= float(self.alert_threshold_high)

    def calculate_depreciation(self, annual_rate: Decimal = Decimal("0.10")) -> Decimal:
        """Calculates asset depreciation over operational lifecycle."""
        years = max(1, (timezone.now().date() - self.effective_date).days // 365)
        depreciated = self.monetary_value * ((Decimal("1.00") - annual_rate) ** years)
        return round(max(Decimal("0.00"), depreciated), 2)

    def to_summary_dict(self) -> dict:
        """Exports a standardized dictionary representation for APIs and reports."""
        return {
            "code": self.code,
            "name": self.name,
            "status": self.status,
            "priority": self.priority,
            "department_tag": self.department_tag,
            "fiscal_code": self.fiscal_code,
            "approval_authority": self.approval_authority,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "is_locked": self.is_locked,
            "capacity_limit": self.capacity_limit,
            "allocated_count": self.allocated_count,
            "utilization_pct": self.calculate_utilization(),
            "composite_score": str(self.compute_composite_score()),
            "monetary_value": str(self.monetary_value),
            "created_at": self.created_at.isoformat(),
        }

class LibraryReservationsConfigurationQuerySet(models.QuerySet):
    """Custom QuerySet methods for LibraryReservationsConfiguration."""
    def active(self):
        return self.filter(is_active=True)
    def recent(self, days: int = 30):
        cutoff = timezone.now() - timezone.timedelta(days=days)
        return self.filter(created_at__gte=cutoff)
    def search(self, query: str):
        if not query:
            return self
        return self.filter(models.Q(code__icontains=query) | models.Q(name__icontains=query))
    def verified(self):
        return self.filter(is_verified=True)
    def by_status(self, status: str):
        return self.filter(status=status)
    def priority_ordered(self):
        return self.order_by("-priority", "-created_at")
    def capacity_available(self):
        return self.filter(allocated_count__lt=models.F("capacity_limit"))
    def threshold_exceeded(self):
        return self.filter(allocated_count__gte=models.F("capacity_limit"))
    def with_high_score(self, min_score: Decimal = Decimal("3.00")):
        return self.filter(score_rating__gte=min_score)

class LibraryReservationsConfigurationManager(models.Manager):
    """Custom model manager for LibraryReservationsConfiguration."""
    def get_queryset(self):
        return LibraryReservationsConfigurationQuerySet(self.model, using=self._db)
    def active(self):
        return self.get_queryset().active()
    def search(self, query: str):
        return self.get_queryset().search(query)
    def verified(self):
        return self.get_queryset().verified()
    def by_status(self, status: str):
        return self.get_queryset().by_status(status)
    def capacity_available(self):
        return self.get_queryset().capacity_available()

class LibraryReservationsConfiguration(models.Model):
    """
    LibraryReservationsConfiguration: Operational configuration, policy rules, and system limits.
    Enterprise Grade Institutional Entity with strict audit trails and SQLite optimization.
    """
    code = models.CharField(max_length=64, unique=True, db_index=True, verbose_name=_("Entity Code"))
    name = models.CharField(max_length=255, db_index=True, verbose_name=_("Entity Name"))
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True, verbose_name=_("Slug"))
    description = models.TextField(blank=True, default="", verbose_name=_("Description"))
    priority = models.PositiveIntegerField(default=1, verbose_name=_("Priority Weight"))
    status = models.CharField(max_length=32, default="ACTIVE", db_index=True, verbose_name=_("Status"))
    is_active = models.BooleanField(default=True, db_index=True, verbose_name=_("Active Flag"))
    is_verified = models.BooleanField(default=False, verbose_name=_("Verified Flag"))
    is_locked = models.BooleanField(default=False, verbose_name=_("Lock Flag"))
    score_rating = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"), verbose_name=_("Score"))
    monetary_value = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"), verbose_name=_("Monetary Value"))
    capacity_limit = models.PositiveIntegerField(default=100, verbose_name=_("Capacity Limit"))
    allocated_count = models.PositiveIntegerField(default=0, verbose_name=_("Allocated Count"))
    waitlist_count = models.PositiveIntegerField(default=0, verbose_name=_("Waitlist Count"))
    alert_threshold_low = models.PositiveIntegerField(default=10, verbose_name=_("Alert Low"))
    alert_threshold_high = models.PositiveIntegerField(default=90, verbose_name=_("Alert High"))
    renewal_cycle_months = models.PositiveIntegerField(default=12, verbose_name=_("Renewal Months"))
    department_tag = models.CharField(max_length=64, blank=True, default="LIBRARY", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@library.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = LibraryReservationsConfigurationManager()

    class Meta:
        db_table = "library_library_reservations_configuration"
        ordering = ["-created_at", "code"]
        verbose_name = _("LibraryReservationsConfiguration")
        verbose_name_plural = _("LibraryReservationsConfigurations")
        indexes = [
            models.Index(fields=["code", "status"], name="librar_librar_fb682715_cd"),
            models.Index(fields=["created_at"], name="librar_librar_fb682715_cr"),
            models.Index(fields=["priority", "status"], name="librar_librar_fb682715_pr"),
            models.Index(fields=["department_tag", "status"], name="librar_librar_fb682715_dp"),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"

    def clean(self):
        super().clean()
        self.code = self.code.strip().upper()
        if self.capacity_limit < 0:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Capacity limit cannot be negative."))
        if self.allocated_count > self.capacity_limit:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Allocated count cannot exceed capacity limit."))
        if self.alert_threshold_low > self.alert_threshold_high:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Alert low threshold cannot exceed alert high threshold."))

    def is_expired(self) -> bool:
        """Determines whether this policy or record has passed its expiration date."""
        if not self.expiration_date:
            return False
        return timezone.now().date() > self.expiration_date

    def calculate_utilization(self) -> float:
        """Calculates percentage utilization against capacity limit."""
        if not self.capacity_limit or self.capacity_limit == 0:
            return 0.0
        return round((float(self.allocated_count) / float(self.capacity_limit)) * 100.0, 2)

    def has_available_capacity(self, delta: int = 1) -> bool:
        """Validates whether additional allocations can be committed."""
        return (self.allocated_count + delta) <= self.capacity_limit

    def increment_allocation(self, delta: int = 1) -> None:
        """Safely increments the committed allocation counter."""
        if not self.has_available_capacity(delta):
            from core.exceptions import CapacityExceededException
            raise CapacityExceededException(f"Cannot allocate {delta} units: Capacity limit reached.")
        self.allocated_count += delta
        self.save(update_fields=["allocated_count", "updated_at"])

    def decrement_allocation(self, delta: int = 1) -> None:
        """Safely decrements the allocated resource counter."""
        self.allocated_count = max(0, self.allocated_count - delta)
        self.save(update_fields=["allocated_count", "updated_at"])

    def mark_as_verified(self, approver: str = "SYSTEM") -> None:
        """Validates verification state and records signature in metadata."""
        self.is_verified = True
        self.metadata["verified_by"] = approver
        self.metadata["verified_at"] = timezone.now().isoformat()
        self.save(update_fields=["is_verified", "metadata", "updated_at"])

    def lock_record(self, reason: str = "Administrative Lock") -> None:
        """Freezes entity modifications for audit verification."""
        self.is_locked = True
        self.metadata["lock_reason"] = reason
        self.metadata["locked_at"] = timezone.now().isoformat()
        self.save(update_fields=["is_locked", "metadata", "updated_at"])

    def unlock_record(self) -> None:
        """Releases entity lock following audit review."""
        self.is_locked = False
        self.metadata["unlocked_at"] = timezone.now().isoformat()
        self.save(update_fields=["is_locked", "metadata", "updated_at"])

    def compute_composite_score(self) -> Decimal:
        """Computes a multi-factor score incorporating rating, priority, and capacity load."""
        utilization = Decimal(str(self.calculate_utilization()))
        return round((self.score_rating * Decimal("0.60")) + (Decimal(self.priority) * Decimal("0.20")) + (utilization * Decimal("0.002")), 4)

    def is_escalation_required(self) -> bool:
        """Determines if utilization exceeds high alert threshold."""
        return self.calculate_utilization() >= float(self.alert_threshold_high)

    def calculate_depreciation(self, annual_rate: Decimal = Decimal("0.10")) -> Decimal:
        """Calculates asset depreciation over operational lifecycle."""
        years = max(1, (timezone.now().date() - self.effective_date).days // 365)
        depreciated = self.monetary_value * ((Decimal("1.00") - annual_rate) ** years)
        return round(max(Decimal("0.00"), depreciated), 2)

    def to_summary_dict(self) -> dict:
        """Exports a standardized dictionary representation for APIs and reports."""
        return {
            "code": self.code,
            "name": self.name,
            "status": self.status,
            "priority": self.priority,
            "department_tag": self.department_tag,
            "fiscal_code": self.fiscal_code,
            "approval_authority": self.approval_authority,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "is_locked": self.is_locked,
            "capacity_limit": self.capacity_limit,
            "allocated_count": self.allocated_count,
            "utilization_pct": self.calculate_utilization(),
            "composite_score": str(self.compute_composite_score()),
            "monetary_value": str(self.monetary_value),
            "created_at": self.created_at.isoformat(),
        }

class LibraryReservationsLedgerQuerySet(models.QuerySet):
    """Custom QuerySet methods for LibraryReservationsLedger."""
    def active(self):
        return self.filter(is_active=True)
    def recent(self, days: int = 30):
        cutoff = timezone.now() - timezone.timedelta(days=days)
        return self.filter(created_at__gte=cutoff)
    def search(self, query: str):
        if not query:
            return self
        return self.filter(models.Q(code__icontains=query) | models.Q(name__icontains=query))
    def verified(self):
        return self.filter(is_verified=True)
    def by_status(self, status: str):
        return self.filter(status=status)
    def priority_ordered(self):
        return self.order_by("-priority", "-created_at")
    def capacity_available(self):
        return self.filter(allocated_count__lt=models.F("capacity_limit"))
    def threshold_exceeded(self):
        return self.filter(allocated_count__gte=models.F("capacity_limit"))
    def with_high_score(self, min_score: Decimal = Decimal("3.00")):
        return self.filter(score_rating__gte=min_score)

class LibraryReservationsLedgerManager(models.Manager):
    """Custom model manager for LibraryReservationsLedger."""
    def get_queryset(self):
        return LibraryReservationsLedgerQuerySet(self.model, using=self._db)
    def active(self):
        return self.get_queryset().active()
    def search(self, query: str):
        return self.get_queryset().search(query)
    def verified(self):
        return self.get_queryset().verified()
    def by_status(self, status: str):
        return self.get_queryset().by_status(status)
    def capacity_available(self):
        return self.get_queryset().capacity_available()

class LibraryReservationsLedger(models.Model):
    """
    LibraryReservationsLedger: Financial and quantitative accounting ledger tracking balance changes.
    Enterprise Grade Institutional Entity with strict audit trails and SQLite optimization.
    """
    code = models.CharField(max_length=64, unique=True, db_index=True, verbose_name=_("Entity Code"))
    name = models.CharField(max_length=255, db_index=True, verbose_name=_("Entity Name"))
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True, verbose_name=_("Slug"))
    description = models.TextField(blank=True, default="", verbose_name=_("Description"))
    priority = models.PositiveIntegerField(default=1, verbose_name=_("Priority Weight"))
    status = models.CharField(max_length=32, default="ACTIVE", db_index=True, verbose_name=_("Status"))
    is_active = models.BooleanField(default=True, db_index=True, verbose_name=_("Active Flag"))
    is_verified = models.BooleanField(default=False, verbose_name=_("Verified Flag"))
    is_locked = models.BooleanField(default=False, verbose_name=_("Lock Flag"))
    score_rating = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"), verbose_name=_("Score"))
    monetary_value = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"), verbose_name=_("Monetary Value"))
    capacity_limit = models.PositiveIntegerField(default=100, verbose_name=_("Capacity Limit"))
    allocated_count = models.PositiveIntegerField(default=0, verbose_name=_("Allocated Count"))
    waitlist_count = models.PositiveIntegerField(default=0, verbose_name=_("Waitlist Count"))
    alert_threshold_low = models.PositiveIntegerField(default=10, verbose_name=_("Alert Low"))
    alert_threshold_high = models.PositiveIntegerField(default=90, verbose_name=_("Alert High"))
    renewal_cycle_months = models.PositiveIntegerField(default=12, verbose_name=_("Renewal Months"))
    department_tag = models.CharField(max_length=64, blank=True, default="LIBRARY", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@library.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = LibraryReservationsLedgerManager()

    class Meta:
        db_table = "library_library_reservations_ledger"
        ordering = ["-created_at", "code"]
        verbose_name = _("LibraryReservationsLedger")
        verbose_name_plural = _("LibraryReservationsLedgers")
        indexes = [
            models.Index(fields=["code", "status"], name="librar_librar_ab0d5805_cd"),
            models.Index(fields=["created_at"], name="librar_librar_ab0d5805_cr"),
            models.Index(fields=["priority", "status"], name="librar_librar_ab0d5805_pr"),
            models.Index(fields=["department_tag", "status"], name="librar_librar_ab0d5805_dp"),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"

    def clean(self):
        super().clean()
        self.code = self.code.strip().upper()
        if self.capacity_limit < 0:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Capacity limit cannot be negative."))
        if self.allocated_count > self.capacity_limit:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Allocated count cannot exceed capacity limit."))
        if self.alert_threshold_low > self.alert_threshold_high:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Alert low threshold cannot exceed alert high threshold."))

    def is_expired(self) -> bool:
        """Determines whether this policy or record has passed its expiration date."""
        if not self.expiration_date:
            return False
        return timezone.now().date() > self.expiration_date

    def calculate_utilization(self) -> float:
        """Calculates percentage utilization against capacity limit."""
        if not self.capacity_limit or self.capacity_limit == 0:
            return 0.0
        return round((float(self.allocated_count) / float(self.capacity_limit)) * 100.0, 2)

    def has_available_capacity(self, delta: int = 1) -> bool:
        """Validates whether additional allocations can be committed."""
        return (self.allocated_count + delta) <= self.capacity_limit

    def increment_allocation(self, delta: int = 1) -> None:
        """Safely increments the committed allocation counter."""
        if not self.has_available_capacity(delta):
            from core.exceptions import CapacityExceededException
            raise CapacityExceededException(f"Cannot allocate {delta} units: Capacity limit reached.")
        self.allocated_count += delta
        self.save(update_fields=["allocated_count", "updated_at"])

    def decrement_allocation(self, delta: int = 1) -> None:
        """Safely decrements the allocated resource counter."""
        self.allocated_count = max(0, self.allocated_count - delta)
        self.save(update_fields=["allocated_count", "updated_at"])

    def mark_as_verified(self, approver: str = "SYSTEM") -> None:
        """Validates verification state and records signature in metadata."""
        self.is_verified = True
        self.metadata["verified_by"] = approver
        self.metadata["verified_at"] = timezone.now().isoformat()
        self.save(update_fields=["is_verified", "metadata", "updated_at"])

    def lock_record(self, reason: str = "Administrative Lock") -> None:
        """Freezes entity modifications for audit verification."""
        self.is_locked = True
        self.metadata["lock_reason"] = reason
        self.metadata["locked_at"] = timezone.now().isoformat()
        self.save(update_fields=["is_locked", "metadata", "updated_at"])

    def unlock_record(self) -> None:
        """Releases entity lock following audit review."""
        self.is_locked = False
        self.metadata["unlocked_at"] = timezone.now().isoformat()
        self.save(update_fields=["is_locked", "metadata", "updated_at"])

    def compute_composite_score(self) -> Decimal:
        """Computes a multi-factor score incorporating rating, priority, and capacity load."""
        utilization = Decimal(str(self.calculate_utilization()))
        return round((self.score_rating * Decimal("0.60")) + (Decimal(self.priority) * Decimal("0.20")) + (utilization * Decimal("0.002")), 4)

    def is_escalation_required(self) -> bool:
        """Determines if utilization exceeds high alert threshold."""
        return self.calculate_utilization() >= float(self.alert_threshold_high)

    def calculate_depreciation(self, annual_rate: Decimal = Decimal("0.10")) -> Decimal:
        """Calculates asset depreciation over operational lifecycle."""
        years = max(1, (timezone.now().date() - self.effective_date).days // 365)
        depreciated = self.monetary_value * ((Decimal("1.00") - annual_rate) ** years)
        return round(max(Decimal("0.00"), depreciated), 2)

    def to_summary_dict(self) -> dict:
        """Exports a standardized dictionary representation for APIs and reports."""
        return {
            "code": self.code,
            "name": self.name,
            "status": self.status,
            "priority": self.priority,
            "department_tag": self.department_tag,
            "fiscal_code": self.fiscal_code,
            "approval_authority": self.approval_authority,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "is_locked": self.is_locked,
            "capacity_limit": self.capacity_limit,
            "allocated_count": self.allocated_count,
            "utilization_pct": self.calculate_utilization(),
            "composite_score": str(self.compute_composite_score()),
            "monetary_value": str(self.monetary_value),
            "created_at": self.created_at.isoformat(),
        }

class LibraryReservationsAuditTransactionQuerySet(models.QuerySet):
    """Custom QuerySet methods for LibraryReservationsAuditTransaction."""
    def active(self):
        return self.filter(is_active=True)
    def recent(self, days: int = 30):
        cutoff = timezone.now() - timezone.timedelta(days=days)
        return self.filter(created_at__gte=cutoff)
    def search(self, query: str):
        if not query:
            return self
        return self.filter(models.Q(code__icontains=query) | models.Q(name__icontains=query))
    def verified(self):
        return self.filter(is_verified=True)
    def by_status(self, status: str):
        return self.filter(status=status)
    def priority_ordered(self):
        return self.order_by("-priority", "-created_at")
    def capacity_available(self):
        return self.filter(allocated_count__lt=models.F("capacity_limit"))
    def threshold_exceeded(self):
        return self.filter(allocated_count__gte=models.F("capacity_limit"))
    def with_high_score(self, min_score: Decimal = Decimal("3.00")):
        return self.filter(score_rating__gte=min_score)

class LibraryReservationsAuditTransactionManager(models.Manager):
    """Custom model manager for LibraryReservationsAuditTransaction."""
    def get_queryset(self):
        return LibraryReservationsAuditTransactionQuerySet(self.model, using=self._db)
    def active(self):
        return self.get_queryset().active()
    def search(self, query: str):
        return self.get_queryset().search(query)
    def verified(self):
        return self.get_queryset().verified()
    def by_status(self, status: str):
        return self.get_queryset().by_status(status)
    def capacity_available(self):
        return self.get_queryset().capacity_available()

class LibraryReservationsAuditTransaction(models.Model):
    """
    LibraryReservationsAuditTransaction: Immutable audit log transaction record capturing user mutations and states.
    Enterprise Grade Institutional Entity with strict audit trails and SQLite optimization.
    """
    code = models.CharField(max_length=64, unique=True, db_index=True, verbose_name=_("Entity Code"))
    name = models.CharField(max_length=255, db_index=True, verbose_name=_("Entity Name"))
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True, verbose_name=_("Slug"))
    description = models.TextField(blank=True, default="", verbose_name=_("Description"))
    priority = models.PositiveIntegerField(default=1, verbose_name=_("Priority Weight"))
    status = models.CharField(max_length=32, default="ACTIVE", db_index=True, verbose_name=_("Status"))
    is_active = models.BooleanField(default=True, db_index=True, verbose_name=_("Active Flag"))
    is_verified = models.BooleanField(default=False, verbose_name=_("Verified Flag"))
    is_locked = models.BooleanField(default=False, verbose_name=_("Lock Flag"))
    score_rating = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"), verbose_name=_("Score"))
    monetary_value = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"), verbose_name=_("Monetary Value"))
    capacity_limit = models.PositiveIntegerField(default=100, verbose_name=_("Capacity Limit"))
    allocated_count = models.PositiveIntegerField(default=0, verbose_name=_("Allocated Count"))
    waitlist_count = models.PositiveIntegerField(default=0, verbose_name=_("Waitlist Count"))
    alert_threshold_low = models.PositiveIntegerField(default=10, verbose_name=_("Alert Low"))
    alert_threshold_high = models.PositiveIntegerField(default=90, verbose_name=_("Alert High"))
    renewal_cycle_months = models.PositiveIntegerField(default=12, verbose_name=_("Renewal Months"))
    department_tag = models.CharField(max_length=64, blank=True, default="LIBRARY", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@library.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = LibraryReservationsAuditTransactionManager()

    class Meta:
        db_table = "library_library_reservations_audittransaction"
        ordering = ["-created_at", "code"]
        verbose_name = _("LibraryReservationsAuditTransaction")
        verbose_name_plural = _("LibraryReservationsAuditTransactions")
        indexes = [
            models.Index(fields=["code", "status"], name="librar_librar_6815bc2e_cd"),
            models.Index(fields=["created_at"], name="librar_librar_6815bc2e_cr"),
            models.Index(fields=["priority", "status"], name="librar_librar_6815bc2e_pr"),
            models.Index(fields=["department_tag", "status"], name="librar_librar_6815bc2e_dp"),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"

    def clean(self):
        super().clean()
        self.code = self.code.strip().upper()
        if self.capacity_limit < 0:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Capacity limit cannot be negative."))
        if self.allocated_count > self.capacity_limit:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Allocated count cannot exceed capacity limit."))
        if self.alert_threshold_low > self.alert_threshold_high:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Alert low threshold cannot exceed alert high threshold."))

    def is_expired(self) -> bool:
        """Determines whether this policy or record has passed its expiration date."""
        if not self.expiration_date:
            return False
        return timezone.now().date() > self.expiration_date

    def calculate_utilization(self) -> float:
        """Calculates percentage utilization against capacity limit."""
        if not self.capacity_limit or self.capacity_limit == 0:
            return 0.0
        return round((float(self.allocated_count) / float(self.capacity_limit)) * 100.0, 2)

    def has_available_capacity(self, delta: int = 1) -> bool:
        """Validates whether additional allocations can be committed."""
        return (self.allocated_count + delta) <= self.capacity_limit

    def increment_allocation(self, delta: int = 1) -> None:
        """Safely increments the committed allocation counter."""
        if not self.has_available_capacity(delta):
            from core.exceptions import CapacityExceededException
            raise CapacityExceededException(f"Cannot allocate {delta} units: Capacity limit reached.")
        self.allocated_count += delta
        self.save(update_fields=["allocated_count", "updated_at"])

    def decrement_allocation(self, delta: int = 1) -> None:
        """Safely decrements the allocated resource counter."""
        self.allocated_count = max(0, self.allocated_count - delta)
        self.save(update_fields=["allocated_count", "updated_at"])

    def mark_as_verified(self, approver: str = "SYSTEM") -> None:
        """Validates verification state and records signature in metadata."""
        self.is_verified = True
        self.metadata["verified_by"] = approver
        self.metadata["verified_at"] = timezone.now().isoformat()
        self.save(update_fields=["is_verified", "metadata", "updated_at"])

    def lock_record(self, reason: str = "Administrative Lock") -> None:
        """Freezes entity modifications for audit verification."""
        self.is_locked = True
        self.metadata["lock_reason"] = reason
        self.metadata["locked_at"] = timezone.now().isoformat()
        self.save(update_fields=["is_locked", "metadata", "updated_at"])

    def unlock_record(self) -> None:
        """Releases entity lock following audit review."""
        self.is_locked = False
        self.metadata["unlocked_at"] = timezone.now().isoformat()
        self.save(update_fields=["is_locked", "metadata", "updated_at"])

    def compute_composite_score(self) -> Decimal:
        """Computes a multi-factor score incorporating rating, priority, and capacity load."""
        utilization = Decimal(str(self.calculate_utilization()))
        return round((self.score_rating * Decimal("0.60")) + (Decimal(self.priority) * Decimal("0.20")) + (utilization * Decimal("0.002")), 4)

    def is_escalation_required(self) -> bool:
        """Determines if utilization exceeds high alert threshold."""
        return self.calculate_utilization() >= float(self.alert_threshold_high)

    def calculate_depreciation(self, annual_rate: Decimal = Decimal("0.10")) -> Decimal:
        """Calculates asset depreciation over operational lifecycle."""
        years = max(1, (timezone.now().date() - self.effective_date).days // 365)
        depreciated = self.monetary_value * ((Decimal("1.00") - annual_rate) ** years)
        return round(max(Decimal("0.00"), depreciated), 2)

    def to_summary_dict(self) -> dict:
        """Exports a standardized dictionary representation for APIs and reports."""
        return {
            "code": self.code,
            "name": self.name,
            "status": self.status,
            "priority": self.priority,
            "department_tag": self.department_tag,
            "fiscal_code": self.fiscal_code,
            "approval_authority": self.approval_authority,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "is_locked": self.is_locked,
            "capacity_limit": self.capacity_limit,
            "allocated_count": self.allocated_count,
            "utilization_pct": self.calculate_utilization(),
            "composite_score": str(self.compute_composite_score()),
            "monetary_value": str(self.monetary_value),
            "created_at": self.created_at.isoformat(),
        }

class LibraryReservationsScheduleMatrixQuerySet(models.QuerySet):
    """Custom QuerySet methods for LibraryReservationsScheduleMatrix."""
    def active(self):
        return self.filter(is_active=True)
    def recent(self, days: int = 30):
        cutoff = timezone.now() - timezone.timedelta(days=days)
        return self.filter(created_at__gte=cutoff)
    def search(self, query: str):
        if not query:
            return self
        return self.filter(models.Q(code__icontains=query) | models.Q(name__icontains=query))
    def verified(self):
        return self.filter(is_verified=True)
    def by_status(self, status: str):
        return self.filter(status=status)
    def priority_ordered(self):
        return self.order_by("-priority", "-created_at")
    def capacity_available(self):
        return self.filter(allocated_count__lt=models.F("capacity_limit"))
    def threshold_exceeded(self):
        return self.filter(allocated_count__gte=models.F("capacity_limit"))
    def with_high_score(self, min_score: Decimal = Decimal("3.00")):
        return self.filter(score_rating__gte=min_score)

class LibraryReservationsScheduleMatrixManager(models.Manager):
    """Custom model manager for LibraryReservationsScheduleMatrix."""
    def get_queryset(self):
        return LibraryReservationsScheduleMatrixQuerySet(self.model, using=self._db)
    def active(self):
        return self.get_queryset().active()
    def search(self, query: str):
        return self.get_queryset().search(query)
    def verified(self):
        return self.get_queryset().verified()
    def by_status(self, status: str):
        return self.get_queryset().by_status(status)
    def capacity_available(self):
        return self.get_queryset().capacity_available()

class LibraryReservationsScheduleMatrix(models.Model):
    """
    LibraryReservationsScheduleMatrix: Temporal planning and operational schedule coordinates.
    Enterprise Grade Institutional Entity with strict audit trails and SQLite optimization.
    """
    code = models.CharField(max_length=64, unique=True, db_index=True, verbose_name=_("Entity Code"))
    name = models.CharField(max_length=255, db_index=True, verbose_name=_("Entity Name"))
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True, verbose_name=_("Slug"))
    description = models.TextField(blank=True, default="", verbose_name=_("Description"))
    priority = models.PositiveIntegerField(default=1, verbose_name=_("Priority Weight"))
    status = models.CharField(max_length=32, default="ACTIVE", db_index=True, verbose_name=_("Status"))
    is_active = models.BooleanField(default=True, db_index=True, verbose_name=_("Active Flag"))
    is_verified = models.BooleanField(default=False, verbose_name=_("Verified Flag"))
    is_locked = models.BooleanField(default=False, verbose_name=_("Lock Flag"))
    score_rating = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"), verbose_name=_("Score"))
    monetary_value = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"), verbose_name=_("Monetary Value"))
    capacity_limit = models.PositiveIntegerField(default=100, verbose_name=_("Capacity Limit"))
    allocated_count = models.PositiveIntegerField(default=0, verbose_name=_("Allocated Count"))
    waitlist_count = models.PositiveIntegerField(default=0, verbose_name=_("Waitlist Count"))
    alert_threshold_low = models.PositiveIntegerField(default=10, verbose_name=_("Alert Low"))
    alert_threshold_high = models.PositiveIntegerField(default=90, verbose_name=_("Alert High"))
    renewal_cycle_months = models.PositiveIntegerField(default=12, verbose_name=_("Renewal Months"))
    department_tag = models.CharField(max_length=64, blank=True, default="LIBRARY", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@library.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = LibraryReservationsScheduleMatrixManager()

    class Meta:
        db_table = "library_library_reservations_schedulematrix"
        ordering = ["-created_at", "code"]
        verbose_name = _("LibraryReservationsScheduleMatrix")
        verbose_name_plural = _("LibraryReservationsScheduleMatrixs")
        indexes = [
            models.Index(fields=["code", "status"], name="librar_librar_79c17784_cd"),
            models.Index(fields=["created_at"], name="librar_librar_79c17784_cr"),
            models.Index(fields=["priority", "status"], name="librar_librar_79c17784_pr"),
            models.Index(fields=["department_tag", "status"], name="librar_librar_79c17784_dp"),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"

    def clean(self):
        super().clean()
        self.code = self.code.strip().upper()
        if self.capacity_limit < 0:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Capacity limit cannot be negative."))
        if self.allocated_count > self.capacity_limit:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Allocated count cannot exceed capacity limit."))
        if self.alert_threshold_low > self.alert_threshold_high:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Alert low threshold cannot exceed alert high threshold."))

    def is_expired(self) -> bool:
        """Determines whether this policy or record has passed its expiration date."""
        if not self.expiration_date:
            return False
        return timezone.now().date() > self.expiration_date

    def calculate_utilization(self) -> float:
        """Calculates percentage utilization against capacity limit."""
        if not self.capacity_limit or self.capacity_limit == 0:
            return 0.0
        return round((float(self.allocated_count) / float(self.capacity_limit)) * 100.0, 2)

    def has_available_capacity(self, delta: int = 1) -> bool:
        """Validates whether additional allocations can be committed."""
        return (self.allocated_count + delta) <= self.capacity_limit

    def increment_allocation(self, delta: int = 1) -> None:
        """Safely increments the committed allocation counter."""
        if not self.has_available_capacity(delta):
            from core.exceptions import CapacityExceededException
            raise CapacityExceededException(f"Cannot allocate {delta} units: Capacity limit reached.")
        self.allocated_count += delta
        self.save(update_fields=["allocated_count", "updated_at"])

    def decrement_allocation(self, delta: int = 1) -> None:
        """Safely decrements the allocated resource counter."""
        self.allocated_count = max(0, self.allocated_count - delta)
        self.save(update_fields=["allocated_count", "updated_at"])

    def mark_as_verified(self, approver: str = "SYSTEM") -> None:
        """Validates verification state and records signature in metadata."""
        self.is_verified = True
        self.metadata["verified_by"] = approver
        self.metadata["verified_at"] = timezone.now().isoformat()
        self.save(update_fields=["is_verified", "metadata", "updated_at"])

    def lock_record(self, reason: str = "Administrative Lock") -> None:
        """Freezes entity modifications for audit verification."""
        self.is_locked = True
        self.metadata["lock_reason"] = reason
        self.metadata["locked_at"] = timezone.now().isoformat()
        self.save(update_fields=["is_locked", "metadata", "updated_at"])

    def unlock_record(self) -> None:
        """Releases entity lock following audit review."""
        self.is_locked = False
        self.metadata["unlocked_at"] = timezone.now().isoformat()
        self.save(update_fields=["is_locked", "metadata", "updated_at"])

    def compute_composite_score(self) -> Decimal:
        """Computes a multi-factor score incorporating rating, priority, and capacity load."""
        utilization = Decimal(str(self.calculate_utilization()))
        return round((self.score_rating * Decimal("0.60")) + (Decimal(self.priority) * Decimal("0.20")) + (utilization * Decimal("0.002")), 4)

    def is_escalation_required(self) -> bool:
        """Determines if utilization exceeds high alert threshold."""
        return self.calculate_utilization() >= float(self.alert_threshold_high)

    def calculate_depreciation(self, annual_rate: Decimal = Decimal("0.10")) -> Decimal:
        """Calculates asset depreciation over operational lifecycle."""
        years = max(1, (timezone.now().date() - self.effective_date).days // 365)
        depreciated = self.monetary_value * ((Decimal("1.00") - annual_rate) ** years)
        return round(max(Decimal("0.00"), depreciated), 2)

    def to_summary_dict(self) -> dict:
        """Exports a standardized dictionary representation for APIs and reports."""
        return {
            "code": self.code,
            "name": self.name,
            "status": self.status,
            "priority": self.priority,
            "department_tag": self.department_tag,
            "fiscal_code": self.fiscal_code,
            "approval_authority": self.approval_authority,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "is_locked": self.is_locked,
            "capacity_limit": self.capacity_limit,
            "allocated_count": self.allocated_count,
            "utilization_pct": self.calculate_utilization(),
            "composite_score": str(self.compute_composite_score()),
            "monetary_value": str(self.monetary_value),
            "created_at": self.created_at.isoformat(),
        }

class LibraryReservationsEvaluationMetricQuerySet(models.QuerySet):
    """Custom QuerySet methods for LibraryReservationsEvaluationMetric."""
    def active(self):
        return self.filter(is_active=True)
    def recent(self, days: int = 30):
        cutoff = timezone.now() - timezone.timedelta(days=days)
        return self.filter(created_at__gte=cutoff)
    def search(self, query: str):
        if not query:
            return self
        return self.filter(models.Q(code__icontains=query) | models.Q(name__icontains=query))
    def verified(self):
        return self.filter(is_verified=True)
    def by_status(self, status: str):
        return self.filter(status=status)
    def priority_ordered(self):
        return self.order_by("-priority", "-created_at")
    def capacity_available(self):
        return self.filter(allocated_count__lt=models.F("capacity_limit"))
    def threshold_exceeded(self):
        return self.filter(allocated_count__gte=models.F("capacity_limit"))
    def with_high_score(self, min_score: Decimal = Decimal("3.00")):
        return self.filter(score_rating__gte=min_score)

class LibraryReservationsEvaluationMetricManager(models.Manager):
    """Custom model manager for LibraryReservationsEvaluationMetric."""
    def get_queryset(self):
        return LibraryReservationsEvaluationMetricQuerySet(self.model, using=self._db)
    def active(self):
        return self.get_queryset().active()
    def search(self, query: str):
        return self.get_queryset().search(query)
    def verified(self):
        return self.get_queryset().verified()
    def by_status(self, status: str):
        return self.get_queryset().by_status(status)
    def capacity_available(self):
        return self.get_queryset().capacity_available()

class LibraryReservationsEvaluationMetric(models.Model):
    """
    LibraryReservationsEvaluationMetric: Performance indicators, rubrics, and assessment scores.
    Enterprise Grade Institutional Entity with strict audit trails and SQLite optimization.
    """
    code = models.CharField(max_length=64, unique=True, db_index=True, verbose_name=_("Entity Code"))
    name = models.CharField(max_length=255, db_index=True, verbose_name=_("Entity Name"))
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True, verbose_name=_("Slug"))
    description = models.TextField(blank=True, default="", verbose_name=_("Description"))
    priority = models.PositiveIntegerField(default=1, verbose_name=_("Priority Weight"))
    status = models.CharField(max_length=32, default="ACTIVE", db_index=True, verbose_name=_("Status"))
    is_active = models.BooleanField(default=True, db_index=True, verbose_name=_("Active Flag"))
    is_verified = models.BooleanField(default=False, verbose_name=_("Verified Flag"))
    is_locked = models.BooleanField(default=False, verbose_name=_("Lock Flag"))
    score_rating = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"), verbose_name=_("Score"))
    monetary_value = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"), verbose_name=_("Monetary Value"))
    capacity_limit = models.PositiveIntegerField(default=100, verbose_name=_("Capacity Limit"))
    allocated_count = models.PositiveIntegerField(default=0, verbose_name=_("Allocated Count"))
    waitlist_count = models.PositiveIntegerField(default=0, verbose_name=_("Waitlist Count"))
    alert_threshold_low = models.PositiveIntegerField(default=10, verbose_name=_("Alert Low"))
    alert_threshold_high = models.PositiveIntegerField(default=90, verbose_name=_("Alert High"))
    renewal_cycle_months = models.PositiveIntegerField(default=12, verbose_name=_("Renewal Months"))
    department_tag = models.CharField(max_length=64, blank=True, default="LIBRARY", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@library.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = LibraryReservationsEvaluationMetricManager()

    class Meta:
        db_table = "library_library_reservations_evaluationmetric"
        ordering = ["-created_at", "code"]
        verbose_name = _("LibraryReservationsEvaluationMetric")
        verbose_name_plural = _("LibraryReservationsEvaluationMetrics")
        indexes = [
            models.Index(fields=["code", "status"], name="librar_librar_253c4726_cd"),
            models.Index(fields=["created_at"], name="librar_librar_253c4726_cr"),
            models.Index(fields=["priority", "status"], name="librar_librar_253c4726_pr"),
            models.Index(fields=["department_tag", "status"], name="librar_librar_253c4726_dp"),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"

    def clean(self):
        super().clean()
        self.code = self.code.strip().upper()
        if self.capacity_limit < 0:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Capacity limit cannot be negative."))
        if self.allocated_count > self.capacity_limit:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Allocated count cannot exceed capacity limit."))
        if self.alert_threshold_low > self.alert_threshold_high:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Alert low threshold cannot exceed alert high threshold."))

    def is_expired(self) -> bool:
        """Determines whether this policy or record has passed its expiration date."""
        if not self.expiration_date:
            return False
        return timezone.now().date() > self.expiration_date

    def calculate_utilization(self) -> float:
        """Calculates percentage utilization against capacity limit."""
        if not self.capacity_limit or self.capacity_limit == 0:
            return 0.0
        return round((float(self.allocated_count) / float(self.capacity_limit)) * 100.0, 2)

    def has_available_capacity(self, delta: int = 1) -> bool:
        """Validates whether additional allocations can be committed."""
        return (self.allocated_count + delta) <= self.capacity_limit

    def increment_allocation(self, delta: int = 1) -> None:
        """Safely increments the committed allocation counter."""
        if not self.has_available_capacity(delta):
            from core.exceptions import CapacityExceededException
            raise CapacityExceededException(f"Cannot allocate {delta} units: Capacity limit reached.")
        self.allocated_count += delta
        self.save(update_fields=["allocated_count", "updated_at"])

    def decrement_allocation(self, delta: int = 1) -> None:
        """Safely decrements the allocated resource counter."""
        self.allocated_count = max(0, self.allocated_count - delta)
        self.save(update_fields=["allocated_count", "updated_at"])

    def mark_as_verified(self, approver: str = "SYSTEM") -> None:
        """Validates verification state and records signature in metadata."""
        self.is_verified = True
        self.metadata["verified_by"] = approver
        self.metadata["verified_at"] = timezone.now().isoformat()
        self.save(update_fields=["is_verified", "metadata", "updated_at"])

    def lock_record(self, reason: str = "Administrative Lock") -> None:
        """Freezes entity modifications for audit verification."""
        self.is_locked = True
        self.metadata["lock_reason"] = reason
        self.metadata["locked_at"] = timezone.now().isoformat()
        self.save(update_fields=["is_locked", "metadata", "updated_at"])

    def unlock_record(self) -> None:
        """Releases entity lock following audit review."""
        self.is_locked = False
        self.metadata["unlocked_at"] = timezone.now().isoformat()
        self.save(update_fields=["is_locked", "metadata", "updated_at"])

    def compute_composite_score(self) -> Decimal:
        """Computes a multi-factor score incorporating rating, priority, and capacity load."""
        utilization = Decimal(str(self.calculate_utilization()))
        return round((self.score_rating * Decimal("0.60")) + (Decimal(self.priority) * Decimal("0.20")) + (utilization * Decimal("0.002")), 4)

    def is_escalation_required(self) -> bool:
        """Determines if utilization exceeds high alert threshold."""
        return self.calculate_utilization() >= float(self.alert_threshold_high)

    def calculate_depreciation(self, annual_rate: Decimal = Decimal("0.10")) -> Decimal:
        """Calculates asset depreciation over operational lifecycle."""
        years = max(1, (timezone.now().date() - self.effective_date).days // 365)
        depreciated = self.monetary_value * ((Decimal("1.00") - annual_rate) ** years)
        return round(max(Decimal("0.00"), depreciated), 2)

    def to_summary_dict(self) -> dict:
        """Exports a standardized dictionary representation for APIs and reports."""
        return {
            "code": self.code,
            "name": self.name,
            "status": self.status,
            "priority": self.priority,
            "department_tag": self.department_tag,
            "fiscal_code": self.fiscal_code,
            "approval_authority": self.approval_authority,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "is_locked": self.is_locked,
            "capacity_limit": self.capacity_limit,
            "allocated_count": self.allocated_count,
            "utilization_pct": self.calculate_utilization(),
            "composite_score": str(self.compute_composite_score()),
            "monetary_value": str(self.monetary_value),
            "created_at": self.created_at.isoformat(),
        }

class LibraryReservationsRosterMappingQuerySet(models.QuerySet):
    """Custom QuerySet methods for LibraryReservationsRosterMapping."""
    def active(self):
        return self.filter(is_active=True)
    def recent(self, days: int = 30):
        cutoff = timezone.now() - timezone.timedelta(days=days)
        return self.filter(created_at__gte=cutoff)
    def search(self, query: str):
        if not query:
            return self
        return self.filter(models.Q(code__icontains=query) | models.Q(name__icontains=query))
    def verified(self):
        return self.filter(is_verified=True)
    def by_status(self, status: str):
        return self.filter(status=status)
    def priority_ordered(self):
        return self.order_by("-priority", "-created_at")
    def capacity_available(self):
        return self.filter(allocated_count__lt=models.F("capacity_limit"))
    def threshold_exceeded(self):
        return self.filter(allocated_count__gte=models.F("capacity_limit"))
    def with_high_score(self, min_score: Decimal = Decimal("3.00")):
        return self.filter(score_rating__gte=min_score)

class LibraryReservationsRosterMappingManager(models.Manager):
    """Custom model manager for LibraryReservationsRosterMapping."""
    def get_queryset(self):
        return LibraryReservationsRosterMappingQuerySet(self.model, using=self._db)
    def active(self):
        return self.get_queryset().active()
    def search(self, query: str):
        return self.get_queryset().search(query)
    def verified(self):
        return self.get_queryset().verified()
    def by_status(self, status: str):
        return self.get_queryset().by_status(status)
    def capacity_available(self):
        return self.get_queryset().capacity_available()

class LibraryReservationsRosterMapping(models.Model):
    """
    LibraryReservationsRosterMapping: Relational participant roster links and enrollment associations.
    Enterprise Grade Institutional Entity with strict audit trails and SQLite optimization.
    """
    code = models.CharField(max_length=64, unique=True, db_index=True, verbose_name=_("Entity Code"))
    name = models.CharField(max_length=255, db_index=True, verbose_name=_("Entity Name"))
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True, verbose_name=_("Slug"))
    description = models.TextField(blank=True, default="", verbose_name=_("Description"))
    priority = models.PositiveIntegerField(default=1, verbose_name=_("Priority Weight"))
    status = models.CharField(max_length=32, default="ACTIVE", db_index=True, verbose_name=_("Status"))
    is_active = models.BooleanField(default=True, db_index=True, verbose_name=_("Active Flag"))
    is_verified = models.BooleanField(default=False, verbose_name=_("Verified Flag"))
    is_locked = models.BooleanField(default=False, verbose_name=_("Lock Flag"))
    score_rating = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"), verbose_name=_("Score"))
    monetary_value = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"), verbose_name=_("Monetary Value"))
    capacity_limit = models.PositiveIntegerField(default=100, verbose_name=_("Capacity Limit"))
    allocated_count = models.PositiveIntegerField(default=0, verbose_name=_("Allocated Count"))
    waitlist_count = models.PositiveIntegerField(default=0, verbose_name=_("Waitlist Count"))
    alert_threshold_low = models.PositiveIntegerField(default=10, verbose_name=_("Alert Low"))
    alert_threshold_high = models.PositiveIntegerField(default=90, verbose_name=_("Alert High"))
    renewal_cycle_months = models.PositiveIntegerField(default=12, verbose_name=_("Renewal Months"))
    department_tag = models.CharField(max_length=64, blank=True, default="LIBRARY", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@library.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = LibraryReservationsRosterMappingManager()

    class Meta:
        db_table = "library_library_reservations_rostermapping"
        ordering = ["-created_at", "code"]
        verbose_name = _("LibraryReservationsRosterMapping")
        verbose_name_plural = _("LibraryReservationsRosterMappings")
        indexes = [
            models.Index(fields=["code", "status"], name="librar_librar_158331ce_cd"),
            models.Index(fields=["created_at"], name="librar_librar_158331ce_cr"),
            models.Index(fields=["priority", "status"], name="librar_librar_158331ce_pr"),
            models.Index(fields=["department_tag", "status"], name="librar_librar_158331ce_dp"),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"

    def clean(self):
        super().clean()
        self.code = self.code.strip().upper()
        if self.capacity_limit < 0:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Capacity limit cannot be negative."))
        if self.allocated_count > self.capacity_limit:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Allocated count cannot exceed capacity limit."))
        if self.alert_threshold_low > self.alert_threshold_high:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Alert low threshold cannot exceed alert high threshold."))

    def is_expired(self) -> bool:
        """Determines whether this policy or record has passed its expiration date."""
        if not self.expiration_date:
            return False
        return timezone.now().date() > self.expiration_date

    def calculate_utilization(self) -> float:
        """Calculates percentage utilization against capacity limit."""
        if not self.capacity_limit or self.capacity_limit == 0:
            return 0.0
        return round((float(self.allocated_count) / float(self.capacity_limit)) * 100.0, 2)

    def has_available_capacity(self, delta: int = 1) -> bool:
        """Validates whether additional allocations can be committed."""
        return (self.allocated_count + delta) <= self.capacity_limit

    def increment_allocation(self, delta: int = 1) -> None:
        """Safely increments the committed allocation counter."""
        if not self.has_available_capacity(delta):
            from core.exceptions import CapacityExceededException
            raise CapacityExceededException(f"Cannot allocate {delta} units: Capacity limit reached.")
        self.allocated_count += delta
        self.save(update_fields=["allocated_count", "updated_at"])

    def decrement_allocation(self, delta: int = 1) -> None:
        """Safely decrements the allocated resource counter."""
        self.allocated_count = max(0, self.allocated_count - delta)
        self.save(update_fields=["allocated_count", "updated_at"])

    def mark_as_verified(self, approver: str = "SYSTEM") -> None:
        """Validates verification state and records signature in metadata."""
        self.is_verified = True
        self.metadata["verified_by"] = approver
        self.metadata["verified_at"] = timezone.now().isoformat()
        self.save(update_fields=["is_verified", "metadata", "updated_at"])

    def lock_record(self, reason: str = "Administrative Lock") -> None:
        """Freezes entity modifications for audit verification."""
        self.is_locked = True
        self.metadata["lock_reason"] = reason
        self.metadata["locked_at"] = timezone.now().isoformat()
        self.save(update_fields=["is_locked", "metadata", "updated_at"])

    def unlock_record(self) -> None:
        """Releases entity lock following audit review."""
        self.is_locked = False
        self.metadata["unlocked_at"] = timezone.now().isoformat()
        self.save(update_fields=["is_locked", "metadata", "updated_at"])

    def compute_composite_score(self) -> Decimal:
        """Computes a multi-factor score incorporating rating, priority, and capacity load."""
        utilization = Decimal(str(self.calculate_utilization()))
        return round((self.score_rating * Decimal("0.60")) + (Decimal(self.priority) * Decimal("0.20")) + (utilization * Decimal("0.002")), 4)

    def is_escalation_required(self) -> bool:
        """Determines if utilization exceeds high alert threshold."""
        return self.calculate_utilization() >= float(self.alert_threshold_high)

    def calculate_depreciation(self, annual_rate: Decimal = Decimal("0.10")) -> Decimal:
        """Calculates asset depreciation over operational lifecycle."""
        years = max(1, (timezone.now().date() - self.effective_date).days // 365)
        depreciated = self.monetary_value * ((Decimal("1.00") - annual_rate) ** years)
        return round(max(Decimal("0.00"), depreciated), 2)

    def to_summary_dict(self) -> dict:
        """Exports a standardized dictionary representation for APIs and reports."""
        return {
            "code": self.code,
            "name": self.name,
            "status": self.status,
            "priority": self.priority,
            "department_tag": self.department_tag,
            "fiscal_code": self.fiscal_code,
            "approval_authority": self.approval_authority,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "is_locked": self.is_locked,
            "capacity_limit": self.capacity_limit,
            "allocated_count": self.allocated_count,
            "utilization_pct": self.calculate_utilization(),
            "composite_score": str(self.compute_composite_score()),
            "monetary_value": str(self.monetary_value),
            "created_at": self.created_at.isoformat(),
        }

class LibraryReservationsVerificationSignatureQuerySet(models.QuerySet):
    """Custom QuerySet methods for LibraryReservationsVerificationSignature."""
    def active(self):
        return self.filter(is_active=True)
    def recent(self, days: int = 30):
        cutoff = timezone.now() - timezone.timedelta(days=days)
        return self.filter(created_at__gte=cutoff)
    def search(self, query: str):
        if not query:
            return self
        return self.filter(models.Q(code__icontains=query) | models.Q(name__icontains=query))
    def verified(self):
        return self.filter(is_verified=True)
    def by_status(self, status: str):
        return self.filter(status=status)
    def priority_ordered(self):
        return self.order_by("-priority", "-created_at")
    def capacity_available(self):
        return self.filter(allocated_count__lt=models.F("capacity_limit"))
    def threshold_exceeded(self):
        return self.filter(allocated_count__gte=models.F("capacity_limit"))
    def with_high_score(self, min_score: Decimal = Decimal("3.00")):
        return self.filter(score_rating__gte=min_score)

class LibraryReservationsVerificationSignatureManager(models.Manager):
    """Custom model manager for LibraryReservationsVerificationSignature."""
    def get_queryset(self):
        return LibraryReservationsVerificationSignatureQuerySet(self.model, using=self._db)
    def active(self):
        return self.get_queryset().active()
    def search(self, query: str):
        return self.get_queryset().search(query)
    def verified(self):
        return self.get_queryset().verified()
    def by_status(self, status: str):
        return self.get_queryset().by_status(status)
    def capacity_available(self):
        return self.get_queryset().capacity_available()

class LibraryReservationsVerificationSignature(models.Model):
    """
    LibraryReservationsVerificationSignature: Cryptographic verification and integrity tokens.
    Enterprise Grade Institutional Entity with strict audit trails and SQLite optimization.
    """
    code = models.CharField(max_length=64, unique=True, db_index=True, verbose_name=_("Entity Code"))
    name = models.CharField(max_length=255, db_index=True, verbose_name=_("Entity Name"))
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True, verbose_name=_("Slug"))
    description = models.TextField(blank=True, default="", verbose_name=_("Description"))
    priority = models.PositiveIntegerField(default=1, verbose_name=_("Priority Weight"))
    status = models.CharField(max_length=32, default="ACTIVE", db_index=True, verbose_name=_("Status"))
    is_active = models.BooleanField(default=True, db_index=True, verbose_name=_("Active Flag"))
    is_verified = models.BooleanField(default=False, verbose_name=_("Verified Flag"))
    is_locked = models.BooleanField(default=False, verbose_name=_("Lock Flag"))
    score_rating = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"), verbose_name=_("Score"))
    monetary_value = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"), verbose_name=_("Monetary Value"))
    capacity_limit = models.PositiveIntegerField(default=100, verbose_name=_("Capacity Limit"))
    allocated_count = models.PositiveIntegerField(default=0, verbose_name=_("Allocated Count"))
    waitlist_count = models.PositiveIntegerField(default=0, verbose_name=_("Waitlist Count"))
    alert_threshold_low = models.PositiveIntegerField(default=10, verbose_name=_("Alert Low"))
    alert_threshold_high = models.PositiveIntegerField(default=90, verbose_name=_("Alert High"))
    renewal_cycle_months = models.PositiveIntegerField(default=12, verbose_name=_("Renewal Months"))
    department_tag = models.CharField(max_length=64, blank=True, default="LIBRARY", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@library.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = LibraryReservationsVerificationSignatureManager()

    class Meta:
        db_table = "library_library_reservations_verificationsignature"
        ordering = ["-created_at", "code"]
        verbose_name = _("LibraryReservationsVerificationSignature")
        verbose_name_plural = _("LibraryReservationsVerificationSignatures")
        indexes = [
            models.Index(fields=["code", "status"], name="librar_librar_45fd70e5_cd"),
            models.Index(fields=["created_at"], name="librar_librar_45fd70e5_cr"),
            models.Index(fields=["priority", "status"], name="librar_librar_45fd70e5_pr"),
            models.Index(fields=["department_tag", "status"], name="librar_librar_45fd70e5_dp"),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"

    def clean(self):
        super().clean()
        self.code = self.code.strip().upper()
        if self.capacity_limit < 0:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Capacity limit cannot be negative."))
        if self.allocated_count > self.capacity_limit:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Allocated count cannot exceed capacity limit."))
        if self.alert_threshold_low > self.alert_threshold_high:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Alert low threshold cannot exceed alert high threshold."))

    def is_expired(self) -> bool:
        """Determines whether this policy or record has passed its expiration date."""
        if not self.expiration_date:
            return False
        return timezone.now().date() > self.expiration_date

    def calculate_utilization(self) -> float:
        """Calculates percentage utilization against capacity limit."""
        if not self.capacity_limit or self.capacity_limit == 0:
            return 0.0
        return round((float(self.allocated_count) / float(self.capacity_limit)) * 100.0, 2)

    def has_available_capacity(self, delta: int = 1) -> bool:
        """Validates whether additional allocations can be committed."""
        return (self.allocated_count + delta) <= self.capacity_limit

    def increment_allocation(self, delta: int = 1) -> None:
        """Safely increments the committed allocation counter."""
        if not self.has_available_capacity(delta):
            from core.exceptions import CapacityExceededException
            raise CapacityExceededException(f"Cannot allocate {delta} units: Capacity limit reached.")
        self.allocated_count += delta
        self.save(update_fields=["allocated_count", "updated_at"])

    def decrement_allocation(self, delta: int = 1) -> None:
        """Safely decrements the allocated resource counter."""
        self.allocated_count = max(0, self.allocated_count - delta)
        self.save(update_fields=["allocated_count", "updated_at"])

    def mark_as_verified(self, approver: str = "SYSTEM") -> None:
        """Validates verification state and records signature in metadata."""
        self.is_verified = True
        self.metadata["verified_by"] = approver
        self.metadata["verified_at"] = timezone.now().isoformat()
        self.save(update_fields=["is_verified", "metadata", "updated_at"])

    def lock_record(self, reason: str = "Administrative Lock") -> None:
        """Freezes entity modifications for audit verification."""
        self.is_locked = True
        self.metadata["lock_reason"] = reason
        self.metadata["locked_at"] = timezone.now().isoformat()
        self.save(update_fields=["is_locked", "metadata", "updated_at"])

    def unlock_record(self) -> None:
        """Releases entity lock following audit review."""
        self.is_locked = False
        self.metadata["unlocked_at"] = timezone.now().isoformat()
        self.save(update_fields=["is_locked", "metadata", "updated_at"])

    def compute_composite_score(self) -> Decimal:
        """Computes a multi-factor score incorporating rating, priority, and capacity load."""
        utilization = Decimal(str(self.calculate_utilization()))
        return round((self.score_rating * Decimal("0.60")) + (Decimal(self.priority) * Decimal("0.20")) + (utilization * Decimal("0.002")), 4)

    def is_escalation_required(self) -> bool:
        """Determines if utilization exceeds high alert threshold."""
        return self.calculate_utilization() >= float(self.alert_threshold_high)

    def calculate_depreciation(self, annual_rate: Decimal = Decimal("0.10")) -> Decimal:
        """Calculates asset depreciation over operational lifecycle."""
        years = max(1, (timezone.now().date() - self.effective_date).days // 365)
        depreciated = self.monetary_value * ((Decimal("1.00") - annual_rate) ** years)
        return round(max(Decimal("0.00"), depreciated), 2)

    def to_summary_dict(self) -> dict:
        """Exports a standardized dictionary representation for APIs and reports."""
        return {
            "code": self.code,
            "name": self.name,
            "status": self.status,
            "priority": self.priority,
            "department_tag": self.department_tag,
            "fiscal_code": self.fiscal_code,
            "approval_authority": self.approval_authority,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "is_locked": self.is_locked,
            "capacity_limit": self.capacity_limit,
            "allocated_count": self.allocated_count,
            "utilization_pct": self.calculate_utilization(),
            "composite_score": str(self.compute_composite_score()),
            "monetary_value": str(self.monetary_value),
            "created_at": self.created_at.isoformat(),
        }

class LibraryReservationsNotificationRuleQuerySet(models.QuerySet):
    """Custom QuerySet methods for LibraryReservationsNotificationRule."""
    def active(self):
        return self.filter(is_active=True)
    def recent(self, days: int = 30):
        cutoff = timezone.now() - timezone.timedelta(days=days)
        return self.filter(created_at__gte=cutoff)
    def search(self, query: str):
        if not query:
            return self
        return self.filter(models.Q(code__icontains=query) | models.Q(name__icontains=query))
    def verified(self):
        return self.filter(is_verified=True)
    def by_status(self, status: str):
        return self.filter(status=status)
    def priority_ordered(self):
        return self.order_by("-priority", "-created_at")
    def capacity_available(self):
        return self.filter(allocated_count__lt=models.F("capacity_limit"))
    def threshold_exceeded(self):
        return self.filter(allocated_count__gte=models.F("capacity_limit"))
    def with_high_score(self, min_score: Decimal = Decimal("3.00")):
        return self.filter(score_rating__gte=min_score)

class LibraryReservationsNotificationRuleManager(models.Manager):
    """Custom model manager for LibraryReservationsNotificationRule."""
    def get_queryset(self):
        return LibraryReservationsNotificationRuleQuerySet(self.model, using=self._db)
    def active(self):
        return self.get_queryset().active()
    def search(self, query: str):
        return self.get_queryset().search(query)
    def verified(self):
        return self.get_queryset().verified()
    def by_status(self, status: str):
        return self.get_queryset().by_status(status)
    def capacity_available(self):
        return self.get_queryset().capacity_available()

class LibraryReservationsNotificationRule(models.Model):
    """
    LibraryReservationsNotificationRule: Event-driven notification triggers and audience matrices.
    Enterprise Grade Institutional Entity with strict audit trails and SQLite optimization.
    """
    code = models.CharField(max_length=64, unique=True, db_index=True, verbose_name=_("Entity Code"))
    name = models.CharField(max_length=255, db_index=True, verbose_name=_("Entity Name"))
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True, verbose_name=_("Slug"))
    description = models.TextField(blank=True, default="", verbose_name=_("Description"))
    priority = models.PositiveIntegerField(default=1, verbose_name=_("Priority Weight"))
    status = models.CharField(max_length=32, default="ACTIVE", db_index=True, verbose_name=_("Status"))
    is_active = models.BooleanField(default=True, db_index=True, verbose_name=_("Active Flag"))
    is_verified = models.BooleanField(default=False, verbose_name=_("Verified Flag"))
    is_locked = models.BooleanField(default=False, verbose_name=_("Lock Flag"))
    score_rating = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"), verbose_name=_("Score"))
    monetary_value = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"), verbose_name=_("Monetary Value"))
    capacity_limit = models.PositiveIntegerField(default=100, verbose_name=_("Capacity Limit"))
    allocated_count = models.PositiveIntegerField(default=0, verbose_name=_("Allocated Count"))
    waitlist_count = models.PositiveIntegerField(default=0, verbose_name=_("Waitlist Count"))
    alert_threshold_low = models.PositiveIntegerField(default=10, verbose_name=_("Alert Low"))
    alert_threshold_high = models.PositiveIntegerField(default=90, verbose_name=_("Alert High"))
    renewal_cycle_months = models.PositiveIntegerField(default=12, verbose_name=_("Renewal Months"))
    department_tag = models.CharField(max_length=64, blank=True, default="LIBRARY", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@library.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = LibraryReservationsNotificationRuleManager()

    class Meta:
        db_table = "library_library_reservations_notificationrule"
        ordering = ["-created_at", "code"]
        verbose_name = _("LibraryReservationsNotificationRule")
        verbose_name_plural = _("LibraryReservationsNotificationRules")
        indexes = [
            models.Index(fields=["code", "status"], name="librar_librar_621bec23_cd"),
            models.Index(fields=["created_at"], name="librar_librar_621bec23_cr"),
            models.Index(fields=["priority", "status"], name="librar_librar_621bec23_pr"),
            models.Index(fields=["department_tag", "status"], name="librar_librar_621bec23_dp"),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"

    def clean(self):
        super().clean()
        self.code = self.code.strip().upper()
        if self.capacity_limit < 0:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Capacity limit cannot be negative."))
        if self.allocated_count > self.capacity_limit:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Allocated count cannot exceed capacity limit."))
        if self.alert_threshold_low > self.alert_threshold_high:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Alert low threshold cannot exceed alert high threshold."))

    def is_expired(self) -> bool:
        """Determines whether this policy or record has passed its expiration date."""
        if not self.expiration_date:
            return False
        return timezone.now().date() > self.expiration_date

    def calculate_utilization(self) -> float:
        """Calculates percentage utilization against capacity limit."""
        if not self.capacity_limit or self.capacity_limit == 0:
            return 0.0
        return round((float(self.allocated_count) / float(self.capacity_limit)) * 100.0, 2)

    def has_available_capacity(self, delta: int = 1) -> bool:
        """Validates whether additional allocations can be committed."""
        return (self.allocated_count + delta) <= self.capacity_limit

    def increment_allocation(self, delta: int = 1) -> None:
        """Safely increments the committed allocation counter."""
        if not self.has_available_capacity(delta):
            from core.exceptions import CapacityExceededException
            raise CapacityExceededException(f"Cannot allocate {delta} units: Capacity limit reached.")
        self.allocated_count += delta
        self.save(update_fields=["allocated_count", "updated_at"])

    def decrement_allocation(self, delta: int = 1) -> None:
        """Safely decrements the allocated resource counter."""
        self.allocated_count = max(0, self.allocated_count - delta)
        self.save(update_fields=["allocated_count", "updated_at"])

    def mark_as_verified(self, approver: str = "SYSTEM") -> None:
        """Validates verification state and records signature in metadata."""
        self.is_verified = True
        self.metadata["verified_by"] = approver
        self.metadata["verified_at"] = timezone.now().isoformat()
        self.save(update_fields=["is_verified", "metadata", "updated_at"])

    def lock_record(self, reason: str = "Administrative Lock") -> None:
        """Freezes entity modifications for audit verification."""
        self.is_locked = True
        self.metadata["lock_reason"] = reason
        self.metadata["locked_at"] = timezone.now().isoformat()
        self.save(update_fields=["is_locked", "metadata", "updated_at"])

    def unlock_record(self) -> None:
        """Releases entity lock following audit review."""
        self.is_locked = False
        self.metadata["unlocked_at"] = timezone.now().isoformat()
        self.save(update_fields=["is_locked", "metadata", "updated_at"])

    def compute_composite_score(self) -> Decimal:
        """Computes a multi-factor score incorporating rating, priority, and capacity load."""
        utilization = Decimal(str(self.calculate_utilization()))
        return round((self.score_rating * Decimal("0.60")) + (Decimal(self.priority) * Decimal("0.20")) + (utilization * Decimal("0.002")), 4)

    def is_escalation_required(self) -> bool:
        """Determines if utilization exceeds high alert threshold."""
        return self.calculate_utilization() >= float(self.alert_threshold_high)

    def calculate_depreciation(self, annual_rate: Decimal = Decimal("0.10")) -> Decimal:
        """Calculates asset depreciation over operational lifecycle."""
        years = max(1, (timezone.now().date() - self.effective_date).days // 365)
        depreciated = self.monetary_value * ((Decimal("1.00") - annual_rate) ** years)
        return round(max(Decimal("0.00"), depreciated), 2)

    def to_summary_dict(self) -> dict:
        """Exports a standardized dictionary representation for APIs and reports."""
        return {
            "code": self.code,
            "name": self.name,
            "status": self.status,
            "priority": self.priority,
            "department_tag": self.department_tag,
            "fiscal_code": self.fiscal_code,
            "approval_authority": self.approval_authority,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "is_locked": self.is_locked,
            "capacity_limit": self.capacity_limit,
            "allocated_count": self.allocated_count,
            "utilization_pct": self.calculate_utilization(),
            "composite_score": str(self.compute_composite_score()),
            "monetary_value": str(self.monetary_value),
            "created_at": self.created_at.isoformat(),
        }

class LibraryReservationsAnalyticalSnapshotQuerySet(models.QuerySet):
    """Custom QuerySet methods for LibraryReservationsAnalyticalSnapshot."""
    def active(self):
        return self.filter(is_active=True)
    def recent(self, days: int = 30):
        cutoff = timezone.now() - timezone.timedelta(days=days)
        return self.filter(created_at__gte=cutoff)
    def search(self, query: str):
        if not query:
            return self
        return self.filter(models.Q(code__icontains=query) | models.Q(name__icontains=query))
    def verified(self):
        return self.filter(is_verified=True)
    def by_status(self, status: str):
        return self.filter(status=status)
    def priority_ordered(self):
        return self.order_by("-priority", "-created_at")
    def capacity_available(self):
        return self.filter(allocated_count__lt=models.F("capacity_limit"))
    def threshold_exceeded(self):
        return self.filter(allocated_count__gte=models.F("capacity_limit"))
    def with_high_score(self, min_score: Decimal = Decimal("3.00")):
        return self.filter(score_rating__gte=min_score)

class LibraryReservationsAnalyticalSnapshotManager(models.Manager):
    """Custom model manager for LibraryReservationsAnalyticalSnapshot."""
    def get_queryset(self):
        return LibraryReservationsAnalyticalSnapshotQuerySet(self.model, using=self._db)
    def active(self):
        return self.get_queryset().active()
    def search(self, query: str):
        return self.get_queryset().search(query)
    def verified(self):
        return self.get_queryset().verified()
    def by_status(self, status: str):
        return self.get_queryset().by_status(status)
    def capacity_available(self):
        return self.get_queryset().capacity_available()

class LibraryReservationsAnalyticalSnapshot(models.Model):
    """
    LibraryReservationsAnalyticalSnapshot: Aggregated telemetry snapshot capturing historical trend data.
    Enterprise Grade Institutional Entity with strict audit trails and SQLite optimization.
    """
    code = models.CharField(max_length=64, unique=True, db_index=True, verbose_name=_("Entity Code"))
    name = models.CharField(max_length=255, db_index=True, verbose_name=_("Entity Name"))
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True, verbose_name=_("Slug"))
    description = models.TextField(blank=True, default="", verbose_name=_("Description"))
    priority = models.PositiveIntegerField(default=1, verbose_name=_("Priority Weight"))
    status = models.CharField(max_length=32, default="ACTIVE", db_index=True, verbose_name=_("Status"))
    is_active = models.BooleanField(default=True, db_index=True, verbose_name=_("Active Flag"))
    is_verified = models.BooleanField(default=False, verbose_name=_("Verified Flag"))
    is_locked = models.BooleanField(default=False, verbose_name=_("Lock Flag"))
    score_rating = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"), verbose_name=_("Score"))
    monetary_value = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"), verbose_name=_("Monetary Value"))
    capacity_limit = models.PositiveIntegerField(default=100, verbose_name=_("Capacity Limit"))
    allocated_count = models.PositiveIntegerField(default=0, verbose_name=_("Allocated Count"))
    waitlist_count = models.PositiveIntegerField(default=0, verbose_name=_("Waitlist Count"))
    alert_threshold_low = models.PositiveIntegerField(default=10, verbose_name=_("Alert Low"))
    alert_threshold_high = models.PositiveIntegerField(default=90, verbose_name=_("Alert High"))
    renewal_cycle_months = models.PositiveIntegerField(default=12, verbose_name=_("Renewal Months"))
    department_tag = models.CharField(max_length=64, blank=True, default="LIBRARY", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@library.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = LibraryReservationsAnalyticalSnapshotManager()

    class Meta:
        db_table = "library_library_reservations_analyticalsnapshot"
        ordering = ["-created_at", "code"]
        verbose_name = _("LibraryReservationsAnalyticalSnapshot")
        verbose_name_plural = _("LibraryReservationsAnalyticalSnapshots")
        indexes = [
            models.Index(fields=["code", "status"], name="librar_librar_e0c8a508_cd"),
            models.Index(fields=["created_at"], name="librar_librar_e0c8a508_cr"),
            models.Index(fields=["priority", "status"], name="librar_librar_e0c8a508_pr"),
            models.Index(fields=["department_tag", "status"], name="librar_librar_e0c8a508_dp"),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"

    def clean(self):
        super().clean()
        self.code = self.code.strip().upper()
        if self.capacity_limit < 0:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Capacity limit cannot be negative."))
        if self.allocated_count > self.capacity_limit:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Allocated count cannot exceed capacity limit."))
        if self.alert_threshold_low > self.alert_threshold_high:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Alert low threshold cannot exceed alert high threshold."))

    def is_expired(self) -> bool:
        """Determines whether this policy or record has passed its expiration date."""
        if not self.expiration_date:
            return False
        return timezone.now().date() > self.expiration_date

    def calculate_utilization(self) -> float:
        """Calculates percentage utilization against capacity limit."""
        if not self.capacity_limit or self.capacity_limit == 0:
            return 0.0
        return round((float(self.allocated_count) / float(self.capacity_limit)) * 100.0, 2)

    def has_available_capacity(self, delta: int = 1) -> bool:
        """Validates whether additional allocations can be committed."""
        return (self.allocated_count + delta) <= self.capacity_limit

    def increment_allocation(self, delta: int = 1) -> None:
        """Safely increments the committed allocation counter."""
        if not self.has_available_capacity(delta):
            from core.exceptions import CapacityExceededException
            raise CapacityExceededException(f"Cannot allocate {delta} units: Capacity limit reached.")
        self.allocated_count += delta
        self.save(update_fields=["allocated_count", "updated_at"])

    def decrement_allocation(self, delta: int = 1) -> None:
        """Safely decrements the allocated resource counter."""
        self.allocated_count = max(0, self.allocated_count - delta)
        self.save(update_fields=["allocated_count", "updated_at"])

    def mark_as_verified(self, approver: str = "SYSTEM") -> None:
        """Validates verification state and records signature in metadata."""
        self.is_verified = True
        self.metadata["verified_by"] = approver
        self.metadata["verified_at"] = timezone.now().isoformat()
        self.save(update_fields=["is_verified", "metadata", "updated_at"])

    def lock_record(self, reason: str = "Administrative Lock") -> None:
        """Freezes entity modifications for audit verification."""
        self.is_locked = True
        self.metadata["lock_reason"] = reason
        self.metadata["locked_at"] = timezone.now().isoformat()
        self.save(update_fields=["is_locked", "metadata", "updated_at"])

    def unlock_record(self) -> None:
        """Releases entity lock following audit review."""
        self.is_locked = False
        self.metadata["unlocked_at"] = timezone.now().isoformat()
        self.save(update_fields=["is_locked", "metadata", "updated_at"])

    def compute_composite_score(self) -> Decimal:
        """Computes a multi-factor score incorporating rating, priority, and capacity load."""
        utilization = Decimal(str(self.calculate_utilization()))
        return round((self.score_rating * Decimal("0.60")) + (Decimal(self.priority) * Decimal("0.20")) + (utilization * Decimal("0.002")), 4)

    def is_escalation_required(self) -> bool:
        """Determines if utilization exceeds high alert threshold."""
        return self.calculate_utilization() >= float(self.alert_threshold_high)

    def calculate_depreciation(self, annual_rate: Decimal = Decimal("0.10")) -> Decimal:
        """Calculates asset depreciation over operational lifecycle."""
        years = max(1, (timezone.now().date() - self.effective_date).days // 365)
        depreciated = self.monetary_value * ((Decimal("1.00") - annual_rate) ** years)
        return round(max(Decimal("0.00"), depreciated), 2)

    def to_summary_dict(self) -> dict:
        """Exports a standardized dictionary representation for APIs and reports."""
        return {
            "code": self.code,
            "name": self.name,
            "status": self.status,
            "priority": self.priority,
            "department_tag": self.department_tag,
            "fiscal_code": self.fiscal_code,
            "approval_authority": self.approval_authority,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "is_locked": self.is_locked,
            "capacity_limit": self.capacity_limit,
            "allocated_count": self.allocated_count,
            "utilization_pct": self.calculate_utilization(),
            "composite_score": str(self.compute_composite_score()),
            "monetary_value": str(self.monetary_value),
            "created_at": self.created_at.isoformat(),
        }

class LibraryReservationsComplianceLogQuerySet(models.QuerySet):
    """Custom QuerySet methods for LibraryReservationsComplianceLog."""
    def active(self):
        return self.filter(is_active=True)
    def recent(self, days: int = 30):
        cutoff = timezone.now() - timezone.timedelta(days=days)
        return self.filter(created_at__gte=cutoff)
    def search(self, query: str):
        if not query:
            return self
        return self.filter(models.Q(code__icontains=query) | models.Q(name__icontains=query))
    def verified(self):
        return self.filter(is_verified=True)
    def by_status(self, status: str):
        return self.filter(status=status)
    def priority_ordered(self):
        return self.order_by("-priority", "-created_at")
    def capacity_available(self):
        return self.filter(allocated_count__lt=models.F("capacity_limit"))
    def threshold_exceeded(self):
        return self.filter(allocated_count__gte=models.F("capacity_limit"))
    def with_high_score(self, min_score: Decimal = Decimal("3.00")):
        return self.filter(score_rating__gte=min_score)

class LibraryReservationsComplianceLogManager(models.Manager):
    """Custom model manager for LibraryReservationsComplianceLog."""
    def get_queryset(self):
        return LibraryReservationsComplianceLogQuerySet(self.model, using=self._db)
    def active(self):
        return self.get_queryset().active()
    def search(self, query: str):
        return self.get_queryset().search(query)
    def verified(self):
        return self.get_queryset().verified()
    def by_status(self, status: str):
        return self.get_queryset().by_status(status)
    def capacity_available(self):
        return self.get_queryset().capacity_available()

class LibraryReservationsComplianceLog(models.Model):
    """
    LibraryReservationsComplianceLog: Regulatory compliance inspections and institutional certifications.
    Enterprise Grade Institutional Entity with strict audit trails and SQLite optimization.
    """
    code = models.CharField(max_length=64, unique=True, db_index=True, verbose_name=_("Entity Code"))
    name = models.CharField(max_length=255, db_index=True, verbose_name=_("Entity Name"))
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True, verbose_name=_("Slug"))
    description = models.TextField(blank=True, default="", verbose_name=_("Description"))
    priority = models.PositiveIntegerField(default=1, verbose_name=_("Priority Weight"))
    status = models.CharField(max_length=32, default="ACTIVE", db_index=True, verbose_name=_("Status"))
    is_active = models.BooleanField(default=True, db_index=True, verbose_name=_("Active Flag"))
    is_verified = models.BooleanField(default=False, verbose_name=_("Verified Flag"))
    is_locked = models.BooleanField(default=False, verbose_name=_("Lock Flag"))
    score_rating = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"), verbose_name=_("Score"))
    monetary_value = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"), verbose_name=_("Monetary Value"))
    capacity_limit = models.PositiveIntegerField(default=100, verbose_name=_("Capacity Limit"))
    allocated_count = models.PositiveIntegerField(default=0, verbose_name=_("Allocated Count"))
    waitlist_count = models.PositiveIntegerField(default=0, verbose_name=_("Waitlist Count"))
    alert_threshold_low = models.PositiveIntegerField(default=10, verbose_name=_("Alert Low"))
    alert_threshold_high = models.PositiveIntegerField(default=90, verbose_name=_("Alert High"))
    renewal_cycle_months = models.PositiveIntegerField(default=12, verbose_name=_("Renewal Months"))
    department_tag = models.CharField(max_length=64, blank=True, default="LIBRARY", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@library.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = LibraryReservationsComplianceLogManager()

    class Meta:
        db_table = "library_library_reservations_compliancelog"
        ordering = ["-created_at", "code"]
        verbose_name = _("LibraryReservationsComplianceLog")
        verbose_name_plural = _("LibraryReservationsComplianceLogs")
        indexes = [
            models.Index(fields=["code", "status"], name="librar_librar_1a1ec693_cd"),
            models.Index(fields=["created_at"], name="librar_librar_1a1ec693_cr"),
            models.Index(fields=["priority", "status"], name="librar_librar_1a1ec693_pr"),
            models.Index(fields=["department_tag", "status"], name="librar_librar_1a1ec693_dp"),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"

    def clean(self):
        super().clean()
        self.code = self.code.strip().upper()
        if self.capacity_limit < 0:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Capacity limit cannot be negative."))
        if self.allocated_count > self.capacity_limit:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Allocated count cannot exceed capacity limit."))
        if self.alert_threshold_low > self.alert_threshold_high:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Alert low threshold cannot exceed alert high threshold."))

    def is_expired(self) -> bool:
        """Determines whether this policy or record has passed its expiration date."""
        if not self.expiration_date:
            return False
        return timezone.now().date() > self.expiration_date

    def calculate_utilization(self) -> float:
        """Calculates percentage utilization against capacity limit."""
        if not self.capacity_limit or self.capacity_limit == 0:
            return 0.0
        return round((float(self.allocated_count) / float(self.capacity_limit)) * 100.0, 2)

    def has_available_capacity(self, delta: int = 1) -> bool:
        """Validates whether additional allocations can be committed."""
        return (self.allocated_count + delta) <= self.capacity_limit

    def increment_allocation(self, delta: int = 1) -> None:
        """Safely increments the committed allocation counter."""
        if not self.has_available_capacity(delta):
            from core.exceptions import CapacityExceededException
            raise CapacityExceededException(f"Cannot allocate {delta} units: Capacity limit reached.")
        self.allocated_count += delta
        self.save(update_fields=["allocated_count", "updated_at"])

    def decrement_allocation(self, delta: int = 1) -> None:
        """Safely decrements the allocated resource counter."""
        self.allocated_count = max(0, self.allocated_count - delta)
        self.save(update_fields=["allocated_count", "updated_at"])

    def mark_as_verified(self, approver: str = "SYSTEM") -> None:
        """Validates verification state and records signature in metadata."""
        self.is_verified = True
        self.metadata["verified_by"] = approver
        self.metadata["verified_at"] = timezone.now().isoformat()
        self.save(update_fields=["is_verified", "metadata", "updated_at"])

    def lock_record(self, reason: str = "Administrative Lock") -> None:
        """Freezes entity modifications for audit verification."""
        self.is_locked = True
        self.metadata["lock_reason"] = reason
        self.metadata["locked_at"] = timezone.now().isoformat()
        self.save(update_fields=["is_locked", "metadata", "updated_at"])

    def unlock_record(self) -> None:
        """Releases entity lock following audit review."""
        self.is_locked = False
        self.metadata["unlocked_at"] = timezone.now().isoformat()
        self.save(update_fields=["is_locked", "metadata", "updated_at"])

    def compute_composite_score(self) -> Decimal:
        """Computes a multi-factor score incorporating rating, priority, and capacity load."""
        utilization = Decimal(str(self.calculate_utilization()))
        return round((self.score_rating * Decimal("0.60")) + (Decimal(self.priority) * Decimal("0.20")) + (utilization * Decimal("0.002")), 4)

    def is_escalation_required(self) -> bool:
        """Determines if utilization exceeds high alert threshold."""
        return self.calculate_utilization() >= float(self.alert_threshold_high)

    def calculate_depreciation(self, annual_rate: Decimal = Decimal("0.10")) -> Decimal:
        """Calculates asset depreciation over operational lifecycle."""
        years = max(1, (timezone.now().date() - self.effective_date).days // 365)
        depreciated = self.monetary_value * ((Decimal("1.00") - annual_rate) ** years)
        return round(max(Decimal("0.00"), depreciated), 2)

    def to_summary_dict(self) -> dict:
        """Exports a standardized dictionary representation for APIs and reports."""
        return {
            "code": self.code,
            "name": self.name,
            "status": self.status,
            "priority": self.priority,
            "department_tag": self.department_tag,
            "fiscal_code": self.fiscal_code,
            "approval_authority": self.approval_authority,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "is_locked": self.is_locked,
            "capacity_limit": self.capacity_limit,
            "allocated_count": self.allocated_count,
            "utilization_pct": self.calculate_utilization(),
            "composite_score": str(self.compute_composite_score()),
            "monetary_value": str(self.monetary_value),
            "created_at": self.created_at.isoformat(),
        }

class LibraryReservationsIntegrationBridgeQuerySet(models.QuerySet):
    """Custom QuerySet methods for LibraryReservationsIntegrationBridge."""
    def active(self):
        return self.filter(is_active=True)
    def recent(self, days: int = 30):
        cutoff = timezone.now() - timezone.timedelta(days=days)
        return self.filter(created_at__gte=cutoff)
    def search(self, query: str):
        if not query:
            return self
        return self.filter(models.Q(code__icontains=query) | models.Q(name__icontains=query))
    def verified(self):
        return self.filter(is_verified=True)
    def by_status(self, status: str):
        return self.filter(status=status)
    def priority_ordered(self):
        return self.order_by("-priority", "-created_at")
    def capacity_available(self):
        return self.filter(allocated_count__lt=models.F("capacity_limit"))
    def threshold_exceeded(self):
        return self.filter(allocated_count__gte=models.F("capacity_limit"))
    def with_high_score(self, min_score: Decimal = Decimal("3.00")):
        return self.filter(score_rating__gte=min_score)

class LibraryReservationsIntegrationBridgeManager(models.Manager):
    """Custom model manager for LibraryReservationsIntegrationBridge."""
    def get_queryset(self):
        return LibraryReservationsIntegrationBridgeQuerySet(self.model, using=self._db)
    def active(self):
        return self.get_queryset().active()
    def search(self, query: str):
        return self.get_queryset().search(query)
    def verified(self):
        return self.get_queryset().verified()
    def by_status(self, status: str):
        return self.get_queryset().by_status(status)
    def capacity_available(self):
        return self.get_queryset().capacity_available()

class LibraryReservationsIntegrationBridge(models.Model):
    """
    LibraryReservationsIntegrationBridge: External system integration endpoints and payload exchange records.
    Enterprise Grade Institutional Entity with strict audit trails and SQLite optimization.
    """
    code = models.CharField(max_length=64, unique=True, db_index=True, verbose_name=_("Entity Code"))
    name = models.CharField(max_length=255, db_index=True, verbose_name=_("Entity Name"))
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True, verbose_name=_("Slug"))
    description = models.TextField(blank=True, default="", verbose_name=_("Description"))
    priority = models.PositiveIntegerField(default=1, verbose_name=_("Priority Weight"))
    status = models.CharField(max_length=32, default="ACTIVE", db_index=True, verbose_name=_("Status"))
    is_active = models.BooleanField(default=True, db_index=True, verbose_name=_("Active Flag"))
    is_verified = models.BooleanField(default=False, verbose_name=_("Verified Flag"))
    is_locked = models.BooleanField(default=False, verbose_name=_("Lock Flag"))
    score_rating = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"), verbose_name=_("Score"))
    monetary_value = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"), verbose_name=_("Monetary Value"))
    capacity_limit = models.PositiveIntegerField(default=100, verbose_name=_("Capacity Limit"))
    allocated_count = models.PositiveIntegerField(default=0, verbose_name=_("Allocated Count"))
    waitlist_count = models.PositiveIntegerField(default=0, verbose_name=_("Waitlist Count"))
    alert_threshold_low = models.PositiveIntegerField(default=10, verbose_name=_("Alert Low"))
    alert_threshold_high = models.PositiveIntegerField(default=90, verbose_name=_("Alert High"))
    renewal_cycle_months = models.PositiveIntegerField(default=12, verbose_name=_("Renewal Months"))
    department_tag = models.CharField(max_length=64, blank=True, default="LIBRARY", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@library.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = LibraryReservationsIntegrationBridgeManager()

    class Meta:
        db_table = "library_library_reservations_integrationbridge"
        ordering = ["-created_at", "code"]
        verbose_name = _("LibraryReservationsIntegrationBridge")
        verbose_name_plural = _("LibraryReservationsIntegrationBridges")
        indexes = [
            models.Index(fields=["code", "status"], name="librar_librar_d864a252_cd"),
            models.Index(fields=["created_at"], name="librar_librar_d864a252_cr"),
            models.Index(fields=["priority", "status"], name="librar_librar_d864a252_pr"),
            models.Index(fields=["department_tag", "status"], name="librar_librar_d864a252_dp"),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"

    def clean(self):
        super().clean()
        self.code = self.code.strip().upper()
        if self.capacity_limit < 0:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Capacity limit cannot be negative."))
        if self.allocated_count > self.capacity_limit:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Allocated count cannot exceed capacity limit."))
        if self.alert_threshold_low > self.alert_threshold_high:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Alert low threshold cannot exceed alert high threshold."))

    def is_expired(self) -> bool:
        """Determines whether this policy or record has passed its expiration date."""
        if not self.expiration_date:
            return False
        return timezone.now().date() > self.expiration_date

    def calculate_utilization(self) -> float:
        """Calculates percentage utilization against capacity limit."""
        if not self.capacity_limit or self.capacity_limit == 0:
            return 0.0
        return round((float(self.allocated_count) / float(self.capacity_limit)) * 100.0, 2)

    def has_available_capacity(self, delta: int = 1) -> bool:
        """Validates whether additional allocations can be committed."""
        return (self.allocated_count + delta) <= self.capacity_limit

    def increment_allocation(self, delta: int = 1) -> None:
        """Safely increments the committed allocation counter."""
        if not self.has_available_capacity(delta):
            from core.exceptions import CapacityExceededException
            raise CapacityExceededException(f"Cannot allocate {delta} units: Capacity limit reached.")
        self.allocated_count += delta
        self.save(update_fields=["allocated_count", "updated_at"])

    def decrement_allocation(self, delta: int = 1) -> None:
        """Safely decrements the allocated resource counter."""
        self.allocated_count = max(0, self.allocated_count - delta)
        self.save(update_fields=["allocated_count", "updated_at"])

    def mark_as_verified(self, approver: str = "SYSTEM") -> None:
        """Validates verification state and records signature in metadata."""
        self.is_verified = True
        self.metadata["verified_by"] = approver
        self.metadata["verified_at"] = timezone.now().isoformat()
        self.save(update_fields=["is_verified", "metadata", "updated_at"])

    def lock_record(self, reason: str = "Administrative Lock") -> None:
        """Freezes entity modifications for audit verification."""
        self.is_locked = True
        self.metadata["lock_reason"] = reason
        self.metadata["locked_at"] = timezone.now().isoformat()
        self.save(update_fields=["is_locked", "metadata", "updated_at"])

    def unlock_record(self) -> None:
        """Releases entity lock following audit review."""
        self.is_locked = False
        self.metadata["unlocked_at"] = timezone.now().isoformat()
        self.save(update_fields=["is_locked", "metadata", "updated_at"])

    def compute_composite_score(self) -> Decimal:
        """Computes a multi-factor score incorporating rating, priority, and capacity load."""
        utilization = Decimal(str(self.calculate_utilization()))
        return round((self.score_rating * Decimal("0.60")) + (Decimal(self.priority) * Decimal("0.20")) + (utilization * Decimal("0.002")), 4)

    def is_escalation_required(self) -> bool:
        """Determines if utilization exceeds high alert threshold."""
        return self.calculate_utilization() >= float(self.alert_threshold_high)

    def calculate_depreciation(self, annual_rate: Decimal = Decimal("0.10")) -> Decimal:
        """Calculates asset depreciation over operational lifecycle."""
        years = max(1, (timezone.now().date() - self.effective_date).days // 365)
        depreciated = self.monetary_value * ((Decimal("1.00") - annual_rate) ** years)
        return round(max(Decimal("0.00"), depreciated), 2)

    def to_summary_dict(self) -> dict:
        """Exports a standardized dictionary representation for APIs and reports."""
        return {
            "code": self.code,
            "name": self.name,
            "status": self.status,
            "priority": self.priority,
            "department_tag": self.department_tag,
            "fiscal_code": self.fiscal_code,
            "approval_authority": self.approval_authority,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "is_locked": self.is_locked,
            "capacity_limit": self.capacity_limit,
            "allocated_count": self.allocated_count,
            "utilization_pct": self.calculate_utilization(),
            "composite_score": str(self.compute_composite_score()),
            "monetary_value": str(self.monetary_value),
            "created_at": self.created_at.isoformat(),
        }

class LibraryReservationsSecurityPermitQuerySet(models.QuerySet):
    """Custom QuerySet methods for LibraryReservationsSecurityPermit."""
    def active(self):
        return self.filter(is_active=True)
    def recent(self, days: int = 30):
        cutoff = timezone.now() - timezone.timedelta(days=days)
        return self.filter(created_at__gte=cutoff)
    def search(self, query: str):
        if not query:
            return self
        return self.filter(models.Q(code__icontains=query) | models.Q(name__icontains=query))
    def verified(self):
        return self.filter(is_verified=True)
    def by_status(self, status: str):
        return self.filter(status=status)
    def priority_ordered(self):
        return self.order_by("-priority", "-created_at")
    def capacity_available(self):
        return self.filter(allocated_count__lt=models.F("capacity_limit"))
    def threshold_exceeded(self):
        return self.filter(allocated_count__gte=models.F("capacity_limit"))
    def with_high_score(self, min_score: Decimal = Decimal("3.00")):
        return self.filter(score_rating__gte=min_score)

class LibraryReservationsSecurityPermitManager(models.Manager):
    """Custom model manager for LibraryReservationsSecurityPermit."""
    def get_queryset(self):
        return LibraryReservationsSecurityPermitQuerySet(self.model, using=self._db)
    def active(self):
        return self.get_queryset().active()
    def search(self, query: str):
        return self.get_queryset().search(query)
    def verified(self):
        return self.get_queryset().verified()
    def by_status(self, status: str):
        return self.get_queryset().by_status(status)
    def capacity_available(self):
        return self.get_queryset().capacity_available()

class LibraryReservationsSecurityPermit(models.Model):
    """
    LibraryReservationsSecurityPermit: Granular authorization token defining scoped operational access.
    Enterprise Grade Institutional Entity with strict audit trails and SQLite optimization.
    """
    code = models.CharField(max_length=64, unique=True, db_index=True, verbose_name=_("Entity Code"))
    name = models.CharField(max_length=255, db_index=True, verbose_name=_("Entity Name"))
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True, verbose_name=_("Slug"))
    description = models.TextField(blank=True, default="", verbose_name=_("Description"))
    priority = models.PositiveIntegerField(default=1, verbose_name=_("Priority Weight"))
    status = models.CharField(max_length=32, default="ACTIVE", db_index=True, verbose_name=_("Status"))
    is_active = models.BooleanField(default=True, db_index=True, verbose_name=_("Active Flag"))
    is_verified = models.BooleanField(default=False, verbose_name=_("Verified Flag"))
    is_locked = models.BooleanField(default=False, verbose_name=_("Lock Flag"))
    score_rating = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"), verbose_name=_("Score"))
    monetary_value = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"), verbose_name=_("Monetary Value"))
    capacity_limit = models.PositiveIntegerField(default=100, verbose_name=_("Capacity Limit"))
    allocated_count = models.PositiveIntegerField(default=0, verbose_name=_("Allocated Count"))
    waitlist_count = models.PositiveIntegerField(default=0, verbose_name=_("Waitlist Count"))
    alert_threshold_low = models.PositiveIntegerField(default=10, verbose_name=_("Alert Low"))
    alert_threshold_high = models.PositiveIntegerField(default=90, verbose_name=_("Alert High"))
    renewal_cycle_months = models.PositiveIntegerField(default=12, verbose_name=_("Renewal Months"))
    department_tag = models.CharField(max_length=64, blank=True, default="LIBRARY", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@library.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = LibraryReservationsSecurityPermitManager()

    class Meta:
        db_table = "library_library_reservations_securitypermit"
        ordering = ["-created_at", "code"]
        verbose_name = _("LibraryReservationsSecurityPermit")
        verbose_name_plural = _("LibraryReservationsSecurityPermits")
        indexes = [
            models.Index(fields=["code", "status"], name="librar_librar_697a46fa_cd"),
            models.Index(fields=["created_at"], name="librar_librar_697a46fa_cr"),
            models.Index(fields=["priority", "status"], name="librar_librar_697a46fa_pr"),
            models.Index(fields=["department_tag", "status"], name="librar_librar_697a46fa_dp"),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"

    def clean(self):
        super().clean()
        self.code = self.code.strip().upper()
        if self.capacity_limit < 0:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Capacity limit cannot be negative."))
        if self.allocated_count > self.capacity_limit:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Allocated count cannot exceed capacity limit."))
        if self.alert_threshold_low > self.alert_threshold_high:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Alert low threshold cannot exceed alert high threshold."))

    def is_expired(self) -> bool:
        """Determines whether this policy or record has passed its expiration date."""
        if not self.expiration_date:
            return False
        return timezone.now().date() > self.expiration_date

    def calculate_utilization(self) -> float:
        """Calculates percentage utilization against capacity limit."""
        if not self.capacity_limit or self.capacity_limit == 0:
            return 0.0
        return round((float(self.allocated_count) / float(self.capacity_limit)) * 100.0, 2)

    def has_available_capacity(self, delta: int = 1) -> bool:
        """Validates whether additional allocations can be committed."""
        return (self.allocated_count + delta) <= self.capacity_limit

    def increment_allocation(self, delta: int = 1) -> None:
        """Safely increments the committed allocation counter."""
        if not self.has_available_capacity(delta):
            from core.exceptions import CapacityExceededException
            raise CapacityExceededException(f"Cannot allocate {delta} units: Capacity limit reached.")
        self.allocated_count += delta
        self.save(update_fields=["allocated_count", "updated_at"])

    def decrement_allocation(self, delta: int = 1) -> None:
        """Safely decrements the allocated resource counter."""
        self.allocated_count = max(0, self.allocated_count - delta)
        self.save(update_fields=["allocated_count", "updated_at"])

    def mark_as_verified(self, approver: str = "SYSTEM") -> None:
        """Validates verification state and records signature in metadata."""
        self.is_verified = True
        self.metadata["verified_by"] = approver
        self.metadata["verified_at"] = timezone.now().isoformat()
        self.save(update_fields=["is_verified", "metadata", "updated_at"])

    def lock_record(self, reason: str = "Administrative Lock") -> None:
        """Freezes entity modifications for audit verification."""
        self.is_locked = True
        self.metadata["lock_reason"] = reason
        self.metadata["locked_at"] = timezone.now().isoformat()
        self.save(update_fields=["is_locked", "metadata", "updated_at"])

    def unlock_record(self) -> None:
        """Releases entity lock following audit review."""
        self.is_locked = False
        self.metadata["unlocked_at"] = timezone.now().isoformat()
        self.save(update_fields=["is_locked", "metadata", "updated_at"])

    def compute_composite_score(self) -> Decimal:
        """Computes a multi-factor score incorporating rating, priority, and capacity load."""
        utilization = Decimal(str(self.calculate_utilization()))
        return round((self.score_rating * Decimal("0.60")) + (Decimal(self.priority) * Decimal("0.20")) + (utilization * Decimal("0.002")), 4)

    def is_escalation_required(self) -> bool:
        """Determines if utilization exceeds high alert threshold."""
        return self.calculate_utilization() >= float(self.alert_threshold_high)

    def calculate_depreciation(self, annual_rate: Decimal = Decimal("0.10")) -> Decimal:
        """Calculates asset depreciation over operational lifecycle."""
        years = max(1, (timezone.now().date() - self.effective_date).days // 365)
        depreciated = self.monetary_value * ((Decimal("1.00") - annual_rate) ** years)
        return round(max(Decimal("0.00"), depreciated), 2)

    def to_summary_dict(self) -> dict:
        """Exports a standardized dictionary representation for APIs and reports."""
        return {
            "code": self.code,
            "name": self.name,
            "status": self.status,
            "priority": self.priority,
            "department_tag": self.department_tag,
            "fiscal_code": self.fiscal_code,
            "approval_authority": self.approval_authority,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "is_locked": self.is_locked,
            "capacity_limit": self.capacity_limit,
            "allocated_count": self.allocated_count,
            "utilization_pct": self.calculate_utilization(),
            "composite_score": str(self.compute_composite_score()),
            "monetary_value": str(self.monetary_value),
            "created_at": self.created_at.isoformat(),
        }

class LibraryReservationsDocumentAttachmentQuerySet(models.QuerySet):
    """Custom QuerySet methods for LibraryReservationsDocumentAttachment."""
    def active(self):
        return self.filter(is_active=True)
    def recent(self, days: int = 30):
        cutoff = timezone.now() - timezone.timedelta(days=days)
        return self.filter(created_at__gte=cutoff)
    def search(self, query: str):
        if not query:
            return self
        return self.filter(models.Q(code__icontains=query) | models.Q(name__icontains=query))
    def verified(self):
        return self.filter(is_verified=True)
    def by_status(self, status: str):
        return self.filter(status=status)
    def priority_ordered(self):
        return self.order_by("-priority", "-created_at")
    def capacity_available(self):
        return self.filter(allocated_count__lt=models.F("capacity_limit"))
    def threshold_exceeded(self):
        return self.filter(allocated_count__gte=models.F("capacity_limit"))
    def with_high_score(self, min_score: Decimal = Decimal("3.00")):
        return self.filter(score_rating__gte=min_score)

class LibraryReservationsDocumentAttachmentManager(models.Manager):
    """Custom model manager for LibraryReservationsDocumentAttachment."""
    def get_queryset(self):
        return LibraryReservationsDocumentAttachmentQuerySet(self.model, using=self._db)
    def active(self):
        return self.get_queryset().active()
    def search(self, query: str):
        return self.get_queryset().search(query)
    def verified(self):
        return self.get_queryset().verified()
    def by_status(self, status: str):
        return self.get_queryset().by_status(status)
    def capacity_available(self):
        return self.get_queryset().capacity_available()

class LibraryReservationsDocumentAttachment(models.Model):
    """
    LibraryReservationsDocumentAttachment: Official digital file attachment container with cryptographic checksums.
    Enterprise Grade Institutional Entity with strict audit trails and SQLite optimization.
    """
    code = models.CharField(max_length=64, unique=True, db_index=True, verbose_name=_("Entity Code"))
    name = models.CharField(max_length=255, db_index=True, verbose_name=_("Entity Name"))
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True, verbose_name=_("Slug"))
    description = models.TextField(blank=True, default="", verbose_name=_("Description"))
    priority = models.PositiveIntegerField(default=1, verbose_name=_("Priority Weight"))
    status = models.CharField(max_length=32, default="ACTIVE", db_index=True, verbose_name=_("Status"))
    is_active = models.BooleanField(default=True, db_index=True, verbose_name=_("Active Flag"))
    is_verified = models.BooleanField(default=False, verbose_name=_("Verified Flag"))
    is_locked = models.BooleanField(default=False, verbose_name=_("Lock Flag"))
    score_rating = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"), verbose_name=_("Score"))
    monetary_value = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"), verbose_name=_("Monetary Value"))
    capacity_limit = models.PositiveIntegerField(default=100, verbose_name=_("Capacity Limit"))
    allocated_count = models.PositiveIntegerField(default=0, verbose_name=_("Allocated Count"))
    waitlist_count = models.PositiveIntegerField(default=0, verbose_name=_("Waitlist Count"))
    alert_threshold_low = models.PositiveIntegerField(default=10, verbose_name=_("Alert Low"))
    alert_threshold_high = models.PositiveIntegerField(default=90, verbose_name=_("Alert High"))
    renewal_cycle_months = models.PositiveIntegerField(default=12, verbose_name=_("Renewal Months"))
    department_tag = models.CharField(max_length=64, blank=True, default="LIBRARY", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@library.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = LibraryReservationsDocumentAttachmentManager()

    class Meta:
        db_table = "library_library_reservations_documentattachment"
        ordering = ["-created_at", "code"]
        verbose_name = _("LibraryReservationsDocumentAttachment")
        verbose_name_plural = _("LibraryReservationsDocumentAttachments")
        indexes = [
            models.Index(fields=["code", "status"], name="librar_librar_a601c4fe_cd"),
            models.Index(fields=["created_at"], name="librar_librar_a601c4fe_cr"),
            models.Index(fields=["priority", "status"], name="librar_librar_a601c4fe_pr"),
            models.Index(fields=["department_tag", "status"], name="librar_librar_a601c4fe_dp"),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"

    def clean(self):
        super().clean()
        self.code = self.code.strip().upper()
        if self.capacity_limit < 0:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Capacity limit cannot be negative."))
        if self.allocated_count > self.capacity_limit:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Allocated count cannot exceed capacity limit."))
        if self.alert_threshold_low > self.alert_threshold_high:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Alert low threshold cannot exceed alert high threshold."))

    def is_expired(self) -> bool:
        """Determines whether this policy or record has passed its expiration date."""
        if not self.expiration_date:
            return False
        return timezone.now().date() > self.expiration_date

    def calculate_utilization(self) -> float:
        """Calculates percentage utilization against capacity limit."""
        if not self.capacity_limit or self.capacity_limit == 0:
            return 0.0
        return round((float(self.allocated_count) / float(self.capacity_limit)) * 100.0, 2)

    def has_available_capacity(self, delta: int = 1) -> bool:
        """Validates whether additional allocations can be committed."""
        return (self.allocated_count + delta) <= self.capacity_limit

    def increment_allocation(self, delta: int = 1) -> None:
        """Safely increments the committed allocation counter."""
        if not self.has_available_capacity(delta):
            from core.exceptions import CapacityExceededException
            raise CapacityExceededException(f"Cannot allocate {delta} units: Capacity limit reached.")
        self.allocated_count += delta
        self.save(update_fields=["allocated_count", "updated_at"])

    def decrement_allocation(self, delta: int = 1) -> None:
        """Safely decrements the allocated resource counter."""
        self.allocated_count = max(0, self.allocated_count - delta)
        self.save(update_fields=["allocated_count", "updated_at"])

    def mark_as_verified(self, approver: str = "SYSTEM") -> None:
        """Validates verification state and records signature in metadata."""
        self.is_verified = True
        self.metadata["verified_by"] = approver
        self.metadata["verified_at"] = timezone.now().isoformat()
        self.save(update_fields=["is_verified", "metadata", "updated_at"])

    def lock_record(self, reason: str = "Administrative Lock") -> None:
        """Freezes entity modifications for audit verification."""
        self.is_locked = True
        self.metadata["lock_reason"] = reason
        self.metadata["locked_at"] = timezone.now().isoformat()
        self.save(update_fields=["is_locked", "metadata", "updated_at"])

    def unlock_record(self) -> None:
        """Releases entity lock following audit review."""
        self.is_locked = False
        self.metadata["unlocked_at"] = timezone.now().isoformat()
        self.save(update_fields=["is_locked", "metadata", "updated_at"])

    def compute_composite_score(self) -> Decimal:
        """Computes a multi-factor score incorporating rating, priority, and capacity load."""
        utilization = Decimal(str(self.calculate_utilization()))
        return round((self.score_rating * Decimal("0.60")) + (Decimal(self.priority) * Decimal("0.20")) + (utilization * Decimal("0.002")), 4)

    def is_escalation_required(self) -> bool:
        """Determines if utilization exceeds high alert threshold."""
        return self.calculate_utilization() >= float(self.alert_threshold_high)

    def calculate_depreciation(self, annual_rate: Decimal = Decimal("0.10")) -> Decimal:
        """Calculates asset depreciation over operational lifecycle."""
        years = max(1, (timezone.now().date() - self.effective_date).days // 365)
        depreciated = self.monetary_value * ((Decimal("1.00") - annual_rate) ** years)
        return round(max(Decimal("0.00"), depreciated), 2)

    def to_summary_dict(self) -> dict:
        """Exports a standardized dictionary representation for APIs and reports."""
        return {
            "code": self.code,
            "name": self.name,
            "status": self.status,
            "priority": self.priority,
            "department_tag": self.department_tag,
            "fiscal_code": self.fiscal_code,
            "approval_authority": self.approval_authority,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "is_locked": self.is_locked,
            "capacity_limit": self.capacity_limit,
            "allocated_count": self.allocated_count,
            "utilization_pct": self.calculate_utilization(),
            "composite_score": str(self.compute_composite_score()),
            "monetary_value": str(self.monetary_value),
            "created_at": self.created_at.isoformat(),
        }

class LibraryReservationsLifecycleTransitionQuerySet(models.QuerySet):
    """Custom QuerySet methods for LibraryReservationsLifecycleTransition."""
    def active(self):
        return self.filter(is_active=True)
    def recent(self, days: int = 30):
        cutoff = timezone.now() - timezone.timedelta(days=days)
        return self.filter(created_at__gte=cutoff)
    def search(self, query: str):
        if not query:
            return self
        return self.filter(models.Q(code__icontains=query) | models.Q(name__icontains=query))
    def verified(self):
        return self.filter(is_verified=True)
    def by_status(self, status: str):
        return self.filter(status=status)
    def priority_ordered(self):
        return self.order_by("-priority", "-created_at")
    def capacity_available(self):
        return self.filter(allocated_count__lt=models.F("capacity_limit"))
    def threshold_exceeded(self):
        return self.filter(allocated_count__gte=models.F("capacity_limit"))
    def with_high_score(self, min_score: Decimal = Decimal("3.00")):
        return self.filter(score_rating__gte=min_score)

class LibraryReservationsLifecycleTransitionManager(models.Manager):
    """Custom model manager for LibraryReservationsLifecycleTransition."""
    def get_queryset(self):
        return LibraryReservationsLifecycleTransitionQuerySet(self.model, using=self._db)
    def active(self):
        return self.get_queryset().active()
    def search(self, query: str):
        return self.get_queryset().search(query)
    def verified(self):
        return self.get_queryset().verified()
    def by_status(self, status: str):
        return self.get_queryset().by_status(status)
    def capacity_available(self):
        return self.get_queryset().capacity_available()

class LibraryReservationsLifecycleTransition(models.Model):
    """
    LibraryReservationsLifecycleTransition: State transition checkpoint recording approval gates and authorizations.
    Enterprise Grade Institutional Entity with strict audit trails and SQLite optimization.
    """
    code = models.CharField(max_length=64, unique=True, db_index=True, verbose_name=_("Entity Code"))
    name = models.CharField(max_length=255, db_index=True, verbose_name=_("Entity Name"))
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True, verbose_name=_("Slug"))
    description = models.TextField(blank=True, default="", verbose_name=_("Description"))
    priority = models.PositiveIntegerField(default=1, verbose_name=_("Priority Weight"))
    status = models.CharField(max_length=32, default="ACTIVE", db_index=True, verbose_name=_("Status"))
    is_active = models.BooleanField(default=True, db_index=True, verbose_name=_("Active Flag"))
    is_verified = models.BooleanField(default=False, verbose_name=_("Verified Flag"))
    is_locked = models.BooleanField(default=False, verbose_name=_("Lock Flag"))
    score_rating = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"), verbose_name=_("Score"))
    monetary_value = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"), verbose_name=_("Monetary Value"))
    capacity_limit = models.PositiveIntegerField(default=100, verbose_name=_("Capacity Limit"))
    allocated_count = models.PositiveIntegerField(default=0, verbose_name=_("Allocated Count"))
    waitlist_count = models.PositiveIntegerField(default=0, verbose_name=_("Waitlist Count"))
    alert_threshold_low = models.PositiveIntegerField(default=10, verbose_name=_("Alert Low"))
    alert_threshold_high = models.PositiveIntegerField(default=90, verbose_name=_("Alert High"))
    renewal_cycle_months = models.PositiveIntegerField(default=12, verbose_name=_("Renewal Months"))
    department_tag = models.CharField(max_length=64, blank=True, default="LIBRARY", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@library.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = LibraryReservationsLifecycleTransitionManager()

    class Meta:
        db_table = "library_library_reservations_lifecycletransition"
        ordering = ["-created_at", "code"]
        verbose_name = _("LibraryReservationsLifecycleTransition")
        verbose_name_plural = _("LibraryReservationsLifecycleTransitions")
        indexes = [
            models.Index(fields=["code", "status"], name="librar_librar_e741a56a_cd"),
            models.Index(fields=["created_at"], name="librar_librar_e741a56a_cr"),
            models.Index(fields=["priority", "status"], name="librar_librar_e741a56a_pr"),
            models.Index(fields=["department_tag", "status"], name="librar_librar_e741a56a_dp"),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"

    def clean(self):
        super().clean()
        self.code = self.code.strip().upper()
        if self.capacity_limit < 0:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Capacity limit cannot be negative."))
        if self.allocated_count > self.capacity_limit:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Allocated count cannot exceed capacity limit."))
        if self.alert_threshold_low > self.alert_threshold_high:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Alert low threshold cannot exceed alert high threshold."))

    def is_expired(self) -> bool:
        """Determines whether this policy or record has passed its expiration date."""
        if not self.expiration_date:
            return False
        return timezone.now().date() > self.expiration_date

    def calculate_utilization(self) -> float:
        """Calculates percentage utilization against capacity limit."""
        if not self.capacity_limit or self.capacity_limit == 0:
            return 0.0
        return round((float(self.allocated_count) / float(self.capacity_limit)) * 100.0, 2)

    def has_available_capacity(self, delta: int = 1) -> bool:
        """Validates whether additional allocations can be committed."""
        return (self.allocated_count + delta) <= self.capacity_limit

    def increment_allocation(self, delta: int = 1) -> None:
        """Safely increments the committed allocation counter."""
        if not self.has_available_capacity(delta):
            from core.exceptions import CapacityExceededException
            raise CapacityExceededException(f"Cannot allocate {delta} units: Capacity limit reached.")
        self.allocated_count += delta
        self.save(update_fields=["allocated_count", "updated_at"])

    def decrement_allocation(self, delta: int = 1) -> None:
        """Safely decrements the allocated resource counter."""
        self.allocated_count = max(0, self.allocated_count - delta)
        self.save(update_fields=["allocated_count", "updated_at"])

    def mark_as_verified(self, approver: str = "SYSTEM") -> None:
        """Validates verification state and records signature in metadata."""
        self.is_verified = True
        self.metadata["verified_by"] = approver
        self.metadata["verified_at"] = timezone.now().isoformat()
        self.save(update_fields=["is_verified", "metadata", "updated_at"])

    def lock_record(self, reason: str = "Administrative Lock") -> None:
        """Freezes entity modifications for audit verification."""
        self.is_locked = True
        self.metadata["lock_reason"] = reason
        self.metadata["locked_at"] = timezone.now().isoformat()
        self.save(update_fields=["is_locked", "metadata", "updated_at"])

    def unlock_record(self) -> None:
        """Releases entity lock following audit review."""
        self.is_locked = False
        self.metadata["unlocked_at"] = timezone.now().isoformat()
        self.save(update_fields=["is_locked", "metadata", "updated_at"])

    def compute_composite_score(self) -> Decimal:
        """Computes a multi-factor score incorporating rating, priority, and capacity load."""
        utilization = Decimal(str(self.calculate_utilization()))
        return round((self.score_rating * Decimal("0.60")) + (Decimal(self.priority) * Decimal("0.20")) + (utilization * Decimal("0.002")), 4)

    def is_escalation_required(self) -> bool:
        """Determines if utilization exceeds high alert threshold."""
        return self.calculate_utilization() >= float(self.alert_threshold_high)

    def calculate_depreciation(self, annual_rate: Decimal = Decimal("0.10")) -> Decimal:
        """Calculates asset depreciation over operational lifecycle."""
        years = max(1, (timezone.now().date() - self.effective_date).days // 365)
        depreciated = self.monetary_value * ((Decimal("1.00") - annual_rate) ** years)
        return round(max(Decimal("0.00"), depreciated), 2)

    def to_summary_dict(self) -> dict:
        """Exports a standardized dictionary representation for APIs and reports."""
        return {
            "code": self.code,
            "name": self.name,
            "status": self.status,
            "priority": self.priority,
            "department_tag": self.department_tag,
            "fiscal_code": self.fiscal_code,
            "approval_authority": self.approval_authority,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "is_locked": self.is_locked,
            "capacity_limit": self.capacity_limit,
            "allocated_count": self.allocated_count,
            "utilization_pct": self.calculate_utilization(),
            "composite_score": str(self.compute_composite_score()),
            "monetary_value": str(self.monetary_value),
            "created_at": self.created_at.isoformat(),
        }

class LibraryReservationsDataArchivalRegistryQuerySet(models.QuerySet):
    """Custom QuerySet methods for LibraryReservationsDataArchivalRegistry."""
    def active(self):
        return self.filter(is_active=True)
    def recent(self, days: int = 30):
        cutoff = timezone.now() - timezone.timedelta(days=days)
        return self.filter(created_at__gte=cutoff)
    def search(self, query: str):
        if not query:
            return self
        return self.filter(models.Q(code__icontains=query) | models.Q(name__icontains=query))
    def verified(self):
        return self.filter(is_verified=True)
    def by_status(self, status: str):
        return self.filter(status=status)
    def priority_ordered(self):
        return self.order_by("-priority", "-created_at")
    def capacity_available(self):
        return self.filter(allocated_count__lt=models.F("capacity_limit"))
    def threshold_exceeded(self):
        return self.filter(allocated_count__gte=models.F("capacity_limit"))
    def with_high_score(self, min_score: Decimal = Decimal("3.00")):
        return self.filter(score_rating__gte=min_score)

class LibraryReservationsDataArchivalRegistryManager(models.Manager):
    """Custom model manager for LibraryReservationsDataArchivalRegistry."""
    def get_queryset(self):
        return LibraryReservationsDataArchivalRegistryQuerySet(self.model, using=self._db)
    def active(self):
        return self.get_queryset().active()
    def search(self, query: str):
        return self.get_queryset().search(query)
    def verified(self):
        return self.get_queryset().verified()
    def by_status(self, status: str):
        return self.get_queryset().by_status(status)
    def capacity_available(self):
        return self.get_queryset().capacity_available()

class LibraryReservationsDataArchivalRegistry(models.Model):
    """
    LibraryReservationsDataArchivalRegistry: Record archival state, cold storage pointers, and legal hold flags.
    Enterprise Grade Institutional Entity with strict audit trails and SQLite optimization.
    """
    code = models.CharField(max_length=64, unique=True, db_index=True, verbose_name=_("Entity Code"))
    name = models.CharField(max_length=255, db_index=True, verbose_name=_("Entity Name"))
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True, verbose_name=_("Slug"))
    description = models.TextField(blank=True, default="", verbose_name=_("Description"))
    priority = models.PositiveIntegerField(default=1, verbose_name=_("Priority Weight"))
    status = models.CharField(max_length=32, default="ACTIVE", db_index=True, verbose_name=_("Status"))
    is_active = models.BooleanField(default=True, db_index=True, verbose_name=_("Active Flag"))
    is_verified = models.BooleanField(default=False, verbose_name=_("Verified Flag"))
    is_locked = models.BooleanField(default=False, verbose_name=_("Lock Flag"))
    score_rating = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"), verbose_name=_("Score"))
    monetary_value = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"), verbose_name=_("Monetary Value"))
    capacity_limit = models.PositiveIntegerField(default=100, verbose_name=_("Capacity Limit"))
    allocated_count = models.PositiveIntegerField(default=0, verbose_name=_("Allocated Count"))
    waitlist_count = models.PositiveIntegerField(default=0, verbose_name=_("Waitlist Count"))
    alert_threshold_low = models.PositiveIntegerField(default=10, verbose_name=_("Alert Low"))
    alert_threshold_high = models.PositiveIntegerField(default=90, verbose_name=_("Alert High"))
    renewal_cycle_months = models.PositiveIntegerField(default=12, verbose_name=_("Renewal Months"))
    department_tag = models.CharField(max_length=64, blank=True, default="LIBRARY", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@library.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = LibraryReservationsDataArchivalRegistryManager()

    class Meta:
        db_table = "library_library_reservations_dataarchivalregistry"
        ordering = ["-created_at", "code"]
        verbose_name = _("LibraryReservationsDataArchivalRegistry")
        verbose_name_plural = _("LibraryReservationsDataArchivalRegistrys")
        indexes = [
            models.Index(fields=["code", "status"], name="librar_librar_1a35aa85_cd"),
            models.Index(fields=["created_at"], name="librar_librar_1a35aa85_cr"),
            models.Index(fields=["priority", "status"], name="librar_librar_1a35aa85_pr"),
            models.Index(fields=["department_tag", "status"], name="librar_librar_1a35aa85_dp"),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"

    def clean(self):
        super().clean()
        self.code = self.code.strip().upper()
        if self.capacity_limit < 0:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Capacity limit cannot be negative."))
        if self.allocated_count > self.capacity_limit:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Allocated count cannot exceed capacity limit."))
        if self.alert_threshold_low > self.alert_threshold_high:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Alert low threshold cannot exceed alert high threshold."))

    def is_expired(self) -> bool:
        """Determines whether this policy or record has passed its expiration date."""
        if not self.expiration_date:
            return False
        return timezone.now().date() > self.expiration_date

    def calculate_utilization(self) -> float:
        """Calculates percentage utilization against capacity limit."""
        if not self.capacity_limit or self.capacity_limit == 0:
            return 0.0
        return round((float(self.allocated_count) / float(self.capacity_limit)) * 100.0, 2)

    def has_available_capacity(self, delta: int = 1) -> bool:
        """Validates whether additional allocations can be committed."""
        return (self.allocated_count + delta) <= self.capacity_limit

    def increment_allocation(self, delta: int = 1) -> None:
        """Safely increments the committed allocation counter."""
        if not self.has_available_capacity(delta):
            from core.exceptions import CapacityExceededException
            raise CapacityExceededException(f"Cannot allocate {delta} units: Capacity limit reached.")
        self.allocated_count += delta
        self.save(update_fields=["allocated_count", "updated_at"])

    def decrement_allocation(self, delta: int = 1) -> None:
        """Safely decrements the allocated resource counter."""
        self.allocated_count = max(0, self.allocated_count - delta)
        self.save(update_fields=["allocated_count", "updated_at"])

    def mark_as_verified(self, approver: str = "SYSTEM") -> None:
        """Validates verification state and records signature in metadata."""
        self.is_verified = True
        self.metadata["verified_by"] = approver
        self.metadata["verified_at"] = timezone.now().isoformat()
        self.save(update_fields=["is_verified", "metadata", "updated_at"])

    def lock_record(self, reason: str = "Administrative Lock") -> None:
        """Freezes entity modifications for audit verification."""
        self.is_locked = True
        self.metadata["lock_reason"] = reason
        self.metadata["locked_at"] = timezone.now().isoformat()
        self.save(update_fields=["is_locked", "metadata", "updated_at"])

    def unlock_record(self) -> None:
        """Releases entity lock following audit review."""
        self.is_locked = False
        self.metadata["unlocked_at"] = timezone.now().isoformat()
        self.save(update_fields=["is_locked", "metadata", "updated_at"])

    def compute_composite_score(self) -> Decimal:
        """Computes a multi-factor score incorporating rating, priority, and capacity load."""
        utilization = Decimal(str(self.calculate_utilization()))
        return round((self.score_rating * Decimal("0.60")) + (Decimal(self.priority) * Decimal("0.20")) + (utilization * Decimal("0.002")), 4)

    def is_escalation_required(self) -> bool:
        """Determines if utilization exceeds high alert threshold."""
        return self.calculate_utilization() >= float(self.alert_threshold_high)

    def calculate_depreciation(self, annual_rate: Decimal = Decimal("0.10")) -> Decimal:
        """Calculates asset depreciation over operational lifecycle."""
        years = max(1, (timezone.now().date() - self.effective_date).days // 365)
        depreciated = self.monetary_value * ((Decimal("1.00") - annual_rate) ** years)
        return round(max(Decimal("0.00"), depreciated), 2)

    def to_summary_dict(self) -> dict:
        """Exports a standardized dictionary representation for APIs and reports."""
        return {
            "code": self.code,
            "name": self.name,
            "status": self.status,
            "priority": self.priority,
            "department_tag": self.department_tag,
            "fiscal_code": self.fiscal_code,
            "approval_authority": self.approval_authority,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "is_locked": self.is_locked,
            "capacity_limit": self.capacity_limit,
            "allocated_count": self.allocated_count,
            "utilization_pct": self.calculate_utilization(),
            "composite_score": str(self.compute_composite_score()),
            "monetary_value": str(self.monetary_value),
            "created_at": self.created_at.isoformat(),
        }

class LibraryReservationsTelemetryEventStreamQuerySet(models.QuerySet):
    """Custom QuerySet methods for LibraryReservationsTelemetryEventStream."""
    def active(self):
        return self.filter(is_active=True)
    def recent(self, days: int = 30):
        cutoff = timezone.now() - timezone.timedelta(days=days)
        return self.filter(created_at__gte=cutoff)
    def search(self, query: str):
        if not query:
            return self
        return self.filter(models.Q(code__icontains=query) | models.Q(name__icontains=query))
    def verified(self):
        return self.filter(is_verified=True)
    def by_status(self, status: str):
        return self.filter(status=status)
    def priority_ordered(self):
        return self.order_by("-priority", "-created_at")
    def capacity_available(self):
        return self.filter(allocated_count__lt=models.F("capacity_limit"))
    def threshold_exceeded(self):
        return self.filter(allocated_count__gte=models.F("capacity_limit"))
    def with_high_score(self, min_score: Decimal = Decimal("3.00")):
        return self.filter(score_rating__gte=min_score)

class LibraryReservationsTelemetryEventStreamManager(models.Manager):
    """Custom model manager for LibraryReservationsTelemetryEventStream."""
    def get_queryset(self):
        return LibraryReservationsTelemetryEventStreamQuerySet(self.model, using=self._db)
    def active(self):
        return self.get_queryset().active()
    def search(self, query: str):
        return self.get_queryset().search(query)
    def verified(self):
        return self.get_queryset().verified()
    def by_status(self, status: str):
        return self.get_queryset().by_status(status)
    def capacity_available(self):
        return self.get_queryset().capacity_available()

class LibraryReservationsTelemetryEventStream(models.Model):
    """
    LibraryReservationsTelemetryEventStream: Real-time telemetry events and activity streams.
    Enterprise Grade Institutional Entity with strict audit trails and SQLite optimization.
    """
    code = models.CharField(max_length=64, unique=True, db_index=True, verbose_name=_("Entity Code"))
    name = models.CharField(max_length=255, db_index=True, verbose_name=_("Entity Name"))
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True, verbose_name=_("Slug"))
    description = models.TextField(blank=True, default="", verbose_name=_("Description"))
    priority = models.PositiveIntegerField(default=1, verbose_name=_("Priority Weight"))
    status = models.CharField(max_length=32, default="ACTIVE", db_index=True, verbose_name=_("Status"))
    is_active = models.BooleanField(default=True, db_index=True, verbose_name=_("Active Flag"))
    is_verified = models.BooleanField(default=False, verbose_name=_("Verified Flag"))
    is_locked = models.BooleanField(default=False, verbose_name=_("Lock Flag"))
    score_rating = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"), verbose_name=_("Score"))
    monetary_value = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"), verbose_name=_("Monetary Value"))
    capacity_limit = models.PositiveIntegerField(default=100, verbose_name=_("Capacity Limit"))
    allocated_count = models.PositiveIntegerField(default=0, verbose_name=_("Allocated Count"))
    waitlist_count = models.PositiveIntegerField(default=0, verbose_name=_("Waitlist Count"))
    alert_threshold_low = models.PositiveIntegerField(default=10, verbose_name=_("Alert Low"))
    alert_threshold_high = models.PositiveIntegerField(default=90, verbose_name=_("Alert High"))
    renewal_cycle_months = models.PositiveIntegerField(default=12, verbose_name=_("Renewal Months"))
    department_tag = models.CharField(max_length=64, blank=True, default="LIBRARY", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@library.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = LibraryReservationsTelemetryEventStreamManager()

    class Meta:
        db_table = "library_library_reservations_telemetryeventstream"
        ordering = ["-created_at", "code"]
        verbose_name = _("LibraryReservationsTelemetryEventStream")
        verbose_name_plural = _("LibraryReservationsTelemetryEventStreams")
        indexes = [
            models.Index(fields=["code", "status"], name="librar_librar_f4fbcea2_cd"),
            models.Index(fields=["created_at"], name="librar_librar_f4fbcea2_cr"),
            models.Index(fields=["priority", "status"], name="librar_librar_f4fbcea2_pr"),
            models.Index(fields=["department_tag", "status"], name="librar_librar_f4fbcea2_dp"),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"

    def clean(self):
        super().clean()
        self.code = self.code.strip().upper()
        if self.capacity_limit < 0:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Capacity limit cannot be negative."))
        if self.allocated_count > self.capacity_limit:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Allocated count cannot exceed capacity limit."))
        if self.alert_threshold_low > self.alert_threshold_high:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Alert low threshold cannot exceed alert high threshold."))

    def is_expired(self) -> bool:
        """Determines whether this policy or record has passed its expiration date."""
        if not self.expiration_date:
            return False
        return timezone.now().date() > self.expiration_date

    def calculate_utilization(self) -> float:
        """Calculates percentage utilization against capacity limit."""
        if not self.capacity_limit or self.capacity_limit == 0:
            return 0.0
        return round((float(self.allocated_count) / float(self.capacity_limit)) * 100.0, 2)

    def has_available_capacity(self, delta: int = 1) -> bool:
        """Validates whether additional allocations can be committed."""
        return (self.allocated_count + delta) <= self.capacity_limit

    def increment_allocation(self, delta: int = 1) -> None:
        """Safely increments the committed allocation counter."""
        if not self.has_available_capacity(delta):
            from core.exceptions import CapacityExceededException
            raise CapacityExceededException(f"Cannot allocate {delta} units: Capacity limit reached.")
        self.allocated_count += delta
        self.save(update_fields=["allocated_count", "updated_at"])

    def decrement_allocation(self, delta: int = 1) -> None:
        """Safely decrements the allocated resource counter."""
        self.allocated_count = max(0, self.allocated_count - delta)
        self.save(update_fields=["allocated_count", "updated_at"])

    def mark_as_verified(self, approver: str = "SYSTEM") -> None:
        """Validates verification state and records signature in metadata."""
        self.is_verified = True
        self.metadata["verified_by"] = approver
        self.metadata["verified_at"] = timezone.now().isoformat()
        self.save(update_fields=["is_verified", "metadata", "updated_at"])

    def lock_record(self, reason: str = "Administrative Lock") -> None:
        """Freezes entity modifications for audit verification."""
        self.is_locked = True
        self.metadata["lock_reason"] = reason
        self.metadata["locked_at"] = timezone.now().isoformat()
        self.save(update_fields=["is_locked", "metadata", "updated_at"])

    def unlock_record(self) -> None:
        """Releases entity lock following audit review."""
        self.is_locked = False
        self.metadata["unlocked_at"] = timezone.now().isoformat()
        self.save(update_fields=["is_locked", "metadata", "updated_at"])

    def compute_composite_score(self) -> Decimal:
        """Computes a multi-factor score incorporating rating, priority, and capacity load."""
        utilization = Decimal(str(self.calculate_utilization()))
        return round((self.score_rating * Decimal("0.60")) + (Decimal(self.priority) * Decimal("0.20")) + (utilization * Decimal("0.002")), 4)

    def is_escalation_required(self) -> bool:
        """Determines if utilization exceeds high alert threshold."""
        return self.calculate_utilization() >= float(self.alert_threshold_high)

    def calculate_depreciation(self, annual_rate: Decimal = Decimal("0.10")) -> Decimal:
        """Calculates asset depreciation over operational lifecycle."""
        years = max(1, (timezone.now().date() - self.effective_date).days // 365)
        depreciated = self.monetary_value * ((Decimal("1.00") - annual_rate) ** years)
        return round(max(Decimal("0.00"), depreciated), 2)

    def to_summary_dict(self) -> dict:
        """Exports a standardized dictionary representation for APIs and reports."""
        return {
            "code": self.code,
            "name": self.name,
            "status": self.status,
            "priority": self.priority,
            "department_tag": self.department_tag,
            "fiscal_code": self.fiscal_code,
            "approval_authority": self.approval_authority,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "is_locked": self.is_locked,
            "capacity_limit": self.capacity_limit,
            "allocated_count": self.allocated_count,
            "utilization_pct": self.calculate_utilization(),
            "composite_score": str(self.compute_composite_score()),
            "monetary_value": str(self.monetary_value),
            "created_at": self.created_at.isoformat(),
        }

class LibraryReservationsAccessGrantMatrixQuerySet(models.QuerySet):
    """Custom QuerySet methods for LibraryReservationsAccessGrantMatrix."""
    def active(self):
        return self.filter(is_active=True)
    def recent(self, days: int = 30):
        cutoff = timezone.now() - timezone.timedelta(days=days)
        return self.filter(created_at__gte=cutoff)
    def search(self, query: str):
        if not query:
            return self
        return self.filter(models.Q(code__icontains=query) | models.Q(name__icontains=query))
    def verified(self):
        return self.filter(is_verified=True)
    def by_status(self, status: str):
        return self.filter(status=status)
    def priority_ordered(self):
        return self.order_by("-priority", "-created_at")
    def capacity_available(self):
        return self.filter(allocated_count__lt=models.F("capacity_limit"))
    def threshold_exceeded(self):
        return self.filter(allocated_count__gte=models.F("capacity_limit"))
    def with_high_score(self, min_score: Decimal = Decimal("3.00")):
        return self.filter(score_rating__gte=min_score)

class LibraryReservationsAccessGrantMatrixManager(models.Manager):
    """Custom model manager for LibraryReservationsAccessGrantMatrix."""
    def get_queryset(self):
        return LibraryReservationsAccessGrantMatrixQuerySet(self.model, using=self._db)
    def active(self):
        return self.get_queryset().active()
    def search(self, query: str):
        return self.get_queryset().search(query)
    def verified(self):
        return self.get_queryset().verified()
    def by_status(self, status: str):
        return self.get_queryset().by_status(status)
    def capacity_available(self):
        return self.get_queryset().capacity_available()

class LibraryReservationsAccessGrantMatrix(models.Model):
    """
    LibraryReservationsAccessGrantMatrix: Granular privilege assignments and operational scope bindings.
    Enterprise Grade Institutional Entity with strict audit trails and SQLite optimization.
    """
    code = models.CharField(max_length=64, unique=True, db_index=True, verbose_name=_("Entity Code"))
    name = models.CharField(max_length=255, db_index=True, verbose_name=_("Entity Name"))
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True, verbose_name=_("Slug"))
    description = models.TextField(blank=True, default="", verbose_name=_("Description"))
    priority = models.PositiveIntegerField(default=1, verbose_name=_("Priority Weight"))
    status = models.CharField(max_length=32, default="ACTIVE", db_index=True, verbose_name=_("Status"))
    is_active = models.BooleanField(default=True, db_index=True, verbose_name=_("Active Flag"))
    is_verified = models.BooleanField(default=False, verbose_name=_("Verified Flag"))
    is_locked = models.BooleanField(default=False, verbose_name=_("Lock Flag"))
    score_rating = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"), verbose_name=_("Score"))
    monetary_value = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"), verbose_name=_("Monetary Value"))
    capacity_limit = models.PositiveIntegerField(default=100, verbose_name=_("Capacity Limit"))
    allocated_count = models.PositiveIntegerField(default=0, verbose_name=_("Allocated Count"))
    waitlist_count = models.PositiveIntegerField(default=0, verbose_name=_("Waitlist Count"))
    alert_threshold_low = models.PositiveIntegerField(default=10, verbose_name=_("Alert Low"))
    alert_threshold_high = models.PositiveIntegerField(default=90, verbose_name=_("Alert High"))
    renewal_cycle_months = models.PositiveIntegerField(default=12, verbose_name=_("Renewal Months"))
    department_tag = models.CharField(max_length=64, blank=True, default="LIBRARY", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@library.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = LibraryReservationsAccessGrantMatrixManager()

    class Meta:
        db_table = "library_library_reservations_accessgrantmatrix"
        ordering = ["-created_at", "code"]
        verbose_name = _("LibraryReservationsAccessGrantMatrix")
        verbose_name_plural = _("LibraryReservationsAccessGrantMatrixs")
        indexes = [
            models.Index(fields=["code", "status"], name="librar_librar_cbe96726_cd"),
            models.Index(fields=["created_at"], name="librar_librar_cbe96726_cr"),
            models.Index(fields=["priority", "status"], name="librar_librar_cbe96726_pr"),
            models.Index(fields=["department_tag", "status"], name="librar_librar_cbe96726_dp"),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"

    def clean(self):
        super().clean()
        self.code = self.code.strip().upper()
        if self.capacity_limit < 0:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Capacity limit cannot be negative."))
        if self.allocated_count > self.capacity_limit:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Allocated count cannot exceed capacity limit."))
        if self.alert_threshold_low > self.alert_threshold_high:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Alert low threshold cannot exceed alert high threshold."))

    def is_expired(self) -> bool:
        """Determines whether this policy or record has passed its expiration date."""
        if not self.expiration_date:
            return False
        return timezone.now().date() > self.expiration_date

    def calculate_utilization(self) -> float:
        """Calculates percentage utilization against capacity limit."""
        if not self.capacity_limit or self.capacity_limit == 0:
            return 0.0
        return round((float(self.allocated_count) / float(self.capacity_limit)) * 100.0, 2)

    def has_available_capacity(self, delta: int = 1) -> bool:
        """Validates whether additional allocations can be committed."""
        return (self.allocated_count + delta) <= self.capacity_limit

    def increment_allocation(self, delta: int = 1) -> None:
        """Safely increments the committed allocation counter."""
        if not self.has_available_capacity(delta):
            from core.exceptions import CapacityExceededException
            raise CapacityExceededException(f"Cannot allocate {delta} units: Capacity limit reached.")
        self.allocated_count += delta
        self.save(update_fields=["allocated_count", "updated_at"])

    def decrement_allocation(self, delta: int = 1) -> None:
        """Safely decrements the allocated resource counter."""
        self.allocated_count = max(0, self.allocated_count - delta)
        self.save(update_fields=["allocated_count", "updated_at"])

    def mark_as_verified(self, approver: str = "SYSTEM") -> None:
        """Validates verification state and records signature in metadata."""
        self.is_verified = True
        self.metadata["verified_by"] = approver
        self.metadata["verified_at"] = timezone.now().isoformat()
        self.save(update_fields=["is_verified", "metadata", "updated_at"])

    def lock_record(self, reason: str = "Administrative Lock") -> None:
        """Freezes entity modifications for audit verification."""
        self.is_locked = True
        self.metadata["lock_reason"] = reason
        self.metadata["locked_at"] = timezone.now().isoformat()
        self.save(update_fields=["is_locked", "metadata", "updated_at"])

    def unlock_record(self) -> None:
        """Releases entity lock following audit review."""
        self.is_locked = False
        self.metadata["unlocked_at"] = timezone.now().isoformat()
        self.save(update_fields=["is_locked", "metadata", "updated_at"])

    def compute_composite_score(self) -> Decimal:
        """Computes a multi-factor score incorporating rating, priority, and capacity load."""
        utilization = Decimal(str(self.calculate_utilization()))
        return round((self.score_rating * Decimal("0.60")) + (Decimal(self.priority) * Decimal("0.20")) + (utilization * Decimal("0.002")), 4)

    def is_escalation_required(self) -> bool:
        """Determines if utilization exceeds high alert threshold."""
        return self.calculate_utilization() >= float(self.alert_threshold_high)

    def calculate_depreciation(self, annual_rate: Decimal = Decimal("0.10")) -> Decimal:
        """Calculates asset depreciation over operational lifecycle."""
        years = max(1, (timezone.now().date() - self.effective_date).days // 365)
        depreciated = self.monetary_value * ((Decimal("1.00") - annual_rate) ** years)
        return round(max(Decimal("0.00"), depreciated), 2)

    def to_summary_dict(self) -> dict:
        """Exports a standardized dictionary representation for APIs and reports."""
        return {
            "code": self.code,
            "name": self.name,
            "status": self.status,
            "priority": self.priority,
            "department_tag": self.department_tag,
            "fiscal_code": self.fiscal_code,
            "approval_authority": self.approval_authority,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "is_locked": self.is_locked,
            "capacity_limit": self.capacity_limit,
            "allocated_count": self.allocated_count,
            "utilization_pct": self.calculate_utilization(),
            "composite_score": str(self.compute_composite_score()),
            "monetary_value": str(self.monetary_value),
            "created_at": self.created_at.isoformat(),
        }

class LibraryReservationsOperationalQuotaQuerySet(models.QuerySet):
    """Custom QuerySet methods for LibraryReservationsOperationalQuota."""
    def active(self):
        return self.filter(is_active=True)
    def recent(self, days: int = 30):
        cutoff = timezone.now() - timezone.timedelta(days=days)
        return self.filter(created_at__gte=cutoff)
    def search(self, query: str):
        if not query:
            return self
        return self.filter(models.Q(code__icontains=query) | models.Q(name__icontains=query))
    def verified(self):
        return self.filter(is_verified=True)
    def by_status(self, status: str):
        return self.filter(status=status)
    def priority_ordered(self):
        return self.order_by("-priority", "-created_at")
    def capacity_available(self):
        return self.filter(allocated_count__lt=models.F("capacity_limit"))
    def threshold_exceeded(self):
        return self.filter(allocated_count__gte=models.F("capacity_limit"))
    def with_high_score(self, min_score: Decimal = Decimal("3.00")):
        return self.filter(score_rating__gte=min_score)

class LibraryReservationsOperationalQuotaManager(models.Manager):
    """Custom model manager for LibraryReservationsOperationalQuota."""
    def get_queryset(self):
        return LibraryReservationsOperationalQuotaQuerySet(self.model, using=self._db)
    def active(self):
        return self.get_queryset().active()
    def search(self, query: str):
        return self.get_queryset().search(query)
    def verified(self):
        return self.get_queryset().verified()
    def by_status(self, status: str):
        return self.get_queryset().by_status(status)
    def capacity_available(self):
        return self.get_queryset().capacity_available()

class LibraryReservationsOperationalQuota(models.Model):
    """
    LibraryReservationsOperationalQuota: Resource quotas, bandwidth/usage limits, and consumption tracking.
    Enterprise Grade Institutional Entity with strict audit trails and SQLite optimization.
    """
    code = models.CharField(max_length=64, unique=True, db_index=True, verbose_name=_("Entity Code"))
    name = models.CharField(max_length=255, db_index=True, verbose_name=_("Entity Name"))
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True, verbose_name=_("Slug"))
    description = models.TextField(blank=True, default="", verbose_name=_("Description"))
    priority = models.PositiveIntegerField(default=1, verbose_name=_("Priority Weight"))
    status = models.CharField(max_length=32, default="ACTIVE", db_index=True, verbose_name=_("Status"))
    is_active = models.BooleanField(default=True, db_index=True, verbose_name=_("Active Flag"))
    is_verified = models.BooleanField(default=False, verbose_name=_("Verified Flag"))
    is_locked = models.BooleanField(default=False, verbose_name=_("Lock Flag"))
    score_rating = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"), verbose_name=_("Score"))
    monetary_value = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"), verbose_name=_("Monetary Value"))
    capacity_limit = models.PositiveIntegerField(default=100, verbose_name=_("Capacity Limit"))
    allocated_count = models.PositiveIntegerField(default=0, verbose_name=_("Allocated Count"))
    waitlist_count = models.PositiveIntegerField(default=0, verbose_name=_("Waitlist Count"))
    alert_threshold_low = models.PositiveIntegerField(default=10, verbose_name=_("Alert Low"))
    alert_threshold_high = models.PositiveIntegerField(default=90, verbose_name=_("Alert High"))
    renewal_cycle_months = models.PositiveIntegerField(default=12, verbose_name=_("Renewal Months"))
    department_tag = models.CharField(max_length=64, blank=True, default="LIBRARY", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@library.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = LibraryReservationsOperationalQuotaManager()

    class Meta:
        db_table = "library_library_reservations_operationalquota"
        ordering = ["-created_at", "code"]
        verbose_name = _("LibraryReservationsOperationalQuota")
        verbose_name_plural = _("LibraryReservationsOperationalQuotas")
        indexes = [
            models.Index(fields=["code", "status"], name="librar_librar_946fa07e_cd"),
            models.Index(fields=["created_at"], name="librar_librar_946fa07e_cr"),
            models.Index(fields=["priority", "status"], name="librar_librar_946fa07e_pr"),
            models.Index(fields=["department_tag", "status"], name="librar_librar_946fa07e_dp"),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"

    def clean(self):
        super().clean()
        self.code = self.code.strip().upper()
        if self.capacity_limit < 0:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Capacity limit cannot be negative."))
        if self.allocated_count > self.capacity_limit:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Allocated count cannot exceed capacity limit."))
        if self.alert_threshold_low > self.alert_threshold_high:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Alert low threshold cannot exceed alert high threshold."))

    def is_expired(self) -> bool:
        """Determines whether this policy or record has passed its expiration date."""
        if not self.expiration_date:
            return False
        return timezone.now().date() > self.expiration_date

    def calculate_utilization(self) -> float:
        """Calculates percentage utilization against capacity limit."""
        if not self.capacity_limit or self.capacity_limit == 0:
            return 0.0
        return round((float(self.allocated_count) / float(self.capacity_limit)) * 100.0, 2)

    def has_available_capacity(self, delta: int = 1) -> bool:
        """Validates whether additional allocations can be committed."""
        return (self.allocated_count + delta) <= self.capacity_limit

    def increment_allocation(self, delta: int = 1) -> None:
        """Safely increments the committed allocation counter."""
        if not self.has_available_capacity(delta):
            from core.exceptions import CapacityExceededException
            raise CapacityExceededException(f"Cannot allocate {delta} units: Capacity limit reached.")
        self.allocated_count += delta
        self.save(update_fields=["allocated_count", "updated_at"])

    def decrement_allocation(self, delta: int = 1) -> None:
        """Safely decrements the allocated resource counter."""
        self.allocated_count = max(0, self.allocated_count - delta)
        self.save(update_fields=["allocated_count", "updated_at"])

    def mark_as_verified(self, approver: str = "SYSTEM") -> None:
        """Validates verification state and records signature in metadata."""
        self.is_verified = True
        self.metadata["verified_by"] = approver
        self.metadata["verified_at"] = timezone.now().isoformat()
        self.save(update_fields=["is_verified", "metadata", "updated_at"])

    def lock_record(self, reason: str = "Administrative Lock") -> None:
        """Freezes entity modifications for audit verification."""
        self.is_locked = True
        self.metadata["lock_reason"] = reason
        self.metadata["locked_at"] = timezone.now().isoformat()
        self.save(update_fields=["is_locked", "metadata", "updated_at"])

    def unlock_record(self) -> None:
        """Releases entity lock following audit review."""
        self.is_locked = False
        self.metadata["unlocked_at"] = timezone.now().isoformat()
        self.save(update_fields=["is_locked", "metadata", "updated_at"])

    def compute_composite_score(self) -> Decimal:
        """Computes a multi-factor score incorporating rating, priority, and capacity load."""
        utilization = Decimal(str(self.calculate_utilization()))
        return round((self.score_rating * Decimal("0.60")) + (Decimal(self.priority) * Decimal("0.20")) + (utilization * Decimal("0.002")), 4)

    def is_escalation_required(self) -> bool:
        """Determines if utilization exceeds high alert threshold."""
        return self.calculate_utilization() >= float(self.alert_threshold_high)

    def calculate_depreciation(self, annual_rate: Decimal = Decimal("0.10")) -> Decimal:
        """Calculates asset depreciation over operational lifecycle."""
        years = max(1, (timezone.now().date() - self.effective_date).days // 365)
        depreciated = self.monetary_value * ((Decimal("1.00") - annual_rate) ** years)
        return round(max(Decimal("0.00"), depreciated), 2)

    def to_summary_dict(self) -> dict:
        """Exports a standardized dictionary representation for APIs and reports."""
        return {
            "code": self.code,
            "name": self.name,
            "status": self.status,
            "priority": self.priority,
            "department_tag": self.department_tag,
            "fiscal_code": self.fiscal_code,
            "approval_authority": self.approval_authority,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "is_locked": self.is_locked,
            "capacity_limit": self.capacity_limit,
            "allocated_count": self.allocated_count,
            "utilization_pct": self.calculate_utilization(),
            "composite_score": str(self.compute_composite_score()),
            "monetary_value": str(self.monetary_value),
            "created_at": self.created_at.isoformat(),
        }

class LibraryReservationsWorkflowAuditCheckpointQuerySet(models.QuerySet):
    """Custom QuerySet methods for LibraryReservationsWorkflowAuditCheckpoint."""
    def active(self):
        return self.filter(is_active=True)
    def recent(self, days: int = 30):
        cutoff = timezone.now() - timezone.timedelta(days=days)
        return self.filter(created_at__gte=cutoff)
    def search(self, query: str):
        if not query:
            return self
        return self.filter(models.Q(code__icontains=query) | models.Q(name__icontains=query))
    def verified(self):
        return self.filter(is_verified=True)
    def by_status(self, status: str):
        return self.filter(status=status)
    def priority_ordered(self):
        return self.order_by("-priority", "-created_at")
    def capacity_available(self):
        return self.filter(allocated_count__lt=models.F("capacity_limit"))
    def threshold_exceeded(self):
        return self.filter(allocated_count__gte=models.F("capacity_limit"))
    def with_high_score(self, min_score: Decimal = Decimal("3.00")):
        return self.filter(score_rating__gte=min_score)

class LibraryReservationsWorkflowAuditCheckpointManager(models.Manager):
    """Custom model manager for LibraryReservationsWorkflowAuditCheckpoint."""
    def get_queryset(self):
        return LibraryReservationsWorkflowAuditCheckpointQuerySet(self.model, using=self._db)
    def active(self):
        return self.get_queryset().active()
    def search(self, query: str):
        return self.get_queryset().search(query)
    def verified(self):
        return self.get_queryset().verified()
    def by_status(self, status: str):
        return self.get_queryset().by_status(status)
    def capacity_available(self):
        return self.get_queryset().capacity_available()

class LibraryReservationsWorkflowAuditCheckpoint(models.Model):
    """
    LibraryReservationsWorkflowAuditCheckpoint: Stage-gate checkpoints and sign-off validations.
    Enterprise Grade Institutional Entity with strict audit trails and SQLite optimization.
    """
    code = models.CharField(max_length=64, unique=True, db_index=True, verbose_name=_("Entity Code"))
    name = models.CharField(max_length=255, db_index=True, verbose_name=_("Entity Name"))
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True, verbose_name=_("Slug"))
    description = models.TextField(blank=True, default="", verbose_name=_("Description"))
    priority = models.PositiveIntegerField(default=1, verbose_name=_("Priority Weight"))
    status = models.CharField(max_length=32, default="ACTIVE", db_index=True, verbose_name=_("Status"))
    is_active = models.BooleanField(default=True, db_index=True, verbose_name=_("Active Flag"))
    is_verified = models.BooleanField(default=False, verbose_name=_("Verified Flag"))
    is_locked = models.BooleanField(default=False, verbose_name=_("Lock Flag"))
    score_rating = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"), verbose_name=_("Score"))
    monetary_value = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"), verbose_name=_("Monetary Value"))
    capacity_limit = models.PositiveIntegerField(default=100, verbose_name=_("Capacity Limit"))
    allocated_count = models.PositiveIntegerField(default=0, verbose_name=_("Allocated Count"))
    waitlist_count = models.PositiveIntegerField(default=0, verbose_name=_("Waitlist Count"))
    alert_threshold_low = models.PositiveIntegerField(default=10, verbose_name=_("Alert Low"))
    alert_threshold_high = models.PositiveIntegerField(default=90, verbose_name=_("Alert High"))
    renewal_cycle_months = models.PositiveIntegerField(default=12, verbose_name=_("Renewal Months"))
    department_tag = models.CharField(max_length=64, blank=True, default="LIBRARY", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@library.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = LibraryReservationsWorkflowAuditCheckpointManager()

    class Meta:
        db_table = "library_library_reservations_workflowauditcheckpoint"
        ordering = ["-created_at", "code"]
        verbose_name = _("LibraryReservationsWorkflowAuditCheckpoint")
        verbose_name_plural = _("LibraryReservationsWorkflowAuditCheckpoints")
        indexes = [
            models.Index(fields=["code", "status"], name="librar_librar_3b61c56a_cd"),
            models.Index(fields=["created_at"], name="librar_librar_3b61c56a_cr"),
            models.Index(fields=["priority", "status"], name="librar_librar_3b61c56a_pr"),
            models.Index(fields=["department_tag", "status"], name="librar_librar_3b61c56a_dp"),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"

    def clean(self):
        super().clean()
        self.code = self.code.strip().upper()
        if self.capacity_limit < 0:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Capacity limit cannot be negative."))
        if self.allocated_count > self.capacity_limit:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Allocated count cannot exceed capacity limit."))
        if self.alert_threshold_low > self.alert_threshold_high:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Alert low threshold cannot exceed alert high threshold."))

    def is_expired(self) -> bool:
        """Determines whether this policy or record has passed its expiration date."""
        if not self.expiration_date:
            return False
        return timezone.now().date() > self.expiration_date

    def calculate_utilization(self) -> float:
        """Calculates percentage utilization against capacity limit."""
        if not self.capacity_limit or self.capacity_limit == 0:
            return 0.0
        return round((float(self.allocated_count) / float(self.capacity_limit)) * 100.0, 2)

    def has_available_capacity(self, delta: int = 1) -> bool:
        """Validates whether additional allocations can be committed."""
        return (self.allocated_count + delta) <= self.capacity_limit

    def increment_allocation(self, delta: int = 1) -> None:
        """Safely increments the committed allocation counter."""
        if not self.has_available_capacity(delta):
            from core.exceptions import CapacityExceededException
            raise CapacityExceededException(f"Cannot allocate {delta} units: Capacity limit reached.")
        self.allocated_count += delta
        self.save(update_fields=["allocated_count", "updated_at"])

    def decrement_allocation(self, delta: int = 1) -> None:
        """Safely decrements the allocated resource counter."""
        self.allocated_count = max(0, self.allocated_count - delta)
        self.save(update_fields=["allocated_count", "updated_at"])

    def mark_as_verified(self, approver: str = "SYSTEM") -> None:
        """Validates verification state and records signature in metadata."""
        self.is_verified = True
        self.metadata["verified_by"] = approver
        self.metadata["verified_at"] = timezone.now().isoformat()
        self.save(update_fields=["is_verified", "metadata", "updated_at"])

    def lock_record(self, reason: str = "Administrative Lock") -> None:
        """Freezes entity modifications for audit verification."""
        self.is_locked = True
        self.metadata["lock_reason"] = reason
        self.metadata["locked_at"] = timezone.now().isoformat()
        self.save(update_fields=["is_locked", "metadata", "updated_at"])

    def unlock_record(self) -> None:
        """Releases entity lock following audit review."""
        self.is_locked = False
        self.metadata["unlocked_at"] = timezone.now().isoformat()
        self.save(update_fields=["is_locked", "metadata", "updated_at"])

    def compute_composite_score(self) -> Decimal:
        """Computes a multi-factor score incorporating rating, priority, and capacity load."""
        utilization = Decimal(str(self.calculate_utilization()))
        return round((self.score_rating * Decimal("0.60")) + (Decimal(self.priority) * Decimal("0.20")) + (utilization * Decimal("0.002")), 4)

    def is_escalation_required(self) -> bool:
        """Determines if utilization exceeds high alert threshold."""
        return self.calculate_utilization() >= float(self.alert_threshold_high)

    def calculate_depreciation(self, annual_rate: Decimal = Decimal("0.10")) -> Decimal:
        """Calculates asset depreciation over operational lifecycle."""
        years = max(1, (timezone.now().date() - self.effective_date).days // 365)
        depreciated = self.monetary_value * ((Decimal("1.00") - annual_rate) ** years)
        return round(max(Decimal("0.00"), depreciated), 2)

    def to_summary_dict(self) -> dict:
        """Exports a standardized dictionary representation for APIs and reports."""
        return {
            "code": self.code,
            "name": self.name,
            "status": self.status,
            "priority": self.priority,
            "department_tag": self.department_tag,
            "fiscal_code": self.fiscal_code,
            "approval_authority": self.approval_authority,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "is_locked": self.is_locked,
            "capacity_limit": self.capacity_limit,
            "allocated_count": self.allocated_count,
            "utilization_pct": self.calculate_utilization(),
            "composite_score": str(self.compute_composite_score()),
            "monetary_value": str(self.monetary_value),
            "created_at": self.created_at.isoformat(),
        }

class LibraryReservationsDisasterRecoveryCheckpointQuerySet(models.QuerySet):
    """Custom QuerySet methods for LibraryReservationsDisasterRecoveryCheckpoint."""
    def active(self):
        return self.filter(is_active=True)
    def recent(self, days: int = 30):
        cutoff = timezone.now() - timezone.timedelta(days=days)
        return self.filter(created_at__gte=cutoff)
    def search(self, query: str):
        if not query:
            return self
        return self.filter(models.Q(code__icontains=query) | models.Q(name__icontains=query))
    def verified(self):
        return self.filter(is_verified=True)
    def by_status(self, status: str):
        return self.filter(status=status)
    def priority_ordered(self):
        return self.order_by("-priority", "-created_at")
    def capacity_available(self):
        return self.filter(allocated_count__lt=models.F("capacity_limit"))
    def threshold_exceeded(self):
        return self.filter(allocated_count__gte=models.F("capacity_limit"))
    def with_high_score(self, min_score: Decimal = Decimal("3.00")):
        return self.filter(score_rating__gte=min_score)

class LibraryReservationsDisasterRecoveryCheckpointManager(models.Manager):
    """Custom model manager for LibraryReservationsDisasterRecoveryCheckpoint."""
    def get_queryset(self):
        return LibraryReservationsDisasterRecoveryCheckpointQuerySet(self.model, using=self._db)
    def active(self):
        return self.get_queryset().active()
    def search(self, query: str):
        return self.get_queryset().search(query)
    def verified(self):
        return self.get_queryset().verified()
    def by_status(self, status: str):
        return self.get_queryset().by_status(status)
    def capacity_available(self):
        return self.get_queryset().capacity_available()

class LibraryReservationsDisasterRecoveryCheckpoint(models.Model):
    """
    LibraryReservationsDisasterRecoveryCheckpoint: Point-in-time state checkpoint for high-availability disaster recovery validation.
    Enterprise Grade Institutional Entity with strict audit trails and SQLite optimization.
    """
    code = models.CharField(max_length=64, unique=True, db_index=True, verbose_name=_("Entity Code"))
    name = models.CharField(max_length=255, db_index=True, verbose_name=_("Entity Name"))
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True, verbose_name=_("Slug"))
    description = models.TextField(blank=True, default="", verbose_name=_("Description"))
    priority = models.PositiveIntegerField(default=1, verbose_name=_("Priority Weight"))
    status = models.CharField(max_length=32, default="ACTIVE", db_index=True, verbose_name=_("Status"))
    is_active = models.BooleanField(default=True, db_index=True, verbose_name=_("Active Flag"))
    is_verified = models.BooleanField(default=False, verbose_name=_("Verified Flag"))
    is_locked = models.BooleanField(default=False, verbose_name=_("Lock Flag"))
    score_rating = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"), verbose_name=_("Score"))
    monetary_value = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"), verbose_name=_("Monetary Value"))
    capacity_limit = models.PositiveIntegerField(default=100, verbose_name=_("Capacity Limit"))
    allocated_count = models.PositiveIntegerField(default=0, verbose_name=_("Allocated Count"))
    waitlist_count = models.PositiveIntegerField(default=0, verbose_name=_("Waitlist Count"))
    alert_threshold_low = models.PositiveIntegerField(default=10, verbose_name=_("Alert Low"))
    alert_threshold_high = models.PositiveIntegerField(default=90, verbose_name=_("Alert High"))
    renewal_cycle_months = models.PositiveIntegerField(default=12, verbose_name=_("Renewal Months"))
    department_tag = models.CharField(max_length=64, blank=True, default="LIBRARY", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@library.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = LibraryReservationsDisasterRecoveryCheckpointManager()

    class Meta:
        db_table = "library_library_reservations_disasterrecoverycheckpoint"
        ordering = ["-created_at", "code"]
        verbose_name = _("LibraryReservationsDisasterRecoveryCheckpoint")
        verbose_name_plural = _("LibraryReservationsDisasterRecoveryCheckpoints")
        indexes = [
            models.Index(fields=["code", "status"], name="librar_librar_ae8698ee_cd"),
            models.Index(fields=["created_at"], name="librar_librar_ae8698ee_cr"),
            models.Index(fields=["priority", "status"], name="librar_librar_ae8698ee_pr"),
            models.Index(fields=["department_tag", "status"], name="librar_librar_ae8698ee_dp"),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"

    def clean(self):
        super().clean()
        self.code = self.code.strip().upper()
        if self.capacity_limit < 0:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Capacity limit cannot be negative."))
        if self.allocated_count > self.capacity_limit:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Allocated count cannot exceed capacity limit."))
        if self.alert_threshold_low > self.alert_threshold_high:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Alert low threshold cannot exceed alert high threshold."))

    def is_expired(self) -> bool:
        """Determines whether this policy or record has passed its expiration date."""
        if not self.expiration_date:
            return False
        return timezone.now().date() > self.expiration_date

    def calculate_utilization(self) -> float:
        """Calculates percentage utilization against capacity limit."""
        if not self.capacity_limit or self.capacity_limit == 0:
            return 0.0
        return round((float(self.allocated_count) / float(self.capacity_limit)) * 100.0, 2)

    def has_available_capacity(self, delta: int = 1) -> bool:
        """Validates whether additional allocations can be committed."""
        return (self.allocated_count + delta) <= self.capacity_limit

    def increment_allocation(self, delta: int = 1) -> None:
        """Safely increments the committed allocation counter."""
        if not self.has_available_capacity(delta):
            from core.exceptions import CapacityExceededException
            raise CapacityExceededException(f"Cannot allocate {delta} units: Capacity limit reached.")
        self.allocated_count += delta
        self.save(update_fields=["allocated_count", "updated_at"])

    def decrement_allocation(self, delta: int = 1) -> None:
        """Safely decrements the allocated resource counter."""
        self.allocated_count = max(0, self.allocated_count - delta)
        self.save(update_fields=["allocated_count", "updated_at"])

    def mark_as_verified(self, approver: str = "SYSTEM") -> None:
        """Validates verification state and records signature in metadata."""
        self.is_verified = True
        self.metadata["verified_by"] = approver
        self.metadata["verified_at"] = timezone.now().isoformat()
        self.save(update_fields=["is_verified", "metadata", "updated_at"])

    def lock_record(self, reason: str = "Administrative Lock") -> None:
        """Freezes entity modifications for audit verification."""
        self.is_locked = True
        self.metadata["lock_reason"] = reason
        self.metadata["locked_at"] = timezone.now().isoformat()
        self.save(update_fields=["is_locked", "metadata", "updated_at"])

    def unlock_record(self) -> None:
        """Releases entity lock following audit review."""
        self.is_locked = False
        self.metadata["unlocked_at"] = timezone.now().isoformat()
        self.save(update_fields=["is_locked", "metadata", "updated_at"])

    def compute_composite_score(self) -> Decimal:
        """Computes a multi-factor score incorporating rating, priority, and capacity load."""
        utilization = Decimal(str(self.calculate_utilization()))
        return round((self.score_rating * Decimal("0.60")) + (Decimal(self.priority) * Decimal("0.20")) + (utilization * Decimal("0.002")), 4)

    def is_escalation_required(self) -> bool:
        """Determines if utilization exceeds high alert threshold."""
        return self.calculate_utilization() >= float(self.alert_threshold_high)

    def calculate_depreciation(self, annual_rate: Decimal = Decimal("0.10")) -> Decimal:
        """Calculates asset depreciation over operational lifecycle."""
        years = max(1, (timezone.now().date() - self.effective_date).days // 365)
        depreciated = self.monetary_value * ((Decimal("1.00") - annual_rate) ** years)
        return round(max(Decimal("0.00"), depreciated), 2)

    def to_summary_dict(self) -> dict:
        """Exports a standardized dictionary representation for APIs and reports."""
        return {
            "code": self.code,
            "name": self.name,
            "status": self.status,
            "priority": self.priority,
            "department_tag": self.department_tag,
            "fiscal_code": self.fiscal_code,
            "approval_authority": self.approval_authority,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "is_locked": self.is_locked,
            "capacity_limit": self.capacity_limit,
            "allocated_count": self.allocated_count,
            "utilization_pct": self.calculate_utilization(),
            "composite_score": str(self.compute_composite_score()),
            "monetary_value": str(self.monetary_value),
            "created_at": self.created_at.isoformat(),
        }

class LibraryReservationsSLAComplianceRegisterQuerySet(models.QuerySet):
    """Custom QuerySet methods for LibraryReservationsSLAComplianceRegister."""
    def active(self):
        return self.filter(is_active=True)
    def recent(self, days: int = 30):
        cutoff = timezone.now() - timezone.timedelta(days=days)
        return self.filter(created_at__gte=cutoff)
    def search(self, query: str):
        if not query:
            return self
        return self.filter(models.Q(code__icontains=query) | models.Q(name__icontains=query))
    def verified(self):
        return self.filter(is_verified=True)
    def by_status(self, status: str):
        return self.filter(status=status)
    def priority_ordered(self):
        return self.order_by("-priority", "-created_at")
    def capacity_available(self):
        return self.filter(allocated_count__lt=models.F("capacity_limit"))
    def threshold_exceeded(self):
        return self.filter(allocated_count__gte=models.F("capacity_limit"))
    def with_high_score(self, min_score: Decimal = Decimal("3.00")):
        return self.filter(score_rating__gte=min_score)

class LibraryReservationsSLAComplianceRegisterManager(models.Manager):
    """Custom model manager for LibraryReservationsSLAComplianceRegister."""
    def get_queryset(self):
        return LibraryReservationsSLAComplianceRegisterQuerySet(self.model, using=self._db)
    def active(self):
        return self.get_queryset().active()
    def search(self, query: str):
        return self.get_queryset().search(query)
    def verified(self):
        return self.get_queryset().verified()
    def by_status(self, status: str):
        return self.get_queryset().by_status(status)
    def capacity_available(self):
        return self.get_queryset().capacity_available()

class LibraryReservationsSLAComplianceRegister(models.Model):
    """
    LibraryReservationsSLAComplianceRegister: Service level agreement compliance tracker for operational responsiveness.
    Enterprise Grade Institutional Entity with strict audit trails and SQLite optimization.
    """
    code = models.CharField(max_length=64, unique=True, db_index=True, verbose_name=_("Entity Code"))
    name = models.CharField(max_length=255, db_index=True, verbose_name=_("Entity Name"))
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True, verbose_name=_("Slug"))
    description = models.TextField(blank=True, default="", verbose_name=_("Description"))
    priority = models.PositiveIntegerField(default=1, verbose_name=_("Priority Weight"))
    status = models.CharField(max_length=32, default="ACTIVE", db_index=True, verbose_name=_("Status"))
    is_active = models.BooleanField(default=True, db_index=True, verbose_name=_("Active Flag"))
    is_verified = models.BooleanField(default=False, verbose_name=_("Verified Flag"))
    is_locked = models.BooleanField(default=False, verbose_name=_("Lock Flag"))
    score_rating = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"), verbose_name=_("Score"))
    monetary_value = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"), verbose_name=_("Monetary Value"))
    capacity_limit = models.PositiveIntegerField(default=100, verbose_name=_("Capacity Limit"))
    allocated_count = models.PositiveIntegerField(default=0, verbose_name=_("Allocated Count"))
    waitlist_count = models.PositiveIntegerField(default=0, verbose_name=_("Waitlist Count"))
    alert_threshold_low = models.PositiveIntegerField(default=10, verbose_name=_("Alert Low"))
    alert_threshold_high = models.PositiveIntegerField(default=90, verbose_name=_("Alert High"))
    renewal_cycle_months = models.PositiveIntegerField(default=12, verbose_name=_("Renewal Months"))
    department_tag = models.CharField(max_length=64, blank=True, default="LIBRARY", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@library.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = LibraryReservationsSLAComplianceRegisterManager()

    class Meta:
        db_table = "library_library_reservations_slacomplianceregister"
        ordering = ["-created_at", "code"]
        verbose_name = _("LibraryReservationsSLAComplianceRegister")
        verbose_name_plural = _("LibraryReservationsSLAComplianceRegisters")
        indexes = [
            models.Index(fields=["code", "status"], name="librar_librar_4a2b0677_cd"),
            models.Index(fields=["created_at"], name="librar_librar_4a2b0677_cr"),
            models.Index(fields=["priority", "status"], name="librar_librar_4a2b0677_pr"),
            models.Index(fields=["department_tag", "status"], name="librar_librar_4a2b0677_dp"),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"

    def clean(self):
        super().clean()
        self.code = self.code.strip().upper()
        if self.capacity_limit < 0:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Capacity limit cannot be negative."))
        if self.allocated_count > self.capacity_limit:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Allocated count cannot exceed capacity limit."))
        if self.alert_threshold_low > self.alert_threshold_high:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Alert low threshold cannot exceed alert high threshold."))

    def is_expired(self) -> bool:
        """Determines whether this policy or record has passed its expiration date."""
        if not self.expiration_date:
            return False
        return timezone.now().date() > self.expiration_date

    def calculate_utilization(self) -> float:
        """Calculates percentage utilization against capacity limit."""
        if not self.capacity_limit or self.capacity_limit == 0:
            return 0.0
        return round((float(self.allocated_count) / float(self.capacity_limit)) * 100.0, 2)

    def has_available_capacity(self, delta: int = 1) -> bool:
        """Validates whether additional allocations can be committed."""
        return (self.allocated_count + delta) <= self.capacity_limit

    def increment_allocation(self, delta: int = 1) -> None:
        """Safely increments the committed allocation counter."""
        if not self.has_available_capacity(delta):
            from core.exceptions import CapacityExceededException
            raise CapacityExceededException(f"Cannot allocate {delta} units: Capacity limit reached.")
        self.allocated_count += delta
        self.save(update_fields=["allocated_count", "updated_at"])

    def decrement_allocation(self, delta: int = 1) -> None:
        """Safely decrements the allocated resource counter."""
        self.allocated_count = max(0, self.allocated_count - delta)
        self.save(update_fields=["allocated_count", "updated_at"])

    def mark_as_verified(self, approver: str = "SYSTEM") -> None:
        """Validates verification state and records signature in metadata."""
        self.is_verified = True
        self.metadata["verified_by"] = approver
        self.metadata["verified_at"] = timezone.now().isoformat()
        self.save(update_fields=["is_verified", "metadata", "updated_at"])

    def lock_record(self, reason: str = "Administrative Lock") -> None:
        """Freezes entity modifications for audit verification."""
        self.is_locked = True
        self.metadata["lock_reason"] = reason
        self.metadata["locked_at"] = timezone.now().isoformat()
        self.save(update_fields=["is_locked", "metadata", "updated_at"])

    def unlock_record(self) -> None:
        """Releases entity lock following audit review."""
        self.is_locked = False
        self.metadata["unlocked_at"] = timezone.now().isoformat()
        self.save(update_fields=["is_locked", "metadata", "updated_at"])

    def compute_composite_score(self) -> Decimal:
        """Computes a multi-factor score incorporating rating, priority, and capacity load."""
        utilization = Decimal(str(self.calculate_utilization()))
        return round((self.score_rating * Decimal("0.60")) + (Decimal(self.priority) * Decimal("0.20")) + (utilization * Decimal("0.002")), 4)

    def is_escalation_required(self) -> bool:
        """Determines if utilization exceeds high alert threshold."""
        return self.calculate_utilization() >= float(self.alert_threshold_high)

    def calculate_depreciation(self, annual_rate: Decimal = Decimal("0.10")) -> Decimal:
        """Calculates asset depreciation over operational lifecycle."""
        years = max(1, (timezone.now().date() - self.effective_date).days // 365)
        depreciated = self.monetary_value * ((Decimal("1.00") - annual_rate) ** years)
        return round(max(Decimal("0.00"), depreciated), 2)

    def to_summary_dict(self) -> dict:
        """Exports a standardized dictionary representation for APIs and reports."""
        return {
            "code": self.code,
            "name": self.name,
            "status": self.status,
            "priority": self.priority,
            "department_tag": self.department_tag,
            "fiscal_code": self.fiscal_code,
            "approval_authority": self.approval_authority,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "is_locked": self.is_locked,
            "capacity_limit": self.capacity_limit,
            "allocated_count": self.allocated_count,
            "utilization_pct": self.calculate_utilization(),
            "composite_score": str(self.compute_composite_score()),
            "monetary_value": str(self.monetary_value),
            "created_at": self.created_at.isoformat(),
        }

class LibraryReservationsIncidentReportRegisterQuerySet(models.QuerySet):
    """Custom QuerySet methods for LibraryReservationsIncidentReportRegister."""
    def active(self):
        return self.filter(is_active=True)
    def recent(self, days: int = 30):
        cutoff = timezone.now() - timezone.timedelta(days=days)
        return self.filter(created_at__gte=cutoff)
    def search(self, query: str):
        if not query:
            return self
        return self.filter(models.Q(code__icontains=query) | models.Q(name__icontains=query))
    def verified(self):
        return self.filter(is_verified=True)
    def by_status(self, status: str):
        return self.filter(status=status)
    def priority_ordered(self):
        return self.order_by("-priority", "-created_at")
    def capacity_available(self):
        return self.filter(allocated_count__lt=models.F("capacity_limit"))
    def threshold_exceeded(self):
        return self.filter(allocated_count__gte=models.F("capacity_limit"))
    def with_high_score(self, min_score: Decimal = Decimal("3.00")):
        return self.filter(score_rating__gte=min_score)

class LibraryReservationsIncidentReportRegisterManager(models.Manager):
    """Custom model manager for LibraryReservationsIncidentReportRegister."""
    def get_queryset(self):
        return LibraryReservationsIncidentReportRegisterQuerySet(self.model, using=self._db)
    def active(self):
        return self.get_queryset().active()
    def search(self, query: str):
        return self.get_queryset().search(query)
    def verified(self):
        return self.get_queryset().verified()
    def by_status(self, status: str):
        return self.get_queryset().by_status(status)
    def capacity_available(self):
        return self.get_queryset().capacity_available()

class LibraryReservationsIncidentReportRegister(models.Model):
    """
    LibraryReservationsIncidentReportRegister: Incident ticketing and remediation tracking register.
    Enterprise Grade Institutional Entity with strict audit trails and SQLite optimization.
    """
    code = models.CharField(max_length=64, unique=True, db_index=True, verbose_name=_("Entity Code"))
    name = models.CharField(max_length=255, db_index=True, verbose_name=_("Entity Name"))
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True, verbose_name=_("Slug"))
    description = models.TextField(blank=True, default="", verbose_name=_("Description"))
    priority = models.PositiveIntegerField(default=1, verbose_name=_("Priority Weight"))
    status = models.CharField(max_length=32, default="ACTIVE", db_index=True, verbose_name=_("Status"))
    is_active = models.BooleanField(default=True, db_index=True, verbose_name=_("Active Flag"))
    is_verified = models.BooleanField(default=False, verbose_name=_("Verified Flag"))
    is_locked = models.BooleanField(default=False, verbose_name=_("Lock Flag"))
    score_rating = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"), verbose_name=_("Score"))
    monetary_value = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"), verbose_name=_("Monetary Value"))
    capacity_limit = models.PositiveIntegerField(default=100, verbose_name=_("Capacity Limit"))
    allocated_count = models.PositiveIntegerField(default=0, verbose_name=_("Allocated Count"))
    waitlist_count = models.PositiveIntegerField(default=0, verbose_name=_("Waitlist Count"))
    alert_threshold_low = models.PositiveIntegerField(default=10, verbose_name=_("Alert Low"))
    alert_threshold_high = models.PositiveIntegerField(default=90, verbose_name=_("Alert High"))
    renewal_cycle_months = models.PositiveIntegerField(default=12, verbose_name=_("Renewal Months"))
    department_tag = models.CharField(max_length=64, blank=True, default="LIBRARY", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@library.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = LibraryReservationsIncidentReportRegisterManager()

    class Meta:
        db_table = "library_library_reservations_incidentreportregister"
        ordering = ["-created_at", "code"]
        verbose_name = _("LibraryReservationsIncidentReportRegister")
        verbose_name_plural = _("LibraryReservationsIncidentReportRegisters")
        indexes = [
            models.Index(fields=["code", "status"], name="librar_librar_f180a745_cd"),
            models.Index(fields=["created_at"], name="librar_librar_f180a745_cr"),
            models.Index(fields=["priority", "status"], name="librar_librar_f180a745_pr"),
            models.Index(fields=["department_tag", "status"], name="librar_librar_f180a745_dp"),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"

    def clean(self):
        super().clean()
        self.code = self.code.strip().upper()
        if self.capacity_limit < 0:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Capacity limit cannot be negative."))
        if self.allocated_count > self.capacity_limit:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Allocated count cannot exceed capacity limit."))
        if self.alert_threshold_low > self.alert_threshold_high:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Alert low threshold cannot exceed alert high threshold."))

    def is_expired(self) -> bool:
        """Determines whether this policy or record has passed its expiration date."""
        if not self.expiration_date:
            return False
        return timezone.now().date() > self.expiration_date

    def calculate_utilization(self) -> float:
        """Calculates percentage utilization against capacity limit."""
        if not self.capacity_limit or self.capacity_limit == 0:
            return 0.0
        return round((float(self.allocated_count) / float(self.capacity_limit)) * 100.0, 2)

    def has_available_capacity(self, delta: int = 1) -> bool:
        """Validates whether additional allocations can be committed."""
        return (self.allocated_count + delta) <= self.capacity_limit

    def increment_allocation(self, delta: int = 1) -> None:
        """Safely increments the committed allocation counter."""
        if not self.has_available_capacity(delta):
            from core.exceptions import CapacityExceededException
            raise CapacityExceededException(f"Cannot allocate {delta} units: Capacity limit reached.")
        self.allocated_count += delta
        self.save(update_fields=["allocated_count", "updated_at"])

    def decrement_allocation(self, delta: int = 1) -> None:
        """Safely decrements the allocated resource counter."""
        self.allocated_count = max(0, self.allocated_count - delta)
        self.save(update_fields=["allocated_count", "updated_at"])

    def mark_as_verified(self, approver: str = "SYSTEM") -> None:
        """Validates verification state and records signature in metadata."""
        self.is_verified = True
        self.metadata["verified_by"] = approver
        self.metadata["verified_at"] = timezone.now().isoformat()
        self.save(update_fields=["is_verified", "metadata", "updated_at"])

    def lock_record(self, reason: str = "Administrative Lock") -> None:
        """Freezes entity modifications for audit verification."""
        self.is_locked = True
        self.metadata["lock_reason"] = reason
        self.metadata["locked_at"] = timezone.now().isoformat()
        self.save(update_fields=["is_locked", "metadata", "updated_at"])

    def unlock_record(self) -> None:
        """Releases entity lock following audit review."""
        self.is_locked = False
        self.metadata["unlocked_at"] = timezone.now().isoformat()
        self.save(update_fields=["is_locked", "metadata", "updated_at"])

    def compute_composite_score(self) -> Decimal:
        """Computes a multi-factor score incorporating rating, priority, and capacity load."""
        utilization = Decimal(str(self.calculate_utilization()))
        return round((self.score_rating * Decimal("0.60")) + (Decimal(self.priority) * Decimal("0.20")) + (utilization * Decimal("0.002")), 4)

    def is_escalation_required(self) -> bool:
        """Determines if utilization exceeds high alert threshold."""
        return self.calculate_utilization() >= float(self.alert_threshold_high)

    def calculate_depreciation(self, annual_rate: Decimal = Decimal("0.10")) -> Decimal:
        """Calculates asset depreciation over operational lifecycle."""
        years = max(1, (timezone.now().date() - self.effective_date).days // 365)
        depreciated = self.monetary_value * ((Decimal("1.00") - annual_rate) ** years)
        return round(max(Decimal("0.00"), depreciated), 2)

    def to_summary_dict(self) -> dict:
        """Exports a standardized dictionary representation for APIs and reports."""
        return {
            "code": self.code,
            "name": self.name,
            "status": self.status,
            "priority": self.priority,
            "department_tag": self.department_tag,
            "fiscal_code": self.fiscal_code,
            "approval_authority": self.approval_authority,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "is_locked": self.is_locked,
            "capacity_limit": self.capacity_limit,
            "allocated_count": self.allocated_count,
            "utilization_pct": self.calculate_utilization(),
            "composite_score": str(self.compute_composite_score()),
            "monetary_value": str(self.monetary_value),
            "created_at": self.created_at.isoformat(),
        }

class LibraryReservationsBusinessContinuityPlanQuerySet(models.QuerySet):
    """Custom QuerySet methods for LibraryReservationsBusinessContinuityPlan."""
    def active(self):
        return self.filter(is_active=True)
    def recent(self, days: int = 30):
        cutoff = timezone.now() - timezone.timedelta(days=days)
        return self.filter(created_at__gte=cutoff)
    def search(self, query: str):
        if not query:
            return self
        return self.filter(models.Q(code__icontains=query) | models.Q(name__icontains=query))
    def verified(self):
        return self.filter(is_verified=True)
    def by_status(self, status: str):
        return self.filter(status=status)
    def priority_ordered(self):
        return self.order_by("-priority", "-created_at")
    def capacity_available(self):
        return self.filter(allocated_count__lt=models.F("capacity_limit"))
    def threshold_exceeded(self):
        return self.filter(allocated_count__gte=models.F("capacity_limit"))
    def with_high_score(self, min_score: Decimal = Decimal("3.00")):
        return self.filter(score_rating__gte=min_score)

class LibraryReservationsBusinessContinuityPlanManager(models.Manager):
    """Custom model manager for LibraryReservationsBusinessContinuityPlan."""
    def get_queryset(self):
        return LibraryReservationsBusinessContinuityPlanQuerySet(self.model, using=self._db)
    def active(self):
        return self.get_queryset().active()
    def search(self, query: str):
        return self.get_queryset().search(query)
    def verified(self):
        return self.get_queryset().verified()
    def by_status(self, status: str):
        return self.get_queryset().by_status(status)
    def capacity_available(self):
        return self.get_queryset().capacity_available()

class LibraryReservationsBusinessContinuityPlan(models.Model):
    """
    LibraryReservationsBusinessContinuityPlan: Business continuity procedures and failover plan coordinates.
    Enterprise Grade Institutional Entity with strict audit trails and SQLite optimization.
    """
    code = models.CharField(max_length=64, unique=True, db_index=True, verbose_name=_("Entity Code"))
    name = models.CharField(max_length=255, db_index=True, verbose_name=_("Entity Name"))
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True, verbose_name=_("Slug"))
    description = models.TextField(blank=True, default="", verbose_name=_("Description"))
    priority = models.PositiveIntegerField(default=1, verbose_name=_("Priority Weight"))
    status = models.CharField(max_length=32, default="ACTIVE", db_index=True, verbose_name=_("Status"))
    is_active = models.BooleanField(default=True, db_index=True, verbose_name=_("Active Flag"))
    is_verified = models.BooleanField(default=False, verbose_name=_("Verified Flag"))
    is_locked = models.BooleanField(default=False, verbose_name=_("Lock Flag"))
    score_rating = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"), verbose_name=_("Score"))
    monetary_value = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"), verbose_name=_("Monetary Value"))
    capacity_limit = models.PositiveIntegerField(default=100, verbose_name=_("Capacity Limit"))
    allocated_count = models.PositiveIntegerField(default=0, verbose_name=_("Allocated Count"))
    waitlist_count = models.PositiveIntegerField(default=0, verbose_name=_("Waitlist Count"))
    alert_threshold_low = models.PositiveIntegerField(default=10, verbose_name=_("Alert Low"))
    alert_threshold_high = models.PositiveIntegerField(default=90, verbose_name=_("Alert High"))
    renewal_cycle_months = models.PositiveIntegerField(default=12, verbose_name=_("Renewal Months"))
    department_tag = models.CharField(max_length=64, blank=True, default="LIBRARY", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@library.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = LibraryReservationsBusinessContinuityPlanManager()

    class Meta:
        db_table = "library_library_reservations_businesscontinuityplan"
        ordering = ["-created_at", "code"]
        verbose_name = _("LibraryReservationsBusinessContinuityPlan")
        verbose_name_plural = _("LibraryReservationsBusinessContinuityPlans")
        indexes = [
            models.Index(fields=["code", "status"], name="librar_librar_fd09d35f_cd"),
            models.Index(fields=["created_at"], name="librar_librar_fd09d35f_cr"),
            models.Index(fields=["priority", "status"], name="librar_librar_fd09d35f_pr"),
            models.Index(fields=["department_tag", "status"], name="librar_librar_fd09d35f_dp"),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"

    def clean(self):
        super().clean()
        self.code = self.code.strip().upper()
        if self.capacity_limit < 0:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Capacity limit cannot be negative."))
        if self.allocated_count > self.capacity_limit:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Allocated count cannot exceed capacity limit."))
        if self.alert_threshold_low > self.alert_threshold_high:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Alert low threshold cannot exceed alert high threshold."))

    def is_expired(self) -> bool:
        """Determines whether this policy or record has passed its expiration date."""
        if not self.expiration_date:
            return False
        return timezone.now().date() > self.expiration_date

    def calculate_utilization(self) -> float:
        """Calculates percentage utilization against capacity limit."""
        if not self.capacity_limit or self.capacity_limit == 0:
            return 0.0
        return round((float(self.allocated_count) / float(self.capacity_limit)) * 100.0, 2)

    def has_available_capacity(self, delta: int = 1) -> bool:
        """Validates whether additional allocations can be committed."""
        return (self.allocated_count + delta) <= self.capacity_limit

    def increment_allocation(self, delta: int = 1) -> None:
        """Safely increments the committed allocation counter."""
        if not self.has_available_capacity(delta):
            from core.exceptions import CapacityExceededException
            raise CapacityExceededException(f"Cannot allocate {delta} units: Capacity limit reached.")
        self.allocated_count += delta
        self.save(update_fields=["allocated_count", "updated_at"])

    def decrement_allocation(self, delta: int = 1) -> None:
        """Safely decrements the allocated resource counter."""
        self.allocated_count = max(0, self.allocated_count - delta)
        self.save(update_fields=["allocated_count", "updated_at"])

    def mark_as_verified(self, approver: str = "SYSTEM") -> None:
        """Validates verification state and records signature in metadata."""
        self.is_verified = True
        self.metadata["verified_by"] = approver
        self.metadata["verified_at"] = timezone.now().isoformat()
        self.save(update_fields=["is_verified", "metadata", "updated_at"])

    def lock_record(self, reason: str = "Administrative Lock") -> None:
        """Freezes entity modifications for audit verification."""
        self.is_locked = True
        self.metadata["lock_reason"] = reason
        self.metadata["locked_at"] = timezone.now().isoformat()
        self.save(update_fields=["is_locked", "metadata", "updated_at"])

    def unlock_record(self) -> None:
        """Releases entity lock following audit review."""
        self.is_locked = False
        self.metadata["unlocked_at"] = timezone.now().isoformat()
        self.save(update_fields=["is_locked", "metadata", "updated_at"])

    def compute_composite_score(self) -> Decimal:
        """Computes a multi-factor score incorporating rating, priority, and capacity load."""
        utilization = Decimal(str(self.calculate_utilization()))
        return round((self.score_rating * Decimal("0.60")) + (Decimal(self.priority) * Decimal("0.20")) + (utilization * Decimal("0.002")), 4)

    def is_escalation_required(self) -> bool:
        """Determines if utilization exceeds high alert threshold."""
        return self.calculate_utilization() >= float(self.alert_threshold_high)

    def calculate_depreciation(self, annual_rate: Decimal = Decimal("0.10")) -> Decimal:
        """Calculates asset depreciation over operational lifecycle."""
        years = max(1, (timezone.now().date() - self.effective_date).days // 365)
        depreciated = self.monetary_value * ((Decimal("1.00") - annual_rate) ** years)
        return round(max(Decimal("0.00"), depreciated), 2)

    def to_summary_dict(self) -> dict:
        """Exports a standardized dictionary representation for APIs and reports."""
        return {
            "code": self.code,
            "name": self.name,
            "status": self.status,
            "priority": self.priority,
            "department_tag": self.department_tag,
            "fiscal_code": self.fiscal_code,
            "approval_authority": self.approval_authority,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "is_locked": self.is_locked,
            "capacity_limit": self.capacity_limit,
            "allocated_count": self.allocated_count,
            "utilization_pct": self.calculate_utilization(),
            "composite_score": str(self.compute_composite_score()),
            "monetary_value": str(self.monetary_value),
            "created_at": self.created_at.isoformat(),
        }

class LibraryReservationsGovernanceAttestationRecordQuerySet(models.QuerySet):
    """Custom QuerySet methods for LibraryReservationsGovernanceAttestationRecord."""
    def active(self):
        return self.filter(is_active=True)
    def recent(self, days: int = 30):
        cutoff = timezone.now() - timezone.timedelta(days=days)
        return self.filter(created_at__gte=cutoff)
    def search(self, query: str):
        if not query:
            return self
        return self.filter(models.Q(code__icontains=query) | models.Q(name__icontains=query))
    def verified(self):
        return self.filter(is_verified=True)
    def by_status(self, status: str):
        return self.filter(status=status)
    def priority_ordered(self):
        return self.order_by("-priority", "-created_at")
    def capacity_available(self):
        return self.filter(allocated_count__lt=models.F("capacity_limit"))
    def threshold_exceeded(self):
        return self.filter(allocated_count__gte=models.F("capacity_limit"))
    def with_high_score(self, min_score: Decimal = Decimal("3.00")):
        return self.filter(score_rating__gte=min_score)

class LibraryReservationsGovernanceAttestationRecordManager(models.Manager):
    """Custom model manager for LibraryReservationsGovernanceAttestationRecord."""
    def get_queryset(self):
        return LibraryReservationsGovernanceAttestationRecordQuerySet(self.model, using=self._db)
    def active(self):
        return self.get_queryset().active()
    def search(self, query: str):
        return self.get_queryset().search(query)
    def verified(self):
        return self.get_queryset().verified()
    def by_status(self, status: str):
        return self.get_queryset().by_status(status)
    def capacity_available(self):
        return self.get_queryset().capacity_available()

class LibraryReservationsGovernanceAttestationRecord(models.Model):
    """
    LibraryReservationsGovernanceAttestationRecord: Formal institutional governance attestations and sign-offs.
    Enterprise Grade Institutional Entity with strict audit trails and SQLite optimization.
    """
    code = models.CharField(max_length=64, unique=True, db_index=True, verbose_name=_("Entity Code"))
    name = models.CharField(max_length=255, db_index=True, verbose_name=_("Entity Name"))
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True, verbose_name=_("Slug"))
    description = models.TextField(blank=True, default="", verbose_name=_("Description"))
    priority = models.PositiveIntegerField(default=1, verbose_name=_("Priority Weight"))
    status = models.CharField(max_length=32, default="ACTIVE", db_index=True, verbose_name=_("Status"))
    is_active = models.BooleanField(default=True, db_index=True, verbose_name=_("Active Flag"))
    is_verified = models.BooleanField(default=False, verbose_name=_("Verified Flag"))
    is_locked = models.BooleanField(default=False, verbose_name=_("Lock Flag"))
    score_rating = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"), verbose_name=_("Score"))
    monetary_value = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"), verbose_name=_("Monetary Value"))
    capacity_limit = models.PositiveIntegerField(default=100, verbose_name=_("Capacity Limit"))
    allocated_count = models.PositiveIntegerField(default=0, verbose_name=_("Allocated Count"))
    waitlist_count = models.PositiveIntegerField(default=0, verbose_name=_("Waitlist Count"))
    alert_threshold_low = models.PositiveIntegerField(default=10, verbose_name=_("Alert Low"))
    alert_threshold_high = models.PositiveIntegerField(default=90, verbose_name=_("Alert High"))
    renewal_cycle_months = models.PositiveIntegerField(default=12, verbose_name=_("Renewal Months"))
    department_tag = models.CharField(max_length=64, blank=True, default="LIBRARY", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@library.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = LibraryReservationsGovernanceAttestationRecordManager()

    class Meta:
        db_table = "library_library_reservations_governanceattestationrecord"
        ordering = ["-created_at", "code"]
        verbose_name = _("LibraryReservationsGovernanceAttestationRecord")
        verbose_name_plural = _("LibraryReservationsGovernanceAttestationRecords")
        indexes = [
            models.Index(fields=["code", "status"], name="librar_librar_40a1f97f_cd"),
            models.Index(fields=["created_at"], name="librar_librar_40a1f97f_cr"),
            models.Index(fields=["priority", "status"], name="librar_librar_40a1f97f_pr"),
            models.Index(fields=["department_tag", "status"], name="librar_librar_40a1f97f_dp"),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"

    def clean(self):
        super().clean()
        self.code = self.code.strip().upper()
        if self.capacity_limit < 0:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Capacity limit cannot be negative."))
        if self.allocated_count > self.capacity_limit:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Allocated count cannot exceed capacity limit."))
        if self.alert_threshold_low > self.alert_threshold_high:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Alert low threshold cannot exceed alert high threshold."))

    def is_expired(self) -> bool:
        """Determines whether this policy or record has passed its expiration date."""
        if not self.expiration_date:
            return False
        return timezone.now().date() > self.expiration_date

    def calculate_utilization(self) -> float:
        """Calculates percentage utilization against capacity limit."""
        if not self.capacity_limit or self.capacity_limit == 0:
            return 0.0
        return round((float(self.allocated_count) / float(self.capacity_limit)) * 100.0, 2)

    def has_available_capacity(self, delta: int = 1) -> bool:
        """Validates whether additional allocations can be committed."""
        return (self.allocated_count + delta) <= self.capacity_limit

    def increment_allocation(self, delta: int = 1) -> None:
        """Safely increments the committed allocation counter."""
        if not self.has_available_capacity(delta):
            from core.exceptions import CapacityExceededException
            raise CapacityExceededException(f"Cannot allocate {delta} units: Capacity limit reached.")
        self.allocated_count += delta
        self.save(update_fields=["allocated_count", "updated_at"])

    def decrement_allocation(self, delta: int = 1) -> None:
        """Safely decrements the allocated resource counter."""
        self.allocated_count = max(0, self.allocated_count - delta)
        self.save(update_fields=["allocated_count", "updated_at"])

    def mark_as_verified(self, approver: str = "SYSTEM") -> None:
        """Validates verification state and records signature in metadata."""
        self.is_verified = True
        self.metadata["verified_by"] = approver
        self.metadata["verified_at"] = timezone.now().isoformat()
        self.save(update_fields=["is_verified", "metadata", "updated_at"])

    def lock_record(self, reason: str = "Administrative Lock") -> None:
        """Freezes entity modifications for audit verification."""
        self.is_locked = True
        self.metadata["lock_reason"] = reason
        self.metadata["locked_at"] = timezone.now().isoformat()
        self.save(update_fields=["is_locked", "metadata", "updated_at"])

    def unlock_record(self) -> None:
        """Releases entity lock following audit review."""
        self.is_locked = False
        self.metadata["unlocked_at"] = timezone.now().isoformat()
        self.save(update_fields=["is_locked", "metadata", "updated_at"])

    def compute_composite_score(self) -> Decimal:
        """Computes a multi-factor score incorporating rating, priority, and capacity load."""
        utilization = Decimal(str(self.calculate_utilization()))
        return round((self.score_rating * Decimal("0.60")) + (Decimal(self.priority) * Decimal("0.20")) + (utilization * Decimal("0.002")), 4)

    def is_escalation_required(self) -> bool:
        """Determines if utilization exceeds high alert threshold."""
        return self.calculate_utilization() >= float(self.alert_threshold_high)

    def calculate_depreciation(self, annual_rate: Decimal = Decimal("0.10")) -> Decimal:
        """Calculates asset depreciation over operational lifecycle."""
        years = max(1, (timezone.now().date() - self.effective_date).days // 365)
        depreciated = self.monetary_value * ((Decimal("1.00") - annual_rate) ** years)
        return round(max(Decimal("0.00"), depreciated), 2)

    def to_summary_dict(self) -> dict:
        """Exports a standardized dictionary representation for APIs and reports."""
        return {
            "code": self.code,
            "name": self.name,
            "status": self.status,
            "priority": self.priority,
            "department_tag": self.department_tag,
            "fiscal_code": self.fiscal_code,
            "approval_authority": self.approval_authority,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "is_locked": self.is_locked,
            "capacity_limit": self.capacity_limit,
            "allocated_count": self.allocated_count,
            "utilization_pct": self.calculate_utilization(),
            "composite_score": str(self.compute_composite_score()),
            "monetary_value": str(self.monetary_value),
            "created_at": self.created_at.isoformat(),
        }
