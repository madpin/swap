from swap.services.rota_parser import RotaParser
from swap.config import settings
from swap.core.database import Session, engine
from sqlmodel import select
from swap.models.rota import Rota
from datetime import datetime
from swap.utils.logger import logger


def rota_to_db():
    rota_parser = RotaParser(
        service_account_file="gcal_service_account.json",
        spreadsheet_id=settings.rota.spreadsheet_id,
        range_name=settings.rota.range_name,
    )

    parsed_rota = rota_parser.parse_rota()

    with Session(engine) as session:
        for entry in parsed_rota:
            try:
                existing_rota = session.exec(
                    select(Rota).where(
                        Rota.name == entry["name"],
                        Rota.date == datetime.strptime(entry["date"], "%Y-%m-%d"),
                    )
                ).first()

                if existing_rota:
                    # Update only if the shift is a working one
                    if entry["is_working"]:
                        existing_rota.start_time = (
                            datetime.strptime(entry["start_date"], "%Y-%m-%d %H:%M:%S")
                            if entry.get("start_date")
                            else None
                        )
                        existing_rota.end_time = (
                            datetime.strptime(entry["end_date"], "%Y-%m-%d %H:%M:%S")
                            if entry.get("end_date")
                            else None
                        )
                    else:
                        existing_rota.start_time = None
                        existing_rota.end_time = None

                    existing_rota.shift_type = entry["shift_type"]
                    existing_rota.is_working = entry["is_working"]
                    existing_rota.updated_at = datetime.utcnow()
                    session.add(existing_rota)
                else:
                    rota = Rota(
                        name=entry["name"],
                        date=datetime.strptime(entry["date"], "%Y-%m-%d"),
                        # Set start_time and end_time only if the shift is a working one
                        start_time=datetime.strptime(
                            entry["start_date"], "%Y-%m-%d %H:%M:%S"
                        )
                        if entry.get("start_date") and entry["is_working"]
                        else None,
                        end_time=datetime.strptime(
                            entry["end_date"], "%Y-%m-%d %H:%M:%S"
                        )
                        if entry.get("end_date") and entry["is_working"]
                        else None,
                        shift_type=entry["shift_type"],
                        is_working=entry["is_working"],
                    )
                    session.add(rota)
            except Exception as e:
                logger.error(f"Error processing entry {entry}: {e}")
                raise

        session.commit()
    return 1
