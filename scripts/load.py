"""
load.py

A script for loading observations from the eBird API using a
scheduler such as cron.

"""

import datetime as dt

from ebird.notebooks import loaders, settings

db_dir = settings.DATABASE_DIR
db_name = "api_checklists"
db_url = f"sqlite+pysqlite:///{db_dir}/{db_name}.sqlite3"

api_key = settings.API_KEY
back = settings.API_PAST_DAYS

today = dt.date.today()
dates = [today - dt.timedelta(days=offset) for offset in range(back)]

loader = loaders.APILoader(api_key, db_url)

for area in settings.API_REGIONS:
    for date in dates:
        loader.load(area, date)
