from sqlalchemy.orm import Session
from database.model import create_country, create_currency, create_country_currency

def run_location_seeder(db: Session):
	country = create_country(db=db, name="Nigeria", full_name="Federal Republic Of Nigeria", code_one="NG", code_two="NGA", status=1)
	currency = create_currency(db=db, name="Naira", symbol="₦", code="NGN", status=1)
	create_country_currency(db=db, country_id=country.id, currency_id=currency.id, status=1)

	return True