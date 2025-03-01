from datetime import datetime


async def send_notification(message: str = ""):
    print(f"Event: {datetime.now()} - {message}")
