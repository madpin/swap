from contextlib import asynccontextmanager
from fastapi import FastAPI
from swap.scheduler import scheduler
from swap.scheduler.scheduler import start_scheduler, stop_scheduler
from swap.api.v1.endpoints import router as api_router
from swap.utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Hello, the answer is 42!")
    start_scheduler()
    yield
    logger.info("Thanks for the fish!")
    stop_scheduler()


app = FastAPI(lifespan=lifespan)
app.include_router(api_router)
