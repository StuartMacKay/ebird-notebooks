import datetime as dt

import pytest

from ebird.notebooks.models import Location, Observation
from ebird.notebooks.queries import ObservationQuery
from tests.factories import ObservationFactory


@pytest.fixture
def observation(session):
    observation = ObservationFactory.create()
    session.flush()
    return observation


def test_select__entities_updated(session):
    query = ObservationQuery(session).clear()
    model = Observation
    query.select(Observation)

    assert model in query.entities


def test_select_multiple__entities_updated(session):
    query = ObservationQuery(session).clear()
    query.select(Observation, Location)

    assert Observation in query.entities
    assert Location in query.entities


def test_select_repeated__entities_updated(session):
    query = ObservationQuery(session).clear()
    query.select(Observation).select(Location)

    assert Observation in query.entities
    assert Location in query.entities


def test_where__clauses_updated(session):
    query = ObservationQuery(session).clear()
    clause = Observation.id == 1
    query.where(clause)

    assert clause in query.clauses


def test_join__joins_updated(session):
    query = ObservationQuery(session).clear()
    column = Observation.checklist
    query.join(column)

    assert query.joins


def test_order__orders_updated(session):
    query = ObservationQuery(session).clear()
    column = Observation.id
    query.order(column)

    assert column in query.orders


def test_clear__all_attributes_cleared(session):
    query = ObservationQuery(session).clear()
    query.where(Observation.id == 1)
    query.order(Observation.id)
    query.clear()

    assert query.entities == []
    assert query.clauses == []
    assert query.joins == []
    assert query.orders == []


def test_fetch__row_contains_objects(session, observation):
    row = ObservationQuery(session).fetch().first()

    assert row.Observation.id == observation.id
    assert row.Location.id == observation.location.id
    assert row.Observer.id == observation.location.id


def test_count__number_returned(session, observation):
    count = ObservationQuery(session).count()

    assert count == 1


def test_for_country__observations_fetched(session, observation):
    country = observation.location.country
    row = ObservationQuery(session).for_country(country).fetch().first()
    assert row.Observation.id == observation.id
    assert row.Location.country == country


def test_for_country_code__observations_fetched(session, observation):
    country_code = observation.location.country_code
    row = ObservationQuery(session).for_country(country_code).fetch().first()
    assert row.Observation.id == observation.id
    assert row.Location.country_code == country_code


def test_for_state__observations_fetched(session, observation):
    state = observation.location.state
    row = ObservationQuery(session).for_state(state).fetch().first()
    assert row.Observation.id == observation.id
    assert row.Location.state == state


def test_for_state_code__observations_fetched(session, observation):
    state_code = observation.location.state_code
    row = ObservationQuery(session).for_state(state_code).fetch().first()
    assert row.Observation.id == observation.id
    assert row.Location.state_code == state_code


def test_for_region__observations_fetched(session, observation):
    region = observation.location.state
    row = ObservationQuery(session).for_region(region).fetch().first()
    assert row.Observation.id == observation.id
    assert row.Location.state == region


def test_for_region_code__observations_fetched(session, observation):
    region_code = observation.location.state_code
    row = ObservationQuery(session).for_region(region_code).fetch().first()
    assert row.Observation.id == observation.id
    assert row.Location.state_code == region_code


def test_for_county__observations_fetched(session, observation):
    county = observation.location.county
    row = ObservationQuery(session).for_county(county).fetch().first()
    assert row.Observation.id == observation.id
    assert row.Location.county == county


def test_for_county_code__observations_fetched(session, observation):
    county_code = observation.location.county_code
    row = ObservationQuery(session).for_county(county_code).fetch().first()
    assert row.Observation.id == observation.id
    assert row.Location.county_code == county_code


def test_for_year__observations_fetched(session, observation):
    year = dt.date.today().year
    observation.checklist.date = observation.checklist.date.replace(year=year)
    session.flush()
    row = ObservationQuery(session).for_year(year).fetch().first()
    assert row.Observation.id == observation.id
    assert row.Checklist.date.year == year


def test_for_month__observations_fetched(session, observation):
    date = dt.date.today()
    year, month = date.year, date.month
    observation.checklist.date = observation.checklist.date.replace(
        year=year, month=month
    )
    session.flush()
    row = ObservationQuery(session).for_month(year, month).fetch().first()
    assert row.Observation.id == observation.id
    assert row.Checklist.date.year == year
    assert row.Checklist.date.month == month


def test_for_day__observations_fetched(session, observation):
    date = dt.date.today()
    year, month, day = date.year, date.month, date.day
    observation.checklist.date = observation.checklist.date.replace(
        year=year, month=month, day=day
    )
    session.flush()
    row = ObservationQuery(session).for_day(year, month, day).fetch().first()
    assert row.Observation.id == observation.id
    assert row.Checklist.date.year == year
    assert row.Checklist.date.month == month
    assert row.Checklist.date.day == day


def test_for_date__observations_fetched(session, observation):
    date = dt.date.today()
    observation.checklist.date = date
    session.flush()
    row = ObservationQuery(session).for_date(date).fetch().first()
    assert row.Observation.id == observation.id
    assert row.Checklist.date == date
