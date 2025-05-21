from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Generic, TypeVar, Any
from pydantic.generics import GenericModel

class CompetitionBase(BaseModel):
    """Base schema for competition data."""
    name: str
    prize_pool: str | None = None
    location: str | None = None
    start_date: datetime | None = None
    description: str | None = None
    image_url: str | None = None


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
    image_url: str | None = None


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
    pretty_match_name: str | None = None
    match_url: str | None = None
    tournament_url: str | None = None
    external_id: str
    planned_start_datetime: datetime | None = None
    end_datetime: datetime | None = None


class MatchOut(MatchBase):
    """Schema for returning match data through external endpoints."""
    match_id: UUID
    status_id: UUID | None = None
    status_name: str | None = None
    competition_name: str | None = None
    news_count: int | None = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SportOut(BaseModel):
    """Schema for returning sport data through external endpoints."""
    sport_id: UUID
    name: str
    description: str | None = None
    image_url: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        



T = TypeVar("T")

class PageMeta(BaseModel):
    page: int
    page_size: int
    total_items: int
    total_pages: int

class Page(GenericModel, Generic[T]):
    data: list[T]
    meta: PageMeta
    facets: dict[str, Any] | None = None
    
    
class MatchEventOut(BaseModel):
    event_id:   UUID            = Field(alias="formatted_news_id")
    title:      str | None      = Field(alias="header")
    description:str             = Field(alias="text")
    timestamp:  datetime | None = Field(alias="news_creation_time")
    respective_relevance: int | None = Field(alias="respective_relevance")
    keywords:   dict[str, list[str]]

    class Config:
        from_attributes   = True           # ← главный флаг
        populate_by_name  = True           # чтобы в JSON были ваши «event_id», а не alias-имена