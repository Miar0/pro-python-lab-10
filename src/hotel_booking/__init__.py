"""Hotel Booking System - Production-oriented Package.

Variant 8: Hotel Reservation System.
"""

from hotel_booking.config import Settings, get_settings
from hotel_booking.models import Guest, Reservation, Room
from hotel_booking.repositories import (
    GuestRepository,
    ReservationRepository,
    RoomRepository,
)
from hotel_booking.services import HotelService

__version__ = "1.0.0"

__all__ = [
    "__version__",
    "Settings",
    "get_settings",
    "Room",
    "Guest",
    "Reservation",
    "RoomRepository",
    "GuestRepository",
    "ReservationRepository",
    "HotelService",
]
