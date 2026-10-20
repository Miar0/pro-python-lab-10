"""Pytest test configuration, fixtures, and database dependency overrides."""

from collections.abc import Generator
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from hotel_booking.api import app
from hotel_booking.database import Base, get_db
from hotel_booking.services import HotelService

# In-memory SQLite for high-speed, isolated testing
TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    expire_on_commit=False,
)


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """Create a fresh schema for each test and yield an active session."""
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Provide a TestClient with overridden get_db dependency."""

    def override_get_db() -> Generator[Session, None, None]:
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def hotel_service(db_session: Session) -> HotelService:
    """Fixture returning an initialized HotelService backed by the test DB."""
    return HotelService(db_session)


@pytest.fixture(scope="function")
def sample_data(hotel_service: HotelService) -> dict[str, object]:
    """Pre-populate test database with typical rooms, guests, and reservations."""
    r101 = hotel_service.create_room(101, "single", 100.0, "available")
    r102 = hotel_service.create_room(102, "double", 150.0, "available")
    r201 = hotel_service.create_room(201, "suite", 250.0, "available")
    r301 = hotel_service.create_room(301, "single", 80.0, "maintenance")

    guest1 = hotel_service.create_guest(
        "Danylo", "Ivasiv", "danylo@example.com", "+380501234567"
    )
    guest2 = hotel_service.create_guest(
        "Taras", "Shevchenko", "taras@example.com", "+380671234567"
    )

    today = date.today()
    res1 = hotel_service.book_room(
        room_number=102,
        guest_name=guest1.full_name,
        check_in=today + timedelta(days=5),
        check_out=today + timedelta(days=8),
        guest_id=guest1.id,
    )

    return {
        "rooms": [r101, r102, r201, r301],
        "guests": [guest1, guest2],
        "reservations": [res1],
    }
