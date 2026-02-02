"""Models for graph-safe signal timing decisions."""
from typing import Literal

from pydantic import BaseModel

from .congestion_models import CongestionLevel


class SignalTimingResponse(BaseModel):
    """Response for GET /traffic/signal/{intersection_id}."""

    intersection_id: str
    active_axis: Literal["X", "Z"]
    green_time: int
    red_time: int
    level: CongestionLevel
    downstream_blocked: bool

