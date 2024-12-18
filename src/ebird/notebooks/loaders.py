import csv
import datetime as dt
import decimal
import json
import re
import sys
import traceback
from pathlib import Path
from typing import Any, Optional, TypeVar
from urllib.error import HTTPError, URLError

from ebird.api import get_checklist, get_taxonomy, get_visits
from sqlalchemy import Row, Select, select
from sqlalchemy.orm import Session

from .models import Checklist, Location, Observation, Observer, Species

Model = TypeVar("Model", Checklist, Location, Observation, Observer, Species)


def _boolean_value(value: Optional[str]) -> Optional[bool]:
    return bool(value) if value else None


def _integer_value(value: Optional[str]) -> Optional[int]:
    return int(value) if value else None


def _decimal_value(value: Optional[str]) -> Optional[decimal.Decimal]:
    return decimal.Decimal(value) if value else None


def _update(obj: Model, values: dict[str, Any]) -> Model:
    for key, value in values.items():
        setattr(obj, key, value)
    return obj


def _get_checklist_status(
    session: Session, identifier: str, last_edited: str
) -> tuple[bool, bool]:
    last_edited_date: dt.datetime = dt.datetime.fromisoformat(last_edited)
    stmt: Select[tuple[dt.datetime]]
    row: Row[tuple[dt.datetime]]
    new: bool
    modified: bool

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
        modified = False
    return new, modified


def _create_or_update_location(
    session: Session, identifier: str, values: dict[str, Any]
) -> Location:
    timestamp: dt.datetime = dt.datetime.now()
    row: Row[tuple[Location]]
    location: Location

    stmt: Select[tuple[Location]] = select(Location).where(
        Location.identifier == identifier
    )
    if row := session.execute(stmt).first():
        location = _update(row[0], values)
        location.modified = timestamp
    else:
        location = Location(created=timestamp, modified=timestamp, **values)
    session.add(location)
    return location


def _create_or_update_observer(
    session: Session, identifier: str, values: dict[str, Any]
) -> Observer:
    timestamp: dt.datetime = dt.datetime.now()
    row: Row[tuple[Observer]]
    observer: Observer

    stmt: Select[tuple[Observer]] = select(Observer).where(
        Observer.identifier == identifier
    )
    if row := session.execute(stmt).first():
        observer = _update(row[0], values)
        observer.modified = timestamp
    else:
        observer = Observer(created=timestamp, modified=timestamp, **values)
    session.add(observer)
    return observer


def _create_or_update_checklist(
    session: Session, identifier: str, values: dict[str, Any]
) -> Checklist:
    timestamp: dt.datetime = dt.datetime.now()
    row: Row[tuple[Checklist]]
    checklist: Checklist

    stmt: Select[tuple[Checklist]] = select(Checklist).where(
        Checklist.identifier == identifier
    )
    if row := session.execute(stmt).first():
        checklist = _update(row[0], values)
        checklist.modified = timestamp
    else:
        checklist = Checklist(created=timestamp, modified=timestamp, **values)
    session.add(checklist)
    return checklist


class BasicDatasetLoader:
    def __init__(self, session: Session) -> None:
        self.session: Session = session

    def _get_location(self, data: dict[str, str]) -> Location:
        identifier: str = data["LOCALITY ID"]

        values: dict[str, Any] = {
            "identifier": identifier,
            "type": data["LOCALITY TYPE"],
            "name": data["LOCALITY"],
            "county": data["COUNTY"],
            "county_code": data["COUNTY CODE"],
            "state": data["STATE"],
            "state_code": data["STATE CODE"],
            "country": data["COUNTRY"],
            "country_code": data["COUNTRY CODE"],
            "latitude": _decimal_value(data["LATITUDE"]),
            "longitude": _decimal_value(data["LONGITUDE"]),
            "iba_code": data["IBA CODE"],
            "bcr_code": data["BCR CODE"],
            "usfws_code": data["USFWS CODE"],
            "atlas_block": data["ATLAS BLOCK"],
            "url": "",
        }

        return _create_or_update_location(self.session, identifier, values)

    def _get_observer(self, data: dict[str, str]) -> Observer:
        identifier: str = data["OBSERVER ID"]

        values: dict[str, Any] = {
            "identifier": identifier,
            "name": "",
        }

        return _create_or_update_observer(self.session, identifier, values)

    def _get_species(self, data: dict[str, str]) -> Species:
        identifier = data["TAXON CONCEPT ID"]
        timestamp = dt.datetime.now()
        stmt: Select[tuple[Species]]
        row: Row[tuple[Species]]
        species: Species

        values: dict[str, Any] = {
            "modified": timestamp,
            "identifier": identifier,
            "code": "",
            "order": data["TAXONOMIC ORDER"],
            "category": data["CATEGORY"],
            "common_name": data["COMMON NAME"],
            "scientific_name": data["SCIENTIFIC NAME"],
            "local_name": "",
            "subspecies_common_name": data["SUBSPECIES COMMON NAME"],
            "subspecies_scientific_name": data["SUBSPECIES SCIENTIFIC NAME"],
            "subspecies_local_name": "",
            "exotic_code": data["EXOTIC CODE"],
        }

        stmt = select(Species).where(Species.identifier == identifier)  # noqa
        if row := self.session.execute(stmt).first():
            species = _update(row[0], values)
        else:
            species = Species(created=timestamp, **values)
        self.session.add(species)
        return species

    def _get_observation(
        self, data: dict[str, str], checklist: Checklist, species: Species
    ) -> Observation:
        identifier = data["GLOBAL UNIQUE IDENTIFIER"]
        timestamp = dt.datetime.now()
        count: Optional[int]
        stmt: Select[tuple[Observation]]
        row: Row[tuple[Observation]]
        observation: Observation

        if re.match(r"\d+", data["OBSERVATION COUNT"]):
            count = _integer_value(data["OBSERVATION COUNT"])
            if count == 0:
                count = None
        else:
            count = None

        values: dict[str, Any] = {
            "modified": timestamp,
            "edited": checklist.edited,
            "identifier": identifier,
            "checklist": checklist,
            "location": checklist.location,
            "observer": checklist.observer,
            "species": species,
            "count": count,
            "breeding_code": data["BREEDING CODE"],
            "breeding_category": data["BREEDING CATEGORY"],
            "behavior_code": data["BEHAVIOR CODE"],
            "age_sex": data["AGE/SEX"],
            "media": _boolean_value(data["HAS MEDIA"]),
            "approved": _boolean_value(data["APPROVED"]),
            "reviewed": _boolean_value(data["REVIEWED"]),
            "reason": data["REASON"],
            "comments": data["SPECIES COMMENTS"],
        }

        stmt = select(Observation).where(Observation.identifier == identifier)
        if row := self.session.execute(stmt).first():
            observation = row[0]
            if observation.edited < checklist.edited:
                observation = _update(row[0], values)
                self.session.add(observation)
        else:
            observation = Observation(created=timestamp, **values)
            self.session.add(observation)
        return observation

    def _get_checklist(
        self,
        row: dict[str, str],
        location: Location,
        observer: Observer,
    ) -> Checklist:
        identifier: str = row["SAMPLING EVENT IDENTIFIER"]
        edited: dt.datetime = dt.datetime.fromisoformat(row["LAST EDITED DATE"])
        time: Optional[dt.time]

        if value := row["TIME OBSERVATIONS STARTED"]:
            time = dt.datetime.strptime(value, "%H:%M:%S").time()
        else:
            time = None

        values: dict[str, Any] = {
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
            "duration": _integer_value(row["DURATION MINUTES"]),
            "distance": _decimal_value(row["EFFORT DISTANCE KM"]),
            "area": _decimal_value(row["EFFORT AREA HA"]),
            "complete": _boolean_value(row["ALL SPECIES REPORTED"]),
            "comments": row["TRIP COMMENTS"],
            "url": "",
        }

        return _create_or_update_checklist(self.session, identifier, values)

    def load(self, path: Path) -> None:
        if not path.exists():
            raise IOError('File "%s" does not exist' % path)

        sys.stdout.write("Loading eBird Basic Dataset from %s\n" % path)

        with open(path) as csvfile:
            added: int = 0
            updated: int = 0
            unchanged: int = 0
            loaded: int = 0
            new: bool
            modified: bool

            reader = csv.DictReader(csvfile, delimiter="\t")
            for row in reader:
                identifier: str = row["GLOBAL UNIQUE IDENTIFIER"]
                last_edited: str = row["LAST EDITED DATE"]

                new, modified = _get_checklist_status(
                    self.session, identifier, last_edited
                )

                if new or modified:
                    location: Location = self._get_location(row)
                    observer: Observer = self._get_observer(row)
                    checklist: Checklist = self._get_checklist(row, location, observer)
                    species: Species = self._get_species(row)
                    self._get_observation(row, checklist, species)

                    self.session.commit()

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
    def __init__(self, api_key: str, session: Session):
        self.api_key: str = api_key
        self.session: Session = session

    @staticmethod
    def _get_observation_global_identifier(row: dict[str, str]) -> str:
        return f"URN:CornellLabOfOrnithology:{row['projId']}:{row['obsId']}"

    def _fetch_visits(
        self,
        region: str,
        date: Optional[dt.date] = None,
        max_results: int = 200,
    ) -> dict:
        visits: dict

        sys.stdout.write("Fetching visits...\n")
        sys.stdout.write(f"Region: {region}\n")

        if date:
            sys.stdout.write(f"Date: {date}\n")

        if max_results == 200:
            sys.stdout.write(f"No. of checklists: {max_results} (Maximum allowed)\n")
        else:
            sys.stdout.write(f"No. of checklists: {max_results}\n")

        sys.stdout.flush()

        try:
            visits = get_visits(
                self.api_key, region, date=date, max_results=max_results
            )
            sys.stdout.write("Visits made: %d\n" % len(visits))
            sys.stdout.flush()
        except (URLError, HTTPError) as err:
            visits = dict()
            sys.stdout.write("Error: visits not fetched...\n")
            sys.stdout.write(err)
            sys.stdout.write("\n")
            sys.stdout.flush()

        return visits

    def _fetch_checklist(self, identifier: str) -> dict[str, Any]:
        data: dict[str, Any]

        try:
            sys.stdout.write(f"Fetching checklist: {identifier}\n")
            sys.stdout.flush()
            data = get_checklist(self.api_key, identifier)
        except (URLError, HTTPError):
            data = dict()
            sys.stdout.write(f"Checklist not fetched: {identifier}\n")
            sys.stdout.write("%{err}\n")
            sys.stdout.flush()
        return data

    def _get_location(self, data: dict[str, Any]) -> Location:
        identifier: str = data["locId"]

        values: dict[str, Any] = {
            "identifier": identifier,
            "type": "",
            "name": data["name"],
            "county": data.get("subnational2Name", ""),
            "county_code": data.get("subnational2Code", ""),
            "state": data["subnational1Name"],
            "state_code": data["subnational1Code"],
            "country": data["countryName"],
            "country_code": data["countryCode"],
            "iba_code": "",
            "bcr_code": "",
            "usfws_code": "",
            "atlas_block": "",
            "latitude": _decimal_value(data["latitude"]),
            "longitude": _decimal_value(data["longitude"]),
            "url": "",
        }

        return _create_or_update_location(self.session, identifier, values)

    def _get_observer(self, data: dict[str, Any]) -> Observer:
        # The observer's name is used as the unique identifier, even
        # though it is not necessarily unique. However this works until
        # better solution is found.
        name: str = data["userDisplayName"]
        timestamp: dt.datetime = dt.datetime.now()
        stmt: Select[tuple[Observer]]
        row: Row[tuple[Observer]]
        observer: Observer

        values: dict[str, Any] = {
            "modified": timestamp,
            "identifier": "",
            "name": name,
        }

        stmt = select(Observer).where(Observer.name == name)  # noqa
        if row := self.session.execute(stmt).first():
            observer = _update(row[0], values)
        else:
            observer = Observer(created=timestamp, **values)
        self.session.add(observer)
        return observer

    def _get_species(self, data: dict[str, Any]) -> Species:
        stmt: Select[tuple[Species]] = select(Species).where(
            Species.code == data["speciesCode"]
        )
        return self.session.execute(stmt).first()[0]

    def _get_observation(
        self, data: dict[str, Any], checklist: Checklist
    ) -> Observation:
        identifier: str = self._get_observation_global_identifier(data)
        timestamp: dt.datetime = dt.datetime.now()
        count: Optional[int]
        stmt: Select[tuple[Observation]]
        row: Row[tuple[Observation]]
        observation: Observation

        if re.match(r"\d+", data["howManyStr"]):
            count = _integer_value(data["howManyStr"])
            if count == 0:
                count = None
        else:
            count = None

        values: dict[str, Any] = {
            "modified": timestamp,
            "edited": checklist.edited,
            "identifier": identifier,
            "checklist": checklist,
            "location": checklist.location,
            "observer": checklist.observer,
            "species": self._get_species(data),
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

        stmt = select(Observation).where(Observation.identifier == identifier)
        if row := self.session.execute(stmt).first():
            observation = _update(row[0], values)
        else:
            observation = Observation(created=timestamp, **values)
        self.session.add(observation)
        return observation

    def _delete_orphans(self, checklist: Checklist) -> None:
        # If the checklist was updated, then any observations with
        # an edited date earlier than checklist edited date must
        # have been deleted.
        for observation in checklist.observations:
            if observation.edited < checklist.edited:
                self.session.delete(observation)
                species = observation.species
                count = observation.count
                sys.stdout.write(f"Observation deleted: {species} - {count}\n")
                sys.stdout.flush()

    def _get_checklist(
        self,
        checklist_data: dict[str, Any],
        location_data: dict[str, Any],
    ) -> Checklist:
        identifier: str = checklist_data["subId"]
        edited: dt.datetime = dt.datetime.fromisoformat(checklist_data["lastEditedDt"])
        checklist: Checklist

        date_str: str = checklist_data["obsDt"].split(" ", 1)[0]
        date: dt.date = dt.datetime.strptime(date_str, "%Y-%m-%d").date()

        time_str: str
        time: Optional[dt.time]

        if checklist_data["obsTimeValid"]:
            time_str = checklist_data["obsDt"].split(" ", 1)[1]
            time = dt.datetime.strptime(time_str, "%H:%M").time()
        else:
            time = None

        duration: Optional[str]

        if "durationHrs" in checklist_data:
            duration = checklist_data["durationHrs"] * 60.0
        else:
            duration = None

        distance: str = checklist_data.get("distKm")
        area: str = checklist_data.get("areaHa")

        values = {
            "identifier": identifier,
            "edited": edited,
            "location": self._get_location(location_data),
            "observer": self._get_observer(checklist_data),
            "observer_count": _integer_value(checklist_data.get("numObservers")),
            "group": "",
            "species_count": checklist_data["numSpecies"],
            "date": date,
            "time": time,
            "protocol": "",
            "protocol_code": checklist_data["protocolId"],
            "project_code": checklist_data["projId"],
            "duration": _integer_value(duration),
            "distance": _decimal_value(distance),
            "area": _decimal_value(area),
            "complete": checklist_data.get("allObsReported", False),
            "comments": "",
            "url": "",
        }

        checklist = _create_or_update_checklist(self.session, identifier, values)

        for observation_data in checklist_data["obs"]:
            try:
                self._get_observation(observation_data, checklist)
            except Exception as err:  # noqa
                sys.stdout.write("----\n")
                sys.stdout.write("Observation not added...\n")
                sys.stdout.write("\n")
                sys.stdout.write(traceback.format_exc())
                sys.stdout.write("\n")
                sys.stdout.write(json.dumps(observation_data))
                sys.stdout.write("\n\n")
                sys.stdout.flush()

        return checklist

    def load(
        self,
        region: str,
        date: Optional[dt.date] = None,
        max_results: int = 200,
    ) -> None:
        added: int = 0
        updated: int = 0
        unchanged: int = 0
        total: int

        for visit in self._fetch_visits(region, date, max_results):
            if (data := self._fetch_checklist(visit["subId"])) is None:
                continue

            identifier: str = visit["subId"]
            last_edited: str = data["lastEditedDt"]
            new: bool
            modified: bool

            new, modified = _get_checklist_status(self.session, identifier, last_edited)
            if new or modified:
                checklist = self._get_checklist(data, visit["loc"])
                if modified:
                    self._delete_orphans(checklist)

            if new:
                added += 1
            elif modified:
                updated += 1
            else:
                unchanged += 1

        self.session.commit()

        total = added + updated + unchanged

        sys.stdout.write(f"{total} checklists fetched\n")
        sys.stdout.write(f"{added} checklists added\n")
        sys.stdout.write(f"{updated} checklists updated\n")
        sys.stdout.write(f"{unchanged} checklists unchanged\n")


class SpeciesLoader:
    def __init__(self, api_key: str, session: Session):
        self.api_key: str = api_key
        self.session: Session = session

    def load(self):
        timestamp: dt.datetime = dt.datetime.now()
        row: dict[str, Any]

        for row in get_taxonomy(self.api_key):
            self.session.add(
                Species(
                    created=timestamp,
                    modified=timestamp,
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
        self.session.commit()


class MyDataLoader:
    def __init__(self, session: Session):
        self.session: Session = session

    def _get_location(self, data: dict[str, Any]) -> Location:
        identifier: str = data["Location ID"]

        values: dict[str, Any] = {
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
            "latitude": _decimal_value(data["Latitude"]),
            "longitude": _decimal_value(data["Longitude"]),
            "url": "",
        }

        return _create_or_update_location(self.session, identifier, values)

    def _get_observer(self, name: str) -> Observer:
        timestamp: dt.datetime = dt.datetime.now()
        stmt: Select[tuple[Observer]]
        row: Row[tuple[Observer]]
        observer: Observer

        values = {"modified": timestamp, "identifier": "", "name": name}

        stmt = select(Observer).where(Observer.name == name)  # noqa
        if row := self.session.execute(stmt).first():
            observer = _update(row[0], values)
        else:
            observer = Observer(created=timestamp, **values)
        self.session.add(observer)
        return observer

    def _get_species(self, data: dict[str, Any]) -> Species:
        order = data["Taxonomic Order"]
        timestamp = dt.datetime.now()
        stmt: Select[tuple[Species]]
        row: Row[tuple[Species]]
        species: Species

        values: dict[str, Any] = {
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

        stmt = select(Species).where(Species.order == order)  # noqa
        if row := self.session.execute(stmt).first():
            species = _update(row[0], values)
        else:
            species = Species(created=timestamp, **values)
        self.session.add(species)
        return species

    def _get_observation(
        self, data: dict[str, Any], checklist: Checklist
    ) -> Observation:
        timestamp: dt.datetime = dt.datetime.now()
        count: Optional[int]

        if re.match(r"\d+", data["Count"]):
            count = _integer_value(data["Count"])
            if count == 0:
                count = None
        else:
            count = None

        values: dict[str, Any] = {
            "modified": timestamp,
            "edited": checklist.edited,
            "identifier": "",
            "species": self._get_species(data),
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

        observation: Observation = Observation(created=timestamp, **values)
        self.session.add(observation)
        return observation

    def _get_checklist(
        self,
        data: dict[str, Any],
        location: Location,
        observer: Observer,
    ) -> Checklist:
        identifier: str = data["Submission ID"]
        time: Optional[dt.time]

        if value := data["Time"]:
            time = dt.datetime.strptime(value, "%H:%M %p").time()
        else:
            time = None

        values: dict[str, Any] = {
            "identifier": identifier,
            "location": location,
            "observer": observer,
            "observer_count": _integer_value(data["Number of Observers"]),
            "group": "",
            "species_count": None,
            "date": dt.datetime.strptime(data["Date"], "%Y-%m-%d").date(),
            "time": time,
            "protocol": data["Protocol"],
            "protocol_code": "",
            "project_code": "",
            "duration": _integer_value(data["Duration (Min)"]),
            "distance": _decimal_value(data["Distance Traveled (km)"]),
            "area": _decimal_value(data["Area Covered (ha)"]),
            "complete": data["All Obs Reported"] == "1",
            "comments": data["Checklist Comments"] or "",
            "url": "",
        }

        return _create_or_update_checklist(self.session, identifier, values)

    def load(self, path: Path, observer_name: str) -> None:
        if not path.exists():
            raise IOError('File "%s" does not exist' % path)

        sys.stdout.write("Loading My eBird Data from %s\n" % path)

        with open(path) as csvfile:
            loaded: int = 0
            reader = csv.DictReader(csvfile, delimiter=",")
            observer: Observer = self._get_observer(observer_name)
            for data in reader:
                location: Location = self._get_location(data)
                checklist: Checklist = self._get_checklist(data, location, observer)
                self._get_observation(data, checklist)

                self.session.commit()

                loaded += 1

                if loaded % 10 == 0:
                    sys.stdout.write("Records added: %d\r" % loaded)
                    sys.stdout.flush()

        sys.stdout.write("Records added: %d\n" % loaded)
        sys.stdout.write("Loading completed successfully\n")
