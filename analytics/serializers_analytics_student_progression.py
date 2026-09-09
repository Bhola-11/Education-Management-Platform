"""
Data Transfer Objects & Serializers for Analytics: Student Retention Analytics
PR #87: Structured Data Mapping and Validation DTOs.
"""

from decimal import Decimal
from typing import Dict, Any, List
from analytics.models_analytics_student_progression import AnalyticsStudentProgressionMaster, AnalyticsStudentProgressionConfiguration

class AnalyticsStudentProgressionMasterDTO:
    """Data Transfer Object representing a validated AnalyticsStudentProgressionMaster instance."""
    def __init__(self, record: AnalyticsStudentProgressionMaster):
        self.code = record.code
        self.name = record.name
        self.status = record.status
        self.priority = record.priority
        self.capacity_limit = record.capacity_limit
        self.allocated_count = record.allocated_count
        self.monetary_value = record.monetary_value
        self.score_rating = record.score_rating
        self.is_active = record.is_active

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "name": self.name,
            "status": self.status,
            "priority": self.priority,
            "capacity_limit": self.capacity_limit,
            "allocated_count": self.allocated_count,
            "monetary_value": str(self.monetary_value),
            "score_rating": str(self.score_rating),
            "is_active": self.is_active,
        }

    @classmethod
    def serialize_queryset(cls, qs) -> List[Dict[str, Any]]:
        return [cls(item).to_dict() for item in qs]
