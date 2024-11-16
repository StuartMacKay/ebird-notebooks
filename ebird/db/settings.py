"""
Settings for the notebooks.
"""
from pathlib import Path

# The directory where this file is located.
THIS_DIR = Path(__file__).parent
# The root directory of the project.
ROOT_DIR = THIS_DIR.parent.parent
# The directory where the database and any data (csv) files are located.
DATA_DIR = ROOT_DIR.joinpath("data")
# The full path to the sqlite3 database.
EBD_DATABASE_PATH = DATA_DIR.joinpath("ebd.sqlite3")
# The URL used by the database engine.
EBD_DATABASE_URL = f"sqlite+pysqlite:///{EBD_DATABASE_PATH}"
# The full path to the sqlite3 database.
API_DATABASE_PATH = DATA_DIR.joinpath("api.sqlite3")
# The URL used by the database engine.
API_DATABASE_URL = f"sqlite+pysqlite:///{API_DATABASE_PATH}"
