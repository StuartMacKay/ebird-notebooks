import csv
import datetime as dt
import decimal
import os
import re
import sys

from ebird.api import get_checklist, get_taxonomy, get_visits
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from .models import Checklist, Location, Observation, Observer, Species


class BasicDatasetLoader:
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
        stmt = select(model).where(model.identifier == identifier)
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
            obj = model(
                created=timestamp,
                modified=timestamp,
                edited=last_edited,
                identifier=identifier,
                **defaults,
            )
            session.add(obj)

        return obj

    def _load_observer(self, session, last_edited, row):
        identifier = row["OBSERVER ID"]
        defaults = {"name": ""}
        return self._create_or_update(
            session, Observer, identifier, last_edited, defaults
        )

    def _load_checklist(self, session, last_edited, row):
        identifier = row["SAMPLING EVENT IDENTIFIER"]
        if value := row["TIME OBSERVATIONS STARTED"]:
            time = dt.datetime.strptime(value, "%H:%M:%S").time()
        else:
            time = None
        defaults = {
            "location": self._load_location(session, last_edited, row),
            "observer": self._load_observer(session, last_edited, row),
            "group": row["GROUP IDENTIFIER"],
            "observer_count": row["NUMBER OBSERVERS"],
            "date": dt.datetime.strptime(row["OBSERVATION DATE"], "%Y-%m-%d").date(),
            "time": time,
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
        return self._create_or_update(
            session, Checklist, identifier, last_edited, defaults
        )

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
        return self._create_or_update(
            session, Location, identifier, last_edited, defaults
        )

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
        return self._create_or_update(
            session, Species, identifier, last_edited, defaults
        )

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
        return self._create_or_update(
            session, Observation, identifier, last_edited, defaults
        )

    def load(self, path):
        if not os.path.exists(path):
            raise IOError('File "%s" does not exist' % path)

        sys.stdout.write("Loading eBird Basic Dataset from %s\n" % path)

        with Session(self.engine) as session:
            with open(path) as csvfile:
                added = updated = unchanged = loaded = 0
                date_loaded = dt.datetime.now()
                reader = csv.DictReader(csvfile, delimiter="\t")
                for row in reader:
                    last_edited = dt.datetime.fromisoformat(row["LAST EDITED DATE"])
                    observation = self._load_observation(session, last_edited, row)
                    if observation.created > date_loaded:
                        added += 1
                    elif observation.modified > date_loaded:
                        updated += 1
                    else:
                        unchanged += 1
                    loaded += 1
                    session.commit()
                    if loaded % 10 == 0:
                        sys.stdout.write("Records loaded: %d\r" % loaded)
                        sys.stdout.flush()

        sys.stdout.write("Records loaded: %d\n" % loaded)
        sys.stdout.write("%d records added\n" % added)
        sys.stdout.write("%d records updated\n" % updated)
        sys.stdout.write("%d records unchanged\n" % unchanged)
        sys.stdout.write("Loading completed successfully\n")


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
        stmt = select(model).where(model.identifier == identifier)
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
            obj = model(
                created=timestamp,
                modified=timestamp,
                edited=last_edited,
                identifier=identifier,
                **defaults,
            )
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
        return self._create_or_update(
            session, Observer, identifier, last_edited, defaults
        )

    def _load_checklist(self, session, last_edited, checklist):
        identifier = checklist["subId"]
        date_str = checklist["obsDt"].split(" ", 1)[0]
        date = dt.datetime.strptime(date_str, "%Y-%m-%d").date()
        if checklist["obsTimeValid"]:
            time_str = checklist["obsDt"].split(" ", 1)[1]
            time = dt.datetime.strptime(time_str, "%H:%M").time()
        else:
            time = None
        if "durationHrs" in checklist:
            duration = checklist["durationHrs"] * 60.0
        else:
            duration = None
        distance = checklist.get("distKm", None)
        area = checklist.get("areaHa", None)
        defaults = {
            "location": self._load_location(session, last_edited, checklist["loc"]),
            "observer": self._load_observer(session, last_edited, checklist),
            "observer_count": self._get_integer_value(
                checklist.get("numObservers", None)
            ),
            "group": "",
            "species_count": checklist["numSpecies"],
            "date": date,
            "time": time,
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
        return self._create_or_update(
            session, Checklist, identifier, last_edited, defaults
        )

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
        return self._create_or_update(
            session, Location, identifier, last_edited, defaults
        )

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
        return self._create_or_update(
            session, Observation, identifier, last_edited, defaults
        )

    def load_taxonomy(self):
        with Session(self.engine) as session:
            timestamp = dt.datetime.now()
            for row in get_taxonomy(self.api_key):
                session.add(
                    Species(
                        created=timestamp,
                        modified=timestamp,
                        edited=timestamp,
                        identifier="",
                        code=row["speciesCode"],
                        category=row["category"],
                        common_name=row["comName"],
                        scientific_name=row["sciName"],
                        local_name="",
                        subspecies_common_name="",
                        subspecies_scientific_name="",
                        subspecies_local_name="",
                        exotic_code="",
                    )
                )
            session.submit()

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
            for date in dates:
                sys.stdout.write("Date: %s\n" % date)
                for area in areas:
                    results = get_visits(self.api_key, area, date=date, max_results=200)
                    visits.extend(results)
                    sys.stdout.write(
                        "%s: %d checklists submitted\n" % (area, len(results))
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
                        observation = self._load_observation(
                            session, last_edited, checklist, observation
                        )
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


class MyDataLoader:
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
    def _create(session, model, values):
        timestamp = dt.datetime.now()
        obj = model(
            created=timestamp,
            modified=timestamp,
            edited=None,
            **values,
        )
        session.add(obj)
        return obj

    @staticmethod
    def _create_or_update(session, model, key, identifier, defaults):
        stmt = select(model).where(getattr(model, key) == identifier)
        timestamp = dt.datetime.now()
        if row := session.execute(stmt).first():
            obj = row[0]
            for key, value in defaults.items():
                setattr(obj, key, value)
            obj.modified = timestamp
            obj.edited = None
            session.add(obj)
        else:
            obj = model(
                created=timestamp,
                modified=timestamp,
                edited=None,
                identifier=identifier,
                **defaults,
            )
            session.add(obj)
        return obj

    def _load_observer(self, session, row):
        identifier = row["Observer"]
        values = {"name": row["Observer"]}
        return self._create_or_update(session, Observer, "name", identifier, values)

    def _load_checklist(self, session, row):
        identifier = row["Submission ID"]
        if value := row["Time"]:
            time = dt.datetime.strptime(value, "%H:%M %p").time()
        else:
            time = None
        defaults = {
            "location": self._load_location(session, row),
            "observer": self._load_observer(session, row),
            "observer_count": self._get_integer_value(row["Number of Observers"]),
            "group": "",
            "species_count": None,
            "date": dt.datetime.strptime(row["Date"], "%Y-%m-%d").date(),
            "time": time,
            "protocol": row["Protocol"],
            "protocol_code": "",
            "project_code": "",
            "duration": self._get_integer_value(row["Duration (Min)"]),
            "distance": self._get_decimal_value(row["Distance Traveled (km)"]),
            "area": self._get_decimal_value(row["Area Covered (ha)"]),
            "complete": self._get_boolean_value(row["All Obs Reported"]),
            "comments": row["Checklist Comments"] or "",
            "url": "",
        }
        return self._create_or_update(
            session, Checklist, "identifier", identifier, defaults
        )

    def _load_location(self, session, row):
        identifier = row["Location ID"]
        defaults = {
            "type": "",
            "name": row["Location"],
            "county": row["County"],
            "county_code": "",
            "state": row["State/Province"],
            "state_code": "",
            "country": "",
            "country_code": row["County"].split("-")[0],
            "iba_code": "",
            "bcr_code": "",
            "usfws_code": "",
            "atlas_block": "",
            "latitude": self._get_decimal_value(row["Latitude"]),
            "longitude": self._get_decimal_value(row["Longitude"]),
            "url": "",
        }
        return self._create_or_update(
            session, Location, "identifier", identifier, defaults
        )

    def _load_species(self, session, row):
        identifier = row["Taxonomic Order"]
        defaults = {
            "code": "",
            "order": row["Taxonomic Order"],
            "category": "",
            "common_name": row["Common Name"],
            "scientific_name": row["Scientific Name"],
            "local_name": "",
            "subspecies_common_name": "",
            "subspecies_scientific_name": "",
            "subspecies_local_name": "",
            "exotic_code": "",
        }
        return self._create_or_update(session, Species, "order", identifier, defaults)

    def _load_observation(self, session, row):
        if row["Count"].lower() == "x":
            count = None
        else:
            count = self._get_integer_value(row["Count"])
        defaults = {
            "identifier": "",
            "checklist": self._load_checklist(session, row),
            "species": self._load_species(session, row),
            "count": count,
            "breeding_code": row["Breeding Code"] or "",
            "breeding_category": "",
            "behavior_code": "",
            "age_sex": "",
            "media": len(row["ML Catalog Num`bers"] or "") > 0,
            "approved": None,
            "reviewed": None,
            "reason": "",
            "comments": row["Observation Details"] or "",
        }
        return self._create(session, Observation, defaults)

    def load(self, path, observer_name):
        if not os.path.exists(path):
            raise IOError('File "%s" does not exist' % path)

        sys.stdout.write("Loading My eBird Data from %s\n" % path)

        with Session(self.engine) as session:
            with open(path) as csvfile:
                loaded = 0
                reader = csv.DictReader(csvfile, delimiter=",")
                for row in reader:
                    row["Observer"] = observer_name
                    self._load_observation(session, row)
                    session.commit()
                    loaded += 1
                    if loaded % 10 == 0:
                        sys.stdout.write("Records added: %d\r" % loaded)
                        sys.stdout.flush()

        sys.stdout.write("Records added: %d\n" % loaded)
        sys.stdout.write("Loading completed successfully\n")
