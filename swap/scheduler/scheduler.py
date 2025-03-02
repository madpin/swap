from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from swap.config import settings
from swap.scheduler.tasks import send_notification, sync_calendars
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from swap.utils.logger import logger

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
    """Start the scheduler and add default jobs"""
    try:
        # Schedule calendar sync job (every 30 minutes by default)
        scheduler.add_job(
            sync_calendars,
            trigger=IntervalTrigger(minutes=30),
            id='calendar_sync',
            name='Calendar Synchronization',
            replace_existing=True
        )
        
        logger.info("Starting scheduler with default jobs")
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

def schedule_notification(cron_expression: str, message: str, recipients: list[str] = None):
    """
    Schedule a new notification job.
    
    Args:
        cron_expression: Cron expression for scheduling
        message: Message to send
        recipients: List of recipient identifiers
    """
    try:
        job_id = f"notification_{message[:20]}_{cron_expression}"  # Create unique job ID
        logger.info(f"Scheduling notification job {job_id} with cron: {cron_expression}")
        
        scheduler.add_job(
            send_notification,
            trigger=CronTrigger.from_crontab(cron_expression),
            id=job_id,
            name=f"Notification: {message[:30]}",
            args=[message, recipients],
            replace_existing=True
        )
        return job_id
    except Exception as e:
        logger.error(f"Failed to schedule notification: {e}")
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
