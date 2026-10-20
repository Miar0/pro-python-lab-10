"""SQLAlchemy ORM models for Hotel Booking domain."""

from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from hotel_booking.database import Base


class Room(Base):
    """Hotel Room entity representing physical accommodation."""

    __tablename__ = "rooms"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True, autoincrement=True
    )
    room_number: Mapped[int] = mapped_column(
        Integer, unique=True, index=True, nullable=False
    )
    room_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # single, double, suite, deluxe
    price: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="available", nullable=False
    )  # available, occupied, maintenance

    reservations: Mapped[list["Reservation"]] = relationship(
        "Reservation", back_populates="room", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Room(number={self.room_number}, type='{self.room_type}', price={self.price}, status='{self.status}')>"


class Guest(Base):
    """Guest entity holding guest contact details."""

    __tablename__ = "guests"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True, autoincrement=True
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    reservations: Mapped[list["Reservation"]] = relationship(
        "Reservation", back_populates="guest"
    )

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def __repr__(self) -> str:
        return f"<Guest(id={self.id}, name='{self.full_name}', email='{self.email}')>"


class Reservation(Base):
    """Reservation entity connecting a guest to a room for a date range."""

    __tablename__ = "reservations"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True, autoincrement=True
    )
    room_number: Mapped[int] = mapped_column(
        Integer, ForeignKey("rooms.room_number"), nullable=False, index=True
    )
    guest_name: Mapped[str] = mapped_column(String(200), nullable=False)
    guest_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("guests.id"), nullable=True
    )
    check_in: Mapped[date] = mapped_column(Date, nullable=False)
    check_out: Mapped[date] = mapped_column(Date, nullable=False)
    total_price: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="confirmed", nullable=False
    )  # confirmed, cancelled
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    room: Mapped["Room"] = relationship("Room", back_populates="reservations")
    guest: Mapped[Optional["Guest"]] = relationship(
        "Guest", back_populates="reservations"
    )

    @property
    def nights(self) -> int:
        return max(1, (self.check_out - self.check_in).days)

    def __repr__(self) -> str:
        return (
            f"<Reservation(id={self.id}, room={self.room_number}, "
            f"guest='{self.guest_name}', {self.check_in}->{self.check_out}, status='{self.status}')>"
        )
