"""
Settings for the notebooks.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# The root directory of the project.
ROOT_DIR = Path(__file__).parent.parent.parent.absolute()
# The location of the .env dile
DOTENV_FILE = ROOT_DIR.joinpath(".env")
# The directory for data
DATA_DIR = ROOT_DIR.joinpath("data")
# The directory where the eBird Basic Dataset files are downloaded to..
DOWNLOAD_DIR = DATA_DIR.joinpath("downloads")
# The directory where the database files are located.
DATABASE_DIR = DATA_DIR.joinpath("databases")

# Load the environment variables. See .env.example for a full description.
load_dotenv(DOTENV_FILE)
# The key needed to access the eBird API.
API_KEY = os.getenv("API_KEY")
# The regions for which to load observations for.
API_REGIONS = os.getenv("API_REGIONS")
# The number of days to fetch checklists for.
API_PAST_DAYS = int(os.getenv("API_PAST_DAYS", "5"))
