"""
load.py

A script for loading observations from the eBird API using a
scheduler such as cron.
"""

from ebird.notebooks import loaders, settings

db_dir = settings.DATABASE_DIR
db_name = "api_checklists"
db_url = f"sqlite+pysqlite:///{db_dir}/{db_name}.sqlite3"

api_key = settings.API_KEY

loader = loaders.APILoader(api_key, db_url)

for area in settings.API_REGIONS:
    for date in settings.API_PAST_DATES:
        loader.load(area, date)
