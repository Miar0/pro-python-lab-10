"""FastAPI REST API application for Hotel Booking System."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import date
from typing import Optional

from fastapi import Depends, FastAPI, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from hotel_booking import __version__
from hotel_booking.config import get_settings, setup_logging
from hotel_booking.database import get_db, init_db
from hotel_booking.exceptions import (
    ConflictException,
    EntityNotFoundException,
    ValidationException,
)
from hotel_booking.schemas import (
    GuestCreate,
    GuestRead,
    GuestUpdate,
    HealthResponse,
    PaginatedResponse,
    ReservationCreate,
    ReservationRead,
    RevenueStatisticsResponse,
    RoomCreate,
    RoomRead,
    RoomUpdate,
)
from hotel_booking.services import HotelService

settings = get_settings()
setup_logging(settings)
logger = logging.getLogger("hotel_booking.api")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager initializing database and logging startup."""
    logger.info("Initializing database schema...")
    init_db()
    logger.info(
        "Hotel Booking API started [env=%s, version=%s]",
        settings.environment,
        __version__,
    )
    yield
    logger.info("Hotel Booking API shutting down...")


app = FastAPI(
    title=settings.app_name,
    version=__version__,
    description="Production-grade REST API for Hotel Booking System (Lab 10, Variant 8)",
    lifespan=lifespan,
)


# -------------------------------------------------------------------------
# Exception Handlers
# -------------------------------------------------------------------------
@app.exception_handler(EntityNotFoundException)
async def not_found_handler(
    request: object, exc: EntityNotFoundException
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": exc.message, "error": "NOT_FOUND"},
    )


@app.exception_handler(ConflictException)
async def conflict_handler(request: object, exc: ConflictException) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": exc.message, "error": "CONFLICT"},
    )


@app.exception_handler(ValidationException)
async def validation_handler(request: object, exc: ValidationException) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": exc.message, "error": "BAD_REQUEST"},
    )


# -------------------------------------------------------------------------
# Health Check Endpoint
# -------------------------------------------------------------------------
@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Health check endpoint",
)
async def health_check() -> HealthResponse:
    """Return application health status and active runtime environment."""
    return HealthResponse(
        status="ok",
        environment=settings.environment,
        version=__version__,
        app_name=settings.app_name,
    )


@app.get("/", tags=["Root"])
async def root() -> dict[str, str]:
    """Root landing endpoint with system metadata and documentation links."""
    return {
        "app": settings.app_name,
        "version": __version__,
        "environment": settings.environment,
        "docs_url": "/docs",
        "health_url": "/health",
    }


# -------------------------------------------------------------------------
# Room Endpoints
# -------------------------------------------------------------------------
@app.get(
    "/rooms",
    response_model=PaginatedResponse[RoomRead],
    tags=["Rooms"],
    summary="List all rooms with filtering and pagination",
)
def list_rooms(
    room_type: Optional[str] = Query(None, description="Filter by room type"),
    status_filter: Optional[str] = Query(
        None, alias="status", description="Filter by status"
    ),
    max_price: Optional[float] = Query(
        None, gt=0, description="Filter by maximum price"
    ),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
) -> PaginatedResponse[RoomRead]:
    service = HotelService(db)
    skip = (page - 1) * page_size
    rooms, total = service.list_rooms(
        room_type=room_type,
        status=status_filter,
        max_price=max_price,
        skip=skip,
        limit=page_size,
    )
    total_pages = max(1, (total + page_size - 1) // page_size)
    return PaginatedResponse[RoomRead](
        items=[RoomRead.model_validate(r) for r in rooms],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@app.post(
    "/rooms",
    response_model=RoomRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Rooms"],
    summary="Create a new hotel room",
)
def create_room(room_in: RoomCreate, db: Session = Depends(get_db)) -> RoomRead:
    service = HotelService(db)
    room = service.create_room(
        room_number=room_in.room_number,
        room_type=room_in.room_type,
        price=room_in.price,
        status=room_in.status,
    )
    return RoomRead.model_validate(room)


@app.get(
    "/rooms/available",
    response_model=list[RoomRead],
    tags=["Rooms"],
    summary="Search for available rooms in a date range",
)
def get_available_rooms(
    check_in: date = Query(..., description="Check-in date (YYYY-MM-DD)"),
    check_out: date = Query(..., description="Check-out date (YYYY-MM-DD)"),
    room_type: Optional[str] = Query(None, description="Optional room type"),
    max_price: Optional[float] = Query(
        None, gt=0, description="Optional maximum price"
    ),
    db: Session = Depends(get_db),
) -> list[RoomRead]:
    service = HotelService(db)
    rooms = service.get_available_rooms(
        check_in=check_in,
        check_out=check_out,
        room_type=room_type,
        max_price=max_price,
    )
    return [RoomRead.model_validate(r) for r in rooms]


@app.get(
    "/rooms/cheapest",
    response_model=RoomRead,
    tags=["Rooms"],
    summary="Find the lowest priced room",
)
def get_cheapest_room(
    room_type: Optional[str] = Query(None, description="Optional room type filter"),
    db: Session = Depends(get_db),
) -> RoomRead:
    service = HotelService(db)
    room = service.find_cheapest_room(room_type=room_type)
    return RoomRead.model_validate(room)


@app.get(
    "/rooms/revenue",
    response_model=RevenueStatisticsResponse,
    tags=["Rooms"],
    summary="Calculate hotel potential and confirmed revenue",
)
def get_revenue_statistics(db: Session = Depends(get_db)) -> RevenueStatisticsResponse:
    service = HotelService(db)
    stats = service.calculate_potential_revenue()
    return RevenueStatisticsResponse(
        total_rooms=int(stats["total_rooms"]),
        active_rooms=int(stats["active_rooms"]),
        confirmed_reservations=int(stats["confirmed_reservations"]),
        total_revenue=stats["total_revenue"],
        potential_revenue=stats["potential_revenue"],
        average_room_price=stats["average_room_price"],
        minimum_room_price=stats["minimum_room_price"],
        maximum_room_price=stats["maximum_room_price"],
        price_std_dev=stats["price_std_dev"],
    )


@app.get(
    "/rooms/{room_id}",
    response_model=RoomRead,
    tags=["Rooms"],
    summary="Get room details by ID",
)
def get_room(room_id: int, db: Session = Depends(get_db)) -> RoomRead:
    service = HotelService(db)
    room = service.get_room(room_id)
    return RoomRead.model_validate(room)


@app.patch(
    "/rooms/{room_id}",
    response_model=RoomRead,
    tags=["Rooms"],
    summary="Update room details",
)
def update_room(
    room_id: int,
    room_in: RoomUpdate,
    db: Session = Depends(get_db),
) -> RoomRead:
    service = HotelService(db)
    room = service.update_room(
        room_id=room_id,
        room_type=room_in.room_type,
        price=room_in.price,
        status=room_in.status,
    )
    return RoomRead.model_validate(room)


@app.delete(
    "/rooms/{room_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Rooms"],
    summary="Delete room",
)
def delete_room(room_id: int, db: Session = Depends(get_db)) -> None:
    service = HotelService(db)
    service.delete_room(room_id)


# -------------------------------------------------------------------------
# Guest Endpoints
# -------------------------------------------------------------------------
@app.post(
    "/guests",
    response_model=GuestRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Guests"],
    summary="Register a new guest",
)
def create_guest(guest_in: GuestCreate, db: Session = Depends(get_db)) -> GuestRead:
    service = HotelService(db)
    guest = service.create_guest(
        first_name=guest_in.first_name,
        last_name=guest_in.last_name,
        email=guest_in.email,
        phone=guest_in.phone,
    )
    return GuestRead.model_validate(guest)


@app.get(
    "/guests",
    response_model=PaginatedResponse[GuestRead],
    tags=["Guests"],
    summary="List guests",
)
def list_guests(
    search: Optional[str] = Query(None, description="Search by name or email"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
) -> PaginatedResponse[GuestRead]:
    service = HotelService(db)
    skip = (page - 1) * page_size
    guests, total = service.list_guests(search=search, skip=skip, limit=page_size)
    total_pages = max(1, (total + page_size - 1) // page_size)
    return PaginatedResponse[GuestRead](
        items=[GuestRead.model_validate(g) for g in guests],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@app.get(
    "/guests/{guest_id}",
    response_model=GuestRead,
    tags=["Guests"],
    summary="Get guest profile",
)
def get_guest(guest_id: int, db: Session = Depends(get_db)) -> GuestRead:
    service = HotelService(db)
    guest = service.get_guest(guest_id)
    return GuestRead.model_validate(guest)


@app.patch(
    "/guests/{guest_id}",
    response_model=GuestRead,
    tags=["Guests"],
    summary="Update guest profile",
)
def update_guest(
    guest_id: int,
    guest_in: GuestUpdate,
    db: Session = Depends(get_db),
) -> GuestRead:
    service = HotelService(db)
    guest = service.update_guest(
        guest_id=guest_id,
        first_name=guest_in.first_name,
        last_name=guest_in.last_name,
        email=guest_in.email,
        phone=guest_in.phone,
    )
    return GuestRead.model_validate(guest)


@app.delete(
    "/guests/{guest_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Guests"],
    summary="Delete guest record",
)
def delete_guest(guest_id: int, db: Session = Depends(get_db)) -> None:
    service = HotelService(db)
    service.delete_guest(guest_id)


# -------------------------------------------------------------------------
# Reservation Endpoints
# -------------------------------------------------------------------------
@app.post(
    "/reservations",
    response_model=ReservationRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Reservations"],
    summary="Create a new reservation with double booking prevention",
)
def create_reservation(
    res_in: ReservationCreate,
    db: Session = Depends(get_db),
) -> ReservationRead:
    service = HotelService(db)
    reservation = service.book_room(
        room_number=res_in.room_number,
        guest_name=res_in.guest_name,
        check_in=res_in.check_in,
        check_out=res_in.check_out,
        guest_id=res_in.guest_id,
    )
    return ReservationRead.model_validate(reservation)


@app.get(
    "/reservations",
    response_model=PaginatedResponse[ReservationRead],
    tags=["Reservations"],
    summary="List all reservations",
)
def list_reservations(
    status_filter: Optional[str] = Query(
        None, alias="status", description="Filter by confirmed/cancelled"
    ),
    room_number: Optional[int] = Query(None, description="Filter by room number"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
) -> PaginatedResponse[ReservationRead]:
    service = HotelService(db)
    skip = (page - 1) * page_size
    reservations, total = service.list_reservations(
        status=status_filter,
        room_number=room_number,
        skip=skip,
        limit=page_size,
    )
    total_pages = max(1, (total + page_size - 1) // page_size)
    return PaginatedResponse[ReservationRead](
        items=[ReservationRead.model_validate(r) for r in reservations],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@app.get(
    "/reservations/{reservation_id}",
    response_model=ReservationRead,
    tags=["Reservations"],
    summary="Get reservation by ID",
)
def get_reservation(
    reservation_id: int,
    db: Session = Depends(get_db),
) -> ReservationRead:
    service = HotelService(db)
    res = service.get_reservation(reservation_id)
    return ReservationRead.model_validate(res)


@app.delete(
    "/reservations/{reservation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Reservations"],
    summary="Cancel / delete reservation",
)
def cancel_reservation(
    reservation_id: int,
    db: Session = Depends(get_db),
) -> None:
    service = HotelService(db)
    service.cancel_reservation(reservation_id)
