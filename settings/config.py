from dotenv import load_dotenv
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.abspath(os.path.join(current_dir, "../../"))
path = os.path.join(base_dir, "configs", ".env")

load_dotenv(path)

def load_env_config():
    return {
        'server': os.getenv("DATABASE_SERVER"),
        'database': os.getenv("DATABASE"),
        'database_user': os.getenv("DATABASE_USERNAME"),
        'database_pass': os.getenv("DATABASE_PASSWORD"),
        'cleardb_database_url': os.getenv("CLEARDB_DATABASE_URL"),
        'cleardb_backup_database_url': os.getenv("CLEARDB_BACKUP_DATABASE_URL"),
        'secret_key': os.getenv("ACCESS_SECRET_KEY"),
        'password_salt': os.getenv("ACCESS_SALT"),
        'algorithm': os.getenv('ALGORITHM'),
    }

