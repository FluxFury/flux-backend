from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Depends
from flux_orm.database import new_session
from flux_orm.models.models import Match, MatchStatus, Sport, Competition
from schemas.cs.schemas import (
    CompetitionOut,
    MatchOut,
    SportOut,
)
from sqlalchemy.orm import joinedload
from sqlalchemy import select, func, or_
from utils.utils import common_pagination_params
from typing import Annotated
from math import ceil
from schemas.cs.schemas import Page, PageMeta
from flux_orm.models.enums import MatchStatusEnum
from flux_orm.models.models import FilteredMatchInNews
router = APIRouter(
    prefix="/main_page",
    tags=["main_page"],
)

@router.get("/sports", response_model=list[SportOut])
async def get_all_sports():
    """
    Returns a list of all sports from the database.
    """
    async with new_session() as session:
        stmt = select(Sport)
        result = await session.execute(stmt)
        sports_list = result.scalars().all()
        return sports_list


@router.get("/statuses", response_model=list[MatchStatusEnum])
async def get_match_statuses_for_sport():
    """
    Returns a list of all statuses from the database.
    """
    return [status.value for status in MatchStatusEnum]


@router.get("/sports/{sport_id}/competitions", response_model=list[CompetitionOut])
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


@router.get("/matches", response_model=Page[MatchOut])
async def list_matches(
    pagination: Annotated[dict, Depends(common_pagination_params)],
    sport_id:       UUID | None = Query(None),
    competition_id: UUID | None = Query(None),      # ← NEW
    status_id:      UUID | None = Query(None),
    status:         str  | None = Query(None),
    search:         str  | None = Query(None),
):
    """
    Выдаёт матчи (можно отфильтровать по виду спорта
    и/или статусу), отсортированные по planned_start_datetime ASC.
    """
    async with new_session() as session:
        # ----------------------------------
        # 1. базовый запрос
        stmt = (
            select(
                Match,
                MatchStatus.name.label("status_name"),
                Competition.name.label("competition_name"),
                func.count(FilteredMatchInNews.news_id).label("news_count")
            )
            .outerjoin(MatchStatus,    Match.status_id      == MatchStatus.status_id)
            .outerjoin(Competition,    Match.competition_id == Competition.competition_id)
            .outerjoin(FilteredMatchInNews, FilteredMatchInNews.match_id == Match.match_id)
            .group_by(
                Match.match_id,
                MatchStatus.name,
                Competition.name
            ))

        # ----------------------------------
        # 2. динамические фильтры
        if sport_id:
            stmt = stmt.where(Match.sport_id == sport_id)
            
        if competition_id:                           # ← NEW
            stmt = stmt.where(Match.competition_id == competition_id)

        if status_id:
            stmt = stmt.where(Match.status_id == status_id)
        elif status:
            statuses = map(lambda x: x.lower(), status.split(","))
            stmt = stmt.where(MatchStatus.name.in_(statuses))
        
        if search:
            term = f"%{search.lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(Match.pretty_match_name).like(term),
                    func.lower(Match.match_name).like(term)
                )
            )
        # ----------------------------------
        # 3. сортировка
        stmt = stmt.order_by(Match.planned_start_datetime.asc())

        # ----------------------------------
        # 4. пагинация
        page     = pagination["page"]
        page_sz  = pagination["page_size"]
        offset   = (page - 1) * page_sz

        # 4a. посчитать total (выглядит длинно, но это один SQL)
        total_subq = stmt.with_only_columns(func.count()).order_by(None)
        total_items = await session.scalar(total_subq)
        if total_items is None:
            total_items = 0

        stmt = stmt.limit(page_sz).offset(offset)
        rows = (await session.execute(stmt)).all()

        # ----------------------------------
        # 5. сборка ответа
        items = [
            MatchOut(
                match_id = m.match_id,
                match_name = m.match_name,
                pretty_match_name = m.pretty_match_name,
                match_url = m.match_url,
                tournament_url = m.tournament_url,
                external_id = m.external_id,
                planned_start_datetime = m.planned_start_datetime,
                end_datetime = m.end_datetime,
                status_id = m.status_id,
                status_name = status_name,
                competition_name = competition_name,
                created_at = m.created_at,
                updated_at = m.updated_at,
                news_count = news_count,
            ) for m, status_name, competition_name, news_count in rows
        ]

        return Page[MatchOut](
            data = items,
            meta = PageMeta(
                page         = page,
                page_size    = page_sz,
                total_items  = total_items,
                total_pages  = ceil(total_items / page_sz) if total_items else 1,
            ),
        )
