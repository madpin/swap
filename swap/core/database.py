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
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from contextlib import contextmanager
from swap.config import settings
from swap.utils.logger import logger

# Sync engine with improved configuration
engine = create_engine(
    settings.database_url,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=settings.system.app_env == "development"
)

# For SQLite, we don't use async operations
if settings.database_url.startswith('sqlite'):
    async_engine = None
else:
    # Async engine only for PostgreSQL
    async_engine = create_async_engine(
        settings.database_url.replace('postgresql://', 'postgresql+asyncpg://'),
        pool_size=20,
        max_overflow=30,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=settings.system.app_env == "development"
    )

@contextmanager
def get_db():
    """Synchronous database session context manager"""
    db = Session(engine)
    try:
        yield db
        db.commit()
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

async def get_async_db():
    """Asynchronous database session context manager"""
    if async_engine is None:
        # Fall back to sync session for SQLite
        with get_db() as session:
            yield session
    else:
        async with AsyncSession(async_engine) as session:
            try:
                yield session
            except Exception as e:
                logger.error(f"Async database connection error: {e}")
                await session.rollback()
                raise

def check_database_health():
    """Check database connectivity and health"""
    try:
        with get_db() as session:
            from sqlalchemy import text
            session.exec(text("SELECT 1 as result")).first()
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False
