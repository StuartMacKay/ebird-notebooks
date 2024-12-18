import datetime as dt
import re

from dateutil import relativedelta
from sqlalchemy import and_, func, select

from .models import Checklist, Location, Observation, Observer, Species


class Checklists:
    def __init__(self, session):
        self.session = session
        self.entities = [Checklist, Location, Observer]
        self.joins = [Location, Observer]
        self.clauses = []
        self.orders = [Checklist.date, Checklist.time]

    def select(self, *entities):
        self.entities.extend(entities)
        return self

    def where(self, *args):
        self.clauses.extend(args)
        return self

    def join(self, *args):
        self.joins.extend(args)
        return self

    def order(self, *args):
        self.orders.extend(args)
        return self

    def clear(self):
        self.entities = []
        self.joins = []
        self.clauses = []
        self.orders = []
        return self

    def fetch(self):
        statement = select(*self.entities)
        for model in self.joins:
            statement = statement.join(model)
        for clause in self.clauses:
            statement = statement.where(clause)
        return self.session.execute(statement)

    def count(self):
        statement = select(func.count(Checklist.id))
        for model in self.joins:
            statement = statement.join(model)
        for clause in self.clauses:
            statement = statement.where(clause)
        return self.session.scalar(statement)

    def latest(self):
        statement = (
            select(Checklist, Location, Observer)
            .join(Location)
            .join(Observer)
            .order_by(Checklist.date.desc(), Checklist.time.desc())
        )
        return self.session.execute(statement).first()

    def for_country(self, value):
        if re.match(r"[A-Z]{2,3}", value):
            self.clauses.append(Location.country_code == value)
        else:
            self.clauses.append(Location.country == value)
        return self

    def for_state(self, value):
        if re.match(r"[A-Z]{2}-[A-Z0-9]{2,3}", value):
            self.clauses.append(Location.state_code == value)
        else:
            self.clauses.append(Location.state == value)
        return self

    def for_region(self, value):
        return self.for_state(value)

    def for_county(self, value):
        if re.match(r"[A-Z]{2,3}-[A-Z0-9]{2,3}-[A-Z0-9]{2,3}", value):
            self.clauses.append(Location.county_code == value)
        else:
            self.clauses.append(Location.county == value)
        return self

    def for_year(self, year: int):
        start = dt.date(year, 1, 1)
        until = dt.date(year + 1, 1, 1)
        self.clauses.append(and_(Checklist.date >= start, Checklist.date < until))
        return self

    def for_month(self, year: int, month: int):
        start = dt.date(year, month, 1)
        until = start + relativedelta.relativedelta(months=1)
        self.clauses.append(and_(Checklist.date >= start, Checklist.date < until))
        return self

    def for_day(self, year: int, month: int, day: int):
        date = dt.date(year, month, day)
        self.clauses.append(Checklist.date == date)
        return self

    def for_date(self, date: dt.date):
        self.clauses.append(Checklist.date == date)
        return self


class Observations:
    def __init__(self, session):
        self.session = session
        self.entities = [Observation, Species, Checklist, Observer, Location]
        self.joins = [
            Observation.species,
            Observation.checklist,
            Observation.observer,
            Observation.location,
        ]
        self.clauses = []
        self.orders = [Checklist.date, Checklist.time]

    def select(self, *entities):
        self.entities.extend(entities)
        return self

    def where(self, *args):
        self.clauses.extend(args)
        return self

    def join(self, *args):
        self.joins.extend(args)
        return self

    def order(self, *args):
        self.orders.extend(args)
        return self

    def clear(self):
        self.entities = []
        self.joins = []
        self.clauses = []
        self.orders = []
        return self

    def fetch(self):
        statement = select(*self.entities)
        for model in self.joins:
            statement = statement.join(model)
        for clause in self.clauses:
            statement = statement.where(clause)
        return self.session.execute(statement)

    def count(self):
        statement = select(func.count(Checklist.id))
        for model in self.joins:
            statement = statement.join(model)
        for clause in self.clauses:
            statement = statement.where(clause)
        return self.session.scalar(statement)

    def latest(self):
        statement = (
            select(Observation, Checklist, Location, Observer)
            .join(Checklist.identifier)
            .join(Location.identifier)
            .join(Observer.identifier)
            .order_by(Checklist.date.desc(), Checklist.time.desc())
        )
        return self.session.execute(statement).first()

    def for_country(self, value):
        if re.match(r"[A-Z]{2,3}", value):
            self.clauses.append(Location.country_code == value)
        else:
            self.clauses.append(Location.country == value)
        return self

    def for_state(self, value):
        if re.match(r"[A-Z]{2}-[A-Z0-9]{2,3}", value):
            self.clauses.append(Location.state_code == value)
        else:
            self.clauses.append(Location.state == value)
        return self

    def for_region(self, value):
        return self.for_state(value)

    def for_county(self, value):
        if re.match(r"[A-Z]{2,3}-[A-Z0-9]{2,3}-[A-Z0-9]{2,3}", value):
            self.clauses.append(Location.county_code == value)
        else:
            self.clauses.append(Location.county == value)
        return self

    def for_year(self, year: int):
        start = dt.date(year, 1, 1)
        until = dt.date(year + 1, 1, 1)
        self.clauses.append(and_(Checklist.date >= start, Checklist.date < until))
        return self

    def for_month(self, year: int, month: int):
        start = dt.date(year, month, 1)
        until = start + relativedelta.relativedelta(months=1)
        self.clauses.append(and_(Checklist.date >= start, Checklist.date < until))
        return self

    def for_day(self, year: int, month: int, day: int):
        date = dt.date(year, month, day)
        self.clauses.append(Checklist.date == date)
        return self

    def for_date(self, date: dt.date):
        self.clauses.append(Checklist.date == date)
        return self
