"""Tests for data access layer repositories."""

from datetime import date, timedelta

from sqlalchemy.orm import Session

from hotel_booking.models import Guest, Reservation, Room
from hotel_booking.repositories import (
    GuestRepository,
    ReservationRepository,
    RoomRepository,
)


def test_room_repository_crud(db_session: Session) -> None:
    repo = RoomRepository(db_session)
    room = Room(room_number=501, room_type="suite", price=300.0, status="available")
    created = repo.create(room)
    assert created.id is not None
    assert created.room_number == 501

    fetched = repo.get_by_id(created.id)
    assert fetched is not None
    assert fetched.room_number == 501

    by_num = repo.get_by_number(501)
    assert by_num is not None
    assert by_num.id == created.id

    # Filter by room_type & status
    all_suites = repo.get_all(room_type="suite", status="available")
    assert len(all_suites) == 1
    assert repo.count(room_type="suite") == 1

    # Filter with max_price
    cheap = repo.get_all(max_price=200.0)
    assert len(cheap) == 0

    # Update
    created.price = 350.0
    updated = repo.update(created)
    assert updated.price == 350.0

    # Delete
    deleted = repo.delete(created.id)
    assert deleted is True
    assert repo.get_by_id(created.id) is None
    assert repo.delete(9999) is False


def test_room_repository_find_cheapest(db_session: Session) -> None:
    repo = RoomRepository(db_session)
    repo.create(
        Room(room_number=101, room_type="single", price=120.0, status="available")
    )
    repo.create(
        Room(room_number=102, room_type="single", price=90.0, status="available")
    )
    repo.create(
        Room(room_number=201, room_type="double", price=150.0, status="available")
    )
    repo.create(
        Room(room_number=301, room_type="single", price=50.0, status="maintenance")
    )

    cheapest = repo.find_cheapest()
    assert cheapest is not None
    assert cheapest.room_number == 102
    assert cheapest.price == 90.0

    cheapest_double = repo.find_cheapest(room_type="double")
    assert cheapest_double is not None
    assert cheapest_double.room_number == 201


def test_guest_repository_crud(db_session: Session) -> None:
    repo = GuestRepository(db_session)
    guest = Guest(
        first_name="Bohdan",
        last_name="Khmelnytsky",
        email="bohdan@example.com",
        phone="+380001",
    )
    created = repo.create(guest)
    assert created.id is not None

    by_email = repo.get_by_email("bohdan@example.com")
    assert by_email is not None
    assert by_email.last_name == "Khmelnytsky"

    all_guests = repo.get_all(search="Bohdan")
    assert len(all_guests) == 1
    assert repo.count(search="Bohdan") == 1

    created.phone = "+380002"
    repo.update(created)
    assert repo.get_by_id(created.id).phone == "+380002"

    assert repo.delete(created.id) is True
    assert repo.delete(9999) is False


def test_reservation_repository_crud_and_conflicts(db_session: Session) -> None:
    r_repo = RoomRepository(db_session)
    r_repo.create(
        Room(room_number=101, room_type="single", price=100.0, status="available")
    )

    repo = ReservationRepository(db_session)
    today = date.today()
    res = Reservation(
        room_number=101,
        guest_name="Test Guest",
        check_in=today + timedelta(days=2),
        check_out=today + timedelta(days=5),
        total_price=300.0,
        status="confirmed",
    )
    created = repo.create(res)
    assert created.id is not None

    # Check collision logic: overlapping range [day 3, day 6)
    conflicts = repo.get_conflicting_reservations(
        room_number=101,
        check_in=today + timedelta(days=3),
        check_out=today + timedelta(days=6),
    )
    assert len(conflicts) == 1
    assert conflicts[0].id == created.id

    # Non-overlapping range [day 5, day 7) - adjacent check_in matches check_out
    adjacent = repo.get_conflicting_reservations(
        room_number=101,
        check_in=today + timedelta(days=5),
        check_out=today + timedelta(days=7),
    )
    assert len(adjacent) == 0

    # Exclude own ID
    excluded = repo.get_conflicting_reservations(
        room_number=101,
        check_in=today + timedelta(days=2),
        check_out=today + timedelta(days=5),
        exclude_reservation_id=created.id,
    )
    assert len(excluded) == 0

    assert repo.count(status="confirmed") == 1
    assert repo.count(room_number=101) == 1

    created.status = "cancelled"
    repo.update(created)
    assert repo.get_by_id(created.id).status == "cancelled"

    assert repo.delete(created.id) is True
    assert repo.delete(9999) is False
