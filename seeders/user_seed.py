from sqlalchemy.orm import Session
from modules.authentication.auth import create_just_user

def run_user_seeder(db: Session):
	admin_user = create_just_user(db=db, username="superadmin", email="superadmin@geeg.com", password="secret", phone_number="08178666383", first_name="Jerry", last_name="Law", is_staff=1)
	main_user = create_just_user(db=db, username="beta_user", email="beta_user@geeg.com", password="secret", phone_number="08146155120", first_name="James", last_name="Bond")

	return True