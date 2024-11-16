import csv
import datetime as dt
import decimal
import os
import sys

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

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
