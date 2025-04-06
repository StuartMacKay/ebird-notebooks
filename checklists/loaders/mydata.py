import csv
import datetime as dt
from decimal import Decimal
import logging
import random
import re
import string
from pathlib import Path

from ..models import Checklist, Location, Observation, Observer, Species

logger = logging.getLogger(__name__)


class MyDataLoader:

    @staticmethod
    def add_location(data: dict) -> Location:
        identifier: str = data["Location ID"]
        location: Location

        values: dict = {
            "identifier": identifier,
            "type": "",
            "name": data["Location"],
            "county": data["County"],
            "county_code": "",
            "state": data["State/Province"],
            "state_code": "",
            "country": "",
            "country_code": data["County"].split("-")[0],
            "iba_code": "",
            "bcr_code": "",
            "usfws_code": "",
            "atlas_block": "",
            "latitude": Decimal(data["Latitude"]),
            "longitude": Decimal(data["Longitude"]),
            "url": "https://ebird.org/region/%s" % identifier,
        }

        if location := Location.objects.filter(identifier=identifier).first():
            for key, value in values.items():
                setattr(location, key, value)
            location.save()
        else:
            location = Location.objects.create(**values)

        return location

    @staticmethod
    def add_observer(name: str) -> Observer:
        observer: Observer

        values = {"identifier": "", "name": name}

        if observer := Observer.objects.filter(name=name).first():
            for key, value in values.items():
                setattr(observer, key, value)
            observer.save()
        else:
            observer = Observer.objects.create(**values)

        return observer

    @staticmethod
    def add_species(data: dict) -> Species:
        order: str = data["Taxonomic Order"]
        species: Species

        values: dict = {
            "taxon_order": order,
            "order": "",
            "category": "",
            "species_code": "",
            "family_code": "",
            "common_name": data["Common Name"],
            "scientific_name": data["Scientific Name"],
            "family_common_name": "",
            "family_scientific_name": "",
            "subspecies_common_name": "",
            "subspecies_scientific_name": "",
            "exotic_code": "",
        }

        if species := Species.objects.filter(order=order).first():
            for key, value in values.items():
                setattr(species, key, value)
            species.save()
        else:
            species = Species.objects.create(**values)

        return species

    def add_observation(
        self, data: dict, checklist: Checklist
    ) -> Observation:

        values: dict = {
            "edited": checklist.edited,
            "identifier": "OBS" + "".join(random.choices(string.digits, k=10)),
            "species": self.add_species(data),
            "checklist": checklist,
            "location": checklist.location,
            "observer": checklist.observer,
            "count": None,
            "breeding_code": data["Breeding Code"] or "",
            "breeding_category": "",
            "behavior_code": "",
            "age_sex": "",
            "media": len(data["ML Catalog Num`bers"] or "") > 0,
            "approved": None,
            "reviewed": None,
            "reason": "",
            "comments": data["Observation Details"] or "",
            "urn": "",
        }

        if re.match(r"\d+", data["Count"]):
            values["count"] = int(data["Count"]) or None

        # There is no unique identifier for an observation, only the
        # count, species, date, time, checklist identifier and location
        # serve to identify it. If any of these change then the original
        # observation cannot be retrieved, so updating records is not
        # practical / possible. It only makes sense to add the record each
        # time the data is loaded. Unless the data is cleared that will
        # result in duplicate records being created.
        return Observation.objects.create(**values)

    @staticmethod
    def add_checklist(
        data: dict, location: Location, observer: Observer
    ) -> Checklist:
        identifier: str = data["Submission ID"]
        checklist: Checklist

        values: dict = {
            "identifier": identifier,
            "location": location,
            "observer": observer,
            "observer_count": int(data["Number of Observers"]),
            "group": "",
            "species_count": None,
            "date": dt.datetime.strptime(data["Date"], "%Y-%m-%d").date(),
            "time": None,
            "protocol": data["Protocol"],
            "protocol_code": "",
            "project_code": "",
            "duration": None,
            "distance": None,
            "area": None,
            "complete": data["All Obs Reported"] == "1",
            "comments": data["Checklist Comments"] or "",
            "url": "https://ebird.org/checklist/%s" % identifier,
        }

        if time := data["Time"]:
            values["time"] = dt.datetime.strptime(time, "%H:%M %p").time()

        if duration := data["Duration (Min)"]:
            values["duration"] = int(duration)

        if distance := data["Distance Traveled (km)"]:
            values["distance"] = Decimal(distance)

        if area := data["Area Covered (ha)"]:
            values["area"] = Decimal(area)

        if checklist := Checklist.objects.filter(identifier=identifier).first():
            for key, value in values.items():
                setattr(checklist, key, value)
            checklist.save()
        else:
            checklist = Checklist.objects.create(**values)

        return checklist

    def load(self, path: Path, observer_name: str) -> None:
        if not path.exists():
            raise IOError('File "%s" does not exist' % path)

        logger.info("Loading My eBird Data", extra={"path": path})

        with open(path) as csvfile:
            loaded: int = 0
            reader = csv.DictReader(csvfile, delimiter=",")
            observer: Observer = self.add_observer(observer_name)
            for data in reader:
                location: Location = self.add_location(data)
                checklist: Checklist = self.add_checklist(data, location, observer)
                self.add_observation(data, checklist)
                loaded += 1

        logger.info("Loaded My eBird Data", extra={"loaded": loaded})
