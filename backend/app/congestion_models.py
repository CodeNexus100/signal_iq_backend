"""Models for graph-aware congestion detection."""
from enum import Enum
from typing import List

from pydantic import BaseModel


class CongestionLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class CongestionResponse(BaseModel):
    """Response for GET /traffic/congestion/{intersection_id}."""
    intersection_id: str
    level: CongestionLevel
    base_level: CongestionLevel
    escalated: bool
    downstream_blocked: bool
    load_score: int
    downstream_intersection_ids: List[str]
