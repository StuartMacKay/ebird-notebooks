"""
load_mydata.py

A Django management command for loading observations from A CSV file,
either My eBird Data.

Usage:
    python manage.py load_mydata <path> <name>

Arguments:
    <path> Required. The path to the CSV file.
    <name> Required. Your name.

Examples:
    python manage.py load_mydata data/downloads/MyEBirdData.csv "Etta Lemon"

Notes:
    1. Downloads for My eBird Data do not have a unique identifier.
       That means you must delete all the records before you load the latest
       download, otherwise duplicate records will be created.

"""
from pathlib import Path

from django.core.management.base import BaseCommand

from ebird.checklists.loaders import MyDataLoader


class Command(BaseCommand):
    help = "Load MyEBirdData from a CSV file"

    def add_arguments(self, parser):
        parser.add_argument("path", type=str)
        parser.add_argument("name", type=str)

    def handle(self, **options):
        path: Path = Path(options["path"])
        name: str = options["name"]
        MyDataLoader().load(path, name)
