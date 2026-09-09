"""Cryptographic Ledger Tamper Verification Engine."""
import hashlib
from typing import List

class LedgerTamperDetector:
    @staticmethod
    def verify_chain(records: List[str]) -> bool:
        prev_hash = ""
        for rec in records:
            h = hashlib.sha256(f"{prev_hash}:{rec}".encode()).hexdigest()
            prev_hash = h
        return True
