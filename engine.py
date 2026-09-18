from dataclasses import dataclass
from typing import Tuple

@dataclass
class DataObject:
    file_id: str
    name: str
    size_mb: float
    days_since_last_access: int
    days_old: int
    is_duplicate: bool
    dependency_count: int
    is_legal_or_compliance: bool
    predicted_reaccess_prob: float

class LifecycleValuationEngine:
    def __init__(self, w_prob=35.0, w_legal=30.0, w_dep=25.0, w_cost=10.0):
        self.w_prob = float(w_prob)
        self.w_legal = float(w_legal)
        self.w_dep = float(w_dep)
        self.w_cost = float(w_cost)

    def evaluate(self, obj: DataObject) -> Tuple[str, float, str]:
        # Safety floor for legal documents
        if obj.is_legal_or_compliance and obj.days_since_last_access > 730:
            return (
                "Deep Archive",
                68.0,
                f"Statutory compliance requirement. Inactive for {obj.days_since_last_access} days, but retained for regulatory audit."
            )

        # Multi-factor score calculation
        prob_score = obj.predicted_reaccess_prob * self.w_prob
        legal_score = (100.0 if obj.is_legal_or_compliance else 0.0) * (self.w_legal / 100.0)
        dep_score = min(obj.dependency_count * 5.0, 100.0) * (self.w_dep / 100.0)
        cost_penalty = min(obj.size_mb / 1024.0, 10.0) * (self.w_cost / 10.0)

        uri = max(0.0, min(100.0, prob_score + legal_score + dep_score - cost_penalty))

        # Tier assignment
        if obj.is_duplicate and not obj.is_legal_or_compliance and obj.dependency_count == 0:
            tier = "Deletion Candidate"
            reason = f"Duplicate file with zero dependencies and no legal hold. Safe for 90-day quarantine."
        elif uri >= 65.0 or obj.days_since_last_access < 45:
            tier = "Active"
            reason = f"High utility score ({uri:.1f}) and recent access. Keep in fast storage."
        elif 40.0 <= uri < 65.0:
            tier = "Archived"
            reason = f"Idle for {obj.days_since_last_access} days, but linked to {obj.dependency_count} dependencies. Store in warm archive."
        elif 20.0 <= uri < 40.0:
            tier = "Deep Archive"
            reason = f"Low re-demand probability, but contains unique history. Preserved in cold tier."
        else:
            tier = "Review"
            reason = f"Low utility index ({uri:.1f}) without duplication flags. Sent to user review queue."

        return tier, round(uri, 1), reason