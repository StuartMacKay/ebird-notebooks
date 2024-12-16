import datetime as dt

import pytest

from ebird.notebooks.models import Checklist, Location
from ebird.notebooks.queries import ChecklistQuery
from tests.factories import ChecklistFactory


@pytest.fixture
def checklist(session):
    checklist = ChecklistFactory.create()
    session.flush()
    return checklist


def test_select__entities_updated(session):
    query = ChecklistQuery(session).clear()
    model = Checklist
    query.select(Checklist)

    assert model in query.entities


def test_select_multiple__entities_updated(session):
    query = ChecklistQuery(session).clear()
    query.select(Checklist, Location)

    assert Checklist in query.entities
    assert Location in query.entities


def test_select_repeated__entities_updated(session):
    query = ChecklistQuery(session).clear()
    query.select(Checklist).select(Location)

    assert Checklist in query.entities
    assert Location in query.entities


def test_where__clauses_updated(session):
    query = ChecklistQuery(session).clear()
    clause = Checklist.id == 1
    query.where(clause)

    assert clause in query.clauses


def test_join__joins_updated(session):
    query = ChecklistQuery(session).clear()
    model = Checklist
    query.join(Checklist)

    assert model in query.joins


def test_order__orders_updated(session):
    query = ChecklistQuery(session).clear()
    column = Checklist.id
    query.order(column)

    assert column in query.orders


def test_clear__all_attributes_cleared(session):
    query = ChecklistQuery(session)
    query.where(Checklist.id == 1)
    query.order(Checklist.id)
    query.clear()

    assert query.entities == []
    assert query.clauses == []
    assert query.joins == []
    assert query.orders == []


def test_fetch__row_contains_objects(session, checklist):
    row = ChecklistQuery(session).fetch().first()

    assert row.Checklist.id == checklist.id
    assert row.Location.id == checklist.location.id
    assert row.Observer.id == checklist.location.id


def test_count__number_returned(session, checklist):
    count = ChecklistQuery(session).count()

    assert count == 1


def test_for_country__checklists_fetched(session, checklist):
    country = checklist.location.country
    row = ChecklistQuery(session).for_country(country).fetch().first()
    assert row.Checklist.id == checklist.id
    assert row.Location.country == country


def test_for_country_code__checklists_fetched(session, checklist):
    country_code = checklist.location.country_code
    row = ChecklistQuery(session).for_country(country_code).fetch().first()
    assert row.Checklist.id == checklist.id
    assert row.Location.country_code == country_code


def test_for_state__checklists_fetched(session, checklist):
    state = checklist.location.state
    row = ChecklistQuery(session).for_state(state).fetch().first()
    assert row.Checklist.id == checklist.id
    assert row.Location.state == state


def test_for_state_code__checklists_fetched(session, checklist):
    state_code = checklist.location.state_code
    row = ChecklistQuery(session).for_state(state_code).fetch().first()
    assert row.Checklist.id == checklist.id
    assert row.Location.state_code == state_code


def test_for_region__checklists_fetched(session, checklist):
    region = checklist.location.state
    row = ChecklistQuery(session).for_region(region).fetch().first()
    assert row.Checklist.id == checklist.id
    assert row.Location.state == region


def test_for_region_code__checklists_fetched(session, checklist):
    region_code = checklist.location.state_code
    row = ChecklistQuery(session).for_region(region_code).fetch().first()
    assert row.Checklist.id == checklist.id
    assert row.Location.state_code == region_code


def test_for_county__checklists_fetched(session, checklist):
    county = checklist.location.county
    row = ChecklistQuery(session).for_county(county).fetch().first()
    assert row.Checklist.id == checklist.id
    assert row.Location.county == county


def test_for_county_code__checklists_fetched(session, checklist):
    county_code = checklist.location.county_code
    row = ChecklistQuery(session).for_county(county_code).fetch().first()
    assert row.Checklist.id == checklist.id
    assert row.Location.county_code == county_code


def test_for_year__checklists_fetched(session, checklist):
    year = dt.date.today().year
    checklist.date = checklist.date.replace(year=year)
    session.flush()
    row = ChecklistQuery(session).for_year(year).fetch().first()
    assert row.Checklist.id == checklist.id
    assert row.Checklist.date.year == year


def test_for_month__checklists_fetched(session, checklist):
    date = dt.date.today()
    year, month = date.year, date.month
    checklist.date = checklist.date.replace(year=year, month=month)
    session.flush()
    row = ChecklistQuery(session).for_month(year, month).fetch().first()
    assert row.Checklist.id == checklist.id
    assert row.Checklist.date.year == year
    assert row.Checklist.date.month == month


def test_for_day__checklists_fetched(session, checklist):
    date = dt.date.today()
    year, month, day = date.year, date.month, date.day
    checklist.date = checklist.date.replace(year=year, month=month, day=day)
    session.flush()
    row = ChecklistQuery(session).for_day(year, month, day).fetch().first()
    assert row.Checklist.id == checklist.id
    assert row.Checklist.date.year == year
    assert row.Checklist.date.month == month
    assert row.Checklist.date.day == day


def test_for_date__checklists_fetched(session, checklist):
    date = dt.date.today()
    checklist.date = date
    session.flush()
    row = ChecklistQuery(session).for_date(date).fetch().first()
    assert row.Checklist.id == checklist.id
    assert row.Checklist.date == date
