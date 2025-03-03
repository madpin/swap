from swap.services.rota_parser import RotaParser
from swap.utils.logger import logger

async def get_rota():
    """This function is used to parse the rota spreadsheet and return the parsed data"""
    spreadsheet_id = "1MqJwH59lHhE6q0kmFNkQZzpteRLTQBlX2vKhEhVltHQ"
    range_name = "Combined Rota!A:M"
    rota_parser = RotaParser(
        service_account_file="gcal_service_account.json",
        spreadsheet_id=spreadsheet_id,
        range_name=range_name,
    )
    parsed_rota = rota_parser.parse_rota()
    logger.info(f"Parsed Rota: {parsed_rota}")
    return parsed_rota
