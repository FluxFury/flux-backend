from typing import Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from datetime import datetime

from flux_orm.database import new_session
from flux_orm.models.models import (
    Match,
    MatchStatus,
    Team,
    TeamMember,
    Sport,
)

from schemas.cs.schemas import (
    MatchOut,
    SportOut
)

router = APIRouter(
    prefix="/match_page",
    tags=["match_page"]
)

@router.get("/matches/{match_id}")
async def get_match_details(match_id: UUID):
    async with new_session() as session:
        stmt = (
            select(Match, MatchStatus.name.label("status_name"))
            .outerjoin(MatchStatus, Match.status_id == MatchStatus.status_id)
            .where(Match.match_id == match_id)
        )
        result = await session.execute(stmt)
        row = result.one_or_none()
        if not row:
            raise HTTPException(status_code=404, detail="Match not found")
        match_obj, status_name = row
        return {
            "match_id": str(match_obj.match_id),
            "match_name": match_obj.match_name,
            "pretty_match_name": match_obj.pretty_match_name,
            "planned_start_datetime": match_obj.planned_start_datetime,
            "end_datetime": match_obj.end_datetime,
            "status_name": status_name,
            "created_at": match_obj.created_at,
            "updated_at": match_obj.updated_at
        }

@router.get("/matches/{match_id}/teams")
async def get_match_teams_and_rosters(match_id: UUID):
    async with new_session() as session:
        stmt = select(Match).options(joinedload(Match.match_teams).options(joinedload(Team.members))).filter_by(match_id=match_id)
        result = await session.execute(stmt)
        match_obj = result.unique().scalar_one_or_none()
        if not match_obj:
            raise HTTPException(status_code=404, detail="Match not found")
        if not match_obj.match_teams:
            return []

        teams_data = []
        for t in match_obj.match_teams:
            members = t.members

            teams_data.append({
                "team_id": str(t.team_id),
                "team_name": t.name,
                "main_roster": [
                    {
                        "player_id": str(m.player_id),
                        "name": m.name,
                        "nickname": m.nickname,
                        "age": m.age,
                        "country": m.country,
                        "status": m.stats.get("status")
                    }
                    for m in members
                ]
            })
        return teams_data

@router.get("/matches/{match_id}/events")
async def get_match_events(
    match_id: UUID,
    sort_by: str = Query("date", pattern="^(date|person|other)$"),
    date_filter: Optional[datetime] = None,
    person_name: Optional[str] = None
):
    async with new_session() as session:
        match_obj = await session.get(Match, match_id)
        if not match_obj:
            raise HTTPException(status_code=404, detail="Match not found")

        # The actual query depends on how you store events.
        # For example, if you have a MatchEvent model:
        # stmt = select(MatchEvent).where(MatchEvent.match_id == match_id)
        # if date_filter is not None: stmt = stmt.where(MatchEvent.timestamp >= date_filter)
        # if person_name is not None: stmt = stmt.where(MatchEvent.person == person_name)
        # if sort_by == "date": stmt = stmt.order_by(MatchEvent.timestamp.desc())
        # if sort_by == "person": stmt = stmt.order_by(MatchEvent.person.asc())
        # ...
        # result = await session.execute(stmt)
        # events = result.scalars().all()

        # Below is only a placeholder response, since the actual logic depends on your model.
        sample_events = [
            {
                "title": "Ronaldo broke his leg",
                "description": "\"My leg is broken\" - Ronaldo said",
                "timestamp": "2020-08-22 18:18:00",
                "person": "Ronaldo"
            },
            {
                "title": "Messi's fan made Haaland cry",
                "description": "Some description...",
                "timestamp": "2020-08-20 18:18:00",
                "person": "Messi's fan"
            }
        ]
        if person_name:
            sample_events = [e for e in sample_events if e["person"] == person_name]
        # This does not handle date filtering or a real model. Example only.

        if sort_by == "date":
            sample_events.sort(key=lambda x: x["timestamp"], reverse=True)
        elif sort_by == "person":
            sample_events.sort(key=lambda x: x["person"])

        return sample_events

@router.get("/sports/{sport_id}")
async def get_sport_details(sport_id: UUID):
    async with new_session() as session:
        stmt = select(Sport).where(Sport.sport_id == sport_id)
        result = await session.execute(stmt)
        sport_obj = result.scalar_one_or_none()
        if not sport_obj:
            raise HTTPException(status_code=404, detail="Sport not found")
        return {
            "sport_id": str(sport_obj.sport_id),
            "name": sport_obj.name,
            "description": sport_obj.description,
            "image_url": sport_obj.image_url,
            "created_at": sport_obj.created_at,
            "updated_at": sport_obj.updated_at
        }
