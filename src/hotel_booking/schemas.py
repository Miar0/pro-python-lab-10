"""Pydantic v2 schemas for request validation and response serialization."""

from datetime import date, datetime
from typing import Generic, Literal, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

T = TypeVar("T")


class HealthResponse(BaseModel):
    """Schema for /health status endpoint."""

    status: str = Field(default="ok", description="Service health status")
    environment: str = Field(..., description="Active runtime environment")
    version: str = Field(default="1.0.0", description="API package version")
    app_name: str = Field(..., description="Application title")


class RoomBase(BaseModel):
    """Base room attributes."""

    room_number: int = Field(
        ..., gt=0, description="Unique room number", examples=[101]
    )
    room_type: Literal["single", "double", "suite", "deluxe"] = Field(
        default="single", description="Room classification"
    )
    price: float = Field(
        ..., gt=0.0, description="Nightly rate in currency units", examples=[150.0]
    )
    status: Literal["available", "occupied", "maintenance"] = Field(
        default="available", description="Operational status"
    )


class RoomCreate(RoomBase):
    """Schema for creating a new room."""

    pass


class RoomUpdate(BaseModel):
    """Schema for modifying room fields."""

    room_type: Optional[Literal["single", "double", "suite", "deluxe"]] = None
    price: Optional[float] = Field(None, gt=0.0)
    status: Optional[Literal["available", "occupied", "maintenance"]] = None


class RoomRead(RoomBase):
    """Schema for reading room information."""

    id: int
    model_config = ConfigDict(from_attributes=True)


class GuestBase(BaseModel):
    """Base guest details."""

    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr = Field(..., description="Unique email address")
    phone: Optional[str] = Field(None, max_length=50)


class GuestCreate(GuestBase):
    """Schema for registering a new guest."""

    pass


class GuestUpdate(BaseModel):
    """Schema for updating guest contact info."""

    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None


class GuestRead(GuestBase):
    """Schema for reading guest profile."""

    id: int
    full_name: str
    model_config = ConfigDict(from_attributes=True)


class ReservationBase(BaseModel):
    """Base reservation attributes."""

    room_number: int = Field(..., gt=0)
    guest_name: str = Field(..., min_length=1, max_length=200)
    guest_id: Optional[int] = None
    check_in: date
    check_out: date

    @model_validator(mode="after")
    def validate_date_order(self) -> "ReservationBase":
        if self.check_out <= self.check_in:
            raise ValueError("check_out date must be strictly after check_in date")
        return self


class ReservationCreate(ReservationBase):
    """Schema for creating a new booking."""

    pass


class ReservationUpdate(BaseModel):
    """Schema for amending a reservation."""

    check_in: Optional[date] = None
    check_out: Optional[date] = None
    status: Optional[Literal["confirmed", "cancelled"]] = None


class ReservationRead(BaseModel):
    """Schema for reading reservation details."""

    id: int
    room_number: int
    guest_name: str
    guest_id: Optional[int] = None
    check_in: date
    check_out: date
    total_price: float
    status: str
    nights: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class RevenueStatisticsResponse(BaseModel):
    """Financial and occupancy overview."""

    total_rooms: int
    active_rooms: int
    confirmed_reservations: int
    total_revenue: float
    potential_revenue: float
    average_room_price: float
    minimum_room_price: float
    maximum_room_price: float
    price_std_dev: float


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard pagination wrapper."""

    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int
