from typing import List
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from flux_orm.database import new_session
from flux_orm.models.models import Match, MatchStatus, Sport
from schemas.cs.schemas import (
    CompetitionOut,
    MatchOut,
    SportOut,
)
from sqlalchemy.orm import joinedload
from sqlalchemy import select

router = APIRouter(
    prefix="/main_page",
    tags=["main_page"],
)

@router.get("/sports", response_model=List[SportOut])
async def get_all_sports():
    """
    Returns a list of all sports from the database.
    """
    async with new_session() as session:
        stmt = select(Sport)
        result = await session.execute(stmt)
        sports_list = result.scalars().all()
        return sports_list



@router.get("/matches", response_model=List[MatchOut])
async def get_all_matches(limit: int = Query(100, ge=1, le=1000)):
    """
    Returns a list of all matches across all sports,
    sorted by updated_at (DESC).
    The `limit` parameter specifies the maximum number of records to return.
    """
    async with new_session() as session:
        stmt = (
            select(Match, MatchStatus.name.label("status_name"))
            .outerjoin(MatchStatus, Match.status_id == MatchStatus.status_id)
            .order_by(Match.updated_at.desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        rows = result.all()

        match_out_list = []
        for match_obj, status_name in rows:
            match_out = MatchOut(
                match_id=match_obj.match_id,
                match_name=match_obj.match_name,
                pretty_match_name=match_obj.pretty_match_name,
                match_url=match_obj.match_url,
                tournament_url=match_obj.tournament_url,
                external_id=match_obj.external_id,
                planned_start_datetime=match_obj.planned_start_datetime,
                end_datetime=match_obj.end_datetime,
                status_id=match_obj.status_id,
                status_name=status_name,
                created_at=match_obj.created_at,
                updated_at=match_obj.updated_at,
            )
            match_out_list.append(match_out)

        return match_out_list



@router.get("/sports/{sport_id}/competitions", response_model=List[CompetitionOut])
async def get_competitions_for_sport(sport_id: UUID):
    """
    Returns a list of competitions associated with the specified sport (sport_id).
    """
    async with new_session() as session:
        stmt = (
            select(Sport)
            .options(joinedload(Sport.competitions))
            .where(Sport.sport_id == sport_id)
        )
        result = await session.execute(stmt)
        sport = result.unique().scalar_one_or_none()
        
        if not sport:
            raise HTTPException(status_code=404, detail="Sport not found")

        return sport.competitions



@router.get("/sports/{sport_id}/matches", response_model=List[MatchOut])
async def get_matches_for_sport(
    sport_id: UUID,
    limit: int = Query(100, ge=1, le=1000),
):
    """
    Returns a list of matches associated with the specified sport (sport_id),
    sorted by updated_at DESC, with an optional limit on how many records to return.
    """
    async with new_session() as session:
        sport = await session.get(Sport, sport_id)
        if not sport:
            raise HTTPException(status_code=404, detail="Sport not found")

        stmt = (
            select(Match, MatchStatus.name.label("status_name"))
            .outerjoin(MatchStatus, Match.status_id == MatchStatus.status_id)
            .where(Match.sport_id == sport_id)
            .order_by(Match.updated_at.desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        rows = result.all()

        match_out_list = []
        for match_obj, status_name in rows:
            match_out = MatchOut(
                match_id=match_obj.match_id,
                match_name=match_obj.match_name,
                pretty_match_name=match_obj.pretty_match_name,
                match_url=match_obj.match_url,
                tournament_url=match_obj.tournament_url,
                external_id=match_obj.external_id,
                planned_start_datetime=match_obj.planned_start_datetime,
                end_datetime=match_obj.end_datetime,
                status_id=match_obj.status_id,
                status_name=status_name,
                created_at=match_obj.created_at,
                updated_at=match_obj.updated_at,
            )
            match_out_list.append(match_out)

        return match_out_list