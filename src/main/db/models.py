"""
SqlAlchemy models used to generate the database tables.

The schema supports loading data from the eBird Basic Dataset v1.14
as well as data obtained via the eBird API 2.0.

You absolutely can, but probably shouldn't, mix records from the two
sources together. The fields returned by the eBird API are a subset of
the ebird Basic Dataset, with a couple of exceptions. There is a very
important difference however. The eBird API data identifies an observer
solely by their name. That means all the observations made by John Smith
are going to be assigned to one person, regards of the number of people
called John Smith, who are submitting checklists. The "nature" of the
sources are different. The eBird Basic Dataset is used for analysis,
whereas the eBird API is more appropriate for getting up to date news
and information.
"""

import datetime as dt
import decimal
from typing import List, Optional

from sqlalchemy import Date, ForeignKey, Numeric, Text, Time
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    # Text fields work equally well for sqlite and postgres. sqlite will
    # store the string, un-truncated, regardless of the varchar length
    # defined in the schema. For postgres, strings are stored as a variable
    # length array. This simplifies life enormously because the eBird Basic
    # Dataset does not define the sizes of the fields.
    type_annotation_map = {
        str: Text,
    }


class Species(Base):
    __tablename__ = "species"

    # The primary key
    id: Mapped[int] = mapped_column(primary_key=True)
    # The date and time the database record was added.
    created: Mapped[dt.datetime]
    # The date and time the database record was modified.
    modified: Mapped[dt.datetime]
    # The date and time the eBird record was last edited.
    edited: Mapped[Optional[dt.datetime]]
    # The taxonomic concept identifier from Avibase.
    identifier: Mapped[str]
    # The species code, e.g. ostric2, used in the eBird API.
    code: Mapped[str]
    # The position in the eBird/Clements taxonomic order.
    order: Mapped[Optional[int]]
    # The category from the eBird/Clements taxonomy.
    category: Mapped[str]
    # The species common name in the eBird/Clements taxonomy.
    common_name: Mapped[str]
    # The species scientific name in the eBird/Clements taxonomy.
    scientific_name: Mapped[str]
    # The species name in the local language.
    local_name: Mapped[str]
    # The subspecies, group or form common name in the eBird/Clements taxonomy.
    subspecies_common_name: Mapped[str]
    # The subspecies, group or form scientific name in the eBird/Clements taxonomy.
    subspecies_scientific_name: Mapped[str]
    # The subspecies, group or form name in the local language.
    subspecies_local_name: Mapped[str]
    # The code used if the species is non-native.
    exotic_code: Mapped[str]

    # The reverse relation to the Checklists for this Location.
    observations: Mapped[List["Observation"]] = relationship(
        back_populates="species", cascade="all, delete-orphan"
    )


class Location(Base):
    __tablename__ = "location"

    # The primary key
    id: Mapped[int] = mapped_column(primary_key=True)
    # The date and time the database record was added.
    created: Mapped[dt.datetime]
    # The date and time the database record was modified.
    modified: Mapped[dt.datetime]
    # The date and time the eBird record was last edited.
    edited: Mapped[Optional[dt.datetime]]
    # The unique identifier for the location.
    identifier: Mapped[str]
    # The location type, e.g. personal, hotspot, town, etc.
    type: Mapped[str]
    # The name of the location.
    name: Mapped[str]
    # The name of the county (subnational2).
    county: Mapped[str]
    # The code used to identify the county.
    county_code: Mapped[str]
    # The name of the state (subnational1).
    state: Mapped[str]
    # The code used to identify the state.
    state_code: Mapped[str]
    # The name of the country.
    country: Mapped[str]
    # The code used to identify the country.
    country_code: Mapped[str]
    # The code used to identify an Important Bird Area.
    iba_code: Mapped[str]
    # The code used to identify a Bird Conservation Region.
    bcr_code: Mapped[str]
    # The code used to identify a US Fish & Wildlife Service region.
    usfws_code: Mapped[str]
    # The code used to identify an area for an atlas.
    atlas_block: Mapped[str]
    # The decimal latitude of the location, relative to the equator.
    latitude: Mapped[decimal.Decimal] = mapped_column(Numeric(precision=9, scale=7))
    # The decimal longitude of the location, relative to the prime meridian.
    longitude: Mapped[decimal.Decimal] = mapped_column(Numeric(precision=10, scale=7))
    # URL of the location page on eBird.
    url: Mapped[str]
    # Is the location a hotspot.
    hotspot: Mapped[Optional[bool]]

    # The reverse relation to the Checklists for this Location.
    checklists: Mapped[List["Checklist"]] = relationship(
        back_populates="location", cascade="all, delete-orphan"
    )


class Observer(Base):
    __tablename__ = "observer"

    # The primary key
    id: Mapped[int] = mapped_column(primary_key=True)
    # The date and time the database record was added.
    created: Mapped[dt.datetime]
    # The date and time the database record was modified.
    modified: Mapped[dt.datetime]
    # The date and time the eBird record was last edited.
    edited: Mapped[Optional[dt.datetime]]
    # The code for the person who submitted the checklist
    identifier: Mapped[str]
    # The name of the observer
    name: Mapped[str]

    # The reverse relation to the Checklists for this Observer.
    checklists: Mapped[List["Checklist"]] = relationship(
        back_populates="observer", cascade="all, delete-orphan"
    )


class Checklist(Base):
    __tablename__ = "checklist"

    # The primary key
    id: Mapped[int] = mapped_column(primary_key=True)
    # The date and time the database record was added.
    created: Mapped[dt.datetime]
    # The date and time the database record was modified.
    modified: Mapped[dt.datetime]
    # The date and time the eBird record was last edited.
    edited: Mapped[Optional[dt.datetime]]
    # The unique identifier for the checklist
    identifier: Mapped[str]
    # The location where checklist was made
    location_id: Mapped[int] = mapped_column(ForeignKey("location.id"))
    location: Mapped["Location"] = relationship(back_populates="checklists")
    # The person who submitted the checklist
    observer_id: Mapped[int] = mapped_column(ForeignKey("observer.id"))
    observer: Mapped["Observer"] = relationship(back_populates="checklists")
    # The identifier for a group of observers
    group: Mapped[str]
    # The total number of observers
    observer_count: Mapped[Optional[int]]
    # The number of species reported
    species_count: Mapped[Optional[int]]
    # The date the checklist was made.
    date: Mapped[dt.date] = mapped_column(Date)
    # The time the checklist was started.
    time: Mapped[Optional[dt.time]] = mapped_column(Time)
    # The protocol followed, e.g. travelling, stationary, etc.
    protocol: Mapped[str]
    # The code used to identify the protocol.
    protocol_code: Mapped[str]
    # The code used to identify the project (portal).
    project_code: Mapped[str]
    # The number of minutes spent counting.
    duration: Mapped[Optional[int]]
    # The distance, in metres, covered while travelling.
    distance: Mapped[Optional[decimal.Decimal]] = mapped_column(
        Numeric(precision=9, scale=3)
    )
    # The area covered, in hectares.
    area: Mapped[Optional[decimal.Decimal]] = mapped_column(
        Numeric(precision=9, scale=3)
    )
    # All species seen are reported.
    complete: Mapped[bool]
    # Any comments about the checklist.
    comments: Mapped[str]
    # URL where the original checklist can be viewed.
    url: Mapped[str]

    # The reverse relation to the Observations for this Checklist.
    observations: Mapped[List["Observation"]] = relationship(
        back_populates="checklist", cascade="all, delete-orphan"
    )


class Observation(Base):
    __tablename__ = "observation"

    # The primary key
    id: Mapped[int] = mapped_column(primary_key=True)
    # The date and time the database record was added.
    created: Mapped[dt.datetime]
    # The date and time the database record was modified.
    modified: Mapped[dt.datetime]
    # The date and time the eBird record was last edited.
    edited: Mapped[Optional[dt.datetime]]
    # A global unique identifier for the observation.
    identifier: Mapped[str]
    # The checklist this observation belongs to.
    checklist_id: Mapped[int] = mapped_column(ForeignKey("checklist.id"))
    checklist: Mapped["Checklist"] = relationship(back_populates="observations")
    # The identified species.
    species_id: Mapped[int] = mapped_column(ForeignKey("species.id"))
    species: Mapped["Species"] = relationship(back_populates="observations")
    # The number of birds seen.
    count: Mapped[Optional[int]]
    # eBird code identifying the breeding status
    breeding_code: Mapped[str]
    # eBird code identifying the breeding category
    breeding_category: Mapped[str]
    # eBird code identifying the behaviour
    behavior_code: Mapped[str]
    # The number of birds seen in each combination of age and sex.
    age_sex: Mapped[str]
    # Has audio, photo or video uploaded to the Macaulay library.
    media: Mapped[Optional[bool]]
    # Has the observation been accepted by eBird's review process.
    approved: Mapped[Optional[bool]]
    # Was the observation reviewed because it failed automatic checks.
    reviewed: Mapped[Optional[bool]]
    # The reason given for the observation to be marked as not confirmed.
    reason: Mapped[str]
    # Any comments about the observation.
    comments: Mapped[str]
