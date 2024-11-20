"""
load.py

A script for loading observations from the eBird API using a
scheduler such as cron.

"""
import os

from dotenv import load_dotenv

from main import settings
from main.db import loaders

load_dotenv(dotenv_path=settings.DOTENV_FILE)

api_key = os.getenv("EBIRD_API_KEY")
region = os.getenv("EBIRD_API_REGION")
back = int(os.getenv("EBIRD_API_PAST_DAYS"))
db_url = settings.API_DATABASE_URL

loader = loaders.APILoader(api_key, db_url)
loader.load(region, back)
