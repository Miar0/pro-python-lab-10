"""Command Line Interface (CLI) and application runner."""

import argparse
import logging
import sys
from datetime import date, timedelta

import uvicorn

from hotel_booking import __version__
from hotel_booking.config import get_settings, setup_logging
from hotel_booking.database import SessionLocal, init_db
from hotel_booking.services import HotelService

logger = logging.getLogger("hotel_booking.main")


def seed_database() -> None:
    """Populate database with demonstration rooms, guests, and reservations."""
    logger.info("Seeding initial database data...")
    init_db()
    with SessionLocal() as db:
        service = HotelService(db)

        # Create demo rooms if not present
        rooms_data = [
            (101, "single", 100.0, "available"),
            (102, "double", 150.0, "available"),
            (103, "suite", 250.0, "available"),
            (201, "single", 110.0, "available"),
            (202, "double", 160.0, "available"),
            (203, "deluxe", 320.0, "available"),
            (301, "suite", 280.0, "maintenance"),
        ]
        for num, r_type, price, status in rooms_data:
            existing = service.room_repo.get_by_number(num)
            if not existing:
                service.create_room(num, r_type, price, status)

        # Create demo guests
        demo_guests = [
            ("Ivan", "Petrenko", "ivan.petrenko@example.com", "+380501112233"),
            ("Olena", "Kovalenko", "olena.kovalenko@example.com", "+380672223344"),
        ]
        for first, last, email, phone in demo_guests:
            if not service.guest_repo.get_by_email(email):
                service.create_guest(first, last, email, phone)

        # Create a confirmed reservation
        guest = service.guest_repo.get_by_email("ivan.petrenko@example.com")
        if guest and not service.reservation_repo.get_all(room_number=102):
            today = date.today()
            service.book_room(
                room_number=102,
                guest_name=guest.full_name,
                check_in=today + timedelta(days=2),
                check_out=today + timedelta(days=5),
                guest_id=guest.id,
            )

    logger.info("Database seeding successfully completed.")


def main() -> None:
    """Entry point for the 'hotel-booking' CLI script."""
    settings = get_settings()
    setup_logging(settings)

    parser = argparse.ArgumentParser(
        description="Hotel Booking System - Production Server & CLI",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--host",
        type=str,
        default=settings.api_host,
        help="Host address to bind the API server",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=settings.api_port,
        help="Port number to bind the API server",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development",
    )
    parser.add_argument(
        "--seed",
        action="store_true",
        help="Seed initial test data into the database before starting",
    )
    parser.add_argument(
        "--seed-only",
        action="store_true",
        help="Seed data and exit immediately without starting the web server",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"Hotel Booking System v{__version__}",
    )

    args = parser.parse_args()

    if args.seed or args.seed_only:
        seed_database()
        if args.seed_only:
            sys.exit(0)

    logger.info("Starting Uvicorn server at %s:%d ...", args.host, args.port)
    uvicorn.run(
        "hotel_booking.api:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
