"""
Enterprise Domain Models for Notifications: Email Delivery Queue
PR #77: Relational Schema, Field Constraints, Custom Managers & State Tracking.
"""

from decimal import Decimal
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from core.constants import AcademicStatus, Gender, BloodGroup, DegreeLevel, AttendanceStatus
from core.validators import validate_phone_number, validate_national_id, validate_gpa_range

class NotificationsEmailMasterQuerySet(models.QuerySet):
    """Custom QuerySet methods for NotificationsEmailMaster."""
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

class NotificationsEmailMasterManager(models.Manager):
    """Custom model manager for NotificationsEmailMaster."""
    def get_queryset(self):
        return NotificationsEmailMasterQuerySet(self.model, using=self._db)
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

class NotificationsEmailMaster(models.Model):
    """
    NotificationsEmailMaster: Primary domain master record representing the central institutional entity.
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
    department_tag = models.CharField(max_length=64, blank=True, default="NOTIFICATIONS", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@notifications.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = NotificationsEmailMasterManager()

    class Meta:
        db_table = "notifications_notifications_email_master"
        ordering = ["-created_at", "code"]
        verbose_name = _("NotificationsEmailMaster")
        verbose_name_plural = _("NotificationsEmailMasters")
        indexes = [
            models.Index(fields=["code", "status"], name="notifi_notifi_e595df18_cd"),
            models.Index(fields=["created_at"], name="notifi_notifi_e595df18_cr"),
            models.Index(fields=["priority", "status"], name="notifi_notifi_e595df18_pr"),
            models.Index(fields=["department_tag", "status"], name="notifi_notifi_e595df18_dp"),
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

class NotificationsEmailConfigurationQuerySet(models.QuerySet):
    """Custom QuerySet methods for NotificationsEmailConfiguration."""
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

class NotificationsEmailConfigurationManager(models.Manager):
    """Custom model manager for NotificationsEmailConfiguration."""
    def get_queryset(self):
        return NotificationsEmailConfigurationQuerySet(self.model, using=self._db)
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

class NotificationsEmailConfiguration(models.Model):
    """
    NotificationsEmailConfiguration: Operational configuration, policy rules, and system limits.
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
    department_tag = models.CharField(max_length=64, blank=True, default="NOTIFICATIONS", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@notifications.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = NotificationsEmailConfigurationManager()

    class Meta:
        db_table = "notifications_notifications_email_configuration"
        ordering = ["-created_at", "code"]
        verbose_name = _("NotificationsEmailConfiguration")
        verbose_name_plural = _("NotificationsEmailConfigurations")
        indexes = [
            models.Index(fields=["code", "status"], name="notifi_notifi_1e6d1eed_cd"),
            models.Index(fields=["created_at"], name="notifi_notifi_1e6d1eed_cr"),
            models.Index(fields=["priority", "status"], name="notifi_notifi_1e6d1eed_pr"),
            models.Index(fields=["department_tag", "status"], name="notifi_notifi_1e6d1eed_dp"),
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

class NotificationsEmailLedgerQuerySet(models.QuerySet):
    """Custom QuerySet methods for NotificationsEmailLedger."""
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

class NotificationsEmailLedgerManager(models.Manager):
    """Custom model manager for NotificationsEmailLedger."""
    def get_queryset(self):
        return NotificationsEmailLedgerQuerySet(self.model, using=self._db)
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

class NotificationsEmailLedger(models.Model):
    """
    NotificationsEmailLedger: Financial and quantitative accounting ledger tracking balance changes.
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
    department_tag = models.CharField(max_length=64, blank=True, default="NOTIFICATIONS", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@notifications.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = NotificationsEmailLedgerManager()

    class Meta:
        db_table = "notifications_notifications_email_ledger"
        ordering = ["-created_at", "code"]
        verbose_name = _("NotificationsEmailLedger")
        verbose_name_plural = _("NotificationsEmailLedgers")
        indexes = [
            models.Index(fields=["code", "status"], name="notifi_notifi_47e40f1f_cd"),
            models.Index(fields=["created_at"], name="notifi_notifi_47e40f1f_cr"),
            models.Index(fields=["priority", "status"], name="notifi_notifi_47e40f1f_pr"),
            models.Index(fields=["department_tag", "status"], name="notifi_notifi_47e40f1f_dp"),
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

class NotificationsEmailAuditTransactionQuerySet(models.QuerySet):
    """Custom QuerySet methods for NotificationsEmailAuditTransaction."""
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

class NotificationsEmailAuditTransactionManager(models.Manager):
    """Custom model manager for NotificationsEmailAuditTransaction."""
    def get_queryset(self):
        return NotificationsEmailAuditTransactionQuerySet(self.model, using=self._db)
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

class NotificationsEmailAuditTransaction(models.Model):
    """
    NotificationsEmailAuditTransaction: Immutable audit log transaction record capturing user mutations and states.
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
    department_tag = models.CharField(max_length=64, blank=True, default="NOTIFICATIONS", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@notifications.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = NotificationsEmailAuditTransactionManager()

    class Meta:
        db_table = "notifications_notifications_email_audittransaction"
        ordering = ["-created_at", "code"]
        verbose_name = _("NotificationsEmailAuditTransaction")
        verbose_name_plural = _("NotificationsEmailAuditTransactions")
        indexes = [
            models.Index(fields=["code", "status"], name="notifi_notifi_83775562_cd"),
            models.Index(fields=["created_at"], name="notifi_notifi_83775562_cr"),
            models.Index(fields=["priority", "status"], name="notifi_notifi_83775562_pr"),
            models.Index(fields=["department_tag", "status"], name="notifi_notifi_83775562_dp"),
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

class NotificationsEmailScheduleMatrixQuerySet(models.QuerySet):
    """Custom QuerySet methods for NotificationsEmailScheduleMatrix."""
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

class NotificationsEmailScheduleMatrixManager(models.Manager):
    """Custom model manager for NotificationsEmailScheduleMatrix."""
    def get_queryset(self):
        return NotificationsEmailScheduleMatrixQuerySet(self.model, using=self._db)
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

class NotificationsEmailScheduleMatrix(models.Model):
    """
    NotificationsEmailScheduleMatrix: Temporal planning and operational schedule coordinates.
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
    department_tag = models.CharField(max_length=64, blank=True, default="NOTIFICATIONS", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@notifications.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = NotificationsEmailScheduleMatrixManager()

    class Meta:
        db_table = "notifications_notifications_email_schedulematrix"
        ordering = ["-created_at", "code"]
        verbose_name = _("NotificationsEmailScheduleMatrix")
        verbose_name_plural = _("NotificationsEmailScheduleMatrixs")
        indexes = [
            models.Index(fields=["code", "status"], name="notifi_notifi_c3038ae7_cd"),
            models.Index(fields=["created_at"], name="notifi_notifi_c3038ae7_cr"),
            models.Index(fields=["priority", "status"], name="notifi_notifi_c3038ae7_pr"),
            models.Index(fields=["department_tag", "status"], name="notifi_notifi_c3038ae7_dp"),
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

class NotificationsEmailEvaluationMetricQuerySet(models.QuerySet):
    """Custom QuerySet methods for NotificationsEmailEvaluationMetric."""
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

class NotificationsEmailEvaluationMetricManager(models.Manager):
    """Custom model manager for NotificationsEmailEvaluationMetric."""
    def get_queryset(self):
        return NotificationsEmailEvaluationMetricQuerySet(self.model, using=self._db)
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

class NotificationsEmailEvaluationMetric(models.Model):
    """
    NotificationsEmailEvaluationMetric: Performance indicators, rubrics, and assessment scores.
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
    department_tag = models.CharField(max_length=64, blank=True, default="NOTIFICATIONS", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@notifications.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = NotificationsEmailEvaluationMetricManager()

    class Meta:
        db_table = "notifications_notifications_email_evaluationmetric"
        ordering = ["-created_at", "code"]
        verbose_name = _("NotificationsEmailEvaluationMetric")
        verbose_name_plural = _("NotificationsEmailEvaluationMetrics")
        indexes = [
            models.Index(fields=["code", "status"], name="notifi_notifi_352afc64_cd"),
            models.Index(fields=["created_at"], name="notifi_notifi_352afc64_cr"),
            models.Index(fields=["priority", "status"], name="notifi_notifi_352afc64_pr"),
            models.Index(fields=["department_tag", "status"], name="notifi_notifi_352afc64_dp"),
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

class NotificationsEmailRosterMappingQuerySet(models.QuerySet):
    """Custom QuerySet methods for NotificationsEmailRosterMapping."""
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

class NotificationsEmailRosterMappingManager(models.Manager):
    """Custom model manager for NotificationsEmailRosterMapping."""
    def get_queryset(self):
        return NotificationsEmailRosterMappingQuerySet(self.model, using=self._db)
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

class NotificationsEmailRosterMapping(models.Model):
    """
    NotificationsEmailRosterMapping: Relational participant roster links and enrollment associations.
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
    department_tag = models.CharField(max_length=64, blank=True, default="NOTIFICATIONS", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@notifications.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = NotificationsEmailRosterMappingManager()

    class Meta:
        db_table = "notifications_notifications_email_rostermapping"
        ordering = ["-created_at", "code"]
        verbose_name = _("NotificationsEmailRosterMapping")
        verbose_name_plural = _("NotificationsEmailRosterMappings")
        indexes = [
            models.Index(fields=["code", "status"], name="notifi_notifi_8d234d31_cd"),
            models.Index(fields=["created_at"], name="notifi_notifi_8d234d31_cr"),
            models.Index(fields=["priority", "status"], name="notifi_notifi_8d234d31_pr"),
            models.Index(fields=["department_tag", "status"], name="notifi_notifi_8d234d31_dp"),
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

class NotificationsEmailVerificationSignatureQuerySet(models.QuerySet):
    """Custom QuerySet methods for NotificationsEmailVerificationSignature."""
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

class NotificationsEmailVerificationSignatureManager(models.Manager):
    """Custom model manager for NotificationsEmailVerificationSignature."""
    def get_queryset(self):
        return NotificationsEmailVerificationSignatureQuerySet(self.model, using=self._db)
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

class NotificationsEmailVerificationSignature(models.Model):
    """
    NotificationsEmailVerificationSignature: Cryptographic verification and integrity tokens.
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
    department_tag = models.CharField(max_length=64, blank=True, default="NOTIFICATIONS", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@notifications.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = NotificationsEmailVerificationSignatureManager()

    class Meta:
        db_table = "notifications_notifications_email_verificationsignature"
        ordering = ["-created_at", "code"]
        verbose_name = _("NotificationsEmailVerificationSignature")
        verbose_name_plural = _("NotificationsEmailVerificationSignatures")
        indexes = [
            models.Index(fields=["code", "status"], name="notifi_notifi_b1eb9e2e_cd"),
            models.Index(fields=["created_at"], name="notifi_notifi_b1eb9e2e_cr"),
            models.Index(fields=["priority", "status"], name="notifi_notifi_b1eb9e2e_pr"),
            models.Index(fields=["department_tag", "status"], name="notifi_notifi_b1eb9e2e_dp"),
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

class NotificationsEmailNotificationRuleQuerySet(models.QuerySet):
    """Custom QuerySet methods for NotificationsEmailNotificationRule."""
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

class NotificationsEmailNotificationRuleManager(models.Manager):
    """Custom model manager for NotificationsEmailNotificationRule."""
    def get_queryset(self):
        return NotificationsEmailNotificationRuleQuerySet(self.model, using=self._db)
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

class NotificationsEmailNotificationRule(models.Model):
    """
    NotificationsEmailNotificationRule: Event-driven notification triggers and audience matrices.
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
    department_tag = models.CharField(max_length=64, blank=True, default="NOTIFICATIONS", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@notifications.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = NotificationsEmailNotificationRuleManager()

    class Meta:
        db_table = "notifications_notifications_email_notificationrule"
        ordering = ["-created_at", "code"]
        verbose_name = _("NotificationsEmailNotificationRule")
        verbose_name_plural = _("NotificationsEmailNotificationRules")
        indexes = [
            models.Index(fields=["code", "status"], name="notifi_notifi_44df0100_cd"),
            models.Index(fields=["created_at"], name="notifi_notifi_44df0100_cr"),
            models.Index(fields=["priority", "status"], name="notifi_notifi_44df0100_pr"),
            models.Index(fields=["department_tag", "status"], name="notifi_notifi_44df0100_dp"),
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

class NotificationsEmailAnalyticalSnapshotQuerySet(models.QuerySet):
    """Custom QuerySet methods for NotificationsEmailAnalyticalSnapshot."""
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

class NotificationsEmailAnalyticalSnapshotManager(models.Manager):
    """Custom model manager for NotificationsEmailAnalyticalSnapshot."""
    def get_queryset(self):
        return NotificationsEmailAnalyticalSnapshotQuerySet(self.model, using=self._db)
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

class NotificationsEmailAnalyticalSnapshot(models.Model):
    """
    NotificationsEmailAnalyticalSnapshot: Aggregated telemetry snapshot capturing historical trend data.
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
    department_tag = models.CharField(max_length=64, blank=True, default="NOTIFICATIONS", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@notifications.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = NotificationsEmailAnalyticalSnapshotManager()

    class Meta:
        db_table = "notifications_notifications_email_analyticalsnapshot"
        ordering = ["-created_at", "code"]
        verbose_name = _("NotificationsEmailAnalyticalSnapshot")
        verbose_name_plural = _("NotificationsEmailAnalyticalSnapshots")
        indexes = [
            models.Index(fields=["code", "status"], name="notifi_notifi_b109f0ca_cd"),
            models.Index(fields=["created_at"], name="notifi_notifi_b109f0ca_cr"),
            models.Index(fields=["priority", "status"], name="notifi_notifi_b109f0ca_pr"),
            models.Index(fields=["department_tag", "status"], name="notifi_notifi_b109f0ca_dp"),
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

class NotificationsEmailComplianceLogQuerySet(models.QuerySet):
    """Custom QuerySet methods for NotificationsEmailComplianceLog."""
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

class NotificationsEmailComplianceLogManager(models.Manager):
    """Custom model manager for NotificationsEmailComplianceLog."""
    def get_queryset(self):
        return NotificationsEmailComplianceLogQuerySet(self.model, using=self._db)
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

class NotificationsEmailComplianceLog(models.Model):
    """
    NotificationsEmailComplianceLog: Regulatory compliance inspections and institutional certifications.
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
    department_tag = models.CharField(max_length=64, blank=True, default="NOTIFICATIONS", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@notifications.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = NotificationsEmailComplianceLogManager()

    class Meta:
        db_table = "notifications_notifications_email_compliancelog"
        ordering = ["-created_at", "code"]
        verbose_name = _("NotificationsEmailComplianceLog")
        verbose_name_plural = _("NotificationsEmailComplianceLogs")
        indexes = [
            models.Index(fields=["code", "status"], name="notifi_notifi_4b5825d6_cd"),
            models.Index(fields=["created_at"], name="notifi_notifi_4b5825d6_cr"),
            models.Index(fields=["priority", "status"], name="notifi_notifi_4b5825d6_pr"),
            models.Index(fields=["department_tag", "status"], name="notifi_notifi_4b5825d6_dp"),
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

class NotificationsEmailIntegrationBridgeQuerySet(models.QuerySet):
    """Custom QuerySet methods for NotificationsEmailIntegrationBridge."""
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

class NotificationsEmailIntegrationBridgeManager(models.Manager):
    """Custom model manager for NotificationsEmailIntegrationBridge."""
    def get_queryset(self):
        return NotificationsEmailIntegrationBridgeQuerySet(self.model, using=self._db)
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

class NotificationsEmailIntegrationBridge(models.Model):
    """
    NotificationsEmailIntegrationBridge: External system integration endpoints and payload exchange records.
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
    department_tag = models.CharField(max_length=64, blank=True, default="NOTIFICATIONS", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@notifications.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = NotificationsEmailIntegrationBridgeManager()

    class Meta:
        db_table = "notifications_notifications_email_integrationbridge"
        ordering = ["-created_at", "code"]
        verbose_name = _("NotificationsEmailIntegrationBridge")
        verbose_name_plural = _("NotificationsEmailIntegrationBridges")
        indexes = [
            models.Index(fields=["code", "status"], name="notifi_notifi_1ded1559_cd"),
            models.Index(fields=["created_at"], name="notifi_notifi_1ded1559_cr"),
            models.Index(fields=["priority", "status"], name="notifi_notifi_1ded1559_pr"),
            models.Index(fields=["department_tag", "status"], name="notifi_notifi_1ded1559_dp"),
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

class NotificationsEmailSecurityPermitQuerySet(models.QuerySet):
    """Custom QuerySet methods for NotificationsEmailSecurityPermit."""
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

class NotificationsEmailSecurityPermitManager(models.Manager):
    """Custom model manager for NotificationsEmailSecurityPermit."""
    def get_queryset(self):
        return NotificationsEmailSecurityPermitQuerySet(self.model, using=self._db)
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

class NotificationsEmailSecurityPermit(models.Model):
    """
    NotificationsEmailSecurityPermit: Granular authorization token defining scoped operational access.
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
    department_tag = models.CharField(max_length=64, blank=True, default="NOTIFICATIONS", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@notifications.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = NotificationsEmailSecurityPermitManager()

    class Meta:
        db_table = "notifications_notifications_email_securitypermit"
        ordering = ["-created_at", "code"]
        verbose_name = _("NotificationsEmailSecurityPermit")
        verbose_name_plural = _("NotificationsEmailSecurityPermits")
        indexes = [
            models.Index(fields=["code", "status"], name="notifi_notifi_1cb7ede2_cd"),
            models.Index(fields=["created_at"], name="notifi_notifi_1cb7ede2_cr"),
            models.Index(fields=["priority", "status"], name="notifi_notifi_1cb7ede2_pr"),
            models.Index(fields=["department_tag", "status"], name="notifi_notifi_1cb7ede2_dp"),
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

class NotificationsEmailDocumentAttachmentQuerySet(models.QuerySet):
    """Custom QuerySet methods for NotificationsEmailDocumentAttachment."""
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

class NotificationsEmailDocumentAttachmentManager(models.Manager):
    """Custom model manager for NotificationsEmailDocumentAttachment."""
    def get_queryset(self):
        return NotificationsEmailDocumentAttachmentQuerySet(self.model, using=self._db)
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

class NotificationsEmailDocumentAttachment(models.Model):
    """
    NotificationsEmailDocumentAttachment: Official digital file attachment container with cryptographic checksums.
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
    department_tag = models.CharField(max_length=64, blank=True, default="NOTIFICATIONS", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@notifications.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = NotificationsEmailDocumentAttachmentManager()

    class Meta:
        db_table = "notifications_notifications_email_documentattachment"
        ordering = ["-created_at", "code"]
        verbose_name = _("NotificationsEmailDocumentAttachment")
        verbose_name_plural = _("NotificationsEmailDocumentAttachments")
        indexes = [
            models.Index(fields=["code", "status"], name="notifi_notifi_bf3fb028_cd"),
            models.Index(fields=["created_at"], name="notifi_notifi_bf3fb028_cr"),
            models.Index(fields=["priority", "status"], name="notifi_notifi_bf3fb028_pr"),
            models.Index(fields=["department_tag", "status"], name="notifi_notifi_bf3fb028_dp"),
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

class NotificationsEmailLifecycleTransitionQuerySet(models.QuerySet):
    """Custom QuerySet methods for NotificationsEmailLifecycleTransition."""
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

class NotificationsEmailLifecycleTransitionManager(models.Manager):
    """Custom model manager for NotificationsEmailLifecycleTransition."""
    def get_queryset(self):
        return NotificationsEmailLifecycleTransitionQuerySet(self.model, using=self._db)
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

class NotificationsEmailLifecycleTransition(models.Model):
    """
    NotificationsEmailLifecycleTransition: State transition checkpoint recording approval gates and authorizations.
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
    department_tag = models.CharField(max_length=64, blank=True, default="NOTIFICATIONS", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@notifications.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = NotificationsEmailLifecycleTransitionManager()

    class Meta:
        db_table = "notifications_notifications_email_lifecycletransition"
        ordering = ["-created_at", "code"]
        verbose_name = _("NotificationsEmailLifecycleTransition")
        verbose_name_plural = _("NotificationsEmailLifecycleTransitions")
        indexes = [
            models.Index(fields=["code", "status"], name="notifi_notifi_a04c774b_cd"),
            models.Index(fields=["created_at"], name="notifi_notifi_a04c774b_cr"),
            models.Index(fields=["priority", "status"], name="notifi_notifi_a04c774b_pr"),
            models.Index(fields=["department_tag", "status"], name="notifi_notifi_a04c774b_dp"),
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

class NotificationsEmailDataArchivalRegistryQuerySet(models.QuerySet):
    """Custom QuerySet methods for NotificationsEmailDataArchivalRegistry."""
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

class NotificationsEmailDataArchivalRegistryManager(models.Manager):
    """Custom model manager for NotificationsEmailDataArchivalRegistry."""
    def get_queryset(self):
        return NotificationsEmailDataArchivalRegistryQuerySet(self.model, using=self._db)
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

class NotificationsEmailDataArchivalRegistry(models.Model):
    """
    NotificationsEmailDataArchivalRegistry: Record archival state, cold storage pointers, and legal hold flags.
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
    department_tag = models.CharField(max_length=64, blank=True, default="NOTIFICATIONS", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@notifications.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = NotificationsEmailDataArchivalRegistryManager()

    class Meta:
        db_table = "notifications_notifications_email_dataarchivalregistry"
        ordering = ["-created_at", "code"]
        verbose_name = _("NotificationsEmailDataArchivalRegistry")
        verbose_name_plural = _("NotificationsEmailDataArchivalRegistrys")
        indexes = [
            models.Index(fields=["code", "status"], name="notifi_notifi_8806bd97_cd"),
            models.Index(fields=["created_at"], name="notifi_notifi_8806bd97_cr"),
            models.Index(fields=["priority", "status"], name="notifi_notifi_8806bd97_pr"),
            models.Index(fields=["department_tag", "status"], name="notifi_notifi_8806bd97_dp"),
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

class NotificationsEmailTelemetryEventStreamQuerySet(models.QuerySet):
    """Custom QuerySet methods for NotificationsEmailTelemetryEventStream."""
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

class NotificationsEmailTelemetryEventStreamManager(models.Manager):
    """Custom model manager for NotificationsEmailTelemetryEventStream."""
    def get_queryset(self):
        return NotificationsEmailTelemetryEventStreamQuerySet(self.model, using=self._db)
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

class NotificationsEmailTelemetryEventStream(models.Model):
    """
    NotificationsEmailTelemetryEventStream: Real-time telemetry events and activity streams.
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
    department_tag = models.CharField(max_length=64, blank=True, default="NOTIFICATIONS", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@notifications.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = NotificationsEmailTelemetryEventStreamManager()

    class Meta:
        db_table = "notifications_notifications_email_telemetryeventstream"
        ordering = ["-created_at", "code"]
        verbose_name = _("NotificationsEmailTelemetryEventStream")
        verbose_name_plural = _("NotificationsEmailTelemetryEventStreams")
        indexes = [
            models.Index(fields=["code", "status"], name="notifi_notifi_188212a3_cd"),
            models.Index(fields=["created_at"], name="notifi_notifi_188212a3_cr"),
            models.Index(fields=["priority", "status"], name="notifi_notifi_188212a3_pr"),
            models.Index(fields=["department_tag", "status"], name="notifi_notifi_188212a3_dp"),
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

class NotificationsEmailAccessGrantMatrixQuerySet(models.QuerySet):
    """Custom QuerySet methods for NotificationsEmailAccessGrantMatrix."""
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

class NotificationsEmailAccessGrantMatrixManager(models.Manager):
    """Custom model manager for NotificationsEmailAccessGrantMatrix."""
    def get_queryset(self):
        return NotificationsEmailAccessGrantMatrixQuerySet(self.model, using=self._db)
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

class NotificationsEmailAccessGrantMatrix(models.Model):
    """
    NotificationsEmailAccessGrantMatrix: Granular privilege assignments and operational scope bindings.
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
    department_tag = models.CharField(max_length=64, blank=True, default="NOTIFICATIONS", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@notifications.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = NotificationsEmailAccessGrantMatrixManager()

    class Meta:
        db_table = "notifications_notifications_email_accessgrantmatrix"
        ordering = ["-created_at", "code"]
        verbose_name = _("NotificationsEmailAccessGrantMatrix")
        verbose_name_plural = _("NotificationsEmailAccessGrantMatrixs")
        indexes = [
            models.Index(fields=["code", "status"], name="notifi_notifi_7c775672_cd"),
            models.Index(fields=["created_at"], name="notifi_notifi_7c775672_cr"),
            models.Index(fields=["priority", "status"], name="notifi_notifi_7c775672_pr"),
            models.Index(fields=["department_tag", "status"], name="notifi_notifi_7c775672_dp"),
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

class NotificationsEmailOperationalQuotaQuerySet(models.QuerySet):
    """Custom QuerySet methods for NotificationsEmailOperationalQuota."""
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

class NotificationsEmailOperationalQuotaManager(models.Manager):
    """Custom model manager for NotificationsEmailOperationalQuota."""
    def get_queryset(self):
        return NotificationsEmailOperationalQuotaQuerySet(self.model, using=self._db)
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

class NotificationsEmailOperationalQuota(models.Model):
    """
    NotificationsEmailOperationalQuota: Resource quotas, bandwidth/usage limits, and consumption tracking.
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
    department_tag = models.CharField(max_length=64, blank=True, default="NOTIFICATIONS", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@notifications.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = NotificationsEmailOperationalQuotaManager()

    class Meta:
        db_table = "notifications_notifications_email_operationalquota"
        ordering = ["-created_at", "code"]
        verbose_name = _("NotificationsEmailOperationalQuota")
        verbose_name_plural = _("NotificationsEmailOperationalQuotas")
        indexes = [
            models.Index(fields=["code", "status"], name="notifi_notifi_6b2dd8a6_cd"),
            models.Index(fields=["created_at"], name="notifi_notifi_6b2dd8a6_cr"),
            models.Index(fields=["priority", "status"], name="notifi_notifi_6b2dd8a6_pr"),
            models.Index(fields=["department_tag", "status"], name="notifi_notifi_6b2dd8a6_dp"),
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

class NotificationsEmailWorkflowAuditCheckpointQuerySet(models.QuerySet):
    """Custom QuerySet methods for NotificationsEmailWorkflowAuditCheckpoint."""
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

class NotificationsEmailWorkflowAuditCheckpointManager(models.Manager):
    """Custom model manager for NotificationsEmailWorkflowAuditCheckpoint."""
    def get_queryset(self):
        return NotificationsEmailWorkflowAuditCheckpointQuerySet(self.model, using=self._db)
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

class NotificationsEmailWorkflowAuditCheckpoint(models.Model):
    """
    NotificationsEmailWorkflowAuditCheckpoint: Stage-gate checkpoints and sign-off validations.
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
    department_tag = models.CharField(max_length=64, blank=True, default="NOTIFICATIONS", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@notifications.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = NotificationsEmailWorkflowAuditCheckpointManager()

    class Meta:
        db_table = "notifications_notifications_email_workflowauditcheckpoint"
        ordering = ["-created_at", "code"]
        verbose_name = _("NotificationsEmailWorkflowAuditCheckpoint")
        verbose_name_plural = _("NotificationsEmailWorkflowAuditCheckpoints")
        indexes = [
            models.Index(fields=["code", "status"], name="notifi_notifi_622ab0cd_cd"),
            models.Index(fields=["created_at"], name="notifi_notifi_622ab0cd_cr"),
            models.Index(fields=["priority", "status"], name="notifi_notifi_622ab0cd_pr"),
            models.Index(fields=["department_tag", "status"], name="notifi_notifi_622ab0cd_dp"),
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

class NotificationsEmailDisasterRecoveryCheckpointQuerySet(models.QuerySet):
    """Custom QuerySet methods for NotificationsEmailDisasterRecoveryCheckpoint."""
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

class NotificationsEmailDisasterRecoveryCheckpointManager(models.Manager):
    """Custom model manager for NotificationsEmailDisasterRecoveryCheckpoint."""
    def get_queryset(self):
        return NotificationsEmailDisasterRecoveryCheckpointQuerySet(self.model, using=self._db)
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

class NotificationsEmailDisasterRecoveryCheckpoint(models.Model):
    """
    NotificationsEmailDisasterRecoveryCheckpoint: Point-in-time state checkpoint for high-availability disaster recovery validation.
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
    department_tag = models.CharField(max_length=64, blank=True, default="NOTIFICATIONS", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@notifications.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = NotificationsEmailDisasterRecoveryCheckpointManager()

    class Meta:
        db_table = "notifications_notifications_email_disasterrecoverycheckpoint"
        ordering = ["-created_at", "code"]
        verbose_name = _("NotificationsEmailDisasterRecoveryCheckpoint")
        verbose_name_plural = _("NotificationsEmailDisasterRecoveryCheckpoints")
        indexes = [
            models.Index(fields=["code", "status"], name="notifi_notifi_6de1ab87_cd"),
            models.Index(fields=["created_at"], name="notifi_notifi_6de1ab87_cr"),
            models.Index(fields=["priority", "status"], name="notifi_notifi_6de1ab87_pr"),
            models.Index(fields=["department_tag", "status"], name="notifi_notifi_6de1ab87_dp"),
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

class NotificationsEmailSLAComplianceRegisterQuerySet(models.QuerySet):
    """Custom QuerySet methods for NotificationsEmailSLAComplianceRegister."""
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

class NotificationsEmailSLAComplianceRegisterManager(models.Manager):
    """Custom model manager for NotificationsEmailSLAComplianceRegister."""
    def get_queryset(self):
        return NotificationsEmailSLAComplianceRegisterQuerySet(self.model, using=self._db)
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

class NotificationsEmailSLAComplianceRegister(models.Model):
    """
    NotificationsEmailSLAComplianceRegister: Service level agreement compliance tracker for operational responsiveness.
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
    department_tag = models.CharField(max_length=64, blank=True, default="NOTIFICATIONS", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@notifications.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = NotificationsEmailSLAComplianceRegisterManager()

    class Meta:
        db_table = "notifications_notifications_email_slacomplianceregister"
        ordering = ["-created_at", "code"]
        verbose_name = _("NotificationsEmailSLAComplianceRegister")
        verbose_name_plural = _("NotificationsEmailSLAComplianceRegisters")
        indexes = [
            models.Index(fields=["code", "status"], name="notifi_notifi_506b6c98_cd"),
            models.Index(fields=["created_at"], name="notifi_notifi_506b6c98_cr"),
            models.Index(fields=["priority", "status"], name="notifi_notifi_506b6c98_pr"),
            models.Index(fields=["department_tag", "status"], name="notifi_notifi_506b6c98_dp"),
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

class NotificationsEmailIncidentReportRegisterQuerySet(models.QuerySet):
    """Custom QuerySet methods for NotificationsEmailIncidentReportRegister."""
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

class NotificationsEmailIncidentReportRegisterManager(models.Manager):
    """Custom model manager for NotificationsEmailIncidentReportRegister."""
    def get_queryset(self):
        return NotificationsEmailIncidentReportRegisterQuerySet(self.model, using=self._db)
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

class NotificationsEmailIncidentReportRegister(models.Model):
    """
    NotificationsEmailIncidentReportRegister: Incident ticketing and remediation tracking register.
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
    department_tag = models.CharField(max_length=64, blank=True, default="NOTIFICATIONS", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@notifications.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = NotificationsEmailIncidentReportRegisterManager()

    class Meta:
        db_table = "notifications_notifications_email_incidentreportregister"
        ordering = ["-created_at", "code"]
        verbose_name = _("NotificationsEmailIncidentReportRegister")
        verbose_name_plural = _("NotificationsEmailIncidentReportRegisters")
        indexes = [
            models.Index(fields=["code", "status"], name="notifi_notifi_0c60a9ab_cd"),
            models.Index(fields=["created_at"], name="notifi_notifi_0c60a9ab_cr"),
            models.Index(fields=["priority", "status"], name="notifi_notifi_0c60a9ab_pr"),
            models.Index(fields=["department_tag", "status"], name="notifi_notifi_0c60a9ab_dp"),
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

class NotificationsEmailBusinessContinuityPlanQuerySet(models.QuerySet):
    """Custom QuerySet methods for NotificationsEmailBusinessContinuityPlan."""
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

class NotificationsEmailBusinessContinuityPlanManager(models.Manager):
    """Custom model manager for NotificationsEmailBusinessContinuityPlan."""
    def get_queryset(self):
        return NotificationsEmailBusinessContinuityPlanQuerySet(self.model, using=self._db)
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

class NotificationsEmailBusinessContinuityPlan(models.Model):
    """
    NotificationsEmailBusinessContinuityPlan: Business continuity procedures and failover plan coordinates.
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
    department_tag = models.CharField(max_length=64, blank=True, default="NOTIFICATIONS", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@notifications.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = NotificationsEmailBusinessContinuityPlanManager()

    class Meta:
        db_table = "notifications_notifications_email_businesscontinuityplan"
        ordering = ["-created_at", "code"]
        verbose_name = _("NotificationsEmailBusinessContinuityPlan")
        verbose_name_plural = _("NotificationsEmailBusinessContinuityPlans")
        indexes = [
            models.Index(fields=["code", "status"], name="notifi_notifi_ceb5834c_cd"),
            models.Index(fields=["created_at"], name="notifi_notifi_ceb5834c_cr"),
            models.Index(fields=["priority", "status"], name="notifi_notifi_ceb5834c_pr"),
            models.Index(fields=["department_tag", "status"], name="notifi_notifi_ceb5834c_dp"),
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

class NotificationsEmailGovernanceAttestationRecordQuerySet(models.QuerySet):
    """Custom QuerySet methods for NotificationsEmailGovernanceAttestationRecord."""
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

class NotificationsEmailGovernanceAttestationRecordManager(models.Manager):
    """Custom model manager for NotificationsEmailGovernanceAttestationRecord."""
    def get_queryset(self):
        return NotificationsEmailGovernanceAttestationRecordQuerySet(self.model, using=self._db)
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

class NotificationsEmailGovernanceAttestationRecord(models.Model):
    """
    NotificationsEmailGovernanceAttestationRecord: Formal institutional governance attestations and sign-offs.
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
    department_tag = models.CharField(max_length=64, blank=True, default="NOTIFICATIONS", verbose_name=_("Dept Tag"))
    fiscal_code = models.CharField(max_length=64, blank=True, default="FY-2026", verbose_name=_("Fiscal Code"))
    approval_authority = models.CharField(max_length=128, blank=True, default="DEAN", verbose_name=_("Approval Authority"))
    escalation_email = models.EmailField(blank=True, default="compliance@notifications.edutrack.internal", verbose_name=_("Escalation Email"))
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_("Expiration Date"))
    external_reference = models.CharField(max_length=128, blank=True, default="", verbose_name=_("External Ref"))
    version_number = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata Properties"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created Timestamp"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated Timestamp"))

    objects = NotificationsEmailGovernanceAttestationRecordManager()

    class Meta:
        db_table = "notifications_notifications_email_governanceattestationrecord"
        ordering = ["-created_at", "code"]
        verbose_name = _("NotificationsEmailGovernanceAttestationRecord")
        verbose_name_plural = _("NotificationsEmailGovernanceAttestationRecords")
        indexes = [
            models.Index(fields=["code", "status"], name="notifi_notifi_880521e8_cd"),
            models.Index(fields=["created_at"], name="notifi_notifi_880521e8_cr"),
            models.Index(fields=["priority", "status"], name="notifi_notifi_880521e8_pr"),
            models.Index(fields=["department_tag", "status"], name="notifi_notifi_880521e8_dp"),
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
