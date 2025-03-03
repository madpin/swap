from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from swap.config import settings
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from swap.utils.logger import logger
from swap.scheduler.tasks import sync_calendars

logger.info(f"Task store URL: {settings.task_store_url}")

# Initialize scheduler with persistent storage
scheduler = AsyncIOScheduler(
    timezone=settings.scheduler_timezone,
    jobstores={
        "default": SQLAlchemyJobStore(url=settings.task_store_url)
    },
    job_defaults={
        'coalesce': True,  # Combine multiple pending runs into a single run
        'max_instances': 1,  # Prevent multiple instances of the same job from running
        'misfire_grace_time': 60  # Allow jobs to fire up to 60 seconds late
    }
)

def start_scheduler():
    """Start the scheduler"""
    try:
        logger.info("Starting scheduler")
        scheduler.start()
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")
        raise

def stop_scheduler():
    """Shutdown the scheduler gracefully"""
    try:
        logger.info("Shutting down scheduler")
        scheduler.shutdown()
    except Exception as e:
        logger.error(f"Error shutting down scheduler: {e}")
        raise

def add_job(func, trigger, job_id: str, **kwargs):
    """
    Add a job to the scheduler.
    
    Args:
        func: Function to schedule
        trigger: APScheduler trigger
        job_id: Unique identifier for the job
        **kwargs: Additional arguments for scheduler.add_job
    """
    try:
        scheduler.add_job(
            func,
            trigger=trigger,
            id=job_id,
            replace_existing=True,
            **kwargs
        )
        logger.info(f"Added job: {job_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to add job {job_id}: {e}")
        raise

def remove_job(job_id: str) -> bool:
    """
    Remove a scheduled job.
    
    Args:
        job_id: ID of the job to remove
        
    Returns:
        bool: True if job was removed, False if not found
    """
    try:
        scheduler.remove_job(job_id)
        logger.info(f"Removed job: {job_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to remove job {job_id}: {e}")
        return False

def get_jobs():
    """Get all scheduled jobs"""
    try:
        return [
            {
                'id': job.id,
                'name': job.name,
                'next_run_time': job.next_run_time,
                'trigger': str(job.trigger)
            }
            for job in scheduler.get_jobs()
        ]
    except Exception as e:
        logger.error(f"Failed to get jobs: {e}")
        raise
