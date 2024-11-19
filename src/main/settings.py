"""
Settings for the notebooks.
"""
from pathlib import Path

# The root directory of the project.
ROOT_DIR = Path(__file__).parent.parent.parent.absolute()
# The directory for data
DATA_DIR = ROOT_DIR.joinpath("data")
# The directory where the eBird Basic Dataset files are downloaded to..
DOWNLOAD_DIR = DATA_DIR.joinpath("downloads")
# The directory where the database files are located.
DATABASE_DIR = DATA_DIR.joinpath("databases")
# The URL used by the database engine.
EBD_DATABASE_URL = f"sqlite+pysqlite:///{DATABASE_DIR}/ebd.sqlite3"
# The URL used by the database engine.
API_DATABASE_URL = f"sqlite+pysqlite:///{DATABASE_DIR}/api.sqlite3"
