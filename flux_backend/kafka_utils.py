from flux_orm.models.utils import model_to_dict, utcnow_naive
from flux_orm import Match, RawNews
from flux_orm.database import new_session
from flux_orm.models.enums import PipelineStatus
from sqlalchemy import select
import json
from aiokafka import AIOKafkaProducer
import asyncio
from flux_backend.custom_logger import logger

NEWS_TOPIC = "CS2_raw_news"
MATCH_TOPIC = "CS2_match"
POLL_INTERVAL = 10  # секунд
MAX_BATCH = 500  # строк за один проход
TIME_THRESHOLD = 5


async def poll_and_publish(producer: AIOKafkaProducer, stop: asyncio.Event):
    """Фоновая корутина: публикуем RawNews + Match"""
    logger.info(f"Starting Kafka producer polling loop with interval {POLL_INTERVAL}s")
    while not stop.is_set():
        try:
            async with new_session() as session:
                news_rows = (
                    (
                        await session.execute(
                            select(RawNews)
                            .where(RawNews.pipeline_status == "NEW")
                            .limit(MAX_BATCH)
                        )
                    )
                    .scalars()
                    .all()
                )

                logger.info(
                    f"Found {len(news_rows)} RawNews records to publish to Kafka"
                )
                for row in news_rows:
                    logger.debug(
                        f"Publishing RawNews with ID {row.raw_news_id} to topic {NEWS_TOPIC}"
                    )
                    # Convert SQLAlchemy model to dictionary
                    row_dict = model_to_dict(row)
                    await producer.send(
                        NEWS_TOPIC,
                        key=str(row.raw_news_id).encode(),  # UUID как key
                        value=json.dumps(row_dict).encode(),
                    )
                    row.pipeline_status = PipelineStatus.SENT
                    row.pipeline_update_time = utcnow_naive()

                match_rows = (
                    (
                        await session.execute(
                            select(Match)
                            .where(Match.pipeline_status == "NEW")
                            .limit(MAX_BATCH)
                        )
                    )
                    .scalars()
                    .all()
                )

                logger.info(
                    f"Found {len(match_rows)} Match records to publish to Kafka"
                )
                for row in match_rows:
                    logger.debug(
                        f"Publishing Match with ID {row.match_id} to topic {MATCH_TOPIC}"
                    )
                    # Convert SQLAlchemy model to dictionary
                    row_dict = model_to_dict(row)
                    await producer.send(
                        MATCH_TOPIC,
                        key=str(row.match_id).encode(),
                        value=json.dumps(row_dict).encode(),
                    )
                    row.pipeline_status = PipelineStatus.SENT
                    row.pipeline_update_time = utcnow_naive()

                if news_rows or match_rows:
                    logger.info(
                        f"Flushing Kafka producer after sending {len(news_rows)} news and {len(match_rows)} match records"
                    )
                    await producer.flush()

                await session.commit()
        except Exception as exc:
            logger.exception("Producer loop error: %s", exc)

        logger.debug(f"Waiting for {POLL_INTERVAL}s before next poll")
        await asyncio.sleep(POLL_INTERVAL)
