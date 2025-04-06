"""
load_dataset.py

A Django management command for loading observations from A CSV file,
either containing the eBird Basic Dataset.

Usage:
    python manage.py load_dataset <path>

Arguments:
    <path> Required. The path to the CSV file.

Examples:
    python manage.py load_dataset data/downloads/MyEBirdData.csv

Notes:
    1. The eBird Basic Dataset has a unique identifier, which never changes,
       for every observation, even if the species changes. That means you
       can load the dataset multiple times. If any of the data changes, the
       Observation will be updated.

"""
from pathlib import Path

from django.core.management.base import BaseCommand

from ebird.checklists.loaders import BasicDatasetLoader


class Command(BaseCommand):
    help = "Load the eBird Basic Dataset from a CSV file"

    def add_arguments(self, parser):
        parser.add_argument("path", type=str)

    def handle(self, *args, **options):
        path: Path = Path(options["path"])
        BasicDatasetLoader().load(path)
