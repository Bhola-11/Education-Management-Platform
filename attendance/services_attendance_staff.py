"""
Enterprise Business Services for Attendance: Staff Timekeeping
PR #38: Transactional Workflows, Algorithmic Validation, and Audit Pipelines.
"""

import logging
from decimal import Decimal
from typing import List, Dict, Optional, Any
from django.db import transaction, models
from django.utils import timezone
from core.exceptions import EduTrackException, AcademicPolicyViolation, CapacityExceededException
from attendance.models_attendance_staff import (
    AttendanceStaffMaster, AttendanceStaffConfiguration, AttendanceStaffLedger,
    AttendanceStaffAuditTransaction, AttendanceStaffScheduleMatrix, AttendanceStaffEvaluationMetric,
    AttendanceStaffRosterMapping, AttendanceStaffVerificationSignature, AttendanceStaffNotificationRule,
    AttendanceStaffAnalyticalSnapshot, AttendanceStaffComplianceLog, AttendanceStaffIntegrationBridge,
    AttendanceStaffSecurityPermit, AttendanceStaffDocumentAttachment, AttendanceStaffLifecycleTransition
)

logger = logging.getLogger("edutrack.attendance.services.attendance_staff")

class AttendanceStaffWorkflowService:
    """
    Orchestrates business lifecycle, approval gates, and state changes for AttendanceStaff.
    Implements ACID guarantees and structured audit telemetry.
    """

    @classmethod
    @transaction.atomic
    def provision_master_entity(
        cls,
        code: str,
        name: str,
        description: str = "",
        capacity: int = 100,
        monetary_value: Decimal = Decimal("0.00"),
        metadata: Optional[Dict[str, Any]] = None
    ) -> AttendanceStaffMaster:
        """Creates and verifies a new master domain entity with operational defaults."""
        clean_code = code.strip().upper()
        logger.info(f"Initiating provisioning workflow for AttendanceStaff with code {clean_code}")

        if AttendanceStaffMaster.objects.filter(code=clean_code).exists():
            raise EduTrackException(
                f"Entity code '{clean_code}' already exists in the institutional database.",
                code="DUPLICATE_CODE"
            )

        master = AttendanceStaffMaster.objects.create(
            code=clean_code,
            name=name.strip(),
            description=description.strip(),
            capacity_limit=capacity,
            monetary_value=monetary_value,
            metadata=metadata or {},
            is_active=True,
            status="INITIALIZED"
        )

        AttendanceStaffConfiguration.objects.create(
            code=f"{clean_code}-CFG",
            name=f"Configuration for {name.strip()}",
            description=f"Auto-generated configuration container for {clean_code}",
            priority=1,
            status="CONFIGURED"
        )

        AttendanceStaffAuditTransaction.objects.create(
            code=f"TX-{clean_code}-INIT",
            name=f"Provisioning Genesis for {clean_code}",
            description=f"System provisioned AttendanceStaff entity record successfully.",
            status="COMPLETED"
        )

        logger.info(f"Provisioned AttendanceStaffMaster [{master.id}] code: {clean_code} successfully.")
        return master

    @classmethod
    @transaction.atomic
    def execute_state_transition(cls, entity_id: int, target_status: str, actor_notes: str = "") -> AttendanceStaffMaster:
        """Transitions entity through operational state machine with verification checks."""
        master = AttendanceStaffMaster.objects.select_for_update().get(pk=entity_id)
        valid_transitions = {
            "INITIALIZED": ["ACTIVE", "SUSPENDED", "DEPRECATED"],
            "ACTIVE": ["LOCKED", "SUSPENDED", "ARCHIVED"],
            "SUSPENDED": ["ACTIVE", "ARCHIVED"],
            "LOCKED": ["ACTIVE", "ARCHIVED"],
            "ARCHIVED": []
        }

        current = master.status
        allowed = valid_transitions.get(current, [])
        if target_status not in allowed:
            raise AcademicPolicyViolation(
                f"Invalid state transition from '{current}' to '{target_status}' for AttendanceStaff.",
                code="ILLEGAL_TRANSITION"
            )

        master.status = target_status
        master.updated_at = timezone.now()
        master.save(update_fields=["status", "updated_at"])

        AttendanceStaffAuditTransaction.objects.create(
            code=f"TX-{master.code}-{target_status}",
            name=f"Transition to {target_status}",
            description=f"Transitioned from {current} to {target_status}. Notes: {actor_notes}",
            status="SUCCESS"
        )

        logger.info(f"AttendanceStaff [{master.id}] status updated: {current} -> {target_status}")
        return master

    @classmethod
    @transaction.atomic
    def allocate_resource_capacity(cls, entity_id: int, units: int = 1) -> AttendanceStaffMaster:
        """Allocates capacity units ensuring capacity limit is not breached."""
        master = AttendanceStaffMaster.objects.select_for_update().get(pk=entity_id)
        if not master.has_available_capacity(units):
            raise CapacityExceededException(
                f"Capacity exceeded for {master.code}. Available: {master.capacity_limit - master.allocated_count}, Requested: {units}"
            )
        master.increment_allocation(units)
        return master

    @classmethod
    @transaction.atomic
    def deallocate_resource_capacity(cls, entity_id: int, units: int = 1) -> AttendanceStaffMaster:
        """Deallocates resource units safely."""
        master = AttendanceStaffMaster.objects.select_for_update().get(pk=entity_id)
        master.decrement_allocation(units)
        return master

    @classmethod
    def calculate_domain_kpis(cls) -> Dict[str, Any]:
        """Computes aggregate analytics and health metrics for AttendanceStaff."""
        total_count = AttendanceStaffMaster.objects.count()
        active_count = AttendanceStaffMaster.objects.filter(is_active=True).count()
        agg = AttendanceStaffMaster.objects.aggregate(
            total_monetary=models.Sum("monetary_value"),
            avg_score=models.Avg("score_rating"),
            total_allocated=models.Sum("allocated_count"),
            total_capacity=models.Sum("capacity_limit")
        )
        
        return {
            "total_records": total_count,
            "active_records": active_count,
            "inactive_records": total_count - active_count,
            "total_monetary_value": agg["total_monetary"] or Decimal("0.00"),
            "average_score_rating": round(agg["avg_score"] or 0.0, 2),
            "total_allocated_units": agg["total_allocated"] or 0,
            "total_capacity_units": agg["total_capacity"] or 0,
            "timestamp": timezone.now()
        }

class AttendanceStaffCalculationEngine:
    """Mathematical and statistical routines for AttendanceStaff governance."""

    @staticmethod
    def compute_weighted_index(records: List[AttendanceStaffMaster]) -> float:
        """Calculates a weighted performance index across records."""
        if not records:
            return 0.0
        total_weight = sum(r.priority for r in records)
        if total_weight == 0:
            return 0.0
        weighted_sum = sum(float(r.score_rating) * r.priority for r in records)
        return round(weighted_sum / total_weight, 4)

    @staticmethod
    def calculate_variance_ratio(actual: Decimal, target: Decimal) -> float:
        """Calculates percentage variance between actual and target metrics."""
        if not target or target == Decimal("0.00"):
            return 0.0
        diff = actual - target
        return round(float(diff / target) * 100.0, 2)

    @staticmethod
    def project_capacity_exhaustion(master: AttendanceStaffMaster, daily_growth_rate: float) -> int:
        """Estimates number of days remaining until capacity exhaustion."""
        available = master.capacity_limit - master.allocated_count
        if available <= 0:
            return 0
        if daily_growth_rate <= 0:
            return 9999
        return int(available / daily_growth_rate)

class AttendanceStaffValidationPolicyEngine:
    """Pre-condition and business invariant validation engine for AttendanceStaff."""

    @staticmethod
    def validate_master_invariants(master: AttendanceStaffMaster) -> List[str]:
        """Performs exhaustive check of institutional invariants."""
        errors = []
        if not master.code:
            errors.append("Master entity code must be present.")
        if master.capacity_limit < 0:
            errors.append("Capacity limit must be non-negative.")
        if master.allocated_count > master.capacity_limit:
            errors.append("Resource allocation exceeds capacity threshold.")
        return errors

    @staticmethod
    def is_eligible_for_transition(master: AttendanceStaffMaster, target_status: str) -> bool:
        """Evaluates whether master satisfies pre-conditions for target status transition."""
        if master.is_locked and target_status != "ARCHIVED":
            return False
        if target_status == "ACTIVE" and not master.is_verified:
            return False
        return True

class AttendanceStaffAuditReportingService:
    """Generates structured audit trail reports and ledger reconciliations."""

    @classmethod
    def compile_audit_dossier(cls, entity_id: int) -> Dict[str, Any]:
        """Compiles complete operational dossier for an entity."""
        master = AttendanceStaffMaster.objects.get(pk=entity_id)
        txs = AttendanceStaffAuditTransaction.objects.filter(name__icontains=master.code)
        
        return {
            "entity": master.to_summary_dict(),
            "transaction_count": txs.count(),
            "recent_audit_entries": [
                {"code": tx.code, "status": tx.status, "timestamp": tx.created_at.isoformat()}
                for tx in txs[:10]
            ],
            "compiled_at": timezone.now().isoformat()
        }

class AttendanceStaffBatchImportExportEngine:
    """Batch ingestion and export processor with line-item validation."""

    @classmethod
    @transaction.atomic
    def process_batch_records(cls, row_data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Processes multiple records within a single transaction."""
        success_count = 0
        errors = []
        for idx, row in enumerate(row_data_list):
            try:
                code = row.get("code", "").strip().upper()
                name = row.get("name", "").strip()
                if not code or not name:
                    errors.append(f"Row {idx + 1}: Code and Name are required.")
                    continue
                if AttendanceStaffMaster.objects.filter(code=code).exists():
                    errors.append(f"Row {idx + 1}: Code '{code}' already exists.")
                    continue
                AttendanceStaffMaster.objects.create(
                    code=code,
                    name=name,
                    status=row.get("status", "ACTIVE"),
                    capacity_limit=int(row.get("capacity_limit", 100)),
                    is_active=True
                )
                success_count += 1
            except Exception as e:
                errors.append(f"Row {idx + 1}: {str(e)}")
        return {"processed": success_count, "errors": errors, "total": len(row_data_list)}
