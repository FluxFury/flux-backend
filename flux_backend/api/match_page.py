from uuid import UUID
from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from typing import Annotated
from math import ceil
from sqlalchemy import func
from flux_orm.database import new_session
from flux_orm.models.models import (
    Match,
    MatchStatus,
    Team,
    Sport,
    FormattedNews,
    FilteredMatchInNews,
    Competition,
)

from flux_backend.utils.utils import common_pagination_params, has_any, order_clause

from schemas.cs.schemas import (
    Page,
    PageMeta,
    MatchEventOut,
)

router = APIRouter(prefix="/match_page", tags=["match_page"])


@router.get("/matches/{match_id}")
async def get_match_details(match_id: UUID):
    async with new_session() as session:
        stmt = (
            select(
                Match,
                MatchStatus.name.label("status_name"),
                Competition.name.label("competition_name"),
                Competition.image_url.label("competition_logo_url"),
            )
            .outerjoin(MatchStatus, Match.status_id == MatchStatus.status_id)
            .outerjoin(Competition, Match.competition_id == Competition.competition_id)
            .where(Match.match_id == match_id)
        )
        result = await session.execute(stmt)
        row = result.one_or_none()
        if not row:
            raise HTTPException(status_code=404, detail="Match not found")
        match_obj, status_name, competition_name, competition_logo_url = row
        return {
            "match_id": str(match_obj.match_id),
            "match_name": match_obj.match_name,
            "pretty_match_name": match_obj.pretty_match_name,
            "planned_start_datetime": match_obj.planned_start_datetime,
            "end_datetime": match_obj.end_datetime,
            "status_name": status_name,
            "competition_name": competition_name,
            "competition_logo_url": competition_logo_url,
            "created_at": match_obj.created_at,
            "updated_at": match_obj.updated_at,
        }


@router.get("/matches/{match_id}/teams")
async def get_match_teams_and_rosters(match_id: UUID):
    async with new_session() as session:
        stmt = (
            select(Match)
            .options(
                joinedload(Match.match_teams).options(joinedload(Team.members)),
                joinedload(Match.match_status),
            )
            .filter_by(match_id=match_id)
        )
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
                "team_name": t.pretty_name if t.pretty_name else t.name,
                "main_roster": [
                    {
                        "player_id": str(m.player_id),
                        "name": m.name,
                        "nickname": m.nickname,
                        "age": m.age,
                        "country": m.country,
                        "status": m.stats.get("status"),
                    }
                    for m in members
                ],
            })
        match_score = match_obj.match_status.status
        teams_data[0]["score"], teams_data[1]["score"] = (
            match_score["team1_score"],
            match_score["team2_score"],
        )
        return teams_data


# ---------- endpoint ---------------------------------------------------------
@router.get(
    "/matches/{match_id}/events",
    response_model=Page[MatchEventOut],
)
async def list_match_events(
    match_id: UUID,
    pagination: Annotated[dict, Depends(common_pagination_params)],
    people: list[str] | None = Query(None),
    orgs: list[str] | None = Query(None),
    locations: list[str] | None = Query(None),
    events_kw: list[str] | None = Query(None, alias="events"),
    others: list[str] | None = Query(None, alias="other"),
    order: str = Query(
        "-timestamp", description="timestamp | -timestamp | title | ..."
    ),
):
    async with new_session() as session:
        # проверяем, что матч существует (быстрая ошибка 404)
        if not await session.get(Match, match_id):
            raise HTTPException(404, "Match not found")

        # ---------------- базовый select ----------------
        stmt = (
            select(FormattedNews, FilteredMatchInNews.respective_relevance)
            .join(
                FilteredMatchInNews,
                FilteredMatchInNews.news_id == FormattedNews.formatted_news_id,
            )
            .where(FilteredMatchInNews.match_id == match_id)
        )
        if people:
            stmt = stmt.where(has_any(FormattedNews.keywords["People"], people))
        if orgs:
            stmt = stmt.where(has_any(FormattedNews.keywords["Organizations"], orgs))
        if locations:
            stmt = stmt.where(has_any(FormattedNews.keywords["Locations"], locations))
        if events_kw:
            stmt = stmt.where(has_any(FormattedNews.keywords["Events"], events_kw))
        if others:
            stmt = stmt.where(has_any(FormattedNews.keywords["Other"], others))

        # --- фасеты
        async def facet(cat: str):
            elem = func.jsonb_array_elements_text(FormattedNews.keywords[cat]).label(
                "kw"
            )
            q = (
                select(elem, func.count())
                .join(
                    FilteredMatchInNews,
                    FilteredMatchInNews.news_id == FormattedNews.formatted_news_id,
                )
                .where(FilteredMatchInNews.match_id == match_id)
                .group_by(elem)
            )
            return [{"keyword": k, "count": c} for k, c in await session.execute(q)]

        stmt = stmt.order_by(order_clause(FormattedNews, order))

        # ---------------- пагинация ---------------------
        page = pagination["page"]
        page_size = pagination["page_size"]
        offset = (page - 1) * page_size

        total_items = await session.scalar(
            select(func.count()).select_from(stmt.subquery())
        )
        if total_items is None:
            total_items = 0

        rows = (await session.execute(stmt.limit(page_size).offset(offset))).all()

        data = []
        # ---------------- сборка dto --------------------
        for news, relevance in rows:
            # Создаём DTO, подставляя relevance вручную:
            item = MatchEventOut.model_validate(
                {
                    **news.__dict__,
                    "respective_relevance": relevance,
                },
                from_attributes=True,
            )
            data.append(item)
        # ---------------- фасеты для сайдбара -----------
        # даты
        dates_q = (
            select(
                func.date_trunc("day", FormattedNews.news_creation_time).label("d"),
                func.count(),
            )
            .join(
                FilteredMatchInNews,
                FilteredMatchInNews.news_id == FormattedNews.formatted_news_id,
            )
            .where(FilteredMatchInNews.match_id == match_id)
            .group_by("d")
            .order_by("d")
        )

        dates_facet = [
            {"date": d.date(), "count": c} for d, c in await session.execute(dates_q)
        ]

        facets = {
            "available_dates": dates_facet,
            "people": await facet("People"),
            "orgs": await facet("Organizations"),
            "locations": await facet("Locations"),
            "events": await facet("Events"),
            "other": await facet("Other"),
        }

        return Page[MatchEventOut](
            data=data,
            meta=PageMeta(
                page=page,
                page_size=page_size,
                total_items=total_items,
                total_pages=ceil(total_items / page_size) if total_items else 1,
            ),
            facets=facets,
        )


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
            "updated_at": sport_obj.updated_at,
        }
