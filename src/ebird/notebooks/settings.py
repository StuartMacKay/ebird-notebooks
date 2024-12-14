"""
Settings for the notebooks.
"""

import datetime as dt
import os
from pathlib import Path

from dotenv import load_dotenv

_today = dt.date.today()

# The root directory of the project.
ROOT_DIR: Path = Path(__file__).parent.parent.parent.parent.absolute()
# The location of the .env dile
DOTENV_FILE: Path = ROOT_DIR.joinpath(".env")
# The directory for data
DATA_DIR: Path = ROOT_DIR.joinpath("data")
# The directory where the eBird Basic Dataset files are downloaded to..
DOWNLOAD_DIR: Path = DATA_DIR.joinpath("downloads")
# The directory where the database files are located.
DATABASE_DIR: Path = DATA_DIR.joinpath("databases")

# Load the environment variables. See .env.example for a full description.
load_dotenv(DOTENV_FILE)
# The key needed to access the eBird API.
API_KEY: str = os.getenv("API_KEY")
# The regions for fetching checklists.
API_REGIONS: list[str] = [
    region.strip() for region in os.getenv("API_REGIONS", "").split(",") if region
]
# The number of days to fetch checklists for.
API_PAST_DAYS: int = int(os.getenv("API_PAST_DAYS", "5"))
# The default dates for fetching checklists. API_PAST_DAYS == 0 returns an empty list.
API_PAST_DATES: list[dt.date] = [
    _today - dt.timedelta(days=offset) for offset in range(API_PAST_DAYS)
]
# The default name for the database where eBird API records are saved
API_DB_NAME: str = os.getenv("API_DB_NAME", "api_checklists")
# The default URL for the eBird API database
API_DB_URL: str = f"sqlite+pysqlite:///{DATABASE_DIR}/{API_DB_NAME}.sqlite3"
