import csv
import datetime as dt
import decimal
import os
import re
import sys
from urllib.error import HTTPError, URLError

from ebird.api import get_checklist, get_taxonomy, get_visits
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from .models import Checklist, Location, Observation, Observer, Species


class BasicDatasetLoader:
    def __init__(self, db_url):
        self.engine = create_engine(db_url)

    @staticmethod
    def _cast_value(value, cast):
        return cast(value) if value else None

    def _boolean_value(self, value):
        return self._cast_value(value, bool)

    def _integer_value(self, value):
        return self._cast_value(value, int)

    def _decimal_value(self, value):
        return self._cast_value(value, decimal.Decimal)

    @staticmethod
    def _update(obj, values):
        for key, value in values.items():
            setattr(obj, key, value)
        return obj

    @staticmethod
    def _get_checklist_status(
        session, identifier: str, last_edited: str
    ) -> tuple[bool, bool]:
        last_edited_date = dt.datetime.fromisoformat(last_edited)

        stmt = select(Checklist.edited).where(Checklist.identifier == identifier)
        if row := session.execute(stmt).first():
            if row[0] < last_edited_date:
                new = False
                modified = True
            else:
                new = False
                modified = False
        else:
            new = True
            modified = True
        return new, modified

    def _get_location(self, session, row):
        identifier = row["LOCALITY ID"]
        timestamp = dt.datetime.now()

        values = {
            "modified": timestamp,
            "identifier": identifier,
            "type": row["LOCALITY TYPE"],
            "name": row["LOCALITY"],
            "county": row["COUNTY"],
            "county_code": row["COUNTY CODE"],
            "state": row["STATE"],
            "state_code": row["STATE CODE"],
            "country": row["COUNTRY"],
            "country_code": row["COUNTRY CODE"],
            "latitude": self._decimal_value(row["LATITUDE"]),
            "longitude": self._decimal_value(row["LONGITUDE"]),
            "iba_code": row["IBA CODE"],
            "bcr_code": row["BCR CODE"],
            "usfws_code": row["USFWS CODE"],
            "atlas_block": row["ATLAS BLOCK"],
            "url": "",
        }

        stmt = select(Location).where(Location.identifier == identifier)
        if row := session.execute(stmt).first():
            location = self._update(row[0], values)
        else:
            location = Location(created=timestamp, **values)
        session.add(location)
        return location

    def _get_observer(self, session, row):
        identifier = row["OBSERVER ID"]
        timestamp = dt.datetime.now()

        values = {"identifier": identifier, "modified": timestamp, "name": ""}

        stmt = select(Observer).where(Observer.identifier == identifier)
        if row := session.execute(stmt).first():
            observer = self._update(row[0], values)
        else:
            observer = Observer(created=timestamp, **values)
        session.add(observer)
        return observer

    def _get_species(self, session, row):
        identifier = row["TAXON CONCEPT ID"]
        timestamp = dt.datetime.now()

        values = {
            "modified": timestamp,
            "identifier": identifier,
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

        stmt = select(Species).where(Species.identifier == identifier)
        if row := session.execute(stmt).first():
            species = self._update(row[0], values)
        else:
            species = Species(created=timestamp, **values)
        session.add(species)
        return species

    def _get_observation(self, session, row, checklist):
        identifier = row["GLOBAL UNIQUE IDENTIFIER"]
        timestamp = dt.datetime.now()

        if re.match(r"\d+", row["OBSERVATION COUNT"]):
            count = self._integer_value(row["OBSERVATION COUNT"])
            if count == 0:
                count = None
        else:
            count = None

        values = {
            "modified": timestamp,
            "edited": checklist.edited,
            "identifier": identifier,
            "checklist": checklist,
            "location": checklist.location,
            "observer": checklist.observer,
            "species": self._get_species(session, row),
            "count": count,
            "breeding_code": row["BREEDING CODE"],
            "breeding_category": row["BREEDING CATEGORY"],
            "behavior_code": row["BEHAVIOR CODE"],
            "age_sex": row["AGE/SEX"],
            "media": self._boolean_value(row["HAS MEDIA"]),
            "approved": self._boolean_value(row["APPROVED"]),
            "reviewed": self._boolean_value(row["REVIEWED"]),
            "reason": row["REASON"],
            "comments": row["SPECIES COMMENTS"],
        }

        stmt = select(Observation).where(Observation.identifier == identifier)
        if row := session.execute(stmt).first():
            observation = row[0]
            if observation.edited < checklist.edited:
                observation = self._update(row[0], values)
                session.add(observation)
        else:
            observation = Observation(created=timestamp, **values)
            session.add(observation)
        return observation

    def _get_checklist(self, session, row, location, observer):
        identifier = row["SAMPLING EVENT IDENTIFIER"]
        timestamp = dt.datetime.now()
        edited = dt.datetime.fromisoformat(row["LAST EDITED DATE"])

        if value := row["TIME OBSERVATIONS STARTED"]:
            time = dt.datetime.strptime(value, "%H:%M:%S").time()
        else:
            time = None

        values = {
            "modified": timestamp,
            "identifier": identifier,
            "edited": edited,
            "location": location,
            "observer": observer,
            "group": row["GROUP IDENTIFIER"],
            "observer_count": row["NUMBER OBSERVERS"],
            "date": dt.datetime.strptime(row["OBSERVATION DATE"], "%Y-%m-%d").date(),
            "time": time,
            "protocol": row["PROTOCOL TYPE"],
            "protocol_code": row["PROTOCOL CODE"],
            "project_code": row["PROJECT CODE"],
            "duration": self._integer_value(row["DURATION MINUTES"]),
            "distance": self._decimal_value(row["EFFORT DISTANCE KM"]),
            "area": self._decimal_value(row["EFFORT AREA HA"]),
            "complete": self._boolean_value(row["ALL SPECIES REPORTED"]),
            "comments": row["TRIP COMMENTS"],
            "url": "",
        }

        stmt = select(Checklist).where(Checklist.identifier == identifier)
        if row := session.execute(stmt).first():
            checklist = self._update(row[0], values)
        else:
            checklist = Checklist(created=timestamp, **values)
        session.add(checklist)
        return checklist

    def load(self, path):
        if not os.path.exists(path):
            raise IOError('File "%s" does not exist' % path)

        sys.stdout.write("Loading eBird Basic Dataset from %s\n" % path)

        with Session(self.engine) as session:
            with open(path) as csvfile:
                added = updated = unchanged = loaded = 0
                reader = csv.DictReader(csvfile, delimiter="\t")
                for row in reader:
                    identifier = row["GLOBAL UNIQUE IDENTIFIER"]
                    last_edited = row["LAST EDITED DATE"]

                    new, modified = self._get_checklist_status(
                        session, identifier, last_edited
                    )

                    if new or modified:
                        location = self._get_location(session, row)
                        observer = self._get_observer(session, row)
                        checklist = self._get_checklist(
                            session, row, location, observer
                        )
                        self._get_observation(session, row, checklist)

                        session.commit()

                    if new:
                        added += 1
                    elif modified:
                        updated += 1
                    else:
                        unchanged += 1

                    loaded += 1

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
            if count == 0:
                count = None
        else:
            count = None
        defaults = {
            "checklist": self._load_checklist(session, last_edited, checklist),
            "species": self._get_species(session, observation),
            "observer": self._load_observer(session, last_edited, checklist),
            "location": self._load_location(session, last_edited, checklist["loc"]),
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
            session.commit()

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
                    try:
                        results = get_visits(
                            self.api_key, area, date=date, max_results=200
                        )
                        visits.extend(results)
                        sys.stdout.write(
                            "%s: %d checklists submitted\n" % (area, len(results))
                        )
                        sys.stdout.flush()
                    except (URLError, HTTPError) as err:
                        sys.stdout.write(
                            "Error: Could not fetch visits for %s\n" % area
                        )
                        sys.stdout.write("%s\n" % str(err))
                        sys.stdout.flush()

            sys.stdout.write("Total number of checklists: %d\n" % len(visits))
            sys.stdout.write("Fetching checklists...\n")

            for visit in visits:
                try:
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
                except (URLError, HTTPError) as err:
                    sys.stdout.write(
                        "Error: Could not fetch checklist %s\n" % identifier
                    )
                    sys.stdout.write("%s\n" % str(err))
                    sys.stdout.flush()

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
    def _cast_value(value, cast):
        return cast(value) if value else None

    def _boolean_value(self, value):
        return self._cast_value(value, bool)

    def _integer_value(self, value):
        return self._cast_value(value, int)

    def _decimal_value(self, value):
        return self._cast_value(value, decimal.Decimal)

    @staticmethod
    def _update(obj, values):
        for key, value in values.items():
            setattr(obj, key, value)
        return obj

    def _get_location(self, session, data):
        identifier = data["Location ID"]
        timestamp = dt.datetime.now()

        values = {
            "modified": timestamp,
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
            "latitude": self._decimal_value(data["Latitude"]),
            "longitude": self._decimal_value(data["Longitude"]),
            "url": "",
        }

        stmt = select(Location).where(Location.identifier == identifier)
        if data := session.execute(stmt).first():
            location = self._update(data[0], values)
        else:
            location = Location(created=timestamp, **values)
        session.add(location)
        return location

    def _get_observer(self, session, name):
        timestamp = dt.datetime.now()

        values = {"modified": timestamp, "identifier": "", "name": name}

        stmt = select(Observer).where(Observer.name == name)
        if data := session.execute(stmt).first():
            observer = self._update(data[0], values)
        else:
            observer = Observer(created=timestamp, **values)
        session.add(observer)
        return observer

    def _get_species(self, session, data):
        order = data["Taxonomic Order"]
        timestamp = dt.datetime.now()

        values = {
            "modified": timestamp,
            "identifier": "",
            "code": "",
            "order": data["Taxonomic Order"],
            "category": "",
            "common_name": data["Common Name"],
            "scientific_name": data["Scientific Name"],
            "local_name": "",
            "subspecies_common_name": "",
            "subspecies_scientific_name": "",
            "subspecies_local_name": "",
            "exotic_code": "",
        }

        stmt = select(Species).where(Species.order == order)
        if data := session.execute(stmt).first():
            species = self._update(data[0], values)
        else:
            species = Species(created=timestamp, **values)
        session.add(species)
        return species

    def _get_observation(self, session, data, checklist):
        timestamp = dt.datetime.now()

        if re.match(r"\d+", data["Count"]):
            count = self._integer_value(data["Count"])
            if count == 0:
                count = None
        else:
            count = None

        values = {
            "modified": timestamp,
            "edited": checklist.edited,
            "identifier": "",
            "species": self._get_species(session, data),
            "checklist": checklist,
            "location": checklist.location,
            "observer": checklist.observer,
            "count": count,
            "breeding_code": data["Breeding Code"] or "",
            "breeding_category": "",
            "behavior_code": "",
            "age_sex": "",
            "media": len(data["ML Catalog Num`bers"] or "") > 0,
            "approved": None,
            "reviewed": None,
            "reason": "",
            "comments": data["Observation Details"] or "",
        }

        observation = Observation(created=timestamp, **values)
        session.add(observation)
        return observation

    def _get_checklist(self, session, data, observer):
        identifier = data["Submission ID"]
        timestamp = dt.datetime.now()

        if value := data["Time"]:
            time = dt.datetime.strptime(value, "%H:%M %p").time()
        else:
            time = None

        values = {
            "modified": timestamp,
            "identifier": identifier,
            "location": self._get_location(session, data),
            "observer": observer,
            "observer_count": self._integer_value(data["Number of Observers"]),
            "group": "",
            "species_count": None,
            "date": dt.datetime.strptime(data["Date"], "%Y-%m-%d").date(),
            "time": time,
            "protocol": data["Protocol"],
            "protocol_code": "",
            "project_code": "",
            "duration": self._integer_value(data["Duration (Min)"]),
            "distance": self._decimal_value(data["Distance Traveled (km)"]),
            "area": self._decimal_value(data["Area Covered (ha)"]),
            "complete": self._boolean_value(data["All Obs Reported"]),
            "comments": data["Checklist Comments"] or "",
            "url": "",
        }

        stmt = select(Checklist).where(Checklist.identifier == identifier)
        if data := session.execute(stmt).first():
            checklist = self._update(data[0], values)
        else:
            checklist = Checklist(created=timestamp, **values)
        session.add(checklist)
        return checklist

    def load(self, path, observer_name):
        if not os.path.exists(path):
            raise IOError('File "%s" does not exist' % path)

        sys.stdout.write("Loading My eBird Data from %s\n" % path)

        with Session(self.engine) as session:
            with open(path) as csvfile:
                loaded = 0
                reader = csv.DictReader(csvfile, delimiter=",")
                observer = self._get_observer(session, observer_name)
                for data in reader:
                    checklist = self._get_checklist(session, data, observer)
                    self._get_observation(session, data, checklist)

                    session.commit()

                    loaded += 1

                    if loaded % 10 == 0:
                        sys.stdout.write("Records added: %d\r" % loaded)
                        sys.stdout.flush()

        sys.stdout.write("Records added: %d\n" % loaded)
        sys.stdout.write("Loading completed successfully\n")
