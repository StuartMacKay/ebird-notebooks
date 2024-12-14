"""
load.py

A script for loading observations from the eBird API using a
scheduler such as cron.
"""

from ebird.notebooks import loaders, settings

loader = loaders.APILoader(settings.API_KEY, settings.API_DB_URL)

for area in settings.API_REGIONS:
    for date in settings.API_PAST_DATES:
        loader.load(area, date)
