from fastapi import APIRouter, HTTPException
from swap.scheduler.scheduler import scheduler, schedule_notification
from swap.models.notification import NotificationRequest
from apscheduler.job import Job
from typing import List, Optional

router = APIRouter(prefix="/scheduler", tags=["scheduler"])

@router.post('/schedule-notification')
async def schedule_notification_endpoint(request: NotificationRequest):
    """Schedule a new notification task."""
    try:
        schedule_notification(request.cron_expression, request.message)
        return {'status': 'Notification scheduled successfully'}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get('/tasks')
async def list_scheduled_tasks() -> List[dict]:
    """List all scheduled tasks."""
    try:
        jobs = scheduler.get_jobs()
        return [{
            'id': job.id,
            'name': job.name,
            'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
            'trigger': str(job.trigger),
            'args': job.args
        } for job in jobs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete('/tasks/{task_id}')
async def delete_scheduled_task(task_id: str):
    """Delete a scheduled task by its ID."""
    try:
        job = scheduler.get_job(task_id)
        if not job:
            raise HTTPException(status_code=404, detail='Task not found')
        scheduler.remove_job(task_id)
        return {'status': f'Task {task_id} deleted successfully'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put('/tasks/{task_id}')
async def update_scheduled_task(task_id: str, request: NotificationRequest):
    """Update an existing scheduled task."""
    try:
        job = scheduler.get_job(task_id)
        if not job:
            raise HTTPException(status_code=404, detail='Task not found')
        
        # Remove the existing job
        scheduler.remove_job(task_id)
        
        # Schedule a new job with updated parameters
        schedule_notification(request.cron_expression, request.message)
        
        return {'status': f'Task {task_id} updated successfully'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post('/pause')
async def pause_scheduler():
    """Pause the scheduler."""
    try:
        scheduler.pause()
        return {'status': 'Scheduler paused successfully'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post('/resume')
async def resume_scheduler():
    """Resume the scheduler."""
    try:
        scheduler.resume()
        return {'status': 'Scheduler resumed successfully'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))