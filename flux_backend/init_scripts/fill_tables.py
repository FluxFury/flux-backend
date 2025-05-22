from flux_orm.database import new_session
from flux_orm import Sport
from sqlalchemy.dialects.postgresql import insert  # именно postgresql.insert


async def upsert_cs_sport() -> None:
    async with new_session() as session:
        stmt = (
            insert(Sport)
            .values(name="CS2", description="Counter-Strike 2")
            .on_conflict_do_update(
                index_elements=["name"], set_={"description": "Counter-Strike 2"}
            )
        )
        await session.execute(stmt)
        await session.commit()
