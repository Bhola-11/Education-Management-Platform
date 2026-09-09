"""
Enterprise Domain Models for Timetables: Time Slot Architecture
PR #31: Relational Schema, Field Constraints, Custom Managers & State Tracking.
"""

from decimal import Decimal
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from core.constants import AcademicStatus, Gender, BloodGroup, DegreeLevel, AttendanceStatus
from core.validators import validate_phone_number, validate_national_id, validate_gpa_range

class TimetablesSlotsMasterQuerySet(models.QuerySet):
    """Custom QuerySet methods for TimetablesSlotsMaster."""
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

class TimetablesSlotsMasterManager(models.Manager):
    """Custom model manager for TimetablesSlotsMaster."""
    def get_queryset(self):
        return TimetablesSlotsMasterQuerySet(self.model, using=self._db)
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

class TimetablesSlotsMaster(models.Model):
    """
    TimetablesSlotsMaster: Primary domain master record representing the central institutional entity.
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
    department_tag = models.CharField(max_length=64, blank=True, default="TIMETABLES", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@timetables.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = TimetablesSlotsMasterManager()

    class Meta:
        db_table = "timetables_timetables_slots_master"
        ordering = ["-created_at", "code"]
        verbose_name = _("TimetablesSlotsMaster")
        verbose_name_plural = _("TimetablesSlotsMasters")
        indexes = [
            models.Index(fields=["code", "status"], name="timeta_timeta_434b5126_cd"),
            models.Index(fields=["created_at"], name="timeta_timeta_434b5126_cr"),
            models.Index(fields=["priority", "status"], name="timeta_timeta_434b5126_pr"),
            models.Index(fields=["department_tag", "status"], name="timeta_timeta_434b5126_dp"),
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

class TimetablesSlotsConfigurationQuerySet(models.QuerySet):
    """Custom QuerySet methods for TimetablesSlotsConfiguration."""
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

class TimetablesSlotsConfigurationManager(models.Manager):
    """Custom model manager for TimetablesSlotsConfiguration."""
    def get_queryset(self):
        return TimetablesSlotsConfigurationQuerySet(self.model, using=self._db)
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

class TimetablesSlotsConfiguration(models.Model):
    """
    TimetablesSlotsConfiguration: Operational configuration, policy rules, and system limits.
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
    department_tag = models.CharField(max_length=64, blank=True, default="TIMETABLES", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@timetables.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = TimetablesSlotsConfigurationManager()

    class Meta:
        db_table = "timetables_timetables_slots_configuration"
        ordering = ["-created_at", "code"]
        verbose_name = _("TimetablesSlotsConfiguration")
        verbose_name_plural = _("TimetablesSlotsConfigurations")
        indexes = [
            models.Index(fields=["code", "status"], name="timeta_timeta_97b78a50_cd"),
            models.Index(fields=["created_at"], name="timeta_timeta_97b78a50_cr"),
            models.Index(fields=["priority", "status"], name="timeta_timeta_97b78a50_pr"),
            models.Index(fields=["department_tag", "status"], name="timeta_timeta_97b78a50_dp"),
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

class TimetablesSlotsLedgerQuerySet(models.QuerySet):
    """Custom QuerySet methods for TimetablesSlotsLedger."""
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

class TimetablesSlotsLedgerManager(models.Manager):
    """Custom model manager for TimetablesSlotsLedger."""
    def get_queryset(self):
        return TimetablesSlotsLedgerQuerySet(self.model, using=self._db)
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

class TimetablesSlotsLedger(models.Model):
    """
    TimetablesSlotsLedger: Financial and quantitative accounting ledger tracking balance changes.
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
    department_tag = models.CharField(max_length=64, blank=True, default="TIMETABLES", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@timetables.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = TimetablesSlotsLedgerManager()

    class Meta:
        db_table = "timetables_timetables_slots_ledger"
        ordering = ["-created_at", "code"]
        verbose_name = _("TimetablesSlotsLedger")
        verbose_name_plural = _("TimetablesSlotsLedgers")
        indexes = [
            models.Index(fields=["code", "status"], name="timeta_timeta_571665f0_cd"),
            models.Index(fields=["created_at"], name="timeta_timeta_571665f0_cr"),
            models.Index(fields=["priority", "status"], name="timeta_timeta_571665f0_pr"),
            models.Index(fields=["department_tag", "status"], name="timeta_timeta_571665f0_dp"),
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

class TimetablesSlotsAuditTransactionQuerySet(models.QuerySet):
    """Custom QuerySet methods for TimetablesSlotsAuditTransaction."""
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

class TimetablesSlotsAuditTransactionManager(models.Manager):
    """Custom model manager for TimetablesSlotsAuditTransaction."""
    def get_queryset(self):
        return TimetablesSlotsAuditTransactionQuerySet(self.model, using=self._db)
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

class TimetablesSlotsAuditTransaction(models.Model):
    """
    TimetablesSlotsAuditTransaction: Immutable audit log transaction record capturing user mutations and states.
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
    department_tag = models.CharField(max_length=64, blank=True, default="TIMETABLES", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@timetables.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = TimetablesSlotsAuditTransactionManager()

    class Meta:
        db_table = "timetables_timetables_slots_audittransaction"
        ordering = ["-created_at", "code"]
        verbose_name = _("TimetablesSlotsAuditTransaction")
        verbose_name_plural = _("TimetablesSlotsAuditTransactions")
        indexes = [
            models.Index(fields=["code", "status"], name="timeta_timeta_751ace82_cd"),
            models.Index(fields=["created_at"], name="timeta_timeta_751ace82_cr"),
            models.Index(fields=["priority", "status"], name="timeta_timeta_751ace82_pr"),
            models.Index(fields=["department_tag", "status"], name="timeta_timeta_751ace82_dp"),
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

class TimetablesSlotsScheduleMatrixQuerySet(models.QuerySet):
    """Custom QuerySet methods for TimetablesSlotsScheduleMatrix."""
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

class TimetablesSlotsScheduleMatrixManager(models.Manager):
    """Custom model manager for TimetablesSlotsScheduleMatrix."""
    def get_queryset(self):
        return TimetablesSlotsScheduleMatrixQuerySet(self.model, using=self._db)
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

class TimetablesSlotsScheduleMatrix(models.Model):
    """
    TimetablesSlotsScheduleMatrix: Temporal planning and operational schedule coordinates.
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
    department_tag = models.CharField(max_length=64, blank=True, default="TIMETABLES", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@timetables.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = TimetablesSlotsScheduleMatrixManager()

    class Meta:
        db_table = "timetables_timetables_slots_schedulematrix"
        ordering = ["-created_at", "code"]
        verbose_name = _("TimetablesSlotsScheduleMatrix")
        verbose_name_plural = _("TimetablesSlotsScheduleMatrixs")
        indexes = [
            models.Index(fields=["code", "status"], name="timeta_timeta_ef92cd49_cd"),
            models.Index(fields=["created_at"], name="timeta_timeta_ef92cd49_cr"),
            models.Index(fields=["priority", "status"], name="timeta_timeta_ef92cd49_pr"),
            models.Index(fields=["department_tag", "status"], name="timeta_timeta_ef92cd49_dp"),
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

class TimetablesSlotsEvaluationMetricQuerySet(models.QuerySet):
    """Custom QuerySet methods for TimetablesSlotsEvaluationMetric."""
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

class TimetablesSlotsEvaluationMetricManager(models.Manager):
    """Custom model manager for TimetablesSlotsEvaluationMetric."""
    def get_queryset(self):
        return TimetablesSlotsEvaluationMetricQuerySet(self.model, using=self._db)
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

class TimetablesSlotsEvaluationMetric(models.Model):
    """
    TimetablesSlotsEvaluationMetric: Performance indicators, rubrics, and assessment scores.
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
    department_tag = models.CharField(max_length=64, blank=True, default="TIMETABLES", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@timetables.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = TimetablesSlotsEvaluationMetricManager()

    class Meta:
        db_table = "timetables_timetables_slots_evaluationmetric"
        ordering = ["-created_at", "code"]
        verbose_name = _("TimetablesSlotsEvaluationMetric")
        verbose_name_plural = _("TimetablesSlotsEvaluationMetrics")
        indexes = [
            models.Index(fields=["code", "status"], name="timeta_timeta_c7d43f72_cd"),
            models.Index(fields=["created_at"], name="timeta_timeta_c7d43f72_cr"),
            models.Index(fields=["priority", "status"], name="timeta_timeta_c7d43f72_pr"),
            models.Index(fields=["department_tag", "status"], name="timeta_timeta_c7d43f72_dp"),
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

class TimetablesSlotsRosterMappingQuerySet(models.QuerySet):
    """Custom QuerySet methods for TimetablesSlotsRosterMapping."""
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

class TimetablesSlotsRosterMappingManager(models.Manager):
    """Custom model manager for TimetablesSlotsRosterMapping."""
    def get_queryset(self):
        return TimetablesSlotsRosterMappingQuerySet(self.model, using=self._db)
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

class TimetablesSlotsRosterMapping(models.Model):
    """
    TimetablesSlotsRosterMapping: Relational participant roster links and enrollment associations.
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
    department_tag = models.CharField(max_length=64, blank=True, default="TIMETABLES", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@timetables.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = TimetablesSlotsRosterMappingManager()

    class Meta:
        db_table = "timetables_timetables_slots_rostermapping"
        ordering = ["-created_at", "code"]
        verbose_name = _("TimetablesSlotsRosterMapping")
        verbose_name_plural = _("TimetablesSlotsRosterMappings")
        indexes = [
            models.Index(fields=["code", "status"], name="timeta_timeta_6938ef35_cd"),
            models.Index(fields=["created_at"], name="timeta_timeta_6938ef35_cr"),
            models.Index(fields=["priority", "status"], name="timeta_timeta_6938ef35_pr"),
            models.Index(fields=["department_tag", "status"], name="timeta_timeta_6938ef35_dp"),
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

class TimetablesSlotsVerificationSignatureQuerySet(models.QuerySet):
    """Custom QuerySet methods for TimetablesSlotsVerificationSignature."""
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

class TimetablesSlotsVerificationSignatureManager(models.Manager):
    """Custom model manager for TimetablesSlotsVerificationSignature."""
    def get_queryset(self):
        return TimetablesSlotsVerificationSignatureQuerySet(self.model, using=self._db)
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

class TimetablesSlotsVerificationSignature(models.Model):
    """
    TimetablesSlotsVerificationSignature: Cryptographic verification and integrity tokens.
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
    department_tag = models.CharField(max_length=64, blank=True, default="TIMETABLES", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@timetables.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = TimetablesSlotsVerificationSignatureManager()

    class Meta:
        db_table = "timetables_timetables_slots_verificationsignature"
        ordering = ["-created_at", "code"]
        verbose_name = _("TimetablesSlotsVerificationSignature")
        verbose_name_plural = _("TimetablesSlotsVerificationSignatures")
        indexes = [
            models.Index(fields=["code", "status"], name="timeta_timeta_7c904a8e_cd"),
            models.Index(fields=["created_at"], name="timeta_timeta_7c904a8e_cr"),
            models.Index(fields=["priority", "status"], name="timeta_timeta_7c904a8e_pr"),
            models.Index(fields=["department_tag", "status"], name="timeta_timeta_7c904a8e_dp"),
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

class TimetablesSlotsNotificationRuleQuerySet(models.QuerySet):
    """Custom QuerySet methods for TimetablesSlotsNotificationRule."""
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

class TimetablesSlotsNotificationRuleManager(models.Manager):
    """Custom model manager for TimetablesSlotsNotificationRule."""
    def get_queryset(self):
        return TimetablesSlotsNotificationRuleQuerySet(self.model, using=self._db)
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

class TimetablesSlotsNotificationRule(models.Model):
    """
    TimetablesSlotsNotificationRule: Event-driven notification triggers and audience matrices.
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
    department_tag = models.CharField(max_length=64, blank=True, default="TIMETABLES", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@timetables.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = TimetablesSlotsNotificationRuleManager()

    class Meta:
        db_table = "timetables_timetables_slots_notificationrule"
        ordering = ["-created_at", "code"]
        verbose_name = _("TimetablesSlotsNotificationRule")
        verbose_name_plural = _("TimetablesSlotsNotificationRules")
        indexes = [
            models.Index(fields=["code", "status"], name="timeta_timeta_d5419e47_cd"),
            models.Index(fields=["created_at"], name="timeta_timeta_d5419e47_cr"),
            models.Index(fields=["priority", "status"], name="timeta_timeta_d5419e47_pr"),
            models.Index(fields=["department_tag", "status"], name="timeta_timeta_d5419e47_dp"),
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

class TimetablesSlotsAnalyticalSnapshotQuerySet(models.QuerySet):
    """Custom QuerySet methods for TimetablesSlotsAnalyticalSnapshot."""
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

class TimetablesSlotsAnalyticalSnapshotManager(models.Manager):
    """Custom model manager for TimetablesSlotsAnalyticalSnapshot."""
    def get_queryset(self):
        return TimetablesSlotsAnalyticalSnapshotQuerySet(self.model, using=self._db)
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

class TimetablesSlotsAnalyticalSnapshot(models.Model):
    """
    TimetablesSlotsAnalyticalSnapshot: Aggregated telemetry snapshot capturing historical trend data.
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
    department_tag = models.CharField(max_length=64, blank=True, default="TIMETABLES", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@timetables.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = TimetablesSlotsAnalyticalSnapshotManager()

    class Meta:
        db_table = "timetables_timetables_slots_analyticalsnapshot"
        ordering = ["-created_at", "code"]
        verbose_name = _("TimetablesSlotsAnalyticalSnapshot")
        verbose_name_plural = _("TimetablesSlotsAnalyticalSnapshots")
        indexes = [
            models.Index(fields=["code", "status"], name="timeta_timeta_18c9383d_cd"),
            models.Index(fields=["created_at"], name="timeta_timeta_18c9383d_cr"),
            models.Index(fields=["priority", "status"], name="timeta_timeta_18c9383d_pr"),
            models.Index(fields=["department_tag", "status"], name="timeta_timeta_18c9383d_dp"),
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

class TimetablesSlotsComplianceLogQuerySet(models.QuerySet):
    """Custom QuerySet methods for TimetablesSlotsComplianceLog."""
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

class TimetablesSlotsComplianceLogManager(models.Manager):
    """Custom model manager for TimetablesSlotsComplianceLog."""
    def get_queryset(self):
        return TimetablesSlotsComplianceLogQuerySet(self.model, using=self._db)
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

class TimetablesSlotsComplianceLog(models.Model):
    """
    TimetablesSlotsComplianceLog: Regulatory compliance inspections and institutional certifications.
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
    department_tag = models.CharField(max_length=64, blank=True, default="TIMETABLES", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@timetables.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = TimetablesSlotsComplianceLogManager()

    class Meta:
        db_table = "timetables_timetables_slots_compliancelog"
        ordering = ["-created_at", "code"]
        verbose_name = _("TimetablesSlotsComplianceLog")
        verbose_name_plural = _("TimetablesSlotsComplianceLogs")
        indexes = [
            models.Index(fields=["code", "status"], name="timeta_timeta_2c6220c2_cd"),
            models.Index(fields=["created_at"], name="timeta_timeta_2c6220c2_cr"),
            models.Index(fields=["priority", "status"], name="timeta_timeta_2c6220c2_pr"),
            models.Index(fields=["department_tag", "status"], name="timeta_timeta_2c6220c2_dp"),
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

class TimetablesSlotsIntegrationBridgeQuerySet(models.QuerySet):
    """Custom QuerySet methods for TimetablesSlotsIntegrationBridge."""
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

class TimetablesSlotsIntegrationBridgeManager(models.Manager):
    """Custom model manager for TimetablesSlotsIntegrationBridge."""
    def get_queryset(self):
        return TimetablesSlotsIntegrationBridgeQuerySet(self.model, using=self._db)
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

class TimetablesSlotsIntegrationBridge(models.Model):
    """
    TimetablesSlotsIntegrationBridge: External system integration endpoints and payload exchange records.
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
    department_tag = models.CharField(max_length=64, blank=True, default="TIMETABLES", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@timetables.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = TimetablesSlotsIntegrationBridgeManager()

    class Meta:
        db_table = "timetables_timetables_slots_integrationbridge"
        ordering = ["-created_at", "code"]
        verbose_name = _("TimetablesSlotsIntegrationBridge")
        verbose_name_plural = _("TimetablesSlotsIntegrationBridges")
        indexes = [
            models.Index(fields=["code", "status"], name="timeta_timeta_b0d09af4_cd"),
            models.Index(fields=["created_at"], name="timeta_timeta_b0d09af4_cr"),
            models.Index(fields=["priority", "status"], name="timeta_timeta_b0d09af4_pr"),
            models.Index(fields=["department_tag", "status"], name="timeta_timeta_b0d09af4_dp"),
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

class TimetablesSlotsSecurityPermitQuerySet(models.QuerySet):
    """Custom QuerySet methods for TimetablesSlotsSecurityPermit."""
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

class TimetablesSlotsSecurityPermitManager(models.Manager):
    """Custom model manager for TimetablesSlotsSecurityPermit."""
    def get_queryset(self):
        return TimetablesSlotsSecurityPermitQuerySet(self.model, using=self._db)
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

class TimetablesSlotsSecurityPermit(models.Model):
    """
    TimetablesSlotsSecurityPermit: Granular authorization token defining scoped operational access.
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
    department_tag = models.CharField(max_length=64, blank=True, default="TIMETABLES", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@timetables.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = TimetablesSlotsSecurityPermitManager()

    class Meta:
        db_table = "timetables_timetables_slots_securitypermit"
        ordering = ["-created_at", "code"]
        verbose_name = _("TimetablesSlotsSecurityPermit")
        verbose_name_plural = _("TimetablesSlotsSecurityPermits")
        indexes = [
            models.Index(fields=["code", "status"], name="timeta_timeta_70ce6f3d_cd"),
            models.Index(fields=["created_at"], name="timeta_timeta_70ce6f3d_cr"),
            models.Index(fields=["priority", "status"], name="timeta_timeta_70ce6f3d_pr"),
            models.Index(fields=["department_tag", "status"], name="timeta_timeta_70ce6f3d_dp"),
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

class TimetablesSlotsDocumentAttachmentQuerySet(models.QuerySet):
    """Custom QuerySet methods for TimetablesSlotsDocumentAttachment."""
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

class TimetablesSlotsDocumentAttachmentManager(models.Manager):
    """Custom model manager for TimetablesSlotsDocumentAttachment."""
    def get_queryset(self):
        return TimetablesSlotsDocumentAttachmentQuerySet(self.model, using=self._db)
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

class TimetablesSlotsDocumentAttachment(models.Model):
    """
    TimetablesSlotsDocumentAttachment: Official digital file attachment container with cryptographic checksums.
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
    department_tag = models.CharField(max_length=64, blank=True, default="TIMETABLES", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@timetables.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = TimetablesSlotsDocumentAttachmentManager()

    class Meta:
        db_table = "timetables_timetables_slots_documentattachment"
        ordering = ["-created_at", "code"]
        verbose_name = _("TimetablesSlotsDocumentAttachment")
        verbose_name_plural = _("TimetablesSlotsDocumentAttachments")
        indexes = [
            models.Index(fields=["code", "status"], name="timeta_timeta_e5404f64_cd"),
            models.Index(fields=["created_at"], name="timeta_timeta_e5404f64_cr"),
            models.Index(fields=["priority", "status"], name="timeta_timeta_e5404f64_pr"),
            models.Index(fields=["department_tag", "status"], name="timeta_timeta_e5404f64_dp"),
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

class TimetablesSlotsLifecycleTransitionQuerySet(models.QuerySet):
    """Custom QuerySet methods for TimetablesSlotsLifecycleTransition."""
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

class TimetablesSlotsLifecycleTransitionManager(models.Manager):
    """Custom model manager for TimetablesSlotsLifecycleTransition."""
    def get_queryset(self):
        return TimetablesSlotsLifecycleTransitionQuerySet(self.model, using=self._db)
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

class TimetablesSlotsLifecycleTransition(models.Model):
    """
    TimetablesSlotsLifecycleTransition: State transition checkpoint recording approval gates and authorizations.
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
    department_tag = models.CharField(max_length=64, blank=True, default="TIMETABLES", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@timetables.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = TimetablesSlotsLifecycleTransitionManager()

    class Meta:
        db_table = "timetables_timetables_slots_lifecycletransition"
        ordering = ["-created_at", "code"]
        verbose_name = _("TimetablesSlotsLifecycleTransition")
        verbose_name_plural = _("TimetablesSlotsLifecycleTransitions")
        indexes = [
            models.Index(fields=["code", "status"], name="timeta_timeta_fc93a126_cd"),
            models.Index(fields=["created_at"], name="timeta_timeta_fc93a126_cr"),
            models.Index(fields=["priority", "status"], name="timeta_timeta_fc93a126_pr"),
            models.Index(fields=["department_tag", "status"], name="timeta_timeta_fc93a126_dp"),
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

class TimetablesSlotsDataArchivalRegistryQuerySet(models.QuerySet):
    """Custom QuerySet methods for TimetablesSlotsDataArchivalRegistry."""
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

class TimetablesSlotsDataArchivalRegistryManager(models.Manager):
    """Custom model manager for TimetablesSlotsDataArchivalRegistry."""
    def get_queryset(self):
        return TimetablesSlotsDataArchivalRegistryQuerySet(self.model, using=self._db)
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

class TimetablesSlotsDataArchivalRegistry(models.Model):
    """
    TimetablesSlotsDataArchivalRegistry: Record archival state, cold storage pointers, and legal hold flags.
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
    department_tag = models.CharField(max_length=64, blank=True, default="TIMETABLES", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@timetables.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = TimetablesSlotsDataArchivalRegistryManager()

    class Meta:
        db_table = "timetables_timetables_slots_dataarchivalregistry"
        ordering = ["-created_at", "code"]
        verbose_name = _("TimetablesSlotsDataArchivalRegistry")
        verbose_name_plural = _("TimetablesSlotsDataArchivalRegistrys")
        indexes = [
            models.Index(fields=["code", "status"], name="timeta_timeta_eedb4f6e_cd"),
            models.Index(fields=["created_at"], name="timeta_timeta_eedb4f6e_cr"),
            models.Index(fields=["priority", "status"], name="timeta_timeta_eedb4f6e_pr"),
            models.Index(fields=["department_tag", "status"], name="timeta_timeta_eedb4f6e_dp"),
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

class TimetablesSlotsTelemetryEventStreamQuerySet(models.QuerySet):
    """Custom QuerySet methods for TimetablesSlotsTelemetryEventStream."""
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

class TimetablesSlotsTelemetryEventStreamManager(models.Manager):
    """Custom model manager for TimetablesSlotsTelemetryEventStream."""
    def get_queryset(self):
        return TimetablesSlotsTelemetryEventStreamQuerySet(self.model, using=self._db)
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

class TimetablesSlotsTelemetryEventStream(models.Model):
    """
    TimetablesSlotsTelemetryEventStream: Real-time telemetry events and activity streams.
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
    department_tag = models.CharField(max_length=64, blank=True, default="TIMETABLES", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@timetables.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = TimetablesSlotsTelemetryEventStreamManager()

    class Meta:
        db_table = "timetables_timetables_slots_telemetryeventstream"
        ordering = ["-created_at", "code"]
        verbose_name = _("TimetablesSlotsTelemetryEventStream")
        verbose_name_plural = _("TimetablesSlotsTelemetryEventStreams")
        indexes = [
            models.Index(fields=["code", "status"], name="timeta_timeta_c4688e16_cd"),
            models.Index(fields=["created_at"], name="timeta_timeta_c4688e16_cr"),
            models.Index(fields=["priority", "status"], name="timeta_timeta_c4688e16_pr"),
            models.Index(fields=["department_tag", "status"], name="timeta_timeta_c4688e16_dp"),
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

class TimetablesSlotsAccessGrantMatrixQuerySet(models.QuerySet):
    """Custom QuerySet methods for TimetablesSlotsAccessGrantMatrix."""
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

class TimetablesSlotsAccessGrantMatrixManager(models.Manager):
    """Custom model manager for TimetablesSlotsAccessGrantMatrix."""
    def get_queryset(self):
        return TimetablesSlotsAccessGrantMatrixQuerySet(self.model, using=self._db)
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

class TimetablesSlotsAccessGrantMatrix(models.Model):
    """
    TimetablesSlotsAccessGrantMatrix: Granular privilege assignments and operational scope bindings.
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
    department_tag = models.CharField(max_length=64, blank=True, default="TIMETABLES", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@timetables.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = TimetablesSlotsAccessGrantMatrixManager()

    class Meta:
        db_table = "timetables_timetables_slots_accessgrantmatrix"
        ordering = ["-created_at", "code"]
        verbose_name = _("TimetablesSlotsAccessGrantMatrix")
        verbose_name_plural = _("TimetablesSlotsAccessGrantMatrixs")
        indexes = [
            models.Index(fields=["code", "status"], name="timeta_timeta_9cdd954d_cd"),
            models.Index(fields=["created_at"], name="timeta_timeta_9cdd954d_cr"),
            models.Index(fields=["priority", "status"], name="timeta_timeta_9cdd954d_pr"),
            models.Index(fields=["department_tag", "status"], name="timeta_timeta_9cdd954d_dp"),
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

class TimetablesSlotsOperationalQuotaQuerySet(models.QuerySet):
    """Custom QuerySet methods for TimetablesSlotsOperationalQuota."""
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

class TimetablesSlotsOperationalQuotaManager(models.Manager):
    """Custom model manager for TimetablesSlotsOperationalQuota."""
    def get_queryset(self):
        return TimetablesSlotsOperationalQuotaQuerySet(self.model, using=self._db)
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

class TimetablesSlotsOperationalQuota(models.Model):
    """
    TimetablesSlotsOperationalQuota: Resource quotas, bandwidth/usage limits, and consumption tracking.
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
    department_tag = models.CharField(max_length=64, blank=True, default="TIMETABLES", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@timetables.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = TimetablesSlotsOperationalQuotaManager()

    class Meta:
        db_table = "timetables_timetables_slots_operationalquota"
        ordering = ["-created_at", "code"]
        verbose_name = _("TimetablesSlotsOperationalQuota")
        verbose_name_plural = _("TimetablesSlotsOperationalQuotas")
        indexes = [
            models.Index(fields=["code", "status"], name="timeta_timeta_18752ce1_cd"),
            models.Index(fields=["created_at"], name="timeta_timeta_18752ce1_cr"),
            models.Index(fields=["priority", "status"], name="timeta_timeta_18752ce1_pr"),
            models.Index(fields=["department_tag", "status"], name="timeta_timeta_18752ce1_dp"),
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

class TimetablesSlotsWorkflowAuditCheckpointQuerySet(models.QuerySet):
    """Custom QuerySet methods for TimetablesSlotsWorkflowAuditCheckpoint."""
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

class TimetablesSlotsWorkflowAuditCheckpointManager(models.Manager):
    """Custom model manager for TimetablesSlotsWorkflowAuditCheckpoint."""
    def get_queryset(self):
        return TimetablesSlotsWorkflowAuditCheckpointQuerySet(self.model, using=self._db)
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

class TimetablesSlotsWorkflowAuditCheckpoint(models.Model):
    """
    TimetablesSlotsWorkflowAuditCheckpoint: Stage-gate checkpoints and sign-off validations.
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
    department_tag = models.CharField(max_length=64, blank=True, default="TIMETABLES", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@timetables.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = TimetablesSlotsWorkflowAuditCheckpointManager()

    class Meta:
        db_table = "timetables_timetables_slots_workflowauditcheckpoint"
        ordering = ["-created_at", "code"]
        verbose_name = _("TimetablesSlotsWorkflowAuditCheckpoint")
        verbose_name_plural = _("TimetablesSlotsWorkflowAuditCheckpoints")
        indexes = [
            models.Index(fields=["code", "status"], name="timeta_timeta_4ebae1d3_cd"),
            models.Index(fields=["created_at"], name="timeta_timeta_4ebae1d3_cr"),
            models.Index(fields=["priority", "status"], name="timeta_timeta_4ebae1d3_pr"),
            models.Index(fields=["department_tag", "status"], name="timeta_timeta_4ebae1d3_dp"),
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

class TimetablesSlotsDisasterRecoveryCheckpointQuerySet(models.QuerySet):
    """Custom QuerySet methods for TimetablesSlotsDisasterRecoveryCheckpoint."""
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

class TimetablesSlotsDisasterRecoveryCheckpointManager(models.Manager):
    """Custom model manager for TimetablesSlotsDisasterRecoveryCheckpoint."""
    def get_queryset(self):
        return TimetablesSlotsDisasterRecoveryCheckpointQuerySet(self.model, using=self._db)
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

class TimetablesSlotsDisasterRecoveryCheckpoint(models.Model):
    """
    TimetablesSlotsDisasterRecoveryCheckpoint: Point-in-time state checkpoint for high-availability disaster recovery validation.
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
    department_tag = models.CharField(max_length=64, blank=True, default="TIMETABLES", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@timetables.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = TimetablesSlotsDisasterRecoveryCheckpointManager()

    class Meta:
        db_table = "timetables_timetables_slots_disasterrecoverycheckpoint"
        ordering = ["-created_at", "code"]
        verbose_name = _("TimetablesSlotsDisasterRecoveryCheckpoint")
        verbose_name_plural = _("TimetablesSlotsDisasterRecoveryCheckpoints")
        indexes = [
            models.Index(fields=["code", "status"], name="timeta_timeta_2568d95d_cd"),
            models.Index(fields=["created_at"], name="timeta_timeta_2568d95d_cr"),
            models.Index(fields=["priority", "status"], name="timeta_timeta_2568d95d_pr"),
            models.Index(fields=["department_tag", "status"], name="timeta_timeta_2568d95d_dp"),
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

class TimetablesSlotsSLAComplianceRegisterQuerySet(models.QuerySet):
    """Custom QuerySet methods for TimetablesSlotsSLAComplianceRegister."""
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

class TimetablesSlotsSLAComplianceRegisterManager(models.Manager):
    """Custom model manager for TimetablesSlotsSLAComplianceRegister."""
    def get_queryset(self):
        return TimetablesSlotsSLAComplianceRegisterQuerySet(self.model, using=self._db)
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

class TimetablesSlotsSLAComplianceRegister(models.Model):
    """
    TimetablesSlotsSLAComplianceRegister: Service level agreement compliance tracker for operational responsiveness.
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
    department_tag = models.CharField(max_length=64, blank=True, default="TIMETABLES", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@timetables.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = TimetablesSlotsSLAComplianceRegisterManager()

    class Meta:
        db_table = "timetables_timetables_slots_slacomplianceregister"
        ordering = ["-created_at", "code"]
        verbose_name = _("TimetablesSlotsSLAComplianceRegister")
        verbose_name_plural = _("TimetablesSlotsSLAComplianceRegisters")
        indexes = [
            models.Index(fields=["code", "status"], name="timeta_timeta_14161d82_cd"),
            models.Index(fields=["created_at"], name="timeta_timeta_14161d82_cr"),
            models.Index(fields=["priority", "status"], name="timeta_timeta_14161d82_pr"),
            models.Index(fields=["department_tag", "status"], name="timeta_timeta_14161d82_dp"),
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

class TimetablesSlotsIncidentReportRegisterQuerySet(models.QuerySet):
    """Custom QuerySet methods for TimetablesSlotsIncidentReportRegister."""
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

class TimetablesSlotsIncidentReportRegisterManager(models.Manager):
    """Custom model manager for TimetablesSlotsIncidentReportRegister."""
    def get_queryset(self):
        return TimetablesSlotsIncidentReportRegisterQuerySet(self.model, using=self._db)
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

class TimetablesSlotsIncidentReportRegister(models.Model):
    """
    TimetablesSlotsIncidentReportRegister: Incident ticketing and remediation tracking register.
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
    department_tag = models.CharField(max_length=64, blank=True, default="TIMETABLES", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@timetables.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = TimetablesSlotsIncidentReportRegisterManager()

    class Meta:
        db_table = "timetables_timetables_slots_incidentreportregister"
        ordering = ["-created_at", "code"]
        verbose_name = _("TimetablesSlotsIncidentReportRegister")
        verbose_name_plural = _("TimetablesSlotsIncidentReportRegisters")
        indexes = [
            models.Index(fields=["code", "status"], name="timeta_timeta_58158548_cd"),
            models.Index(fields=["created_at"], name="timeta_timeta_58158548_cr"),
            models.Index(fields=["priority", "status"], name="timeta_timeta_58158548_pr"),
            models.Index(fields=["department_tag", "status"], name="timeta_timeta_58158548_dp"),
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

class TimetablesSlotsBusinessContinuityPlanQuerySet(models.QuerySet):
    """Custom QuerySet methods for TimetablesSlotsBusinessContinuityPlan."""
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

class TimetablesSlotsBusinessContinuityPlanManager(models.Manager):
    """Custom model manager for TimetablesSlotsBusinessContinuityPlan."""
    def get_queryset(self):
        return TimetablesSlotsBusinessContinuityPlanQuerySet(self.model, using=self._db)
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

class TimetablesSlotsBusinessContinuityPlan(models.Model):
    """
    TimetablesSlotsBusinessContinuityPlan: Business continuity procedures and failover plan coordinates.
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
    department_tag = models.CharField(max_length=64, blank=True, default="TIMETABLES", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@timetables.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = TimetablesSlotsBusinessContinuityPlanManager()

    class Meta:
        db_table = "timetables_timetables_slots_businesscontinuityplan"
        ordering = ["-created_at", "code"]
        verbose_name = _("TimetablesSlotsBusinessContinuityPlan")
        verbose_name_plural = _("TimetablesSlotsBusinessContinuityPlans")
        indexes = [
            models.Index(fields=["code", "status"], name="timeta_timeta_bd88949a_cd"),
            models.Index(fields=["created_at"], name="timeta_timeta_bd88949a_cr"),
            models.Index(fields=["priority", "status"], name="timeta_timeta_bd88949a_pr"),
            models.Index(fields=["department_tag", "status"], name="timeta_timeta_bd88949a_dp"),
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

class TimetablesSlotsGovernanceAttestationRecordQuerySet(models.QuerySet):
    """Custom QuerySet methods for TimetablesSlotsGovernanceAttestationRecord."""
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

class TimetablesSlotsGovernanceAttestationRecordManager(models.Manager):
    """Custom model manager for TimetablesSlotsGovernanceAttestationRecord."""
    def get_queryset(self):
        return TimetablesSlotsGovernanceAttestationRecordQuerySet(self.model, using=self._db)
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

class TimetablesSlotsGovernanceAttestationRecord(models.Model):
    """
    TimetablesSlotsGovernanceAttestationRecord: Formal institutional governance attestations and sign-offs.
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
    department_tag = models.CharField(max_length=64, blank=True, default="TIMETABLES", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@timetables.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = TimetablesSlotsGovernanceAttestationRecordManager()

    class Meta:
        db_table = "timetables_timetables_slots_governanceattestationrecord"
        ordering = ["-created_at", "code"]
        verbose_name = _("TimetablesSlotsGovernanceAttestationRecord")
        verbose_name_plural = _("TimetablesSlotsGovernanceAttestationRecords")
        indexes = [
            models.Index(fields=["code", "status"], name="timeta_timeta_1e19e4e2_cd"),
            models.Index(fields=["created_at"], name="timeta_timeta_1e19e4e2_cr"),
            models.Index(fields=["priority", "status"], name="timeta_timeta_1e19e4e2_pr"),
            models.Index(fields=["department_tag", "status"], name="timeta_timeta_1e19e4e2_dp"),
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
