import pytest
from sqlalchemy import create_engine, orm

from ebird.notebooks.models import Base
from tests.factories import (ChecklistFactory, LocationFactory,
                             ObservationFactory, ObserverFactory,
                             SpeciesFactory)


@pytest.fixture(scope="session")
def db_url():
    return "sqlite:///:memory:"


@pytest.fixture(scope="session")
def engine(db_url):
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)
    yield engine  # db engine to the test session
    Base.metadata.drop_all(engine)


@pytest.fixture(autouse=True, scope="function")
def session(engine):
    session = orm.sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
        expire_on_commit=False,
    )()
    yield session
    session.rollback()
    session.close()


@pytest.fixture(autouse=True, scope="function")
def factories(session):
    ChecklistFactory._meta.sqlalchemy_session = session  # noqa
    LocationFactory._meta.sqlalchemy_session = session  # noqa
    ObserverFactory._meta.sqlalchemy_session = session  # noqa
    ObservationFactory._meta.sqlalchemy_session = session  # noqa
    SpeciesFactory._meta.sqlalchemy_session = session  # noqa
