
from flux_orm.database import new_session
from flux_orm import Sport


async def add_cs_sport():
    async with new_session() as session:
        cs = Sport(name="CS2", description="Counter-Strike 2")
        session.add(cs)
        await session.commit()
