"""
Enterprise Domain Models for Analytics: Institutional Financial Analytics
PR #88: Relational Schema, Field Constraints, Custom Managers & State Tracking.
"""

from decimal import Decimal
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from core.constants import AcademicStatus, Gender, BloodGroup, DegreeLevel, AttendanceStatus
from core.validators import validate_phone_number, validate_national_id, validate_gpa_range

class AnalyticsFinancialMasterQuerySet(models.QuerySet):
    """Custom QuerySet methods for AnalyticsFinancialMaster."""
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

class AnalyticsFinancialMasterManager(models.Manager):
    """Custom model manager for AnalyticsFinancialMaster."""
    def get_queryset(self):
        return AnalyticsFinancialMasterQuerySet(self.model, using=self._db)
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

class AnalyticsFinancialMaster(models.Model):
    """
    AnalyticsFinancialMaster: Primary domain master record representing the central institutional entity.
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
    department_tag = models.CharField(max_length=64, blank=True, default="ANALYTICS", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@analytics.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = AnalyticsFinancialMasterManager()

    class Meta:
        db_table = "analytics_analytics_financial_master"
        ordering = ["-created_at", "code"]
        verbose_name = _("AnalyticsFinancialMaster")
        verbose_name_plural = _("AnalyticsFinancialMasters")
        indexes = [
            models.Index(fields=["code", "status"], name="analyt_analyt_55085035_cd"),
            models.Index(fields=["created_at"], name="analyt_analyt_55085035_cr"),
            models.Index(fields=["priority", "status"], name="analyt_analyt_55085035_pr"),
            models.Index(fields=["department_tag", "status"], name="analyt_analyt_55085035_dp"),
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

class AnalyticsFinancialConfigurationQuerySet(models.QuerySet):
    """Custom QuerySet methods for AnalyticsFinancialConfiguration."""
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

class AnalyticsFinancialConfigurationManager(models.Manager):
    """Custom model manager for AnalyticsFinancialConfiguration."""
    def get_queryset(self):
        return AnalyticsFinancialConfigurationQuerySet(self.model, using=self._db)
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

class AnalyticsFinancialConfiguration(models.Model):
    """
    AnalyticsFinancialConfiguration: Operational configuration, policy rules, and system limits.
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
    department_tag = models.CharField(max_length=64, blank=True, default="ANALYTICS", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@analytics.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = AnalyticsFinancialConfigurationManager()

    class Meta:
        db_table = "analytics_analytics_financial_configuration"
        ordering = ["-created_at", "code"]
        verbose_name = _("AnalyticsFinancialConfiguration")
        verbose_name_plural = _("AnalyticsFinancialConfigurations")
        indexes = [
            models.Index(fields=["code", "status"], name="analyt_analyt_d8ff75a9_cd"),
            models.Index(fields=["created_at"], name="analyt_analyt_d8ff75a9_cr"),
            models.Index(fields=["priority", "status"], name="analyt_analyt_d8ff75a9_pr"),
            models.Index(fields=["department_tag", "status"], name="analyt_analyt_d8ff75a9_dp"),
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

class AnalyticsFinancialLedgerQuerySet(models.QuerySet):
    """Custom QuerySet methods for AnalyticsFinancialLedger."""
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

class AnalyticsFinancialLedgerManager(models.Manager):
    """Custom model manager for AnalyticsFinancialLedger."""
    def get_queryset(self):
        return AnalyticsFinancialLedgerQuerySet(self.model, using=self._db)
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

class AnalyticsFinancialLedger(models.Model):
    """
    AnalyticsFinancialLedger: Financial and quantitative accounting ledger tracking balance changes.
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
    department_tag = models.CharField(max_length=64, blank=True, default="ANALYTICS", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@analytics.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = AnalyticsFinancialLedgerManager()

    class Meta:
        db_table = "analytics_analytics_financial_ledger"
        ordering = ["-created_at", "code"]
        verbose_name = _("AnalyticsFinancialLedger")
        verbose_name_plural = _("AnalyticsFinancialLedgers")
        indexes = [
            models.Index(fields=["code", "status"], name="analyt_analyt_927abf29_cd"),
            models.Index(fields=["created_at"], name="analyt_analyt_927abf29_cr"),
            models.Index(fields=["priority", "status"], name="analyt_analyt_927abf29_pr"),
            models.Index(fields=["department_tag", "status"], name="analyt_analyt_927abf29_dp"),
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

class AnalyticsFinancialAuditTransactionQuerySet(models.QuerySet):
    """Custom QuerySet methods for AnalyticsFinancialAuditTransaction."""
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

class AnalyticsFinancialAuditTransactionManager(models.Manager):
    """Custom model manager for AnalyticsFinancialAuditTransaction."""
    def get_queryset(self):
        return AnalyticsFinancialAuditTransactionQuerySet(self.model, using=self._db)
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

class AnalyticsFinancialAuditTransaction(models.Model):
    """
    AnalyticsFinancialAuditTransaction: Immutable audit log transaction record capturing user mutations and states.
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
    department_tag = models.CharField(max_length=64, blank=True, default="ANALYTICS", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@analytics.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = AnalyticsFinancialAuditTransactionManager()

    class Meta:
        db_table = "analytics_analytics_financial_audittransaction"
        ordering = ["-created_at", "code"]
        verbose_name = _("AnalyticsFinancialAuditTransaction")
        verbose_name_plural = _("AnalyticsFinancialAuditTransactions")
        indexes = [
            models.Index(fields=["code", "status"], name="analyt_analyt_bb9ec54c_cd"),
            models.Index(fields=["created_at"], name="analyt_analyt_bb9ec54c_cr"),
            models.Index(fields=["priority", "status"], name="analyt_analyt_bb9ec54c_pr"),
            models.Index(fields=["department_tag", "status"], name="analyt_analyt_bb9ec54c_dp"),
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

class AnalyticsFinancialScheduleMatrixQuerySet(models.QuerySet):
    """Custom QuerySet methods for AnalyticsFinancialScheduleMatrix."""
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

class AnalyticsFinancialScheduleMatrixManager(models.Manager):
    """Custom model manager for AnalyticsFinancialScheduleMatrix."""
    def get_queryset(self):
        return AnalyticsFinancialScheduleMatrixQuerySet(self.model, using=self._db)
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

class AnalyticsFinancialScheduleMatrix(models.Model):
    """
    AnalyticsFinancialScheduleMatrix: Temporal planning and operational schedule coordinates.
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
    department_tag = models.CharField(max_length=64, blank=True, default="ANALYTICS", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@analytics.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = AnalyticsFinancialScheduleMatrixManager()

    class Meta:
        db_table = "analytics_analytics_financial_schedulematrix"
        ordering = ["-created_at", "code"]
        verbose_name = _("AnalyticsFinancialScheduleMatrix")
        verbose_name_plural = _("AnalyticsFinancialScheduleMatrixs")
        indexes = [
            models.Index(fields=["code", "status"], name="analyt_analyt_0c02c167_cd"),
            models.Index(fields=["created_at"], name="analyt_analyt_0c02c167_cr"),
            models.Index(fields=["priority", "status"], name="analyt_analyt_0c02c167_pr"),
            models.Index(fields=["department_tag", "status"], name="analyt_analyt_0c02c167_dp"),
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

class AnalyticsFinancialEvaluationMetricQuerySet(models.QuerySet):
    """Custom QuerySet methods for AnalyticsFinancialEvaluationMetric."""
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

class AnalyticsFinancialEvaluationMetricManager(models.Manager):
    """Custom model manager for AnalyticsFinancialEvaluationMetric."""
    def get_queryset(self):
        return AnalyticsFinancialEvaluationMetricQuerySet(self.model, using=self._db)
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

class AnalyticsFinancialEvaluationMetric(models.Model):
    """
    AnalyticsFinancialEvaluationMetric: Performance indicators, rubrics, and assessment scores.
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
    department_tag = models.CharField(max_length=64, blank=True, default="ANALYTICS", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@analytics.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = AnalyticsFinancialEvaluationMetricManager()

    class Meta:
        db_table = "analytics_analytics_financial_evaluationmetric"
        ordering = ["-created_at", "code"]
        verbose_name = _("AnalyticsFinancialEvaluationMetric")
        verbose_name_plural = _("AnalyticsFinancialEvaluationMetrics")
        indexes = [
            models.Index(fields=["code", "status"], name="analyt_analyt_d9bb2ba5_cd"),
            models.Index(fields=["created_at"], name="analyt_analyt_d9bb2ba5_cr"),
            models.Index(fields=["priority", "status"], name="analyt_analyt_d9bb2ba5_pr"),
            models.Index(fields=["department_tag", "status"], name="analyt_analyt_d9bb2ba5_dp"),
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

class AnalyticsFinancialRosterMappingQuerySet(models.QuerySet):
    """Custom QuerySet methods for AnalyticsFinancialRosterMapping."""
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

class AnalyticsFinancialRosterMappingManager(models.Manager):
    """Custom model manager for AnalyticsFinancialRosterMapping."""
    def get_queryset(self):
        return AnalyticsFinancialRosterMappingQuerySet(self.model, using=self._db)
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

class AnalyticsFinancialRosterMapping(models.Model):
    """
    AnalyticsFinancialRosterMapping: Relational participant roster links and enrollment associations.
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
    department_tag = models.CharField(max_length=64, blank=True, default="ANALYTICS", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@analytics.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = AnalyticsFinancialRosterMappingManager()

    class Meta:
        db_table = "analytics_analytics_financial_rostermapping"
        ordering = ["-created_at", "code"]
        verbose_name = _("AnalyticsFinancialRosterMapping")
        verbose_name_plural = _("AnalyticsFinancialRosterMappings")
        indexes = [
            models.Index(fields=["code", "status"], name="analyt_analyt_17c177a9_cd"),
            models.Index(fields=["created_at"], name="analyt_analyt_17c177a9_cr"),
            models.Index(fields=["priority", "status"], name="analyt_analyt_17c177a9_pr"),
            models.Index(fields=["department_tag", "status"], name="analyt_analyt_17c177a9_dp"),
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

class AnalyticsFinancialVerificationSignatureQuerySet(models.QuerySet):
    """Custom QuerySet methods for AnalyticsFinancialVerificationSignature."""
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

class AnalyticsFinancialVerificationSignatureManager(models.Manager):
    """Custom model manager for AnalyticsFinancialVerificationSignature."""
    def get_queryset(self):
        return AnalyticsFinancialVerificationSignatureQuerySet(self.model, using=self._db)
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

class AnalyticsFinancialVerificationSignature(models.Model):
    """
    AnalyticsFinancialVerificationSignature: Cryptographic verification and integrity tokens.
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
    department_tag = models.CharField(max_length=64, blank=True, default="ANALYTICS", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@analytics.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = AnalyticsFinancialVerificationSignatureManager()

    class Meta:
        db_table = "analytics_analytics_financial_verificationsignature"
        ordering = ["-created_at", "code"]
        verbose_name = _("AnalyticsFinancialVerificationSignature")
        verbose_name_plural = _("AnalyticsFinancialVerificationSignatures")
        indexes = [
            models.Index(fields=["code", "status"], name="analyt_analyt_b0de2655_cd"),
            models.Index(fields=["created_at"], name="analyt_analyt_b0de2655_cr"),
            models.Index(fields=["priority", "status"], name="analyt_analyt_b0de2655_pr"),
            models.Index(fields=["department_tag", "status"], name="analyt_analyt_b0de2655_dp"),
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

class AnalyticsFinancialNotificationRuleQuerySet(models.QuerySet):
    """Custom QuerySet methods for AnalyticsFinancialNotificationRule."""
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

class AnalyticsFinancialNotificationRuleManager(models.Manager):
    """Custom model manager for AnalyticsFinancialNotificationRule."""
    def get_queryset(self):
        return AnalyticsFinancialNotificationRuleQuerySet(self.model, using=self._db)
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

class AnalyticsFinancialNotificationRule(models.Model):
    """
    AnalyticsFinancialNotificationRule: Event-driven notification triggers and audience matrices.
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
    department_tag = models.CharField(max_length=64, blank=True, default="ANALYTICS", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@analytics.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = AnalyticsFinancialNotificationRuleManager()

    class Meta:
        db_table = "analytics_analytics_financial_notificationrule"
        ordering = ["-created_at", "code"]
        verbose_name = _("AnalyticsFinancialNotificationRule")
        verbose_name_plural = _("AnalyticsFinancialNotificationRules")
        indexes = [
            models.Index(fields=["code", "status"], name="analyt_analyt_ec0e4688_cd"),
            models.Index(fields=["created_at"], name="analyt_analyt_ec0e4688_cr"),
            models.Index(fields=["priority", "status"], name="analyt_analyt_ec0e4688_pr"),
            models.Index(fields=["department_tag", "status"], name="analyt_analyt_ec0e4688_dp"),
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

class AnalyticsFinancialAnalyticalSnapshotQuerySet(models.QuerySet):
    """Custom QuerySet methods for AnalyticsFinancialAnalyticalSnapshot."""
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

class AnalyticsFinancialAnalyticalSnapshotManager(models.Manager):
    """Custom model manager for AnalyticsFinancialAnalyticalSnapshot."""
    def get_queryset(self):
        return AnalyticsFinancialAnalyticalSnapshotQuerySet(self.model, using=self._db)
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

class AnalyticsFinancialAnalyticalSnapshot(models.Model):
    """
    AnalyticsFinancialAnalyticalSnapshot: Aggregated telemetry snapshot capturing historical trend data.
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
    department_tag = models.CharField(max_length=64, blank=True, default="ANALYTICS", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@analytics.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = AnalyticsFinancialAnalyticalSnapshotManager()

    class Meta:
        db_table = "analytics_analytics_financial_analyticalsnapshot"
        ordering = ["-created_at", "code"]
        verbose_name = _("AnalyticsFinancialAnalyticalSnapshot")
        verbose_name_plural = _("AnalyticsFinancialAnalyticalSnapshots")
        indexes = [
            models.Index(fields=["code", "status"], name="analyt_analyt_00ee98f1_cd"),
            models.Index(fields=["created_at"], name="analyt_analyt_00ee98f1_cr"),
            models.Index(fields=["priority", "status"], name="analyt_analyt_00ee98f1_pr"),
            models.Index(fields=["department_tag", "status"], name="analyt_analyt_00ee98f1_dp"),
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

class AnalyticsFinancialComplianceLogQuerySet(models.QuerySet):
    """Custom QuerySet methods for AnalyticsFinancialComplianceLog."""
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

class AnalyticsFinancialComplianceLogManager(models.Manager):
    """Custom model manager for AnalyticsFinancialComplianceLog."""
    def get_queryset(self):
        return AnalyticsFinancialComplianceLogQuerySet(self.model, using=self._db)
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

class AnalyticsFinancialComplianceLog(models.Model):
    """
    AnalyticsFinancialComplianceLog: Regulatory compliance inspections and institutional certifications.
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
    department_tag = models.CharField(max_length=64, blank=True, default="ANALYTICS", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@analytics.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = AnalyticsFinancialComplianceLogManager()

    class Meta:
        db_table = "analytics_analytics_financial_compliancelog"
        ordering = ["-created_at", "code"]
        verbose_name = _("AnalyticsFinancialComplianceLog")
        verbose_name_plural = _("AnalyticsFinancialComplianceLogs")
        indexes = [
            models.Index(fields=["code", "status"], name="analyt_analyt_ba45443f_cd"),
            models.Index(fields=["created_at"], name="analyt_analyt_ba45443f_cr"),
            models.Index(fields=["priority", "status"], name="analyt_analyt_ba45443f_pr"),
            models.Index(fields=["department_tag", "status"], name="analyt_analyt_ba45443f_dp"),
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

class AnalyticsFinancialIntegrationBridgeQuerySet(models.QuerySet):
    """Custom QuerySet methods for AnalyticsFinancialIntegrationBridge."""
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

class AnalyticsFinancialIntegrationBridgeManager(models.Manager):
    """Custom model manager for AnalyticsFinancialIntegrationBridge."""
    def get_queryset(self):
        return AnalyticsFinancialIntegrationBridgeQuerySet(self.model, using=self._db)
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

class AnalyticsFinancialIntegrationBridge(models.Model):
    """
    AnalyticsFinancialIntegrationBridge: External system integration endpoints and payload exchange records.
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
    department_tag = models.CharField(max_length=64, blank=True, default="ANALYTICS", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@analytics.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = AnalyticsFinancialIntegrationBridgeManager()

    class Meta:
        db_table = "analytics_analytics_financial_integrationbridge"
        ordering = ["-created_at", "code"]
        verbose_name = _("AnalyticsFinancialIntegrationBridge")
        verbose_name_plural = _("AnalyticsFinancialIntegrationBridges")
        indexes = [
            models.Index(fields=["code", "status"], name="analyt_analyt_46f7bd46_cd"),
            models.Index(fields=["created_at"], name="analyt_analyt_46f7bd46_cr"),
            models.Index(fields=["priority", "status"], name="analyt_analyt_46f7bd46_pr"),
            models.Index(fields=["department_tag", "status"], name="analyt_analyt_46f7bd46_dp"),
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

class AnalyticsFinancialSecurityPermitQuerySet(models.QuerySet):
    """Custom QuerySet methods for AnalyticsFinancialSecurityPermit."""
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

class AnalyticsFinancialSecurityPermitManager(models.Manager):
    """Custom model manager for AnalyticsFinancialSecurityPermit."""
    def get_queryset(self):
        return AnalyticsFinancialSecurityPermitQuerySet(self.model, using=self._db)
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

class AnalyticsFinancialSecurityPermit(models.Model):
    """
    AnalyticsFinancialSecurityPermit: Granular authorization token defining scoped operational access.
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
    department_tag = models.CharField(max_length=64, blank=True, default="ANALYTICS", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@analytics.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = AnalyticsFinancialSecurityPermitManager()

    class Meta:
        db_table = "analytics_analytics_financial_securitypermit"
        ordering = ["-created_at", "code"]
        verbose_name = _("AnalyticsFinancialSecurityPermit")
        verbose_name_plural = _("AnalyticsFinancialSecurityPermits")
        indexes = [
            models.Index(fields=["code", "status"], name="analyt_analyt_a96803da_cd"),
            models.Index(fields=["created_at"], name="analyt_analyt_a96803da_cr"),
            models.Index(fields=["priority", "status"], name="analyt_analyt_a96803da_pr"),
            models.Index(fields=["department_tag", "status"], name="analyt_analyt_a96803da_dp"),
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

class AnalyticsFinancialDocumentAttachmentQuerySet(models.QuerySet):
    """Custom QuerySet methods for AnalyticsFinancialDocumentAttachment."""
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

class AnalyticsFinancialDocumentAttachmentManager(models.Manager):
    """Custom model manager for AnalyticsFinancialDocumentAttachment."""
    def get_queryset(self):
        return AnalyticsFinancialDocumentAttachmentQuerySet(self.model, using=self._db)
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

class AnalyticsFinancialDocumentAttachment(models.Model):
    """
    AnalyticsFinancialDocumentAttachment: Official digital file attachment container with cryptographic checksums.
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
    department_tag = models.CharField(max_length=64, blank=True, default="ANALYTICS", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@analytics.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = AnalyticsFinancialDocumentAttachmentManager()

    class Meta:
        db_table = "analytics_analytics_financial_documentattachment"
        ordering = ["-created_at", "code"]
        verbose_name = _("AnalyticsFinancialDocumentAttachment")
        verbose_name_plural = _("AnalyticsFinancialDocumentAttachments")
        indexes = [
            models.Index(fields=["code", "status"], name="analyt_analyt_7c44cd0f_cd"),
            models.Index(fields=["created_at"], name="analyt_analyt_7c44cd0f_cr"),
            models.Index(fields=["priority", "status"], name="analyt_analyt_7c44cd0f_pr"),
            models.Index(fields=["department_tag", "status"], name="analyt_analyt_7c44cd0f_dp"),
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

class AnalyticsFinancialLifecycleTransitionQuerySet(models.QuerySet):
    """Custom QuerySet methods for AnalyticsFinancialLifecycleTransition."""
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

class AnalyticsFinancialLifecycleTransitionManager(models.Manager):
    """Custom model manager for AnalyticsFinancialLifecycleTransition."""
    def get_queryset(self):
        return AnalyticsFinancialLifecycleTransitionQuerySet(self.model, using=self._db)
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

class AnalyticsFinancialLifecycleTransition(models.Model):
    """
    AnalyticsFinancialLifecycleTransition: State transition checkpoint recording approval gates and authorizations.
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
    department_tag = models.CharField(max_length=64, blank=True, default="ANALYTICS", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@analytics.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = AnalyticsFinancialLifecycleTransitionManager()

    class Meta:
        db_table = "analytics_analytics_financial_lifecycletransition"
        ordering = ["-created_at", "code"]
        verbose_name = _("AnalyticsFinancialLifecycleTransition")
        verbose_name_plural = _("AnalyticsFinancialLifecycleTransitions")
        indexes = [
            models.Index(fields=["code", "status"], name="analyt_analyt_28e50c68_cd"),
            models.Index(fields=["created_at"], name="analyt_analyt_28e50c68_cr"),
            models.Index(fields=["priority", "status"], name="analyt_analyt_28e50c68_pr"),
            models.Index(fields=["department_tag", "status"], name="analyt_analyt_28e50c68_dp"),
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

class AnalyticsFinancialDataArchivalRegistryQuerySet(models.QuerySet):
    """Custom QuerySet methods for AnalyticsFinancialDataArchivalRegistry."""
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

class AnalyticsFinancialDataArchivalRegistryManager(models.Manager):
    """Custom model manager for AnalyticsFinancialDataArchivalRegistry."""
    def get_queryset(self):
        return AnalyticsFinancialDataArchivalRegistryQuerySet(self.model, using=self._db)
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

class AnalyticsFinancialDataArchivalRegistry(models.Model):
    """
    AnalyticsFinancialDataArchivalRegistry: Record archival state, cold storage pointers, and legal hold flags.
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
    department_tag = models.CharField(max_length=64, blank=True, default="ANALYTICS", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@analytics.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = AnalyticsFinancialDataArchivalRegistryManager()

    class Meta:
        db_table = "analytics_analytics_financial_dataarchivalregistry"
        ordering = ["-created_at", "code"]
        verbose_name = _("AnalyticsFinancialDataArchivalRegistry")
        verbose_name_plural = _("AnalyticsFinancialDataArchivalRegistrys")
        indexes = [
            models.Index(fields=["code", "status"], name="analyt_analyt_a636105e_cd"),
            models.Index(fields=["created_at"], name="analyt_analyt_a636105e_cr"),
            models.Index(fields=["priority", "status"], name="analyt_analyt_a636105e_pr"),
            models.Index(fields=["department_tag", "status"], name="analyt_analyt_a636105e_dp"),
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

class AnalyticsFinancialTelemetryEventStreamQuerySet(models.QuerySet):
    """Custom QuerySet methods for AnalyticsFinancialTelemetryEventStream."""
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

class AnalyticsFinancialTelemetryEventStreamManager(models.Manager):
    """Custom model manager for AnalyticsFinancialTelemetryEventStream."""
    def get_queryset(self):
        return AnalyticsFinancialTelemetryEventStreamQuerySet(self.model, using=self._db)
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

class AnalyticsFinancialTelemetryEventStream(models.Model):
    """
    AnalyticsFinancialTelemetryEventStream: Real-time telemetry events and activity streams.
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
    department_tag = models.CharField(max_length=64, blank=True, default="ANALYTICS", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@analytics.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = AnalyticsFinancialTelemetryEventStreamManager()

    class Meta:
        db_table = "analytics_analytics_financial_telemetryeventstream"
        ordering = ["-created_at", "code"]
        verbose_name = _("AnalyticsFinancialTelemetryEventStream")
        verbose_name_plural = _("AnalyticsFinancialTelemetryEventStreams")
        indexes = [
            models.Index(fields=["code", "status"], name="analyt_analyt_279512b7_cd"),
            models.Index(fields=["created_at"], name="analyt_analyt_279512b7_cr"),
            models.Index(fields=["priority", "status"], name="analyt_analyt_279512b7_pr"),
            models.Index(fields=["department_tag", "status"], name="analyt_analyt_279512b7_dp"),
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

class AnalyticsFinancialAccessGrantMatrixQuerySet(models.QuerySet):
    """Custom QuerySet methods for AnalyticsFinancialAccessGrantMatrix."""
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

class AnalyticsFinancialAccessGrantMatrixManager(models.Manager):
    """Custom model manager for AnalyticsFinancialAccessGrantMatrix."""
    def get_queryset(self):
        return AnalyticsFinancialAccessGrantMatrixQuerySet(self.model, using=self._db)
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

class AnalyticsFinancialAccessGrantMatrix(models.Model):
    """
    AnalyticsFinancialAccessGrantMatrix: Granular privilege assignments and operational scope bindings.
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
    department_tag = models.CharField(max_length=64, blank=True, default="ANALYTICS", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@analytics.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = AnalyticsFinancialAccessGrantMatrixManager()

    class Meta:
        db_table = "analytics_analytics_financial_accessgrantmatrix"
        ordering = ["-created_at", "code"]
        verbose_name = _("AnalyticsFinancialAccessGrantMatrix")
        verbose_name_plural = _("AnalyticsFinancialAccessGrantMatrixs")
        indexes = [
            models.Index(fields=["code", "status"], name="analyt_analyt_60a5becd_cd"),
            models.Index(fields=["created_at"], name="analyt_analyt_60a5becd_cr"),
            models.Index(fields=["priority", "status"], name="analyt_analyt_60a5becd_pr"),
            models.Index(fields=["department_tag", "status"], name="analyt_analyt_60a5becd_dp"),
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

class AnalyticsFinancialOperationalQuotaQuerySet(models.QuerySet):
    """Custom QuerySet methods for AnalyticsFinancialOperationalQuota."""
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

class AnalyticsFinancialOperationalQuotaManager(models.Manager):
    """Custom model manager for AnalyticsFinancialOperationalQuota."""
    def get_queryset(self):
        return AnalyticsFinancialOperationalQuotaQuerySet(self.model, using=self._db)
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

class AnalyticsFinancialOperationalQuota(models.Model):
    """
    AnalyticsFinancialOperationalQuota: Resource quotas, bandwidth/usage limits, and consumption tracking.
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
    department_tag = models.CharField(max_length=64, blank=True, default="ANALYTICS", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@analytics.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = AnalyticsFinancialOperationalQuotaManager()

    class Meta:
        db_table = "analytics_analytics_financial_operationalquota"
        ordering = ["-created_at", "code"]
        verbose_name = _("AnalyticsFinancialOperationalQuota")
        verbose_name_plural = _("AnalyticsFinancialOperationalQuotas")
        indexes = [
            models.Index(fields=["code", "status"], name="analyt_analyt_4613c5f0_cd"),
            models.Index(fields=["created_at"], name="analyt_analyt_4613c5f0_cr"),
            models.Index(fields=["priority", "status"], name="analyt_analyt_4613c5f0_pr"),
            models.Index(fields=["department_tag", "status"], name="analyt_analyt_4613c5f0_dp"),
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

class AnalyticsFinancialWorkflowAuditCheckpointQuerySet(models.QuerySet):
    """Custom QuerySet methods for AnalyticsFinancialWorkflowAuditCheckpoint."""
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

class AnalyticsFinancialWorkflowAuditCheckpointManager(models.Manager):
    """Custom model manager for AnalyticsFinancialWorkflowAuditCheckpoint."""
    def get_queryset(self):
        return AnalyticsFinancialWorkflowAuditCheckpointQuerySet(self.model, using=self._db)
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

class AnalyticsFinancialWorkflowAuditCheckpoint(models.Model):
    """
    AnalyticsFinancialWorkflowAuditCheckpoint: Stage-gate checkpoints and sign-off validations.
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
    department_tag = models.CharField(max_length=64, blank=True, default="ANALYTICS", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@analytics.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = AnalyticsFinancialWorkflowAuditCheckpointManager()

    class Meta:
        db_table = "analytics_analytics_financial_workflowauditcheckpoint"
        ordering = ["-created_at", "code"]
        verbose_name = _("AnalyticsFinancialWorkflowAuditCheckpoint")
        verbose_name_plural = _("AnalyticsFinancialWorkflowAuditCheckpoints")
        indexes = [
            models.Index(fields=["code", "status"], name="analyt_analyt_e64f9ce5_cd"),
            models.Index(fields=["created_at"], name="analyt_analyt_e64f9ce5_cr"),
            models.Index(fields=["priority", "status"], name="analyt_analyt_e64f9ce5_pr"),
            models.Index(fields=["department_tag", "status"], name="analyt_analyt_e64f9ce5_dp"),
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

class AnalyticsFinancialDisasterRecoveryCheckpointQuerySet(models.QuerySet):
    """Custom QuerySet methods for AnalyticsFinancialDisasterRecoveryCheckpoint."""
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

class AnalyticsFinancialDisasterRecoveryCheckpointManager(models.Manager):
    """Custom model manager for AnalyticsFinancialDisasterRecoveryCheckpoint."""
    def get_queryset(self):
        return AnalyticsFinancialDisasterRecoveryCheckpointQuerySet(self.model, using=self._db)
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

class AnalyticsFinancialDisasterRecoveryCheckpoint(models.Model):
    """
    AnalyticsFinancialDisasterRecoveryCheckpoint: Point-in-time state checkpoint for high-availability disaster recovery validation.
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
    department_tag = models.CharField(max_length=64, blank=True, default="ANALYTICS", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@analytics.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = AnalyticsFinancialDisasterRecoveryCheckpointManager()

    class Meta:
        db_table = "analytics_analytics_financial_disasterrecoverycheckpoint"
        ordering = ["-created_at", "code"]
        verbose_name = _("AnalyticsFinancialDisasterRecoveryCheckpoint")
        verbose_name_plural = _("AnalyticsFinancialDisasterRecoveryCheckpoints")
        indexes = [
            models.Index(fields=["code", "status"], name="analyt_analyt_ac8487a0_cd"),
            models.Index(fields=["created_at"], name="analyt_analyt_ac8487a0_cr"),
            models.Index(fields=["priority", "status"], name="analyt_analyt_ac8487a0_pr"),
            models.Index(fields=["department_tag", "status"], name="analyt_analyt_ac8487a0_dp"),
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

class AnalyticsFinancialSLAComplianceRegisterQuerySet(models.QuerySet):
    """Custom QuerySet methods for AnalyticsFinancialSLAComplianceRegister."""
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

class AnalyticsFinancialSLAComplianceRegisterManager(models.Manager):
    """Custom model manager for AnalyticsFinancialSLAComplianceRegister."""
    def get_queryset(self):
        return AnalyticsFinancialSLAComplianceRegisterQuerySet(self.model, using=self._db)
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

class AnalyticsFinancialSLAComplianceRegister(models.Model):
    """
    AnalyticsFinancialSLAComplianceRegister: Service level agreement compliance tracker for operational responsiveness.
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
    department_tag = models.CharField(max_length=64, blank=True, default="ANALYTICS", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@analytics.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = AnalyticsFinancialSLAComplianceRegisterManager()

    class Meta:
        db_table = "analytics_analytics_financial_slacomplianceregister"
        ordering = ["-created_at", "code"]
        verbose_name = _("AnalyticsFinancialSLAComplianceRegister")
        verbose_name_plural = _("AnalyticsFinancialSLAComplianceRegisters")
        indexes = [
            models.Index(fields=["code", "status"], name="analyt_analyt_8ded7cbf_cd"),
            models.Index(fields=["created_at"], name="analyt_analyt_8ded7cbf_cr"),
            models.Index(fields=["priority", "status"], name="analyt_analyt_8ded7cbf_pr"),
            models.Index(fields=["department_tag", "status"], name="analyt_analyt_8ded7cbf_dp"),
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

class AnalyticsFinancialIncidentReportRegisterQuerySet(models.QuerySet):
    """Custom QuerySet methods for AnalyticsFinancialIncidentReportRegister."""
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

class AnalyticsFinancialIncidentReportRegisterManager(models.Manager):
    """Custom model manager for AnalyticsFinancialIncidentReportRegister."""
    def get_queryset(self):
        return AnalyticsFinancialIncidentReportRegisterQuerySet(self.model, using=self._db)
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

class AnalyticsFinancialIncidentReportRegister(models.Model):
    """
    AnalyticsFinancialIncidentReportRegister: Incident ticketing and remediation tracking register.
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
    department_tag = models.CharField(max_length=64, blank=True, default="ANALYTICS", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@analytics.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = AnalyticsFinancialIncidentReportRegisterManager()

    class Meta:
        db_table = "analytics_analytics_financial_incidentreportregister"
        ordering = ["-created_at", "code"]
        verbose_name = _("AnalyticsFinancialIncidentReportRegister")
        verbose_name_plural = _("AnalyticsFinancialIncidentReportRegisters")
        indexes = [
            models.Index(fields=["code", "status"], name="analyt_analyt_f9671e24_cd"),
            models.Index(fields=["created_at"], name="analyt_analyt_f9671e24_cr"),
            models.Index(fields=["priority", "status"], name="analyt_analyt_f9671e24_pr"),
            models.Index(fields=["department_tag", "status"], name="analyt_analyt_f9671e24_dp"),
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

class AnalyticsFinancialBusinessContinuityPlanQuerySet(models.QuerySet):
    """Custom QuerySet methods for AnalyticsFinancialBusinessContinuityPlan."""
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

class AnalyticsFinancialBusinessContinuityPlanManager(models.Manager):
    """Custom model manager for AnalyticsFinancialBusinessContinuityPlan."""
    def get_queryset(self):
        return AnalyticsFinancialBusinessContinuityPlanQuerySet(self.model, using=self._db)
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

class AnalyticsFinancialBusinessContinuityPlan(models.Model):
    """
    AnalyticsFinancialBusinessContinuityPlan: Business continuity procedures and failover plan coordinates.
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
    department_tag = models.CharField(max_length=64, blank=True, default="ANALYTICS", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@analytics.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = AnalyticsFinancialBusinessContinuityPlanManager()

    class Meta:
        db_table = "analytics_analytics_financial_businesscontinuityplan"
        ordering = ["-created_at", "code"]
        verbose_name = _("AnalyticsFinancialBusinessContinuityPlan")
        verbose_name_plural = _("AnalyticsFinancialBusinessContinuityPlans")
        indexes = [
            models.Index(fields=["code", "status"], name="analyt_analyt_98526284_cd"),
            models.Index(fields=["created_at"], name="analyt_analyt_98526284_cr"),
            models.Index(fields=["priority", "status"], name="analyt_analyt_98526284_pr"),
            models.Index(fields=["department_tag", "status"], name="analyt_analyt_98526284_dp"),
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

class AnalyticsFinancialGovernanceAttestationRecordQuerySet(models.QuerySet):
    """Custom QuerySet methods for AnalyticsFinancialGovernanceAttestationRecord."""
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

class AnalyticsFinancialGovernanceAttestationRecordManager(models.Manager):
    """Custom model manager for AnalyticsFinancialGovernanceAttestationRecord."""
    def get_queryset(self):
        return AnalyticsFinancialGovernanceAttestationRecordQuerySet(self.model, using=self._db)
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

class AnalyticsFinancialGovernanceAttestationRecord(models.Model):
    """
    AnalyticsFinancialGovernanceAttestationRecord: Formal institutional governance attestations and sign-offs.
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
    department_tag = models.CharField(max_length=64, blank=True, default="ANALYTICS", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@analytics.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = AnalyticsFinancialGovernanceAttestationRecordManager()

    class Meta:
        db_table = "analytics_analytics_financial_governanceattestationrecord"
        ordering = ["-created_at", "code"]
        verbose_name = _("AnalyticsFinancialGovernanceAttestationRecord")
        verbose_name_plural = _("AnalyticsFinancialGovernanceAttestationRecords")
        indexes = [
            models.Index(fields=["code", "status"], name="analyt_analyt_a42d5c55_cd"),
            models.Index(fields=["created_at"], name="analyt_analyt_a42d5c55_cr"),
            models.Index(fields=["priority", "status"], name="analyt_analyt_a42d5c55_pr"),
            models.Index(fields=["department_tag", "status"], name="analyt_analyt_a42d5c55_dp"),
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

class AnalyticsFinancialRiskMitigationProtocolQuerySet(models.QuerySet):
    """Custom QuerySet methods for AnalyticsFinancialRiskMitigationProtocol."""
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

class AnalyticsFinancialRiskMitigationProtocolManager(models.Manager):
    """Custom model manager for AnalyticsFinancialRiskMitigationProtocol."""
    def get_queryset(self):
        return AnalyticsFinancialRiskMitigationProtocolQuerySet(self.model, using=self._db)
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

class AnalyticsFinancialRiskMitigationProtocol(models.Model):
    """
    AnalyticsFinancialRiskMitigationProtocol: Institutional risk registry, threat scoring, and mitigation control actions.
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
    department_tag = models.CharField(max_length=64, blank=True, default="ANALYTICS", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@analytics.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = AnalyticsFinancialRiskMitigationProtocolManager()

    class Meta:
        db_table = "analytics_analytics_financial_riskmitigationprotocol"
        ordering = ["-created_at", "code"]
        verbose_name = _("AnalyticsFinancialRiskMitigationProtocol")
        verbose_name_plural = _("AnalyticsFinancialRiskMitigationProtocols")
        indexes = [
            models.Index(fields=["code", "status"], name="analyt_analyt_73585377_cd"),
            models.Index(fields=["created_at"], name="analyt_analyt_73585377_cr"),
            models.Index(fields=["priority", "status"], name="analyt_analyt_73585377_pr"),
            models.Index(fields=["department_tag", "status"], name="analyt_analyt_73585377_dp"),
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

class AnalyticsFinancialInteroperabilityGatewayQuerySet(models.QuerySet):
    """Custom QuerySet methods for AnalyticsFinancialInteroperabilityGateway."""
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

class AnalyticsFinancialInteroperabilityGatewayManager(models.Manager):
    """Custom model manager for AnalyticsFinancialInteroperabilityGateway."""
    def get_queryset(self):
        return AnalyticsFinancialInteroperabilityGatewayQuerySet(self.model, using=self._db)
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

class AnalyticsFinancialInteroperabilityGateway(models.Model):
    """
    AnalyticsFinancialInteroperabilityGateway: External schema normalization and bidirectional data synchronization gateway.
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
    department_tag = models.CharField(max_length=64, blank=True, default="ANALYTICS", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@analytics.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = AnalyticsFinancialInteroperabilityGatewayManager()

    class Meta:
        db_table = "analytics_analytics_financial_interoperabilitygateway"
        ordering = ["-created_at", "code"]
        verbose_name = _("AnalyticsFinancialInteroperabilityGateway")
        verbose_name_plural = _("AnalyticsFinancialInteroperabilityGateways")
        indexes = [
            models.Index(fields=["code", "status"], name="analyt_analyt_c708a7d7_cd"),
            models.Index(fields=["created_at"], name="analyt_analyt_c708a7d7_cr"),
            models.Index(fields=["priority", "status"], name="analyt_analyt_c708a7d7_pr"),
            models.Index(fields=["department_tag", "status"], name="analyt_analyt_c708a7d7_dp"),
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

class AnalyticsFinancialCapacityForecastIndexQuerySet(models.QuerySet):
    """Custom QuerySet methods for AnalyticsFinancialCapacityForecastIndex."""
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

class AnalyticsFinancialCapacityForecastIndexManager(models.Manager):
    """Custom model manager for AnalyticsFinancialCapacityForecastIndex."""
    def get_queryset(self):
        return AnalyticsFinancialCapacityForecastIndexQuerySet(self.model, using=self._db)
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

class AnalyticsFinancialCapacityForecastIndex(models.Model):
    """
    AnalyticsFinancialCapacityForecastIndex: Predictive demand forecasting, cohort growth simulations, and resource quotas.
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
    department_tag = models.CharField(max_length=64, blank=True, default="ANALYTICS", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@analytics.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = AnalyticsFinancialCapacityForecastIndexManager()

    class Meta:
        db_table = "analytics_analytics_financial_capacityforecastindex"
        ordering = ["-created_at", "code"]
        verbose_name = _("AnalyticsFinancialCapacityForecastIndex")
        verbose_name_plural = _("AnalyticsFinancialCapacityForecastIndexs")
        indexes = [
            models.Index(fields=["code", "status"], name="analyt_analyt_0bb27f38_cd"),
            models.Index(fields=["created_at"], name="analyt_analyt_0bb27f38_cr"),
            models.Index(fields=["priority", "status"], name="analyt_analyt_0bb27f38_pr"),
            models.Index(fields=["department_tag", "status"], name="analyt_analyt_0bb27f38_dp"),
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

class AnalyticsFinancialSecurityCredentialLedgerQuerySet(models.QuerySet):
    """Custom QuerySet methods for AnalyticsFinancialSecurityCredentialLedger."""
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

class AnalyticsFinancialSecurityCredentialLedgerManager(models.Manager):
    """Custom model manager for AnalyticsFinancialSecurityCredentialLedger."""
    def get_queryset(self):
        return AnalyticsFinancialSecurityCredentialLedgerQuerySet(self.model, using=self._db)
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

class AnalyticsFinancialSecurityCredentialLedger(models.Model):
    """
    AnalyticsFinancialSecurityCredentialLedger: Cryptographic key rotation, API access tokens, and security credential records.
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
    department_tag = models.CharField(max_length=64, blank=True, default="ANALYTICS", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@analytics.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = AnalyticsFinancialSecurityCredentialLedgerManager()

    class Meta:
        db_table = "analytics_analytics_financial_securitycredentialledger"
        ordering = ["-created_at", "code"]
        verbose_name = _("AnalyticsFinancialSecurityCredentialLedger")
        verbose_name_plural = _("AnalyticsFinancialSecurityCredentialLedgers")
        indexes = [
            models.Index(fields=["code", "status"], name="analyt_analyt_fd1867c2_cd"),
            models.Index(fields=["created_at"], name="analyt_analyt_fd1867c2_cr"),
            models.Index(fields=["priority", "status"], name="analyt_analyt_fd1867c2_pr"),
            models.Index(fields=["department_tag", "status"], name="analyt_analyt_fd1867c2_dp"),
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
