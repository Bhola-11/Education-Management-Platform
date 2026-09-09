"""
Data Transfer Objects & Serializers for Accounts: Authentication
PR #3: Structured Data Mapping and Validation DTOs.
"""

from decimal import Decimal
from typing import Dict, Any, List
from accounts.models_accounts_custom_user import AccountsCustomUserMaster, AccountsCustomUserConfiguration

class AccountsCustomUserMasterDTO:
    """Data Transfer Object representing a validated AccountsCustomUserMaster instance."""
    def __init__(self, record: AccountsCustomUserMaster):
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
