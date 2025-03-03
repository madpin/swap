# swap/db_init.py

from sqlmodel import SQLModel
from swap.core.database import engine

from swap.models.rota import Rota  # Import Rota first
from swap.models.calendar import Calendar, Event  # Then Calendar and Event

def create_records():
    # Create a new Rota instance
    new_rota = Rota(
        name="New Rota",
        description="This is a new rota",
        start_date="2021-01-01",
        end_date="2023-12-31",
        is_active=True,
    )
    
def create_tables():
    # Drop all existing tables first
    SQLModel.metadata.drop_all(engine)
    # Create all tables
    SQLModel.metadata.create_all(engine)


if __name__ == "__main__":
    create_tables()
