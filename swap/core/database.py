# # swap/core/database.py
# from sqlmodel import create_engine, Session
# from sqlalchemy.pool import QueuePool
# from swap.config import settings
# from swap.utils.logger import logger
# from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

# async_engine = create_async_engine(
#     settings.sqlite.database_url, echo=settings.debug, pool_pre_ping=True
# )

# engine = create_engine(
#     settings.sqlite.database_url,
#     poolclass=QueuePool,
#     pool_size=5,
#     max_overflow=10,
#     pool_timeout=30,
# )


# engine = create_engine(settings.sqlite.database_url)


# def get_db():
#     try:
#         db = Session(engine)
#         db.exec("SELECT 1")  # Test connection
#         yield db
#     except Exception as e:
#         logger.error(f"Database connection error: {e}")
#         raise
#     finally:
#         db.close()


# async def get_async_db():
#     async with AsyncSession(async_engine) as session:
#         yield session


# def check_database_health():
#     try:
#         with Session(engine) as session:
#             session.exec("SELECT 1")
#         return True
#     except Exception:
#         return False

# swap/core/database.py
from sqlmodel import create_engine, Session
from sqlalchemy.pool import QueuePool
from swap.config import settings
from swap.utils.logger import logger

engine = create_engine(
    settings.database_url,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
)


def get_db():
    try:
        db = Session(engine)
        yield db
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise
    finally:
        db.close()


def check_database_health():
    try:
        with Session(engine) as session:
            session.exec("SELECT 1")
        return True
    except Exception:
        return False
