from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class CompetitionBase(BaseModel):
    """Base schema for competition data."""
    name: str
    prize_pool: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[datetime] = None
    description: Optional[str] = None
    image_url: Optional[str] = None


class CompetitionOut(CompetitionBase):
    """Schema for returning competition data through external endpoints."""
    competition_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MatchStatusBase(BaseModel):
    """Base schema for match status data."""
    name: str
    image_url: Optional[str] = None


class MatchStatusOut(MatchStatusBase):
    """Schema for returning match status data through external endpoints."""
    status_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MatchBase(BaseModel):
    """Base schema for match data."""
    match_name: str
    pretty_match_name: Optional[str] = None
    match_url: Optional[str] = None
    tournament_url: Optional[str] = None
    external_id: str
    planned_start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None


class MatchOut(MatchBase):
    """Schema for returning match data through external endpoints."""
    match_id: UUID
    status_id: Optional[UUID] = None
    status_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SportOut(BaseModel):
    """Schema for returning sport data through external endpoints."""
    sport_id: UUID
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True