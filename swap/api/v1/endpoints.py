from fastapi import APIRouter, HTTPException, logger
from swap.scheduler.scheduler import schedule_notification
from swap.models.notification import NotificationRequest

from swap.api.v1.scheduler import router as scheduler_router
from swap.services.rota_parser import RotaParser
from swap.api.v1.calendar import router as calendar_router

# Create the main router
router = APIRouter()

# Include the scheduler router
router.include_router(scheduler_router)

# Include the calendar router
router.include_router(calendar_router)



@router.post("/schedule-notification")
async def schedule_notification_endpoint(request: NotificationRequest):
    try:
        schedule_notification(request.cron_expression, request.message)
        print("I've been here")
        return {"status": "Notification scheduled successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/rota")
async def get_rota():
    spreadsheet_id = "1MqJwH59lHhE6q0kmFNkQZzpteRLTQBlX2vKhEhVltHQ"
    range_name = "Combined Rota!A:M"
    # return RotaParser
    rota_parser = RotaParser(
        service_account_file="gcal_service_account.json",
        spreadsheet_id=spreadsheet_id,
        range_name=range_name,
    )
    parsed_rota = rota_parser.parse_rota()
    logger.info(f"Parsed Rota: {parsed_rota}")
    return parsed_rota
