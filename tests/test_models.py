"""Tests for domain ORM models: Room, Guest, Reservation."""

from datetime import date, timedelta

from hotel_booking.models import Guest, Reservation, Room


def test_room_model_attributes_and_repr() -> None:
    room = Room(room_number=105, room_type="deluxe", price=199.99, status="available")
    assert room.room_number == 105
    assert room.room_type == "deluxe"
    assert room.price == 199.99
    assert room.status == "available"
    assert "<Room(number=105" in repr(room)


def test_guest_model_attributes_and_full_name() -> None:
    guest = Guest(
        first_name="Ivan",
        last_name="Franko",
        email="franko@example.com",
        phone="+380991112233",
    )
    assert guest.full_name == "Ivan Franko"
    assert "<Guest" in repr(guest)


def test_reservation_model_nights_calculation() -> None:
    today = date(2026, 11, 1)
    res = Reservation(
        room_number=101,
        guest_name="Lesya Ukrainka",
        check_in=today,
        check_out=today + timedelta(days=4),
        total_price=400.0,
        status="confirmed",
    )
    assert res.nights == 4
    assert "<Reservation" in repr(res)


def test_reservation_minimum_one_night() -> None:
    today = date(2026, 11, 1)
    res = Reservation(
        room_number=101,
        guest_name="Test Guest",
        check_in=today,
        check_out=today,
        total_price=100.0,
        status="confirmed",
    )
    assert res.nights == 1
