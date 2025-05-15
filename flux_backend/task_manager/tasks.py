# tasks.py
# type: ignore
import time
from typing import Any

from celery import chain
from webnews_parser.schedulers.scheduler import schedule_spider
from webnews_parser.main import scrapyd
from .redis_app import (
    redis_client,
    LOCK_KEY_CR_MATCHES,
    LOCK_TIMEOUT_CR_MATCHES,
    LOCK_KEY_UPDATE_MATCHES,
    LOCK_TIMEOUT_UPDATE_MATCHES,
    LOCK_KEY_NEWS_SPIDER,
    LOCK_TIMEOUT_NEWS_SPIDER,
    LOCK_KEY_PAST_MATCHES_SPIDER,
    LOCK_TIMEOUT_PAST_MATCHES_SPIDER,
    LOCK_KEY_PLAYERS_SPIDER,
    LOCK_TIMEOUT_PLAYERS_SPIDER,
    LOCK_KEY_TEAMS_SPIDER,
    LOCK_TIMEOUT_TEAMS_SPIDER,
    LOCK_KEY_TOURNAMENTS_SPIDER,
    LOCK_TIMEOUT_TOURNAMENTS_SPIDER,
)
from .celery_app import celery_app
from functools import wraps


def with_redis_lock(lock_key: str, lock_timeout: int):

    def decorator(func):
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Acquire the lock
            lock_acquired = redis_client.set(lock_key, "locked", nx=True, ex=lock_timeout)

            if not lock_acquired:
                print("Another chain is still running. Exiting.")
                return
            try:
                # Execute the function (which defines the chain)
                result = func(*args, **kwargs)
                print("Chain scheduled. Lock stays until final step.")
                return result
            except Exception as e:
                # Handle any exceptions that might occur
                print(f"An error occurred: {e}")
                redis_client.delete(lock_key)  # Release the lock in case of an error
                raise
        return wrapper
    return decorator


def is_spider_finished(job_id: str, project_name: str = "webnews_parser") -> bool:
    return scrapyd.job_status(project_name, job_id) in {"finished", "failed"}


@celery_app.task
def run_spider_and_wait(spider_name: str, **kwargs: Any) -> str:
    job_id = schedule_spider(spider_name, **kwargs)
    if not job_id:
        raise ValueError(f"Failed to schedule spider {spider_name}")

    while not is_spider_finished(job_id):
        time.sleep(20)

    return job_id

@celery_app.task
def release_lock(lock_key: str) -> None:
    redis_client.delete(lock_key)

 
@celery_app.task
@with_redis_lock(lock_key=LOCK_KEY_CR_MATCHES, lock_timeout=LOCK_TIMEOUT_CR_MATCHES)
def cr_matches_chain() -> None:
    c = chain(
        run_spider_and_wait.si(spider_name="CSCreateLiveScheduledMatchesSpider"),
        release_lock.si(LOCK_KEY_CR_MATCHES),
    )
    
    c.apply_async()
    
@celery_app.task
@with_redis_lock(lock_key=LOCK_KEY_UPDATE_MATCHES, lock_timeout=LOCK_TIMEOUT_UPDATE_MATCHES)
def u_matches_chain() -> None:
    c = chain(
        run_spider_and_wait.si(spider_name="CSUpdateLiveScheduledMatchesSpider"),
        release_lock.si(LOCK_KEY_UPDATE_MATCHES),
    )
    
    c.apply_async()
    
@celery_app.task
@with_redis_lock(lock_key=LOCK_KEY_NEWS_SPIDER, lock_timeout=LOCK_TIMEOUT_NEWS_SPIDER)
def news_spider_chain() -> None:
    c = chain(
        run_spider_and_wait.si(spider_name="CSNewsSpider"),
        release_lock.si(LOCK_KEY_NEWS_SPIDER),
    )
    
    c.apply_async()
    
@celery_app.task
@with_redis_lock(lock_key=LOCK_KEY_PAST_MATCHES_SPIDER, lock_timeout=LOCK_TIMEOUT_PAST_MATCHES_SPIDER)
def past_matches_spider_chain() -> None:
    c = chain(
        run_spider_and_wait.si(spider_name="CSpMatchesSpider"),
        release_lock.si(LOCK_KEY_PAST_MATCHES_SPIDER),
    )
    
    c.apply_async()

@celery_app.task
@with_redis_lock(lock_key=LOCK_KEY_TEAMS_SPIDER, lock_timeout=LOCK_TIMEOUT_TEAMS_SPIDER)
def teams_spider_chain() -> None:
    c = chain(
        run_spider_and_wait.si(spider_name="CSTeamsSpider"),
        release_lock.si(LOCK_KEY_TEAMS_SPIDER),
    )
    
    c.apply_async()
    
@celery_app.task
@with_redis_lock(lock_key=LOCK_KEY_PLAYERS_SPIDER, lock_timeout=LOCK_TIMEOUT_PLAYERS_SPIDER)
def players_spider_chain() -> None:
    c = chain(
        run_spider_and_wait.si(spider_name="CSPlayersSpider"),
        release_lock.si(LOCK_KEY_PLAYERS_SPIDER),
    )
    
    c.apply_async()
    
@celery_app.task
@with_redis_lock(lock_key=LOCK_KEY_TOURNAMENTS_SPIDER, lock_timeout=LOCK_TIMEOUT_TOURNAMENTS_SPIDER)
def u_tournaments_spider_chain() -> None:
    c = chain(
        run_spider_and_wait.si(spider_name="CSUpdateTournamentsSpider"),
        release_lock.si(LOCK_KEY_TOURNAMENTS_SPIDER),
    )
    
    c.apply_async()