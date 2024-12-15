import datetime as dt
import random
import string

import factory

from ebird.notebooks.models import Checklist, Location, Observer, Species

PROJECTS = [
    "EBIRD",
]

PROTOCOLS = {
    "P21": "Stationary",
    "P22": "Traveling",
}


def random_key(values):
    return random.choice(list(values.keys()))


def random_code(length: int, prefix: str = ""):
    return prefix + "".join(random.choices(string.digits, k=length))


def random_uppercase(length: int, prefix: str = ""):
    return prefix + "".join(random.choices(string.ascii_uppercase, k=length))


def random_state_code(country_code: str) -> str:
    return random_uppercase(2, f"{country_code}-")


def url(category: str, code: str) -> str:
    return f"https://ebird.org/{category}/{code}"


def hotspot_url(code: str) -> str:
    return url("hotspot", code)


def checklist_url(code: str) -> str:
    return url("checklist", code)


def random_county_code(country_code: str) -> str:
    state_code = random_state_code(country_code)
    county_code = random_uppercase(random.randint(2, 3))
    return f"{country_code}-{state_code}-{county_code}"


class LocationFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Location

    created = factory.LazyFunction(dt.datetime.now)
    modified = factory.LazyFunction(dt.datetime.now)
    identifier = factory.LazyAttribute(lambda _: random_code(6, "L"))
    type = ""
    name = factory.Faker("street_name")
    county = factory.Faker("city")  # OK for now
    county_code = factory.LazyAttribute(lambda o: random_county_code(o.country_code))
    state = factory.Faker("city")  # OK for now
    state_code = factory.LazyAttribute(lambda o: random_state_code(o.country_code))
    country = factory.Faker("country")
    country_code = factory.Faker("country_code")
    iba_code = ""
    bcr_code = ""
    usfws_code = ""
    atlas_block = ""
    latitude = factory.Faker("latitude")
    longitude = factory.Faker("longitude")
    url = factory.LazyAttribute(lambda o: hotspot_url(o.identifier))
    hotspot = True


class ObserverFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Observer

    created = factory.LazyFunction(dt.datetime.now)
    modified = factory.LazyFunction(dt.datetime.now)
    identifier = factory.LazyAttribute(lambda _: random_code(7, "obsr"))
    name = factory.Faker("name")


class SpeciesFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Species

    created = factory.LazyFunction(dt.datetime.now)
    modified = factory.LazyFunction(dt.datetime.now)


class ChecklistFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Checklist

    created = factory.LazyFunction(dt.datetime.now)
    modified = factory.LazyFunction(dt.datetime.now)
    identifier = factory.LazyAttribute(lambda _: random_code(9, "S"))
    location = factory.SubFactory(LocationFactory)
    observer = factory.SubFactory(ObserverFactory)
    date = factory.Faker("date_object")
    time = factory.Faker("time_object")
    group = ""
    protocol = factory.LazyAttribute(lambda obj: PROTOCOLS[obj.protocol_code])
    protocol_code = factory.LazyAttribute(lambda _: random_key(PROTOCOLS))
    project_code = factory.LazyAttribute(lambda _: random.choice(PROJECTS))
    complete = True
    comments = ""
    url = factory.LazyAttribute(lambda o: checklist_url(o.identifier))
