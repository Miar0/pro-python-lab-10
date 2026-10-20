"""Service layer encapsulating domain business logic and transactional integrity."""

from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from hotel_booking.exceptions import (
    ConflictException,
    EntityNotFoundException,
    ValidationException,
)
from hotel_booking.models import Guest, Reservation, Room
from hotel_booking.repositories import (
    GuestRepository,
    ReservationRepository,
    RoomRepository,
)


def has_date_conflict(
    check_in_1: date,
    check_out_1: date,
    check_in_2: date,
    check_out_2: date,
) -> bool:
    """Check if two half-open date intervals [in_1, out_1) and [in_2, out_2) overlap."""
    return check_in_1 < check_out_2 and check_out_1 > check_in_2


class HotelService:
    """Core domain service for hotel room inventory, reservations, and financial metrics."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.room_repo = RoomRepository(session)
        self.guest_repo = GuestRepository(session)
        self.reservation_repo = ReservationRepository(session)

    # -------------------------------------------------------------------------
    # Room operations
    # -------------------------------------------------------------------------
    def create_room(
        self,
        room_number: int,
        room_type: str,
        price: float,
        status: str = "available",
    ) -> Room:
        if price <= 0:
            raise ValidationException("Room price must be strictly greater than 0.")
        existing = self.room_repo.get_by_number(room_number)
        if existing:
            raise ConflictException(f"Room number {room_number} already exists.")

        room = Room(
            room_number=room_number,
            room_type=room_type,
            price=price,
            status=status,
        )
        return self.room_repo.create(room)

    def get_room(self, room_id: int) -> Room:
        room = self.room_repo.get_by_id(room_id)
        if not room:
            raise EntityNotFoundException("Room", room_id)
        return room

    def get_room_by_number(self, room_number: int) -> Room:
        room = self.room_repo.get_by_number(room_number)
        if not room:
            raise EntityNotFoundException("Room", room_number)
        return room

    def list_rooms(
        self,
        room_type: Optional[str] = None,
        status: Optional[str] = None,
        max_price: Optional[float] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[Room], int]:
        rooms = self.room_repo.get_all(
            room_type=room_type,
            status=status,
            max_price=max_price,
            skip=skip,
            limit=limit,
        )
        total = self.room_repo.count(
            room_type=room_type, status=status, max_price=max_price
        )
        return rooms, total

    def update_room(
        self,
        room_id: int,
        room_type: Optional[str] = None,
        price: Optional[float] = None,
        status: Optional[str] = None,
    ) -> Room:
        room = self.get_room(room_id)
        if price is not None:
            if price <= 0:
                raise ValidationException("Price must be greater than 0.")
            room.price = price
        if room_type is not None:
            room.room_type = room_type
        if status is not None:
            room.status = status
        return self.room_repo.update(room)

    def delete_room(self, room_id: int) -> None:
        room = self.get_room(room_id)
        self.room_repo.delete(room.id)

    def get_available_rooms(
        self,
        check_in: date,
        check_out: date,
        room_type: Optional[str] = None,
        max_price: Optional[float] = None,
    ) -> list[Room]:
        """Find active rooms without overlapping confirmed reservations for the given date range."""
        if check_out <= check_in:
            raise ValidationException(
                "check_out date must be strictly after check_in date."
            )

        all_rooms = self.room_repo.get_all(
            room_type=room_type,
            status="available",
            max_price=max_price,
            limit=1000,
        )

        available_rooms: list[Room] = []
        for room in all_rooms:
            conflicts = self.reservation_repo.get_conflicting_reservations(
                room_number=room.room_number,
                check_in=check_in,
                check_out=check_out,
            )
            if not conflicts:
                available_rooms.append(room)

        return available_rooms

    def find_cheapest_room(self, room_type: Optional[str] = None) -> Room:
        room = self.room_repo.find_cheapest(room_type=room_type)
        if not room:
            raise EntityNotFoundException("Cheapest room", room_type or "all")
        return room

    # -------------------------------------------------------------------------
    # Guest operations
    # -------------------------------------------------------------------------
    def create_guest(
        self,
        first_name: str,
        last_name: str,
        email: str,
        phone: Optional[str] = None,
    ) -> Guest:
        existing = self.guest_repo.get_by_email(email)
        if existing:
            raise ConflictException(
                f"Guest with email '{email}' is already registered."
            )

        guest = Guest(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
        )
        return self.guest_repo.create(guest)

    def get_guest(self, guest_id: int) -> Guest:
        guest = self.guest_repo.get_by_id(guest_id)
        if not guest:
            raise EntityNotFoundException("Guest", guest_id)
        return guest

    def list_guests(
        self,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[Guest], int]:
        guests = self.guest_repo.get_all(search=search, skip=skip, limit=limit)
        total = self.guest_repo.count(search=search)
        return guests, total

    def update_guest(
        self,
        guest_id: int,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
    ) -> Guest:
        guest = self.get_guest(guest_id)
        if email is not None and email != guest.email:
            existing = self.guest_repo.get_by_email(email)
            if existing:
                raise ConflictException(f"Email '{email}' is already in use.")
            guest.email = email
        if first_name is not None:
            guest.first_name = first_name
        if last_name is not None:
            guest.last_name = last_name
        if phone is not None:
            guest.phone = phone
        return self.guest_repo.update(guest)

    def delete_guest(self, guest_id: int) -> None:
        guest = self.get_guest(guest_id)
        self.guest_repo.delete(guest.id)

    # -------------------------------------------------------------------------
    # Reservation operations
    # -------------------------------------------------------------------------
    def book_room(
        self,
        room_number: int,
        guest_name: str,
        check_in: date,
        check_out: date,
        guest_id: Optional[int] = None,
    ) -> Reservation:
        """Create booking with double booking collision prevention."""
        if check_out <= check_in:
            raise ValidationException(
                "check_out date must be strictly after check_in date."
            )

        room = self.room_repo.get_by_number(room_number)
        if not room:
            raise EntityNotFoundException("Room", room_number)

        if room.status == "maintenance":
            raise ConflictException(
                f"Room {room_number} is currently under maintenance and cannot be booked."
            )

        # Check collision with confirmed reservations
        conflicts = self.reservation_repo.get_conflicting_reservations(
            room_number=room_number,
            check_in=check_in,
            check_out=check_out,
        )
        if conflicts:
            conflict_dates = ", ".join(
                f"[{c.check_in} to {c.check_out}]" for c in conflicts
            )
            raise ConflictException(
                f"Double booking collision detected for room {room_number}. "
                f"Existing reservation(s): {conflict_dates}"
            )

        nights = max(1, (check_out - check_in).days)
        total_price = round(room.price * nights, 2)

        reservation = Reservation(
            room_number=room_number,
            guest_name=guest_name,
            guest_id=guest_id,
            check_in=check_in,
            check_out=check_out,
            total_price=total_price,
            status="confirmed",
        )
        return self.reservation_repo.create(reservation)

    def cancel_reservation(self, reservation_id: int) -> Reservation:
        reservation = self.reservation_repo.get_by_id(reservation_id)
        if not reservation:
            raise EntityNotFoundException("Reservation", reservation_id)

        reservation.status = "cancelled"
        return self.reservation_repo.update(reservation)

    def get_reservation(self, reservation_id: int) -> Reservation:
        reservation = self.reservation_repo.get_by_id(reservation_id)
        if not reservation:
            raise EntityNotFoundException("Reservation", reservation_id)
        return reservation

    def list_reservations(
        self,
        status: Optional[str] = None,
        room_number: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[Reservation], int]:
        reservations = self.reservation_repo.get_all(
            status=status,
            room_number=room_number,
            skip=skip,
            limit=limit,
        )
        total = self.reservation_repo.count(status=status, room_number=room_number)
        return reservations, total

    def delete_reservation(self, reservation_id: int) -> None:
        reservation = self.get_reservation(reservation_id)
        self.reservation_repo.delete(reservation.id)

    # -------------------------------------------------------------------------
    # Revenue & analytics operations
    # -------------------------------------------------------------------------
    def calculate_potential_revenue(self) -> dict[str, float]:
        """Calculate total booked revenue, potential room inventory revenue, and price statistics."""
        rooms = self.room_repo.get_all(limit=10000)
        reservations = self.reservation_repo.get_all(status="confirmed", limit=10000)

        total_rooms = len(rooms)
        active_rooms = sum(1 for r in rooms if r.status != "maintenance")
        confirmed_count = len(reservations)

        total_confirmed_revenue = sum(res.total_price for res in reservations)
        potential_room_revenue = sum(
            room.price * 30 for room in rooms if room.status != "maintenance"
        )

        prices = [r.price for r in rooms] if rooms else [0.0]
        import numpy as np

        prices_arr = np.array(prices, dtype=float)
        avg_price = float(np.mean(prices_arr)) if len(prices_arr) > 0 else 0.0
        min_price = float(np.min(prices_arr)) if len(prices_arr) > 0 else 0.0
        max_price = float(np.max(prices_arr)) if len(prices_arr) > 0 else 0.0
        std_price = float(np.std(prices_arr)) if len(prices_arr) > 0 else 0.0

        return {
            "total_rooms": float(total_rooms),
            "active_rooms": float(active_rooms),
            "confirmed_reservations": float(confirmed_count),
            "total_revenue": round(float(total_confirmed_revenue), 2),
            "potential_revenue": round(float(potential_room_revenue), 2),
            "average_room_price": round(avg_price, 2),
            "minimum_room_price": round(min_price, 2),
            "maximum_room_price": round(max_price, 2),
            "price_std_dev": round(std_price, 2),
        }
