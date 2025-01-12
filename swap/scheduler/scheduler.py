from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from swap.config import settings
from swap.scheduler.tasks import send_notification
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from swap.utils.logger import logger

logger.info(f"settings.task_store_url = {settings.task_store_url}")
scheduler = AsyncIOScheduler(
    timezone=settings.scheduler_timezone,
    jobstores={"default": SQLAlchemyJobStore(url=settings.task_store_url)},
    
)


def start_scheduler():
    scheduler.start()


def stop_scheduler():
    scheduler.shutdown()


def schedule_notification(cron_expression: str, message: str):
    logger.info(f"Scheduling notification with cron expression: {cron_expression}")
    scheduler.add_job(
        send_notification,
        trigger=CronTrigger.from_crontab(cron_expression),
        args=[message],
    )
