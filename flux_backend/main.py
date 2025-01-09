from contextlib import asynccontextmanager

import uvicorn
from api.routers import all_routers
from fastapi import FastAPI
from flux_orm.database import create_tables, delete_tables

from init_scripts.fill_tables import add_cs_sport

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("База готова")
    yield
    print("База очищена")

app = FastAPI(lifespan=lifespan)

for router in all_routers:
    app.include_router(router)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        workers=1
    )