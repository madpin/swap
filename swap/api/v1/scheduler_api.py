from fastapi import APIRouter, HTTPException
from swap.scheduler.scheduler import add_job, remove_job, get_jobs
from swap.scheduler.tasks import send_notification
from apscheduler.triggers.cron import CronTrigger

router = APIRouter(prefix="/scheduler", tags=["scheduler"])

@router.get("/jobs")
async def list_jobs():
    """List all scheduled jobs"""
    return get_jobs()

@router.post("/jobs/{job_id}/cancel")
async def cancel_job(job_id: str):
    """Cancel a scheduled job"""
    if remove_job(job_id):
        return {"status": "success", "message": f"Job {job_id} cancelled"}
    raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

@router.post("/notification")
async def schedule_notification(message: str, cron: str):
    """Schedule a new notification"""
    try:
        job_id = f"notification_{message[:20]}_{cron}"
        add_job(
            send_notification,
            CronTrigger.from_crontab(cron),
            job_id,
            args=[message]
        )
        return {"status": "success", "job_id": job_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
