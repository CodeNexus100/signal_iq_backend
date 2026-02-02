"""Pydantic models for city topology (intersections and roads)."""
from typing import Optional

from pydantic import BaseModel, Field


class Position(BaseModel):
    """Geographic or cartesian position."""
    lat: float = Field(..., description="Latitude or X coordinate")
    lng: float = Field(..., description="Longitude or Y coordinate")


class IntersectionCreate(BaseModel):
    """Schema for creating an intersection."""
    intersection_id: str = Field(..., min_length=1)
    name: Optional[str] = None
    position: Optional[Position] = None


class IntersectionResponse(BaseModel):
    """Schema for intersection in API responses."""
    intersection_id: str
    name: Optional[str] = None
    position: Optional[Position] = None


class RoadCreate(BaseModel):
    """Schema for creating a directed road (edge)."""
    from_intersection_id: str = Field(..., description="Source intersection ID")
    to_intersection_id: str = Field(..., description="Target intersection ID")
    road_id: Optional[str] = None
    length_m: Optional[float] = None
    name: Optional[str] = None


class RoadResponse(BaseModel):
    """Schema for road in API responses."""
    road_id: str
    from_intersection_id: str
    to_intersection_id: str
    length_m: Optional[float] = None
    name: Optional[str] = None
