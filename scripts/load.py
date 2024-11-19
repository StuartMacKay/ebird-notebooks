"""
load.py

A script for loading observations from the eBird API using a
scheduler such as cron.

"""
import os
import sys

from pathlib import Path

from dotenv import load_dotenv

# Get the root directory of the project
root_dir =Path(__file__).absolute().parent.parent
# Get the directory where the python code lives
src_dir = root_dir.joinpath("src")
# Add it to PYTHONPATH so we can import the loader
sys.path.insert(0, str(src_dir))

# Now we can load the local python
from ebird import settings
from ebird.db import loaders

# Change to the root directory
os.chdir(root_dir)
# Load the environment variables from the .env file
load_dotenv()

api_key = os.getenv("EBIRD_API_KEY")
region = os.getenv("EBIRD_API_REGION")
db_url = settings.API_DATABASE_URL

loader = loaders.APILoader(api_key, db_url)
loader.load(region)
