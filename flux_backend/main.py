import asyncio
import json
import os
from contextlib import asynccontextmanager

import uvicorn
from aiokafka import AIOKafkaProducer
from fastapi import FastAPI
from flux_orm import Match, RawNews
from flux_orm.database import new_session
from flux_orm.models.enums import PipelineStatus
from sqlalchemy import select

from flux_backend.api.routers import all_routers
from flux_backend.custom_logger import logger
from flux_orm.models.utils import model_to_dict, utcnow_naive

NEWS_TOPIC     = "CS2_raw_news"
MATCH_TOPIC    = "CS2_match"
POLL_INTERVAL   = 10          # секунд
MAX_BATCH       = 500         # строк за один проход
TIME_THRESHOLD  = 5  

KAFKA_BOOTSTRAP_SERVER = os.environ.get("KAFKA_BOOTSTRAP_SERVER")


async def _poll_and_publish(producer: AIOKafkaProducer, stop: asyncio.Event):
    """Фоновая корутина: публикуем RawNews + Match"""
    logger.info(f"Starting Kafka producer polling loop with interval {POLL_INTERVAL}s")
    while not stop.is_set():
        try:
            async with new_session() as session:

                news_rows = (await session.execute(
                    select(RawNews)
                    .where(RawNews.pipeline_status == "NEW")
                    .limit(MAX_BATCH)
                )).scalars().all()

                logger.info(f"Found {len(news_rows)} RawNews records to publish to Kafka")
                for row in news_rows:
                    logger.debug(f"Publishing RawNews with ID {row.raw_news_id} to topic {NEWS_TOPIC}")
                    # Convert SQLAlchemy model to dictionary
                    row_dict = model_to_dict(row)
                    await producer.send(
                        NEWS_TOPIC,
                        key=str(row.raw_news_id).encode(),                # UUID как key
                        value=json.dumps(row_dict).encode()
                    )
                    row.pipeline_status      = PipelineStatus.SENT
                    row.pipeline_update_time = utcnow_naive()

                match_rows = (await session.execute(
                    select(Match)
                    .where(Match.pipeline_status == "NEW")
                    .limit(MAX_BATCH)
                )).scalars().all()

                logger.info(f"Found {len(match_rows)} Match records to publish to Kafka")
                for row in match_rows:
                    logger.debug(f"Publishing Match with ID {row.match_id} to topic {MATCH_TOPIC}")
                    # Convert SQLAlchemy model to dictionary
                    row_dict = model_to_dict(row)
                    await producer.send(
                        MATCH_TOPIC,
                        key=str(row.match_id).encode(),
                        value=json.dumps(row_dict).encode()
                    )
                    row.pipeline_status      = PipelineStatus.SENT
                    row.pipeline_update_time = utcnow_naive()

                if news_rows or match_rows:
                    logger.info(f"Flushing Kafka producer after sending {len(news_rows)} news and {len(match_rows)} match records")
                    await producer.flush()
                
                await session.commit()
        except Exception as exc:
            logger.exception("Producer loop error: %s", exc)

        logger.debug(f"Waiting for {POLL_INTERVAL}s before next poll")
        await asyncio.sleep(POLL_INTERVAL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Запускаем producer и фоновый loop"""
    logger.info(f"Initializing Kafka producer with bootstrap servers: {KAFKA_BOOTSTRAP_SERVER}")
    producer  = AIOKafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVER)
    
    logger.info("Starting Kafka producer")
    await producer.start()
    logger.info("Kafka producer started successfully")

    stop_evt  = asyncio.Event()
    logger.info("Starting background polling task")
    bg_task   = asyncio.create_task(_poll_and_publish(producer, stop_evt))

    try:
        yield {"producer": producer}
    finally:
        logger.info("Shutting down Kafka producer")
        stop_evt.set()
        logger.info("Waiting for background polling task to complete")
        await bg_task
        logger.info("Stopping Kafka producer")
        await producer.stop()
        logger.info("Kafka producer stopped successfully")

app = FastAPI(lifespan=lifespan, title="Fluxfury Backend")

for router in all_routers:
    app.include_router(router)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        workers=1,
        log_config=None,
        log_level=None,
    )