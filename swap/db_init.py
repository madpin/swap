# swap/db_init.py

from sqlmodel import SQLModel
from swap.core.database import engine

from swap.models.rota import Rota  # Import Rota first
from swap.models.calendar import Calendar, Event  # Then Calendar and Event


def create_tables():
    # Drop all existing tables first
    SQLModel.metadata.drop_all(engine)
    # Create all tables
    SQLModel.metadata.create_all(engine)


if __name__ == "__main__":
    create_tables()
