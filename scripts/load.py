"""
load.py

A script for loading observations from the eBird API using a
scheduler such as cron.

"""

from main import settings
from main.db import loaders

db_dir = settings.DATABASE_DIR
db_name = "api_checklists"
db_url = f"sqlite+pysqlite:///{db_dir}/{db_name}.sqlite3"

api_key = settings.API_KEY
regions = settings.API_REGIONS
back = settings.API_PAST_DAYS

loader = loaders.APILoader(api_key, db_url)
loader.load(regions, back)
