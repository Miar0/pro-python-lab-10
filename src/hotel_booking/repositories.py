"""Repository layer providing clean data access for Room, Guest, and Reservation."""

from datetime import date
from typing import Optional

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from hotel_booking.models import Guest, Reservation, Room


class RoomRepository:
    """Data access repository for Room entity."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, room: Room) -> Room:
        self.session.add(room)
        self.session.commit()
        self.session.refresh(room)
        return room

    def get_by_id(self, room_id: int) -> Optional[Room]:
        return self.session.get(Room, room_id)

    def get_by_number(self, room_number: int) -> Optional[Room]:
        stmt = select(Room).where(Room.room_number == room_number)
        return self.session.scalars(stmt).first()

    def get_all(
        self,
        room_type: Optional[str] = None,
        status: Optional[str] = None,
        max_price: Optional[float] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Room]:
        stmt = select(Room)
        if room_type:
            stmt = stmt.where(Room.room_type == room_type)
        if status:
            stmt = stmt.where(Room.status == status)
        if max_price is not None:
            stmt = stmt.where(Room.price <= max_price)
        stmt = stmt.order_by(Room.room_number.asc()).offset(skip).limit(limit)
        return list(self.session.scalars(stmt).all())

    def count(
        self,
        room_type: Optional[str] = None,
        status: Optional[str] = None,
        max_price: Optional[float] = None,
    ) -> int:
        stmt = select(Room)
        if room_type:
            stmt = stmt.where(Room.room_type == room_type)
        if status:
            stmt = stmt.where(Room.status == status)
        if max_price is not None:
            stmt = stmt.where(Room.price <= max_price)
        return len(list(self.session.scalars(stmt).all()))

    def find_cheapest(self, room_type: Optional[str] = None) -> Optional[Room]:
        stmt = select(Room).where(Room.status != "maintenance")
        if room_type:
            stmt = stmt.where(Room.room_type == room_type)
        stmt = stmt.order_by(Room.price.asc(), Room.room_number.asc()).limit(1)
        return self.session.scalars(stmt).first()

    def update(self, room: Room) -> Room:
        self.session.commit()
        self.session.refresh(room)
        return room

    def delete(self, room_id: int) -> bool:
        room = self.get_by_id(room_id)
        if not room:
            return False
        self.session.delete(room)
        self.session.commit()
        return True


class GuestRepository:
    """Data access repository for Guest entity."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, guest: Guest) -> Guest:
        self.session.add(guest)
        self.session.commit()
        self.session.refresh(guest)
        return guest

    def get_by_id(self, guest_id: int) -> Optional[Guest]:
        return self.session.get(Guest, guest_id)

    def get_by_email(self, email: str) -> Optional[Guest]:
        stmt = select(Guest).where(Guest.email == email)
        return self.session.scalars(stmt).first()

    def get_all(
        self,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Guest]:
        stmt = select(Guest)
        if search:
            pattern = f"%{search}%"
            stmt = stmt.where(
                or_(
                    Guest.first_name.ilike(pattern),
                    Guest.last_name.ilike(pattern),
                    Guest.email.ilike(pattern),
                )
            )
        stmt = stmt.order_by(Guest.id.asc()).offset(skip).limit(limit)
        return list(self.session.scalars(stmt).all())

    def count(self, search: Optional[str] = None) -> int:
        stmt = select(Guest)
        if search:
            pattern = f"%{search}%"
            stmt = stmt.where(
                or_(
                    Guest.first_name.ilike(pattern),
                    Guest.last_name.ilike(pattern),
                    Guest.email.ilike(pattern),
                )
            )
        return len(list(self.session.scalars(stmt).all()))

    def update(self, guest: Guest) -> Guest:
        self.session.commit()
        self.session.refresh(guest)
        return guest

    def delete(self, guest_id: int) -> bool:
        guest = self.get_by_id(guest_id)
        if not guest:
            return False
        self.session.delete(guest)
        self.session.commit()
        return True


class ReservationRepository:
    """Data access repository for Reservation entity with collision checks."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, reservation: Reservation) -> Reservation:
        self.session.add(reservation)
        self.session.commit()
        self.session.refresh(reservation)
        return reservation

    def get_by_id(self, reservation_id: int) -> Optional[Reservation]:
        return self.session.get(Reservation, reservation_id)

    def get_all(
        self,
        status: Optional[str] = None,
        room_number: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Reservation]:
        stmt = select(Reservation)
        if status:
            stmt = stmt.where(Reservation.status == status)
        if room_number:
            stmt = stmt.where(Reservation.room_number == room_number)
        stmt = stmt.order_by(Reservation.id.desc()).offset(skip).limit(limit)
        return list(self.session.scalars(stmt).all())

    def count(
        self,
        status: Optional[str] = None,
        room_number: Optional[int] = None,
    ) -> int:
        stmt = select(Reservation)
        if status:
            stmt = stmt.where(Reservation.status == status)
        if room_number:
            stmt = stmt.where(Reservation.room_number == room_number)
        return len(list(self.session.scalars(stmt).all()))

    def get_conflicting_reservations(
        self,
        room_number: int,
        check_in: date,
        check_out: date,
        exclude_reservation_id: Optional[int] = None,
    ) -> list[Reservation]:
        """Detect date collision: two intervals [A, B) and [C, D) overlap iff A < D and B > C."""
        stmt = select(Reservation).where(
            and_(
                Reservation.room_number == room_number,
                Reservation.status == "confirmed",
                Reservation.check_in < check_out,
                Reservation.check_out > check_in,
            )
        )
        if exclude_reservation_id is not None:
            stmt = stmt.where(Reservation.id != exclude_reservation_id)
        return list(self.session.scalars(stmt).all())

    def update(self, reservation: Reservation) -> Reservation:
        self.session.commit()
        self.session.refresh(reservation)
        return reservation

    def delete(self, reservation_id: int) -> bool:
        res = self.get_by_id(reservation_id)
        if not res:
            return False
        self.session.delete(res)
        self.session.commit()
        return True
