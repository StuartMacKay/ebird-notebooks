import datetime as dt
import logging
import re
import socket

from decimal import Decimal
from typing import List, Optional, Tuple
from urllib.error import HTTPError, URLError

from django.utils.timezone import get_default_timezone
from ebird.api import get_checklist, get_location, get_regions, get_visits, get_taxonomy
from ebird.api.constants import API_MAX_RESULTS

from checklists.models import (
    Checklist,
    Country,
    Location,
    Observation,
    Observer,
    Region,
    Species,
    District,
)

logger = logging.getLogger(__name__)


def str2datetime(value: str) -> dt.datetime:
    return dt.datetime.fromisoformat(value).replace(tzinfo=get_default_timezone())


class APILoader:
    """
    The APILoader downloads checklists from the eBird API and saves
    them to the database.

    Arguments:

        api_key: Your key to access the eBird API.
            Your can request a key at https://ebird.org/data/download.
            You will need an eBird account to do so.

        locale: The language to load for Species common names.
            The default is English.. ebird.api.get_taxonomy_locales returns
            the complete list of languages supported by eBird.

        timeout: The timeout, in seconds, to use when connecting to the
            eBird servers.

    The eBird API limits the number of records returned to 200. When downloading
    the visits for a given region if 200 hundred records are returned then it is
    assumed there are more and the loader will fetch the sub-regions and download
    the visits for each, repeating the process if necessary. To give an extreme
    example if you download the visits for the United States, "US", then the API
    will always return 200 results and the loader then download the visits to
    each of the 50 states and then each of the 3143 counties. DON'T TRY THIS
    AT HOME. Even if you don't get banned, if you melt the eBird servers, then
    karma will ensure bad things happen to you.

    Just occasionally, when fetching data from the eBird API, the connection will
    freeze and the APILoader will sit there doing nothing. The timeout will force
    the connection to be dropped, so you can try again. The APILoader does not
    retry making the connection. Connection freezes are sufficiently rare that
    it's not worth adding code to handle this, for now.

    """

    def __init__(self, api_key: str, locale: str, timeout: int = 30):
        self.api_key: str = api_key
        self.locale: str = locale
        socket.setdefaulttimeout(timeout)

    @staticmethod
    def is_checklist(identifier: str) -> bool:
        return Checklist.objects.filter(identifier=identifier).exists()

    def add_checklist(self, data: dict) -> Tuple[Checklist, bool]:
        identifier: str = data["subId"]
        created: dt.datetime = str2datetime(data["creationDt"])
        edited: dt.datetime = str2datetime(data["lastEditedDt"])
        started: dt.datetime = str2datetime(data["obsDt"])
        location: Location = self.get_location(data)
        checklist: Checklist

        values: dict = {
            "created": created,
            "edited": edited,
            "country": location.country,
            "region": location.region,
            "district": location.district,
            "area": location.area,
            "location": location,
            "observer": self.get_observer(data),
            "observer_count": None,
            "group": "",
            "species_count": data["numSpecies"],
            "date": started.date(),
            "time": None,
            "started": started,
            "protocol": "",
            "protocol_code": data["protocolId"],
            "project_code": data["projId"],
            "duration": None,
            "complete": data["allObsReported"],
            "comments": "",
            "url": "https://ebird.org/checklist/%s" % identifier,
        }

        if data["obsTimeValid"]:
            values["time"] = started.time()

        if "numObservers" in data:
            values["observer_count"] = int(data["numObservers"])

        if duration := data.get("durationHrs"):
            values["duration"] = int(duration * 60.0)

        if data["protocolId"] == "P22":
            dist: str = data["effortDistanceKm"]
            values["distance"] = round(Decimal(dist), 3)
        elif data["protocolId"] == "P23":
            coverage: str = data["effortAreaHa"]
            values["coverage"] = round(Decimal(coverage), 3)

        if "comments" in data:
            values["comments"] = data["comments"]

        added: bool = False

        if checklist := Checklist.objects.filter(identifier=identifier).first():
            for key, value in values.items():
                setattr(checklist, key, value)
            checklist.save()
        else:
            checklist = Checklist.objects.create(identifier=identifier, **values)
            added = True

        for observation_data in data["obs"]:
            self.add_observation(observation_data, checklist)

        for observation in checklist.observations.filter(edited__lt=edited):  # pyright: ignore [reportAttributeAccessIssue]
            logger.info(
                "Deleting observation: %s",
                identifier,
                extra={
                    "identifier": identifier,
                    "species": observation.species.common_name,
                    "count": observation.count,
                },
            )
            observation.delete()

        return checklist, added

    @staticmethod
    def add_country(data: dict) -> Country:
        code: str = data["countryCode"]
        country: Country

        values: dict = {
            "name": data["countryName"],
            "place": data["countryName"],
        }

        if country := Country.objects.filter(code=code).first():
            for key, value in values.items():
                setattr(country, key, value)
            country.save()
        else:
            country = Country.objects.create(code=code, **values)

        return country

    @staticmethod
    def add_region(data: dict) -> Region:
        code: str = data["subnational1Code"]
        region: Region

        values: dict = {
            "name": data["subnational1Name"],
            "place": "%s, %s" % (data["subnational1Name"], data["countryName"]),
        }

        if region := Region.objects.filter(code=code).first():
            for key, value in values.items():
                setattr(region, key, value)
            region.save()
        else:
            region = Region.objects.create(code=code, **values)

        return region

    @staticmethod
    def add_district(data: dict) -> District:
        code: str = data["subnational2Code"]
        district: District

        values: dict = {
            "name": data["subnational2Name"],
            "place": "%s, %s, %s"
            % (data["subnational2Name"], data["subnational1Name"], data["countryName"]),
        }

        if district := District.objects.filter(code=code).first():
            for key, value in values.items():
                setattr(district, key, value)
            district.save()
        else:
            district = District.objects.create(code=code, **values)

        return district

    def add_location(self, data: dict) -> Location:
        identifier: str = data["locId"]
        location: Location

        values: dict = {
            "identifier": identifier,
            "type": "",
            "name": data["name"],
            "district": None,
            "region": self.add_region(data),
            "country": self.add_country(data),
            "hotspot": data["isHotspot"],
            "iba_code": "",
            "bcr_code": "",
            "usfws_code": "",
            "atlas_block": "",
            "latitude": Decimal(data["latitude"]),
            "longitude": Decimal(data["longitude"]),
            "url": "https://ebird.org/region/%s" % identifier,
        }

        if "subnational2Code" in data:
            values["district"] = self.add_district(data)

        if location := Location.objects.filter(identifier=identifier).first():
            for key, value in values.items():
                setattr(location, key, value)
            location.save()
        else:
            location = Location.objects.create(**values)

        return location

    def add_observation(self, data: dict, checklist: Checklist) -> Observation:
        identifier: str = data["obsId"]
        observation: Observation
        species: Species = self.get_species(data)

        values: dict = {
            "edited": checklist.edited,
            "identifier": identifier,
            "checklist": checklist,
            "country": checklist.country,
            "region": checklist.region,
            "district": checklist.district,
            "area": checklist.area,
            "location": checklist.location,
            "observer": checklist.observer,
            "species": species,
            "identified": species.is_identified(),
            "date": checklist.date,
            "count": None,
            "breeding_code": "",
            "breeding_category": "",
            "behavior_code": "",
            "age_sex": "",
            "media": False,
            "approved": None,
            "reviewed": None,
            "reason": "",
            "comments": "",
            "urn": self.get_urn(checklist.project_code, data),
        }

        if re.match(r"\d+", data["howManyStr"]):
            values["count"] = int(data["howManyStr"]) or None

        if "comments" in data:
            values["comments"] = data["comments"]

        if observation := Observation.objects.filter(identifier=identifier).first():
            for key, value in values.items():
                setattr(observation, key, value)
            observation.save()
        else:
            observation = Observation.objects.create(**values)
        return observation

    @staticmethod
    def add_observer(data: dict) -> Observer:
        name: str = data["userDisplayName"]
        observer, _ = Observer.objects.get_or_create(name=name)
        return observer

    @staticmethod
    def add_species(data: dict) -> Species:
        code: str = data["speciesCode"]
        species: Species

        values: dict = {
            "taxon_order": int(data["taxonOrder"]),
            "order": data.get("order", ""),
            "category": data["category"],
            "family_code": data.get("familyCode", ""),
            "common_name": data["comName"],
            "scientific_name": data["sciName"],
            "family_common_name": data.get("familyComName", ""),
            "family_scientific_name": data.get("familySciName", ""),
            "subspecies_common_name": "",
            "subspecies_scientific_name": "",
            "exotic_code": "",
            "data": {"common_name": {}},
        }

        if species := Species.objects.filter(species_code=code).first():
            for key, value in values.items():
                setattr(species, key, value)
            species.save()
        else:
            species = Species.objects.create(species_code=code, **values)

        return species

    @staticmethod
    def get_urn(project_id, row: dict) -> str:
        return f"URN:CornellLabOfOrnithology:{project_id}:{row['obsId']}"

    def get_location(self, data: dict) -> Location:
        identifier: str = data["locId"]
        location: Location = Location.objects.filter(identifier=identifier).first()
        if location is None:
            location = self.load_location(identifier)
        return location

    @staticmethod
    def get_observer(data: dict) -> Observer:
        name: str = data["userDisplayName"]
        observer: Observer = Observer.objects.filter(name=name).first()
        if observer is None:
            observer = Observer.objects.create(name=name)
        return observer

    def get_species(self, data: dict) -> Species:
        code: str = data["speciesCode"]
        species: Species
        if (species := Species.objects.filter(species_code=code).first()) is None:
            species = self.load_species(code)
        return species

    def fetch_checklist(self, identifier: str) -> dict:
        data: dict = get_checklist(self.api_key, identifier)
        return data

    def fetch_species(self, code: str, locale: str) -> dict:
        logger.info(
            "Fetching species: %s, %s",
            code,
            locale,
            extra={"code": code, "locale": locale},
        )
        return get_taxonomy(self.api_key, locale=locale, species=code)[0]

    def fetch_subregions(self, region: str) -> List[str]:
        logger.info(
            "Fetching sub-regions: %s",
            region,
            extra={"region": region},
        )
        region_types: list = ["subnational1", "subnational2", None]
        levels: int = len(region.split("-", 2))
        region_type: Optional[str] = region_types[levels - 1]

        if region_type:
            items: list = get_regions(self.api_key, region_type, region)
            sub_regions = [item["code"] for item in items]
        else:
            sub_regions = []

        return sub_regions

    def fetch_visits(self, region: str, date: Optional[dt.date] = None):
        visits = []

        results: list = get_visits(
            self.api_key, region, date=date, max_results=API_MAX_RESULTS
        )

        if len(results) == API_MAX_RESULTS:
            if sub_regions := self.fetch_subregions(region):
                for sub_region in sub_regions:
                    logger.info(
                        "Loading checklists for sub-regions: %s, %s",
                        sub_region,
                        date,
                        extra={"region": sub_region, "date": date},
                    )
                    visits.extend(self.fetch_visits(sub_region, date))
            else:
                # No more sub-regions, issue a warning and return the results
                visits.extend(results)
                logger.warning(
                    "Loading checklists - API limit reached: %s, %s",
                    region,
                    date,
                    extra={"region": region, "date": date},
                )
        else:
            visits.extend(results)

        return visits

    def fetch_location(self, identifier: str) -> dict:
        return get_location(self.api_key, identifier)

    def load_species(self, code: str) -> Species:
        """
        Load the species with the eBird code.

        Arguments:
            code: the eBird code for the species, e.g. 'horlar' (Horned Lark).

        """

        logger.info("Loading species: %s", code, extra={"code": code})

        data: dict = self.fetch_species(code, self.locale)
        species = self.add_species(data)

        return species

    def load_location(self, identifier: str) -> Location:
        """
        Load the location with the given identifier.

        Arguments:
            identifier; the eBird identifier for the location, e.g. "L901738".

        """
        logger.info(
            "Loading location: %s", identifier, extra={"identifier": identifier}
        )
        data: dict = self.fetch_location(identifier)
        return self.add_location(data)

    def load_checklist(self, identifier: str) -> Tuple[Checklist, bool]:
        """
        Load the checklist with the given identifier.

        IMPORTANT: If the Location does not exist then it will be created,
        and a warning is logged. The data returned by the API  only contains
        the identifier and the state code. You can update the location record
        using the load_location() method, but this only works for hotspots.
        If the location is private then you will have to add the information
        in the Django Admin or shell.

        The Observer is also created if it does not exist. However, since the
        API only ever returns the observer's name, this is not a problem. A
        warning is still logged, in case the frequency at which this occurs
        becomes useful at some point.

        Arguments:
            identifier: the eBird identifier for the checklist, e.g. "S318722167"

        """
        logger.info(
            "Loading checklist: %s", identifier, extra={"identifier": identifier}
        )
        data: dict = self.fetch_checklist(identifier)
        return self.add_checklist(data)

    def load_checklists(self, region: str, date: dt.date, new_only: bool) -> None:
        """
        Load all the checklists submitted for a region for a given date.

        Arguments:
            region: The code for a national, subnational1, subnational2
                 area or hotspot identifier. For example, US, US-NY,
                 US-NY-109, or L1379126, respectively.

            date: The date the observations were made.

            new_only: If true, Load only new checklists, otherwise load all.

        """
        scope = "new" if new_only else "all"

        logger.info(
            "Loading %s checklists: %s, %s",
            scope,
            region,
            date,
            extra={"region": region, "date": date, "scope": scope},
        )
        visits: list[dict]
        number_of_visits: int = 0
        locations: dict = {}
        checklists: List[str] = []
        added: int = 0
        loaded: int = 0

        try:
            visits = self.fetch_visits(region, date)
            number_of_visits = len(visits)

            for visit in visits:
                location = visit["loc"]
                identifier = location["locId"]
                locations[identifier] = location

            if new_only:
                for visit in visits:
                    identifier = visit["subId"]
                    if not self.is_checklist(identifier):
                        checklists.append(identifier)
            else:
                for visit in visits:
                    identifier = visit["subId"]
                    checklists.append(identifier)

            for data in locations.values():
                self.add_location(data)

            for identifier in checklists:
                _, created = self.load_checklist(identifier)
                if created:
                    added += 1
                loaded += 1

            logger.info(
                "Loading %s checklists succeeded: %s, %s",
                scope,
                region,
                date,
                extra={
                    "region": region,
                    "date": date,
                    "scope": scope,
                    "visits": number_of_visits,
                    "added": added,
                    "loaded": loaded,
                },
            )

        except (URLError, HTTPError):
            logger.exception(
                "Loading %s checklists failed: %s, %s",
                scope,
                region,
                date,
                extra={
                    "region": region,
                    "date": date,
                    "scope": scope,
                    "visits": number_of_visits,
                    "added": added,
                    "loaded": loaded,
                },
            )

    def load_recent(self, days: int, region: str, new: bool):
        today: dt.date = dt.date.today()
        dates: list[dt.date] = [today - dt.timedelta(days=n) for n in range(days)]
        for date in dates:
            self.load_checklists(region, date, new)
