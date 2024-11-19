"""
load.py

A script for loading observations from the eBird API using a
scheduler such as cron.

"""
import os

from pathlib import Path

from dotenv import load_dotenv

# Get the root directory of the project
root_dir =Path(__file__).absolute().parent.parent

# Now we can load the local python
from main import settings
from main.db import loaders

# Change to the root directory
os.chdir(root_dir)
# Load the environment variables from the .env file
load_dotenv()

api_key = os.getenv("EBIRD_API_KEY")
region = os.getenv("EBIRD_API_REGION")
db_url = settings.API_DATABASE_URL

loader = loaders.APILoader(api_key, db_url)
loader.load(region)
