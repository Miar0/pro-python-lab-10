"""Integration tests for FastAPI REST API endpoints."""

from datetime import date, timedelta

from fastapi.testclient import TestClient


def test_rooms_api_crud_flow(client: TestClient) -> None:
    # 1. Create room
    payload = {
        "room_number": 401,
        "room_type": "suite",
        "price": 220.0,
        "status": "available",
    }
    create_resp = client.post("/rooms", json=payload)
    assert create_resp.status_code == 201
    room = create_resp.json()
    assert room["room_number"] == 401
    room_id = room["id"]

    # Duplicate room conflict (409)
    dup_resp = client.post("/rooms", json=payload)
    assert dup_resp.status_code == 409
    assert dup_resp.json()["error"] == "CONFLICT"

    # 2. Get room by ID
    get_resp = client.get(f"/rooms/{room_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["room_number"] == 401

    # 3. List rooms
    list_resp = client.get("/rooms?page=1&page_size=10")
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] >= 1

    # 4. Patch room
    patch_resp = client.patch(f"/rooms/{room_id}", json={"price": 240.0})
    assert patch_resp.status_code == 200
    assert patch_resp.json()["price"] == 240.0

    # 5. Delete room
    del_resp = client.delete(f"/rooms/{room_id}")
    assert del_resp.status_code == 204

    # 6. Verify 404
    get_404 = client.get(f"/rooms/{room_id}")
    assert get_404.status_code == 404


def test_available_and_cheapest_rooms_api(client: TestClient) -> None:
    # Seed rooms
    client.post(
        "/rooms",
        json={
            "room_number": 110,
            "room_type": "single",
            "price": 95.0,
            "status": "available",
        },
    )
    client.post(
        "/rooms",
        json={
            "room_number": 120,
            "room_type": "double",
            "price": 140.0,
            "status": "available",
        },
    )

    today = date.today()
    check_in = (today + timedelta(days=1)).isoformat()
    check_out = (today + timedelta(days=3)).isoformat()

    # Search available rooms
    avail_resp = client.get(
        f"/rooms/available?check_in={check_in}&check_out={check_out}"
    )
    assert avail_resp.status_code == 200
    rooms = avail_resp.json()
    assert len(rooms) >= 2

    # Invalid dates (checkout before checkin)
    invalid_resp = client.get(
        f"/rooms/available?check_in={check_out}&check_out={check_in}"
    )
    assert invalid_resp.status_code == 400

    # Cheapest room
    cheap_resp = client.get("/rooms/cheapest")
    assert cheap_resp.status_code == 200
    assert cheap_resp.json()["price"] <= 95.0


def test_revenue_statistics_api(client: TestClient) -> None:
    client.post(
        "/rooms",
        json={
            "room_number": 210,
            "room_type": "single",
            "price": 100.0,
            "status": "available",
        },
    )
    client.post(
        "/rooms",
        json={
            "room_number": 220,
            "room_type": "double",
            "price": 200.0,
            "status": "available",
        },
    )

    resp = client.get("/rooms/revenue")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_rooms"] >= 2
    assert data["average_room_price"] > 0


def test_guests_api_crud_flow(client: TestClient) -> None:
    guest_data = {
        "first_name": "Serhiy",
        "last_name": "Zhadan",
        "email": "zhadan@example.com",
        "phone": "+380509998877",
    }
    create_resp = client.post("/guests", json=guest_data)
    assert create_resp.status_code == 201
    guest_id = create_resp.json()["id"]

    # Duplicate email conflict
    dup_resp = client.post("/guests", json=guest_data)
    assert dup_resp.status_code == 409

    # Get guest
    get_resp = client.get(f"/guests/{guest_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["email"] == "zhadan@example.com"

    # List guests
    list_resp = client.get("/guests?search=Zhadan")
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] == 1

    # Update guest
    patch_resp = client.patch(
        f"/guests/{guest_id}", json={"first_name": "Serhiy-Updated"}
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["first_name"] == "Serhiy-Updated"

    # Delete guest
    del_resp = client.delete(f"/guests/{guest_id}")
    assert del_resp.status_code == 204


def test_reservations_api_double_booking_prevention(client: TestClient) -> None:
    # Setup room
    client.post(
        "/rooms",
        json={
            "room_number": 555,
            "room_type": "suite",
            "price": 200.0,
            "status": "available",
        },
    )

    today = date.today()
    check_in = (today + timedelta(days=10)).isoformat()
    check_out = (today + timedelta(days=15)).isoformat()

    res_payload = {
        "room_number": 555,
        "guest_name": "Oksana Zabuzhko",
        "check_in": check_in,
        "check_out": check_out,
    }

    # 1. First booking succeeds (201)
    res_resp = client.post("/reservations", json=res_payload)
    assert res_resp.status_code == 201
    res_data = res_resp.json()
    assert res_data["total_price"] == 1000.0  # 5 nights * 200
    res_id = res_data["id"]

    # 2. Conflicting booking for overlapping interval (409 Conflict)
    collision_payload = {
        "room_number": 555,
        "guest_name": "Second Guest",
        "check_in": (today + timedelta(days=12)).isoformat(),
        "check_out": (today + timedelta(days=16)).isoformat(),
    }
    conflict_resp = client.post("/reservations", json=collision_payload)
    assert conflict_resp.status_code == 409
    assert "Double booking collision" in conflict_resp.json()["detail"]

    # 3. Get reservation by ID
    get_res = client.get(f"/reservations/{res_id}")
    assert get_res.status_code == 200
    assert get_res.json()["room_number"] == 555

    # 4. List reservations
    list_res = client.get("/reservations?room_number=555")
    assert list_res.status_code == 200
    assert list_res.json()["total"] == 1

    # 5. Cancel reservation (delete endpoint)
    cancel_resp = client.delete(f"/reservations/{res_id}")
    assert cancel_resp.status_code == 204

    # Verify status changed to cancelled
    get_cancelled = client.get(f"/reservations/{res_id}")
    assert get_cancelled.json()["status"] == "cancelled"
