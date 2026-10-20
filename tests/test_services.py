"""Tests for service layer business logic and validation rules."""

from datetime import date, timedelta

import pytest

from hotel_booking.exceptions import (
    ConflictException,
    EntityNotFoundException,
    ValidationException,
)
from hotel_booking.services import HotelService, has_date_conflict


def test_has_date_conflict_logic() -> None:
    d1 = date(2026, 11, 1)
    d5 = date(2026, 11, 5)
    d10 = date(2026, 11, 10)
    d15 = date(2026, 11, 15)

    # Overlapping intervals [1, 10) and [5, 15)
    assert has_date_conflict(d1, d10, d5, d15) is True
    # Non-overlapping intervals [1, 5) and [10, 15)
    assert has_date_conflict(d1, d5, d10, d15) is False
    # Adjacent intervals [1, 5) and [5, 10) (no conflict, checkout day = checkin day)
    assert has_date_conflict(d1, d5, d5, d10) is False
    # Contained interval [1, 15) and [5, 10)
    assert has_date_conflict(d1, d15, d5, d10) is True


def test_create_room_and_validations(hotel_service: HotelService) -> None:
    room = hotel_service.create_room(101, "single", 120.0)
    assert room.room_number == 101

    # Price validation
    with pytest.raises(ValidationException, match="greater than 0"):
        hotel_service.create_room(102, "single", -10.0)
    with pytest.raises(ValidationException, match="greater than 0"):
        hotel_service.create_room(102, "single", 0.0)

    # Duplicate room number
    with pytest.raises(ConflictException, match="already exists"):
        hotel_service.create_room(101, "double", 150.0)


def test_get_room_and_not_found(hotel_service: HotelService) -> None:
    hotel_service.create_room(101, "single", 100.0)
    room = hotel_service.get_room_by_number(101)
    assert room.room_number == 101

    with pytest.raises(EntityNotFoundException):
        hotel_service.get_room(9999)

    with pytest.raises(EntityNotFoundException):
        hotel_service.get_room_by_number(9999)


def test_update_and_delete_room(hotel_service: HotelService) -> None:
    room = hotel_service.create_room(101, "single", 100.0)
    updated = hotel_service.update_room(
        room.id, room_type="double", price=140.0, status="occupied"
    )
    assert updated.room_type == "double"
    assert updated.price == 140.0
    assert updated.status == "occupied"

    with pytest.raises(ValidationException):
        hotel_service.update_room(room.id, price=-50.0)

    hotel_service.delete_room(room.id)
    with pytest.raises(EntityNotFoundException):
        hotel_service.get_room(room.id)


def test_get_available_rooms_filtering(
    hotel_service: HotelService, sample_data: dict[str, object]
) -> None:
    today = date.today()
    # Sample data has room 102 booked from day+5 to day+8
    available = hotel_service.get_available_rooms(
        check_in=today + timedelta(days=5),
        check_out=today + timedelta(days=8),
    )
    available_numbers = [r.room_number for r in available]
    assert 101 in available_numbers
    assert 201 in available_numbers
    assert 102 not in available_numbers  # Booked
    assert 301 not in available_numbers  # Maintenance

    # Filter with max_price
    cheap_available = hotel_service.get_available_rooms(
        check_in=today + timedelta(days=5),
        check_out=today + timedelta(days=8),
        max_price=120.0,
    )
    assert len(cheap_available) == 1
    assert cheap_available[0].room_number == 101

    # Date validation: check_out <= check_in
    with pytest.raises(ValidationException, match="after check_in"):
        hotel_service.get_available_rooms(
            check_in=today + timedelta(days=5),
            check_out=today + timedelta(days=5),
        )


def test_find_cheapest_room(
    hotel_service: HotelService, sample_data: dict[str, object]
) -> None:
    cheapest = hotel_service.find_cheapest_room()
    assert cheapest.room_number == 101
    assert cheapest.price == 100.0

    cheapest_suite = hotel_service.find_cheapest_room(room_type="suite")
    assert cheapest_suite.room_number == 201


def test_guest_crud_and_validations(hotel_service: HotelService) -> None:
    g1 = hotel_service.create_guest("Andriy", "Shevchenko", "andriy@example.com")
    assert g1.id is not None

    with pytest.raises(ConflictException, match="already registered"):
        hotel_service.create_guest("Duplicate", "User", "andriy@example.com")

    g_fetched = hotel_service.get_guest(g1.id)
    assert g_fetched.email == "andriy@example.com"

    # Update guest
    updated = hotel_service.update_guest(g1.id, phone="+380998887766")
    assert updated.phone == "+380998887766"

    # Guest not found
    with pytest.raises(EntityNotFoundException):
        hotel_service.get_guest(9999)

    hotel_service.delete_guest(g1.id)
    with pytest.raises(EntityNotFoundException):
        hotel_service.get_guest(g1.id)


def test_book_room_double_booking_prevention(
    hotel_service: HotelService, sample_data: dict[str, object]
) -> None:
    today = date.today()

    # Valid booking
    res = hotel_service.book_room(
        room_number=101,
        guest_name="Vasyl Stus",
        check_in=today + timedelta(days=1),
        check_out=today + timedelta(days=4),
    )
    assert res.id is not None
    assert res.total_price == 300.0  # 3 nights * 100

    # Collision test: attempt to book overlapping dates for room 101
    with pytest.raises(ConflictException, match="Double booking collision detected"):
        hotel_service.book_room(
            room_number=101,
            guest_name="Another Guest",
            check_in=today + timedelta(days=2),
            check_out=today + timedelta(days=5),
        )

    # Attempt to book room under maintenance (301)
    with pytest.raises(ConflictException, match="under maintenance"):
        hotel_service.book_room(
            room_number=301,
            guest_name="Maintenance Tester",
            check_in=today + timedelta(days=1),
            check_out=today + timedelta(days=2),
        )

    # Attempt to book non-existent room
    with pytest.raises(EntityNotFoundException):
        hotel_service.book_room(
            room_number=999,
            guest_name="Ghost",
            check_in=today + timedelta(days=1),
            check_out=today + timedelta(days=2),
        )

    # Validation: invalid date order
    with pytest.raises(ValidationException):
        hotel_service.book_room(
            room_number=101,
            guest_name="Invalid Dates",
            check_in=today + timedelta(days=5),
            check_out=today + timedelta(days=3),
        )


def test_cancel_and_delete_reservation(
    hotel_service: HotelService, sample_data: dict[str, object]
) -> None:
    res_list, total = hotel_service.list_reservations()
    assert total >= 1
    res = res_list[0]

    cancelled = hotel_service.cancel_reservation(res.id)
    assert cancelled.status == "cancelled"

    with pytest.raises(EntityNotFoundException):
        hotel_service.cancel_reservation(9999)

    hotel_service.delete_reservation(res.id)
    with pytest.raises(EntityNotFoundException):
        hotel_service.get_reservation(res.id)


def test_calculate_potential_revenue(
    hotel_service: HotelService, sample_data: dict[str, object]
) -> None:
    stats = hotel_service.calculate_potential_revenue()
    assert stats["total_rooms"] == 4.0
    assert stats["active_rooms"] == 3.0  # Room 301 is maintenance
    assert stats["confirmed_reservations"] >= 1.0
    assert stats["total_revenue"] > 0.0
    assert stats["potential_revenue"] > 0.0
    assert stats["average_room_price"] > 0.0
    assert stats["minimum_room_price"] == 80.0
    assert stats["maximum_room_price"] == 250.0
