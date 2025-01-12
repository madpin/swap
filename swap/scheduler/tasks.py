from datetime import datetime


async def send_notification(message: str = ""):
    print(f"{datetime.now()} - {message}")
