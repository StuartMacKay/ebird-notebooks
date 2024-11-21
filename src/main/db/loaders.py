import csv
import datetime as dt
import decimal
import os
import re
import sys

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from ebird.api import get_visits, get_checklist, get_taxonomy

from .models import Checklist, Location, Observation, Observer, Species

class EBDLoader:

    def __init__(self, db_url):
        self.engine = create_engine(db_url)

    @staticmethod
    def _get_value(value, cast):
        return cast(value) if value else None

    def _get_boolean_value(self, value):
        return self._get_value(value, bool)

    def _get_integer_value(self, value):
        return self._get_value(value, int)

    def _get_decimal_value(self, value):
        return self._get_value(value, decimal.Decimal)

    @staticmethod
    def _create_or_update(session, model, identifier, last_edited, defaults):
        stmt = select(model).where(model.identifier==identifier)
        if row := session.execute(stmt).first():
            obj = row[0]
            if last_edited > obj.edited:
                for key, value in defaults.items():
                    setattr(obj, key, value)
                obj.modified = dt.datetime.now()
                obj.edited = last_edited
                session.add(obj)
        else:
            timestamp = dt.datetime.now()
            obj = model(created=timestamp, modified=timestamp, edited=last_edited, identifier=identifier, **defaults)
            session.add(obj)

        return obj

    def _load_observer(self, session, last_edited, row):
        identifier = row["OBSERVER ID"]
        defaults = {
            "name": ""
        }
        return self._create_or_update(session, Observer, identifier, last_edited, defaults)

    def _load_checklist(self, session, last_edited, row):
        identifier = row["SAMPLING EVENT IDENTIFIER"]
        defaults = {
            "location": self._load_location(session, last_edited, row),
            "observer": self._load_observer(session, last_edited, row),
            "group": row["GROUP IDENTIFIER"],
            "observer_count": row["NUMBER OBSERVERS"],
            "date": dt.datetime.strptime(row["OBSERVATION DATE"], "%Y-%m-%d").date(),
            "time": dt.datetime.strptime(row["TIME OBSERVATIONS STARTED"], "%H:%M:%S").time(),
            "protocol": row["PROTOCOL TYPE"],
            "protocol_code": row["PROTOCOL CODE"],
            "project_code": row["PROJECT CODE"],
            "duration": self._get_integer_value(row["DURATION MINUTES"]),
            "distance": self._get_decimal_value(row["EFFORT DISTANCE KM"]),
            "area": self._get_decimal_value(row["EFFORT AREA HA"]),
            "complete": self._get_boolean_value(row["ALL SPECIES REPORTED"]),
            "comments": row["TRIP COMMENTS"],
            "url": "",
        }
        return self._create_or_update(session, Checklist, identifier, last_edited, defaults)

    def _load_location(self, session, last_edited, row):
        identifier = row["LOCALITY ID"]
        defaults = {
            "type": row["LOCALITY TYPE"],
            "name": row["LOCALITY"],
            "county": row["COUNTY"],
            "county_code": row["COUNTY CODE"],
            "state": row["STATE"],
            "state_code": row["STATE CODE"],
            "country": row["COUNTRY"],
            "country_code": row["COUNTRY CODE"],
            "latitude": self._get_decimal_value(row["LATITUDE"]),
            "longitude": self._get_decimal_value(row["LONGITUDE"]),
            "iba_code": row["IBA CODE"],
            "bcr_code": row["BCR CODE"],
            "usfws_code": row["USFWS CODE"],
            "atlas_block": row["ATLAS BLOCK"],
            "url": "",
        }
        return self._create_or_update(session, Location, identifier, last_edited, defaults)

    def _load_species(self, session, last_edited, row):
        identifier = row["TAXON CONCEPT ID"]
        defaults = {
            "code": "",
            "order": row["TAXONOMIC ORDER"],
            "category": row["CATEGORY"],
            "common_name": row["COMMON NAME"],
            "scientific_name": row["SCIENTIFIC NAME"],
            "local_name": "",
            "subspecies_common_name": row["SUBSPECIES COMMON NAME"],
            "subspecies_scientific_name": row["SUBSPECIES SCIENTIFIC NAME"],
            "subspecies_local_name": "",
            "exotic_code": row["EXOTIC CODE"],
        }
        return self._create_or_update(session, Species, identifier, last_edited, defaults)

    def _load_observation(self, session, last_edited, row):
        identifier = row["GLOBAL UNIQUE IDENTIFIER"]
        defaults = {
            "checklist": self._load_checklist(session, last_edited, row),
            "species": self._load_species(session, last_edited, row),
            "count": self._get_integer_value(row["OBSERVATION COUNT"]),
            "breeding_code": row["BREEDING CODE"],
            "breeding_category": row["BREEDING CATEGORY"],
            "behavior_code": row["BEHAVIOR CODE"],
            "age_sex": row["AGE/SEX"],
            "media": self._get_boolean_value(row["HAS MEDIA"]),
            "approved": self._get_boolean_value(row["APPROVED"]),
            "reviewed": self._get_boolean_value(row["REVIEWED"]),
            "reason": row["REASON"],
            "comments": row["SPECIES COMMENTS"],
        }
        return self._create_or_update(session, Observation, identifier, last_edited, defaults)

    def load(self, path):
        if not os.path.exists(path):
            raise IOError('File "%s" does not exist' % path)

        sys.stdout.write("Loading eBird Basic Dataset from %s\n" % path)

        with Session(self.engine) as session:
            with open(path) as csvfile:
                added = updated = unchanged = 0
                loaded = dt.datetime.now()
                reader = csv.DictReader(csvfile, delimiter="\t")
                for row in reader:
                    last_edited = dt.datetime.fromisoformat(row["LAST EDITED DATE"])
                    observation = self._load_observation(session, last_edited, row)
                    if observation.created > loaded:
                        added += 1
                    elif observation.modified > loaded:
                        updated += 1
                    else:
                        unchanged += 1
                    session.commit()
                    sys.stdout.write(".")
                    sys.stdout.flush()

        total = added + updated + unchanged

        sys.stdout.write("\nSuccessfully loaded eBird Basic Dataset\n")
        sys.stdout.write("%d records added\n" % added)
        sys.stdout.write("%d records updated\n" % updated)
        sys.stdout.write("%d records unchanged\n" % unchanged)
        sys.stdout.write("%d records in total\n" % total)


class APILoader:

    def __init__(self, api_key, db_url):
        self.api_key = api_key
        self.engine = create_engine(db_url)

    @staticmethod
    def _get_value(value, cast):
        return cast(value) if value is not None else None

    def _get_boolean_value(self, value):
        return self._get_value(value, bool)

    def _get_integer_value(self, value):
        return self._get_value(value, int)

    def _get_decimal_value(self, value):
        return self._get_value(value, decimal.Decimal)

    @staticmethod
    def _get_observation_global_identifier(row):
        return f"URN:CornellLabOfOrnithology:{row['projId']}:{row['obsId']}"

    @staticmethod
    def _get_species(session, obs):
        stmt = select(Species).where(Species.code == obs["speciesCode"])
        return session.execute(stmt).first()[0]

    @staticmethod
    def _create_or_update(session, model, identifier, last_edited, defaults):
        stmt = select(model).where(model.identifier==identifier)
        if row := session.execute(stmt).first():
            obj = row[0]
            if last_edited > obj.edited:
                for key, value in defaults.items():
                    setattr(obj, key, value)
                obj.modified = dt.datetime.now()
                obj.edited = last_edited
                session.add(obj)
        else:
            timestamp = dt.datetime.now()
            obj = model(created=timestamp, modified=timestamp, edited=last_edited, identifier=identifier, **defaults)
            session.add(obj)
        return obj

    def _load_observer(self, session, last_edited, checklist):
        # The observer's name is used as the unique identifier, even
        # though it is not necessarily unique. However this works until
        # better solution is found.
        identifier = checklist["userDisplayName"]
        defaults = {
            "name": "",
        }
        return self._create_or_update(session, Observer, identifier, last_edited, defaults)

    def _load_checklist(self, session, last_edited, checklist):
        identifier = checklist["subId"]
        date, time = checklist["obsDt"].split(" ", 1)
        if "durationHrs" in checklist:
            duration = checklist["durationHrs"] * 60.0
        else:
            duration = None
        distance = checklist.get("distKm", None)
        area = checklist.get("areaHa", None)
        defaults = {
            "location": self._load_location(session, last_edited, checklist["loc"]),
            "observer": self._load_observer(session, last_edited, checklist),
            "observer_count": self._get_integer_value(checklist.get("numObservers", None)),
            "group": "",
            "species_count": checklist["numSpecies"],
            "date": dt.datetime.strptime(date, "%Y-%m-%d").date(),
            "time": dt.datetime.strptime(time, "%H:%M").time(),
            "protocol": "",
            "protocol_code": checklist["protocolId"],
            "project_code": checklist["projId"],
            "duration": self._get_integer_value(duration),
            "distance": self._get_decimal_value(distance),
            "area": self._get_decimal_value(area),
            "complete": self._get_boolean_value(checklist.get("allObsReported", False)),
            "comments": "",
            "url": "",
        }
        return self._create_or_update(session, Checklist, identifier, last_edited, defaults)

    def _load_location(self, session, last_edited, row):
        identifier = row["locId"]
        defaults = {
            "type": "",
            "name": row["name"],
            "county": row["subnational2Name"],
            "county_code": row["subnational2Code"],
            "state": row["subnational1Name"],
            "state_code": row["subnational1Code"],
            "country": row["countryName"],
            "country_code": row["countryCode"],
            "iba_code": "",
            "bcr_code": "",
            "usfws_code": "",
            "atlas_block": "",
            "latitude": self._get_decimal_value(row["latitude"]),
            "longitude": self._get_decimal_value(row["longitude"]),
            "url": "",
        }
        return self._create_or_update(session, Location, identifier, last_edited, defaults)

    def _load_observation(self, session, last_edited, checklist, observation):
        identifier = self._get_observation_global_identifier(observation)
        if re.match(r"\d+", observation["howManyStr"]):
            count = self._get_integer_value(observation["howManyStr"])
        else:
            count = None
        defaults = {
            "checklist": self._load_checklist(session, last_edited, checklist),
            "species": self._get_species(session, observation),
            "count": count,
            "breeding_code": "",
            "breeding_category": "",
            "behavior_code": "",
            "age_sex": "",
            "media": False,
            "approved": None,
            "reviewed": None,
            "reason": "",
            "comments": "",
        }
        return self._create_or_update(session, Observation, identifier, last_edited, defaults)

    def _load_taxonomy(self, session):
        timestamp = dt.datetime.now()
        for row in get_taxonomy(self.api_key):
            session.add(Species(
                created=timestamp,
                modified=timestamp,
                edited=timestamp,
                identifier="",
                code=row["speciesCode"],
                category=row["category"],
                common_name = row["comName"],
                scientific_name = row["sciName"],
                local_name="",
                subspecies_common_name="",
                subspecies_scientific_name="",
                subspecies_local_name="",
                exotic_code="",
            ))

    def load(self, regions, back):
        today = dt.date.today()
        loaded = dt.datetime.now()
        areas = [region.strip() for region in regions.split(",")]
        dates = [today - dt.timedelta(days=offset) for offset in range(back)]
        added = updated = unchanged = 0
        visits = []

        sys.stdout.write("Fetching visits...\n")
        sys.stdout.write("For areas: %s\n" % ", ".join(areas))
        sys.stdout.write("For the past %d days\n" % back)

        with Session(self.engine) as session:
            if session.query(Species.id).count() == 0:
                sys.stdout.write("Loading eBird taxonomy\n")
                self._load_taxonomy(session)

            for date in dates:
                sys.stdout.write("Date: %s\n" % date)
                for area in areas:
                    results = get_visits(self.api_key, area, date=date, max_results=200)
                    visits.extend(results)
                    sys.stdout.write("%s: %d checklists submitted\n"
                        % (area, len(results))
                    )
                    sys.stdout.flush()

            sys.stdout.write("Total number of checklists: %d\n" % len(visits))
            sys.stdout.write("Fetching checklists...\n")

            for visit in visits:
                identifier = visit["subId"]
                location = visit["loc"]["name"]
                area = visit["loc"]["subnational1Code"]
                sys.stdout.write(f"{identifier}, {area}, {location}\n")
                checklist = get_checklist(self.api_key, identifier)
                checklist["loc"] = visit["loc"]
                last_edited = dt.datetime.fromisoformat(checklist["lastEditedDt"])
                for observation in checklist.pop("obs"):
                    try:
                        observation = self._load_observation(session, last_edited, checklist, observation)
                        if observation.created > loaded:
                            added += 1
                        elif observation.modified > loaded:
                            updated += 1
                        else:
                            unchanged += 1
                    except Exception as err:
                        sys.stdout.write("Error: %s\n\n" % str(err))
                        sys.stdout.write("Checklist: %s\n\n" % str(checklist))
                        sys.stdout.write("Observation: %s\n" % str(observation))

                session.commit()

        total = added + updated + unchanged

        sys.stdout.write("Success\n")
        sys.stdout.write("%d checklists fetched\n" % len(visits))
        sys.stdout.write("%d observations added\n" % added)
        sys.stdout.write("%d observations updated\n" % updated)
        sys.stdout.write("%d observations unchanged\n" % unchanged)
        sys.stdout.write("%d observations in total\n" % total)
