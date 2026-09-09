"""
Enterprise Domain Models for Fees: Payment Processing
PR #62: Relational Schema, Field Constraints, Custom Managers & State Tracking.
"""

from decimal import Decimal
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from core.constants import AcademicStatus, Gender, BloodGroup, DegreeLevel, AttendanceStatus
from core.validators import validate_phone_number, validate_national_id, validate_gpa_range

class FeesPaymentsMasterQuerySet(models.QuerySet):
    """Custom QuerySet methods for FeesPaymentsMaster."""
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

class FeesPaymentsMasterManager(models.Manager):
    """Custom model manager for FeesPaymentsMaster."""
    def get_queryset(self):
        return FeesPaymentsMasterQuerySet(self.model, using=self._db)
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

class FeesPaymentsMaster(models.Model):
    """
    FeesPaymentsMaster: Primary domain master record representing the central institutional entity.
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
    department_tag = models.CharField(max_length=64, blank=True, default="FEES", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@fees.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = FeesPaymentsMasterManager()

    class Meta:
        db_table = "fees_fees_payments_master"
        ordering = ["-created_at", "code"]
        verbose_name = _("FeesPaymentsMaster")
        verbose_name_plural = _("FeesPaymentsMasters")
        indexes = [
            models.Index(fields=["code", "status"], name="fees_fees_p_92ea7a92_cd"),
            models.Index(fields=["created_at"], name="fees_fees_p_92ea7a92_cr"),
            models.Index(fields=["priority", "status"], name="fees_fees_p_92ea7a92_pr"),
            models.Index(fields=["department_tag", "status"], name="fees_fees_p_92ea7a92_dp"),
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

class FeesPaymentsConfigurationQuerySet(models.QuerySet):
    """Custom QuerySet methods for FeesPaymentsConfiguration."""
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

class FeesPaymentsConfigurationManager(models.Manager):
    """Custom model manager for FeesPaymentsConfiguration."""
    def get_queryset(self):
        return FeesPaymentsConfigurationQuerySet(self.model, using=self._db)
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

class FeesPaymentsConfiguration(models.Model):
    """
    FeesPaymentsConfiguration: Operational configuration, policy rules, and system limits.
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
    department_tag = models.CharField(max_length=64, blank=True, default="FEES", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@fees.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = FeesPaymentsConfigurationManager()

    class Meta:
        db_table = "fees_fees_payments_configuration"
        ordering = ["-created_at", "code"]
        verbose_name = _("FeesPaymentsConfiguration")
        verbose_name_plural = _("FeesPaymentsConfigurations")
        indexes = [
            models.Index(fields=["code", "status"], name="fees_fees_p_0d50be69_cd"),
            models.Index(fields=["created_at"], name="fees_fees_p_0d50be69_cr"),
            models.Index(fields=["priority", "status"], name="fees_fees_p_0d50be69_pr"),
            models.Index(fields=["department_tag", "status"], name="fees_fees_p_0d50be69_dp"),
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

class FeesPaymentsLedgerQuerySet(models.QuerySet):
    """Custom QuerySet methods for FeesPaymentsLedger."""
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

class FeesPaymentsLedgerManager(models.Manager):
    """Custom model manager for FeesPaymentsLedger."""
    def get_queryset(self):
        return FeesPaymentsLedgerQuerySet(self.model, using=self._db)
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

class FeesPaymentsLedger(models.Model):
    """
    FeesPaymentsLedger: Financial and quantitative accounting ledger tracking balance changes.
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
    department_tag = models.CharField(max_length=64, blank=True, default="FEES", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@fees.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = FeesPaymentsLedgerManager()

    class Meta:
        db_table = "fees_fees_payments_ledger"
        ordering = ["-created_at", "code"]
        verbose_name = _("FeesPaymentsLedger")
        verbose_name_plural = _("FeesPaymentsLedgers")
        indexes = [
            models.Index(fields=["code", "status"], name="fees_fees_p_737cb416_cd"),
            models.Index(fields=["created_at"], name="fees_fees_p_737cb416_cr"),
            models.Index(fields=["priority", "status"], name="fees_fees_p_737cb416_pr"),
            models.Index(fields=["department_tag", "status"], name="fees_fees_p_737cb416_dp"),
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

class FeesPaymentsAuditTransactionQuerySet(models.QuerySet):
    """Custom QuerySet methods for FeesPaymentsAuditTransaction."""
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

class FeesPaymentsAuditTransactionManager(models.Manager):
    """Custom model manager for FeesPaymentsAuditTransaction."""
    def get_queryset(self):
        return FeesPaymentsAuditTransactionQuerySet(self.model, using=self._db)
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

class FeesPaymentsAuditTransaction(models.Model):
    """
    FeesPaymentsAuditTransaction: Immutable audit log transaction record capturing user mutations and states.
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
    department_tag = models.CharField(max_length=64, blank=True, default="FEES", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@fees.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = FeesPaymentsAuditTransactionManager()

    class Meta:
        db_table = "fees_fees_payments_audittransaction"
        ordering = ["-created_at", "code"]
        verbose_name = _("FeesPaymentsAuditTransaction")
        verbose_name_plural = _("FeesPaymentsAuditTransactions")
        indexes = [
            models.Index(fields=["code", "status"], name="fees_fees_p_6cea8774_cd"),
            models.Index(fields=["created_at"], name="fees_fees_p_6cea8774_cr"),
            models.Index(fields=["priority", "status"], name="fees_fees_p_6cea8774_pr"),
            models.Index(fields=["department_tag", "status"], name="fees_fees_p_6cea8774_dp"),
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

class FeesPaymentsScheduleMatrixQuerySet(models.QuerySet):
    """Custom QuerySet methods for FeesPaymentsScheduleMatrix."""
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

class FeesPaymentsScheduleMatrixManager(models.Manager):
    """Custom model manager for FeesPaymentsScheduleMatrix."""
    def get_queryset(self):
        return FeesPaymentsScheduleMatrixQuerySet(self.model, using=self._db)
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

class FeesPaymentsScheduleMatrix(models.Model):
    """
    FeesPaymentsScheduleMatrix: Temporal planning and operational schedule coordinates.
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
    department_tag = models.CharField(max_length=64, blank=True, default="FEES", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@fees.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = FeesPaymentsScheduleMatrixManager()

    class Meta:
        db_table = "fees_fees_payments_schedulematrix"
        ordering = ["-created_at", "code"]
        verbose_name = _("FeesPaymentsScheduleMatrix")
        verbose_name_plural = _("FeesPaymentsScheduleMatrixs")
        indexes = [
            models.Index(fields=["code", "status"], name="fees_fees_p_ffcf68ce_cd"),
            models.Index(fields=["created_at"], name="fees_fees_p_ffcf68ce_cr"),
            models.Index(fields=["priority", "status"], name="fees_fees_p_ffcf68ce_pr"),
            models.Index(fields=["department_tag", "status"], name="fees_fees_p_ffcf68ce_dp"),
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

class FeesPaymentsEvaluationMetricQuerySet(models.QuerySet):
    """Custom QuerySet methods for FeesPaymentsEvaluationMetric."""
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

class FeesPaymentsEvaluationMetricManager(models.Manager):
    """Custom model manager for FeesPaymentsEvaluationMetric."""
    def get_queryset(self):
        return FeesPaymentsEvaluationMetricQuerySet(self.model, using=self._db)
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

class FeesPaymentsEvaluationMetric(models.Model):
    """
    FeesPaymentsEvaluationMetric: Performance indicators, rubrics, and assessment scores.
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
    department_tag = models.CharField(max_length=64, blank=True, default="FEES", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@fees.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = FeesPaymentsEvaluationMetricManager()

    class Meta:
        db_table = "fees_fees_payments_evaluationmetric"
        ordering = ["-created_at", "code"]
        verbose_name = _("FeesPaymentsEvaluationMetric")
        verbose_name_plural = _("FeesPaymentsEvaluationMetrics")
        indexes = [
            models.Index(fields=["code", "status"], name="fees_fees_p_7d299c70_cd"),
            models.Index(fields=["created_at"], name="fees_fees_p_7d299c70_cr"),
            models.Index(fields=["priority", "status"], name="fees_fees_p_7d299c70_pr"),
            models.Index(fields=["department_tag", "status"], name="fees_fees_p_7d299c70_dp"),
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

class FeesPaymentsRosterMappingQuerySet(models.QuerySet):
    """Custom QuerySet methods for FeesPaymentsRosterMapping."""
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

class FeesPaymentsRosterMappingManager(models.Manager):
    """Custom model manager for FeesPaymentsRosterMapping."""
    def get_queryset(self):
        return FeesPaymentsRosterMappingQuerySet(self.model, using=self._db)
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

class FeesPaymentsRosterMapping(models.Model):
    """
    FeesPaymentsRosterMapping: Relational participant roster links and enrollment associations.
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
    department_tag = models.CharField(max_length=64, blank=True, default="FEES", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@fees.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = FeesPaymentsRosterMappingManager()

    class Meta:
        db_table = "fees_fees_payments_rostermapping"
        ordering = ["-created_at", "code"]
        verbose_name = _("FeesPaymentsRosterMapping")
        verbose_name_plural = _("FeesPaymentsRosterMappings")
        indexes = [
            models.Index(fields=["code", "status"], name="fees_fees_p_03b200c2_cd"),
            models.Index(fields=["created_at"], name="fees_fees_p_03b200c2_cr"),
            models.Index(fields=["priority", "status"], name="fees_fees_p_03b200c2_pr"),
            models.Index(fields=["department_tag", "status"], name="fees_fees_p_03b200c2_dp"),
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

class FeesPaymentsVerificationSignatureQuerySet(models.QuerySet):
    """Custom QuerySet methods for FeesPaymentsVerificationSignature."""
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

class FeesPaymentsVerificationSignatureManager(models.Manager):
    """Custom model manager for FeesPaymentsVerificationSignature."""
    def get_queryset(self):
        return FeesPaymentsVerificationSignatureQuerySet(self.model, using=self._db)
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

class FeesPaymentsVerificationSignature(models.Model):
    """
    FeesPaymentsVerificationSignature: Cryptographic verification and integrity tokens.
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
    department_tag = models.CharField(max_length=64, blank=True, default="FEES", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@fees.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = FeesPaymentsVerificationSignatureManager()

    class Meta:
        db_table = "fees_fees_payments_verificationsignature"
        ordering = ["-created_at", "code"]
        verbose_name = _("FeesPaymentsVerificationSignature")
        verbose_name_plural = _("FeesPaymentsVerificationSignatures")
        indexes = [
            models.Index(fields=["code", "status"], name="fees_fees_p_6c7b2c14_cd"),
            models.Index(fields=["created_at"], name="fees_fees_p_6c7b2c14_cr"),
            models.Index(fields=["priority", "status"], name="fees_fees_p_6c7b2c14_pr"),
            models.Index(fields=["department_tag", "status"], name="fees_fees_p_6c7b2c14_dp"),
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

class FeesPaymentsNotificationRuleQuerySet(models.QuerySet):
    """Custom QuerySet methods for FeesPaymentsNotificationRule."""
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

class FeesPaymentsNotificationRuleManager(models.Manager):
    """Custom model manager for FeesPaymentsNotificationRule."""
    def get_queryset(self):
        return FeesPaymentsNotificationRuleQuerySet(self.model, using=self._db)
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

class FeesPaymentsNotificationRule(models.Model):
    """
    FeesPaymentsNotificationRule: Event-driven notification triggers and audience matrices.
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
    department_tag = models.CharField(max_length=64, blank=True, default="FEES", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@fees.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = FeesPaymentsNotificationRuleManager()

    class Meta:
        db_table = "fees_fees_payments_notificationrule"
        ordering = ["-created_at", "code"]
        verbose_name = _("FeesPaymentsNotificationRule")
        verbose_name_plural = _("FeesPaymentsNotificationRules")
        indexes = [
            models.Index(fields=["code", "status"], name="fees_fees_p_5a00d19d_cd"),
            models.Index(fields=["created_at"], name="fees_fees_p_5a00d19d_cr"),
            models.Index(fields=["priority", "status"], name="fees_fees_p_5a00d19d_pr"),
            models.Index(fields=["department_tag", "status"], name="fees_fees_p_5a00d19d_dp"),
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

class FeesPaymentsAnalyticalSnapshotQuerySet(models.QuerySet):
    """Custom QuerySet methods for FeesPaymentsAnalyticalSnapshot."""
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

class FeesPaymentsAnalyticalSnapshotManager(models.Manager):
    """Custom model manager for FeesPaymentsAnalyticalSnapshot."""
    def get_queryset(self):
        return FeesPaymentsAnalyticalSnapshotQuerySet(self.model, using=self._db)
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

class FeesPaymentsAnalyticalSnapshot(models.Model):
    """
    FeesPaymentsAnalyticalSnapshot: Aggregated telemetry snapshot capturing historical trend data.
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
    department_tag = models.CharField(max_length=64, blank=True, default="FEES", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@fees.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = FeesPaymentsAnalyticalSnapshotManager()

    class Meta:
        db_table = "fees_fees_payments_analyticalsnapshot"
        ordering = ["-created_at", "code"]
        verbose_name = _("FeesPaymentsAnalyticalSnapshot")
        verbose_name_plural = _("FeesPaymentsAnalyticalSnapshots")
        indexes = [
            models.Index(fields=["code", "status"], name="fees_fees_p_282d1d7b_cd"),
            models.Index(fields=["created_at"], name="fees_fees_p_282d1d7b_cr"),
            models.Index(fields=["priority", "status"], name="fees_fees_p_282d1d7b_pr"),
            models.Index(fields=["department_tag", "status"], name="fees_fees_p_282d1d7b_dp"),
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

class FeesPaymentsComplianceLogQuerySet(models.QuerySet):
    """Custom QuerySet methods for FeesPaymentsComplianceLog."""
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

class FeesPaymentsComplianceLogManager(models.Manager):
    """Custom model manager for FeesPaymentsComplianceLog."""
    def get_queryset(self):
        return FeesPaymentsComplianceLogQuerySet(self.model, using=self._db)
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

class FeesPaymentsComplianceLog(models.Model):
    """
    FeesPaymentsComplianceLog: Regulatory compliance inspections and institutional certifications.
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
    department_tag = models.CharField(max_length=64, blank=True, default="FEES", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@fees.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = FeesPaymentsComplianceLogManager()

    class Meta:
        db_table = "fees_fees_payments_compliancelog"
        ordering = ["-created_at", "code"]
        verbose_name = _("FeesPaymentsComplianceLog")
        verbose_name_plural = _("FeesPaymentsComplianceLogs")
        indexes = [
            models.Index(fields=["code", "status"], name="fees_fees_p_20d0e662_cd"),
            models.Index(fields=["created_at"], name="fees_fees_p_20d0e662_cr"),
            models.Index(fields=["priority", "status"], name="fees_fees_p_20d0e662_pr"),
            models.Index(fields=["department_tag", "status"], name="fees_fees_p_20d0e662_dp"),
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

class FeesPaymentsIntegrationBridgeQuerySet(models.QuerySet):
    """Custom QuerySet methods for FeesPaymentsIntegrationBridge."""
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

class FeesPaymentsIntegrationBridgeManager(models.Manager):
    """Custom model manager for FeesPaymentsIntegrationBridge."""
    def get_queryset(self):
        return FeesPaymentsIntegrationBridgeQuerySet(self.model, using=self._db)
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

class FeesPaymentsIntegrationBridge(models.Model):
    """
    FeesPaymentsIntegrationBridge: External system integration endpoints and payload exchange records.
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
    department_tag = models.CharField(max_length=64, blank=True, default="FEES", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@fees.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = FeesPaymentsIntegrationBridgeManager()

    class Meta:
        db_table = "fees_fees_payments_integrationbridge"
        ordering = ["-created_at", "code"]
        verbose_name = _("FeesPaymentsIntegrationBridge")
        verbose_name_plural = _("FeesPaymentsIntegrationBridges")
        indexes = [
            models.Index(fields=["code", "status"], name="fees_fees_p_9c131bf3_cd"),
            models.Index(fields=["created_at"], name="fees_fees_p_9c131bf3_cr"),
            models.Index(fields=["priority", "status"], name="fees_fees_p_9c131bf3_pr"),
            models.Index(fields=["department_tag", "status"], name="fees_fees_p_9c131bf3_dp"),
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

class FeesPaymentsSecurityPermitQuerySet(models.QuerySet):
    """Custom QuerySet methods for FeesPaymentsSecurityPermit."""
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

class FeesPaymentsSecurityPermitManager(models.Manager):
    """Custom model manager for FeesPaymentsSecurityPermit."""
    def get_queryset(self):
        return FeesPaymentsSecurityPermitQuerySet(self.model, using=self._db)
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

class FeesPaymentsSecurityPermit(models.Model):
    """
    FeesPaymentsSecurityPermit: Granular authorization token defining scoped operational access.
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
    department_tag = models.CharField(max_length=64, blank=True, default="FEES", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@fees.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = FeesPaymentsSecurityPermitManager()

    class Meta:
        db_table = "fees_fees_payments_securitypermit"
        ordering = ["-created_at", "code"]
        verbose_name = _("FeesPaymentsSecurityPermit")
        verbose_name_plural = _("FeesPaymentsSecurityPermits")
        indexes = [
            models.Index(fields=["code", "status"], name="fees_fees_p_e5fba4a9_cd"),
            models.Index(fields=["created_at"], name="fees_fees_p_e5fba4a9_cr"),
            models.Index(fields=["priority", "status"], name="fees_fees_p_e5fba4a9_pr"),
            models.Index(fields=["department_tag", "status"], name="fees_fees_p_e5fba4a9_dp"),
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

class FeesPaymentsDocumentAttachmentQuerySet(models.QuerySet):
    """Custom QuerySet methods for FeesPaymentsDocumentAttachment."""
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

class FeesPaymentsDocumentAttachmentManager(models.Manager):
    """Custom model manager for FeesPaymentsDocumentAttachment."""
    def get_queryset(self):
        return FeesPaymentsDocumentAttachmentQuerySet(self.model, using=self._db)
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

class FeesPaymentsDocumentAttachment(models.Model):
    """
    FeesPaymentsDocumentAttachment: Official digital file attachment container with cryptographic checksums.
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
    department_tag = models.CharField(max_length=64, blank=True, default="FEES", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@fees.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = FeesPaymentsDocumentAttachmentManager()

    class Meta:
        db_table = "fees_fees_payments_documentattachment"
        ordering = ["-created_at", "code"]
        verbose_name = _("FeesPaymentsDocumentAttachment")
        verbose_name_plural = _("FeesPaymentsDocumentAttachments")
        indexes = [
            models.Index(fields=["code", "status"], name="fees_fees_p_49c01d89_cd"),
            models.Index(fields=["created_at"], name="fees_fees_p_49c01d89_cr"),
            models.Index(fields=["priority", "status"], name="fees_fees_p_49c01d89_pr"),
            models.Index(fields=["department_tag", "status"], name="fees_fees_p_49c01d89_dp"),
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

class FeesPaymentsLifecycleTransitionQuerySet(models.QuerySet):
    """Custom QuerySet methods for FeesPaymentsLifecycleTransition."""
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

class FeesPaymentsLifecycleTransitionManager(models.Manager):
    """Custom model manager for FeesPaymentsLifecycleTransition."""
    def get_queryset(self):
        return FeesPaymentsLifecycleTransitionQuerySet(self.model, using=self._db)
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

class FeesPaymentsLifecycleTransition(models.Model):
    """
    FeesPaymentsLifecycleTransition: State transition checkpoint recording approval gates and authorizations.
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
    department_tag = models.CharField(max_length=64, blank=True, default="FEES", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@fees.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = FeesPaymentsLifecycleTransitionManager()

    class Meta:
        db_table = "fees_fees_payments_lifecycletransition"
        ordering = ["-created_at", "code"]
        verbose_name = _("FeesPaymentsLifecycleTransition")
        verbose_name_plural = _("FeesPaymentsLifecycleTransitions")
        indexes = [
            models.Index(fields=["code", "status"], name="fees_fees_p_96bae304_cd"),
            models.Index(fields=["created_at"], name="fees_fees_p_96bae304_cr"),
            models.Index(fields=["priority", "status"], name="fees_fees_p_96bae304_pr"),
            models.Index(fields=["department_tag", "status"], name="fees_fees_p_96bae304_dp"),
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

class FeesPaymentsDataArchivalRegistryQuerySet(models.QuerySet):
    """Custom QuerySet methods for FeesPaymentsDataArchivalRegistry."""
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

class FeesPaymentsDataArchivalRegistryManager(models.Manager):
    """Custom model manager for FeesPaymentsDataArchivalRegistry."""
    def get_queryset(self):
        return FeesPaymentsDataArchivalRegistryQuerySet(self.model, using=self._db)
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

class FeesPaymentsDataArchivalRegistry(models.Model):
    """
    FeesPaymentsDataArchivalRegistry: Record archival state, cold storage pointers, and legal hold flags.
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
    department_tag = models.CharField(max_length=64, blank=True, default="FEES", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@fees.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = FeesPaymentsDataArchivalRegistryManager()

    class Meta:
        db_table = "fees_fees_payments_dataarchivalregistry"
        ordering = ["-created_at", "code"]
        verbose_name = _("FeesPaymentsDataArchivalRegistry")
        verbose_name_plural = _("FeesPaymentsDataArchivalRegistrys")
        indexes = [
            models.Index(fields=["code", "status"], name="fees_fees_p_49c5fd4b_cd"),
            models.Index(fields=["created_at"], name="fees_fees_p_49c5fd4b_cr"),
            models.Index(fields=["priority", "status"], name="fees_fees_p_49c5fd4b_pr"),
            models.Index(fields=["department_tag", "status"], name="fees_fees_p_49c5fd4b_dp"),
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

class FeesPaymentsTelemetryEventStreamQuerySet(models.QuerySet):
    """Custom QuerySet methods for FeesPaymentsTelemetryEventStream."""
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

class FeesPaymentsTelemetryEventStreamManager(models.Manager):
    """Custom model manager for FeesPaymentsTelemetryEventStream."""
    def get_queryset(self):
        return FeesPaymentsTelemetryEventStreamQuerySet(self.model, using=self._db)
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

class FeesPaymentsTelemetryEventStream(models.Model):
    """
    FeesPaymentsTelemetryEventStream: Real-time telemetry events and activity streams.
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
    department_tag = models.CharField(max_length=64, blank=True, default="FEES", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@fees.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = FeesPaymentsTelemetryEventStreamManager()

    class Meta:
        db_table = "fees_fees_payments_telemetryeventstream"
        ordering = ["-created_at", "code"]
        verbose_name = _("FeesPaymentsTelemetryEventStream")
        verbose_name_plural = _("FeesPaymentsTelemetryEventStreams")
        indexes = [
            models.Index(fields=["code", "status"], name="fees_fees_p_680991f4_cd"),
            models.Index(fields=["created_at"], name="fees_fees_p_680991f4_cr"),
            models.Index(fields=["priority", "status"], name="fees_fees_p_680991f4_pr"),
            models.Index(fields=["department_tag", "status"], name="fees_fees_p_680991f4_dp"),
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

class FeesPaymentsAccessGrantMatrixQuerySet(models.QuerySet):
    """Custom QuerySet methods for FeesPaymentsAccessGrantMatrix."""
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

class FeesPaymentsAccessGrantMatrixManager(models.Manager):
    """Custom model manager for FeesPaymentsAccessGrantMatrix."""
    def get_queryset(self):
        return FeesPaymentsAccessGrantMatrixQuerySet(self.model, using=self._db)
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

class FeesPaymentsAccessGrantMatrix(models.Model):
    """
    FeesPaymentsAccessGrantMatrix: Granular privilege assignments and operational scope bindings.
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
    department_tag = models.CharField(max_length=64, blank=True, default="FEES", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@fees.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = FeesPaymentsAccessGrantMatrixManager()

    class Meta:
        db_table = "fees_fees_payments_accessgrantmatrix"
        ordering = ["-created_at", "code"]
        verbose_name = _("FeesPaymentsAccessGrantMatrix")
        verbose_name_plural = _("FeesPaymentsAccessGrantMatrixs")
        indexes = [
            models.Index(fields=["code", "status"], name="fees_fees_p_136ce887_cd"),
            models.Index(fields=["created_at"], name="fees_fees_p_136ce887_cr"),
            models.Index(fields=["priority", "status"], name="fees_fees_p_136ce887_pr"),
            models.Index(fields=["department_tag", "status"], name="fees_fees_p_136ce887_dp"),
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

class FeesPaymentsOperationalQuotaQuerySet(models.QuerySet):
    """Custom QuerySet methods for FeesPaymentsOperationalQuota."""
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

class FeesPaymentsOperationalQuotaManager(models.Manager):
    """Custom model manager for FeesPaymentsOperationalQuota."""
    def get_queryset(self):
        return FeesPaymentsOperationalQuotaQuerySet(self.model, using=self._db)
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

class FeesPaymentsOperationalQuota(models.Model):
    """
    FeesPaymentsOperationalQuota: Resource quotas, bandwidth/usage limits, and consumption tracking.
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
    department_tag = models.CharField(max_length=64, blank=True, default="FEES", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@fees.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = FeesPaymentsOperationalQuotaManager()

    class Meta:
        db_table = "fees_fees_payments_operationalquota"
        ordering = ["-created_at", "code"]
        verbose_name = _("FeesPaymentsOperationalQuota")
        verbose_name_plural = _("FeesPaymentsOperationalQuotas")
        indexes = [
            models.Index(fields=["code", "status"], name="fees_fees_p_038888df_cd"),
            models.Index(fields=["created_at"], name="fees_fees_p_038888df_cr"),
            models.Index(fields=["priority", "status"], name="fees_fees_p_038888df_pr"),
            models.Index(fields=["department_tag", "status"], name="fees_fees_p_038888df_dp"),
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

class FeesPaymentsWorkflowAuditCheckpointQuerySet(models.QuerySet):
    """Custom QuerySet methods for FeesPaymentsWorkflowAuditCheckpoint."""
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

class FeesPaymentsWorkflowAuditCheckpointManager(models.Manager):
    """Custom model manager for FeesPaymentsWorkflowAuditCheckpoint."""
    def get_queryset(self):
        return FeesPaymentsWorkflowAuditCheckpointQuerySet(self.model, using=self._db)
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

class FeesPaymentsWorkflowAuditCheckpoint(models.Model):
    """
    FeesPaymentsWorkflowAuditCheckpoint: Stage-gate checkpoints and sign-off validations.
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
    department_tag = models.CharField(max_length=64, blank=True, default="FEES", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@fees.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = FeesPaymentsWorkflowAuditCheckpointManager()

    class Meta:
        db_table = "fees_fees_payments_workflowauditcheckpoint"
        ordering = ["-created_at", "code"]
        verbose_name = _("FeesPaymentsWorkflowAuditCheckpoint")
        verbose_name_plural = _("FeesPaymentsWorkflowAuditCheckpoints")
        indexes = [
            models.Index(fields=["code", "status"], name="fees_fees_p_83c9d742_cd"),
            models.Index(fields=["created_at"], name="fees_fees_p_83c9d742_cr"),
            models.Index(fields=["priority", "status"], name="fees_fees_p_83c9d742_pr"),
            models.Index(fields=["department_tag", "status"], name="fees_fees_p_83c9d742_dp"),
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

class FeesPaymentsDisasterRecoveryCheckpointQuerySet(models.QuerySet):
    """Custom QuerySet methods for FeesPaymentsDisasterRecoveryCheckpoint."""
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

class FeesPaymentsDisasterRecoveryCheckpointManager(models.Manager):
    """Custom model manager for FeesPaymentsDisasterRecoveryCheckpoint."""
    def get_queryset(self):
        return FeesPaymentsDisasterRecoveryCheckpointQuerySet(self.model, using=self._db)
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

class FeesPaymentsDisasterRecoveryCheckpoint(models.Model):
    """
    FeesPaymentsDisasterRecoveryCheckpoint: Point-in-time state checkpoint for high-availability disaster recovery validation.
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
    department_tag = models.CharField(max_length=64, blank=True, default="FEES", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@fees.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = FeesPaymentsDisasterRecoveryCheckpointManager()

    class Meta:
        db_table = "fees_fees_payments_disasterrecoverycheckpoint"
        ordering = ["-created_at", "code"]
        verbose_name = _("FeesPaymentsDisasterRecoveryCheckpoint")
        verbose_name_plural = _("FeesPaymentsDisasterRecoveryCheckpoints")
        indexes = [
            models.Index(fields=["code", "status"], name="fees_fees_p_d8354c84_cd"),
            models.Index(fields=["created_at"], name="fees_fees_p_d8354c84_cr"),
            models.Index(fields=["priority", "status"], name="fees_fees_p_d8354c84_pr"),
            models.Index(fields=["department_tag", "status"], name="fees_fees_p_d8354c84_dp"),
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

class FeesPaymentsSLAComplianceRegisterQuerySet(models.QuerySet):
    """Custom QuerySet methods for FeesPaymentsSLAComplianceRegister."""
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

class FeesPaymentsSLAComplianceRegisterManager(models.Manager):
    """Custom model manager for FeesPaymentsSLAComplianceRegister."""
    def get_queryset(self):
        return FeesPaymentsSLAComplianceRegisterQuerySet(self.model, using=self._db)
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

class FeesPaymentsSLAComplianceRegister(models.Model):
    """
    FeesPaymentsSLAComplianceRegister: Service level agreement compliance tracker for operational responsiveness.
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
    department_tag = models.CharField(max_length=64, blank=True, default="FEES", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@fees.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = FeesPaymentsSLAComplianceRegisterManager()

    class Meta:
        db_table = "fees_fees_payments_slacomplianceregister"
        ordering = ["-created_at", "code"]
        verbose_name = _("FeesPaymentsSLAComplianceRegister")
        verbose_name_plural = _("FeesPaymentsSLAComplianceRegisters")
        indexes = [
            models.Index(fields=["code", "status"], name="fees_fees_p_d7af6515_cd"),
            models.Index(fields=["created_at"], name="fees_fees_p_d7af6515_cr"),
            models.Index(fields=["priority", "status"], name="fees_fees_p_d7af6515_pr"),
            models.Index(fields=["department_tag", "status"], name="fees_fees_p_d7af6515_dp"),
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

class FeesPaymentsIncidentReportRegisterQuerySet(models.QuerySet):
    """Custom QuerySet methods for FeesPaymentsIncidentReportRegister."""
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

class FeesPaymentsIncidentReportRegisterManager(models.Manager):
    """Custom model manager for FeesPaymentsIncidentReportRegister."""
    def get_queryset(self):
        return FeesPaymentsIncidentReportRegisterQuerySet(self.model, using=self._db)
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

class FeesPaymentsIncidentReportRegister(models.Model):
    """
    FeesPaymentsIncidentReportRegister: Incident ticketing and remediation tracking register.
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
    department_tag = models.CharField(max_length=64, blank=True, default="FEES", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@fees.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = FeesPaymentsIncidentReportRegisterManager()

    class Meta:
        db_table = "fees_fees_payments_incidentreportregister"
        ordering = ["-created_at", "code"]
        verbose_name = _("FeesPaymentsIncidentReportRegister")
        verbose_name_plural = _("FeesPaymentsIncidentReportRegisters")
        indexes = [
            models.Index(fields=["code", "status"], name="fees_fees_p_611bcc10_cd"),
            models.Index(fields=["created_at"], name="fees_fees_p_611bcc10_cr"),
            models.Index(fields=["priority", "status"], name="fees_fees_p_611bcc10_pr"),
            models.Index(fields=["department_tag", "status"], name="fees_fees_p_611bcc10_dp"),
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

class FeesPaymentsBusinessContinuityPlanQuerySet(models.QuerySet):
    """Custom QuerySet methods for FeesPaymentsBusinessContinuityPlan."""
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

class FeesPaymentsBusinessContinuityPlanManager(models.Manager):
    """Custom model manager for FeesPaymentsBusinessContinuityPlan."""
    def get_queryset(self):
        return FeesPaymentsBusinessContinuityPlanQuerySet(self.model, using=self._db)
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

class FeesPaymentsBusinessContinuityPlan(models.Model):
    """
    FeesPaymentsBusinessContinuityPlan: Business continuity procedures and failover plan coordinates.
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
    department_tag = models.CharField(max_length=64, blank=True, default="FEES", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@fees.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = FeesPaymentsBusinessContinuityPlanManager()

    class Meta:
        db_table = "fees_fees_payments_businesscontinuityplan"
        ordering = ["-created_at", "code"]
        verbose_name = _("FeesPaymentsBusinessContinuityPlan")
        verbose_name_plural = _("FeesPaymentsBusinessContinuityPlans")
        indexes = [
            models.Index(fields=["code", "status"], name="fees_fees_p_7a0d6e49_cd"),
            models.Index(fields=["created_at"], name="fees_fees_p_7a0d6e49_cr"),
            models.Index(fields=["priority", "status"], name="fees_fees_p_7a0d6e49_pr"),
            models.Index(fields=["department_tag", "status"], name="fees_fees_p_7a0d6e49_dp"),
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

class FeesPaymentsGovernanceAttestationRecordQuerySet(models.QuerySet):
    """Custom QuerySet methods for FeesPaymentsGovernanceAttestationRecord."""
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

class FeesPaymentsGovernanceAttestationRecordManager(models.Manager):
    """Custom model manager for FeesPaymentsGovernanceAttestationRecord."""
    def get_queryset(self):
        return FeesPaymentsGovernanceAttestationRecordQuerySet(self.model, using=self._db)
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

class FeesPaymentsGovernanceAttestationRecord(models.Model):
    """
    FeesPaymentsGovernanceAttestationRecord: Formal institutional governance attestations and sign-offs.
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
    department_tag = models.CharField(max_length=64, blank=True, default="FEES", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@fees.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = FeesPaymentsGovernanceAttestationRecordManager()

    class Meta:
        db_table = "fees_fees_payments_governanceattestationrecord"
        ordering = ["-created_at", "code"]
        verbose_name = _("FeesPaymentsGovernanceAttestationRecord")
        verbose_name_plural = _("FeesPaymentsGovernanceAttestationRecords")
        indexes = [
            models.Index(fields=["code", "status"], name="fees_fees_p_d82b8c7f_cd"),
            models.Index(fields=["created_at"], name="fees_fees_p_d82b8c7f_cr"),
            models.Index(fields=["priority", "status"], name="fees_fees_p_d82b8c7f_pr"),
            models.Index(fields=["department_tag", "status"], name="fees_fees_p_d82b8c7f_dp"),
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

class FeesPaymentsRiskMitigationProtocolQuerySet(models.QuerySet):
    """Custom QuerySet methods for FeesPaymentsRiskMitigationProtocol."""
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

class FeesPaymentsRiskMitigationProtocolManager(models.Manager):
    """Custom model manager for FeesPaymentsRiskMitigationProtocol."""
    def get_queryset(self):
        return FeesPaymentsRiskMitigationProtocolQuerySet(self.model, using=self._db)
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

class FeesPaymentsRiskMitigationProtocol(models.Model):
    """
    FeesPaymentsRiskMitigationProtocol: Institutional risk registry, threat scoring, and mitigation control actions.
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
    department_tag = models.CharField(max_length=64, blank=True, default="FEES", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@fees.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = FeesPaymentsRiskMitigationProtocolManager()

    class Meta:
        db_table = "fees_fees_payments_riskmitigationprotocol"
        ordering = ["-created_at", "code"]
        verbose_name = _("FeesPaymentsRiskMitigationProtocol")
        verbose_name_plural = _("FeesPaymentsRiskMitigationProtocols")
        indexes = [
            models.Index(fields=["code", "status"], name="fees_fees_p_19fcfe34_cd"),
            models.Index(fields=["created_at"], name="fees_fees_p_19fcfe34_cr"),
            models.Index(fields=["priority", "status"], name="fees_fees_p_19fcfe34_pr"),
            models.Index(fields=["department_tag", "status"], name="fees_fees_p_19fcfe34_dp"),
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

class FeesPaymentsInteroperabilityGatewayQuerySet(models.QuerySet):
    """Custom QuerySet methods for FeesPaymentsInteroperabilityGateway."""
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

class FeesPaymentsInteroperabilityGatewayManager(models.Manager):
    """Custom model manager for FeesPaymentsInteroperabilityGateway."""
    def get_queryset(self):
        return FeesPaymentsInteroperabilityGatewayQuerySet(self.model, using=self._db)
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

class FeesPaymentsInteroperabilityGateway(models.Model):
    """
    FeesPaymentsInteroperabilityGateway: External schema normalization and bidirectional data synchronization gateway.
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
    department_tag = models.CharField(max_length=64, blank=True, default="FEES", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@fees.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = FeesPaymentsInteroperabilityGatewayManager()

    class Meta:
        db_table = "fees_fees_payments_interoperabilitygateway"
        ordering = ["-created_at", "code"]
        verbose_name = _("FeesPaymentsInteroperabilityGateway")
        verbose_name_plural = _("FeesPaymentsInteroperabilityGateways")
        indexes = [
            models.Index(fields=["code", "status"], name="fees_fees_p_f3c08734_cd"),
            models.Index(fields=["created_at"], name="fees_fees_p_f3c08734_cr"),
            models.Index(fields=["priority", "status"], name="fees_fees_p_f3c08734_pr"),
            models.Index(fields=["department_tag", "status"], name="fees_fees_p_f3c08734_dp"),
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

class FeesPaymentsCapacityForecastIndexQuerySet(models.QuerySet):
    """Custom QuerySet methods for FeesPaymentsCapacityForecastIndex."""
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

class FeesPaymentsCapacityForecastIndexManager(models.Manager):
    """Custom model manager for FeesPaymentsCapacityForecastIndex."""
    def get_queryset(self):
        return FeesPaymentsCapacityForecastIndexQuerySet(self.model, using=self._db)
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

class FeesPaymentsCapacityForecastIndex(models.Model):
    """
    FeesPaymentsCapacityForecastIndex: Predictive demand forecasting, cohort growth simulations, and resource quotas.
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
    department_tag = models.CharField(max_length=64, blank=True, default="FEES", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@fees.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = FeesPaymentsCapacityForecastIndexManager()

    class Meta:
        db_table = "fees_fees_payments_capacityforecastindex"
        ordering = ["-created_at", "code"]
        verbose_name = _("FeesPaymentsCapacityForecastIndex")
        verbose_name_plural = _("FeesPaymentsCapacityForecastIndexs")
        indexes = [
            models.Index(fields=["code", "status"], name="fees_fees_p_e81fbcbd_cd"),
            models.Index(fields=["created_at"], name="fees_fees_p_e81fbcbd_cr"),
            models.Index(fields=["priority", "status"], name="fees_fees_p_e81fbcbd_pr"),
            models.Index(fields=["department_tag", "status"], name="fees_fees_p_e81fbcbd_dp"),
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

class FeesPaymentsSecurityCredentialLedgerQuerySet(models.QuerySet):
    """Custom QuerySet methods for FeesPaymentsSecurityCredentialLedger."""
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

class FeesPaymentsSecurityCredentialLedgerManager(models.Manager):
    """Custom model manager for FeesPaymentsSecurityCredentialLedger."""
    def get_queryset(self):
        return FeesPaymentsSecurityCredentialLedgerQuerySet(self.model, using=self._db)
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

class FeesPaymentsSecurityCredentialLedger(models.Model):
    """
    FeesPaymentsSecurityCredentialLedger: Cryptographic key rotation, API access tokens, and security credential records.
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
    department_tag = models.CharField(max_length=64, blank=True, default="FEES", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@fees.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = FeesPaymentsSecurityCredentialLedgerManager()

    class Meta:
        db_table = "fees_fees_payments_securitycredentialledger"
        ordering = ["-created_at", "code"]
        verbose_name = _("FeesPaymentsSecurityCredentialLedger")
        verbose_name_plural = _("FeesPaymentsSecurityCredentialLedgers")
        indexes = [
            models.Index(fields=["code", "status"], name="fees_fees_p_f0477c67_cd"),
            models.Index(fields=["created_at"], name="fees_fees_p_f0477c67_cr"),
            models.Index(fields=["priority", "status"], name="fees_fees_p_f0477c67_pr"),
            models.Index(fields=["department_tag", "status"], name="fees_fees_p_f0477c67_dp"),
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
