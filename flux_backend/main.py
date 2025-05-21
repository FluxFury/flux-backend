import asyncio
import os
from contextlib import asynccontextmanager

import uvicorn
from aiokafka import AIOKafkaProducer
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from flux_backend.kafka_utils import poll_and_publish
from flux_backend.api.routers import all_routers
from flux_backend.custom_logger import logger
from flux_backend.init_scripts.fill_tables import upsert_cs_sport


KAFKA_BOOTSTRAP_SERVER = os.environ.get("KAFKA_BOOTSTRAP_SERVER", "localhost:9092")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Запускаем producer и фоновый loop"""
    logger.info("Adding cs2 sport")
    await upsert_cs_sport()

    logger.info(f"Initializing Kafka producer with bootstrap servers: {KAFKA_BOOTSTRAP_SERVER}")
    producer  = AIOKafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVER)
    
    logger.info("Starting Kafka producer")
    try:
        await producer.start()
        logger.info("Kafka producer started successfully")
    except Exception as e:
        logger.error(f"Error starting Kafka producer: {e}")
        raise e

    stop_evt  = asyncio.Event()
    logger.info("Starting background polling task")
    bg_task   = asyncio.create_task(poll_and_publish(producer, stop_evt))

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

app = FastAPI(lifespan=lifespan, title="FluxFury Backend")

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    # сюда добавите прод-домены
]

app.add_middleware(
    CORSMiddleware,
    allow_origins     = origins,
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)


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