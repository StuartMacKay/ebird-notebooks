"""
load.py

A script for loading observations from the eBird API using a
scheduler such as cron.

"""

import datetime as dt

from main import settings
from main.db import loaders

db_dir = settings.DATABASE_DIR
db_name = "api_checklists"
db_url = f"sqlite+pysqlite:///{db_dir}/{db_name}.sqlite3"

api_key = settings.API_KEY
regions = settings.API_REGIONS
back = settings.API_PAST_DAYS

today = dt.date.today()
areas = [region.strip() for region in regions.split(",")]
dates = [today - dt.timedelta(days=offset) for offset in range(back)]

loader = loaders.APILoader(api_key, db_url)

for area in areas:
    for date in dates:
        loader.load(area, date)
