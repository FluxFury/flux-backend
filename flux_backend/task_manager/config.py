from datetime import timedelta

broker_url = "redis://redis:6379/0"
result_backend = "redis://redis:6379/1"

broker_connection_retry_on_startup = True

timezone = 'UTC'

CELERY_BEAT_SCHEDULE = {
    "create_matches": {
        "task": "flux_backend.task_manager.tasks.cr_matches_chain",
        "schedule": timedelta(minutes=3),
        "args": ()
    },
    "update_matches": {
        "task": "flux_backend.task_manager.tasks.u_matches_chain",
        "schedule": timedelta(minutes=2),
        "args": ()
    },
    "create_news": {
        "task": "flux_backend.task_manager.tasks.news_spider_chain",
        "schedule": timedelta(minutes=2),
        "args": ()
    },
    "create_past_matches": {
        "task": "flux_backend.task_manager.tasks.past_matches_spider_chain",
        "schedule": timedelta(minutes=5),
        "args": ()
    },
    "create_players": {
        "task": "flux_backend.task_manager.tasks.players_spider_chain",
        "schedule": timedelta(minutes=60),
        "args": ()
    },
    "create_teams": {
        "task": "flux_backend.task_manager.tasks.teams_spider_chain",
        "schedule": timedelta(minutes=30),
        "args": ()
    },
    "update_tournaments": {
        "task": "flux_backend.task_manager.tasks.u_tournaments_spider_chain",
        "schedule": timedelta(minutes=10),
        "args": ()
    }
    
}
