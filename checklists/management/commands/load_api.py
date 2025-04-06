"""
load_api.py

A Django management command for loading observations from the eBird API.

Modes:
    new   Only load new checklists
    all   Load all checklists

Usage:
    python manage.py load_api new <days> <region>+
    python manage.py load_api all <date> <region>+

Arguments:
    <days>   Required. The number of previous days to load new checklists for.

    <date>   Required. The date to load all checklists.

    <region> Required. One or more national, subnational1, subnational2, or hotspot
             codes used by eBird. For example, US, US-NY, US-NY-109, L1379126

Examples:
    # Load checklists added in the past week for New York state
    python manage.py load_api new 7 US-NY

    # Load checklists all checklists added on the last Big Day
    python manage.py load_api all 2024-10-05 US-NY

Notes:
    1. The eBird API returns a maximum of 200 results. The APILoader works
       around this by fetching checklists from sub-regions if necessary.
       Downloading checklists once a day should be sufficient for all hotspots
       or subnational2 areas. For large countries or places with lots of birders
       downloads will have to be more frequent. For really large area, i.e. the
       USA you shouldn't be using the API at all. Instead use the data from the
       eBird Basic Dataset.

    2. Why is loading all checklists limited to a specific date?
       The number of checklists that are updated is relatively small, typically
       less than 1%. The problem with the eBird API is that you can only find
       out whether a checklist has changed by downloading it. This app basically
       mirrors the eBird database for a given region so there's a strong temptation
       to repeatedly download everything to keep the checklists in sync. That
       means repeatedly downloading all the checklists submitted in the past week
       or month, or longer to pick up a few changes. That's a heavy load on the
       eBird servers and a lot of bandwidth for relatively little gain, so this
       "behaviour" is discouraged. You can still keep the checklists more or less
       in sync by setting up a cron task that runs at midnight and downloads all
       the checklists from 1 week, or 1 month ago. That means it will take a few
       days for all the changes to be applied to the database, but they will
       eventually be in sync. That's still a lot of downloads for a few changes,
       so it's not recommended. You can, of course, write your own loader and
       do whatever you want.

       The API is really a news service. For accuracy and completeness you should
       really use the eBird Basic Dataset, which is published on the 15th of each
       month.

    3. It's important to note that the data from the API has limitations. Observers
       are only identified by name. So if there are two Juan Garcias birding in a
       region, then all the observations will appear to belong to one person. Also
       the observations will not have been reviewed by moderators, so there are
       likely to be records where the identification is incorrect.

    4. You automate running the command using a scheduler such as cron. If you use
       the absolute paths to python and the command, then you don't need to deal
       with activating the virtual environment, for example:

       # At midnight Load all checklists added in the past week
       0 0 * * * /home/me/my-project/.venv/bin/python /home/me/my-project/manage.py load_api new 7 US-NY

"""

import datetime as dt

from django.conf import settings
from django.core.management.base import BaseCommand

from ebird.checklists.loaders import APILoader


class Command(BaseCommand):
    help = "Load checklists from the eBird API"

    def add_arguments(self, parser):
        subparsers = parser.add_subparsers(
            title="sub-commands",
            required=True,
        )

        new_parser = subparsers.add_parser(
            "new",
            help="Load new checklists.",
        )
        new_parser.set_defaults(method=self.new_checklists)
        new_parser.add_argument(
            "days", type=int, help="The number of previous days to load"
        )
        new_parser.add_argument(
            "regions",
            nargs="+",
            type=str,
            help="Codes for the eBird regions, e.g US-NY",
        )

        all_parser = subparsers.add_parser(
            "all",
            help="Load all checklists for a given date.",
        )
        all_parser.set_defaults(method=self.all_checklists)
        all_parser.add_argument("date", type=str, help="The checklist date")
        all_parser.add_argument(
            "regions",
            nargs="+",
            type=str,
            help="Codes for the eBird regions, e.g US-NY",
        )

    @staticmethod
    def get_loader() -> APILoader:
        key: str = getattr(settings, "EBIRD_API_KEY")
        locale: str = getattr(settings, "EBIRD_API_LOCALE")
        return APILoader(key, locale)

    @staticmethod
    def get_dates(days) -> list[dt.date]:
        today: dt.date = dt.date.today()
        return [today - dt.timedelta(days=n) for n in range(days)]

    def handle(self, *args, method, **options):
        method(*args, **options)

    def new_checklists(self, **options) -> None:
        loader: APILoader = self.get_loader()
        dates: list[dt.date] = self.get_dates(options["days"])
        region: str
        date: dt.date

        for region in options["regions"]:
            for date in dates:
                loader.load_checklists(region, date, True)

    def all_checklists(self, **options) -> None:
        loader: APILoader = self.get_loader()
        region: str
        date: dt.date = dt.datetime.strptime(options["date"], "%Y-%m-%d").date()

        for region in options["regions"]:
            loader.load_checklists(region, date, False)
