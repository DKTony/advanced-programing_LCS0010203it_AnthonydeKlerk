from __future__ import annotations

import pytest

from api import create_app
from models import DatabaseManager, Delivery, Repository, Truck


@pytest.fixture()
def repository(tmp_path):
    DatabaseManager.reset_instance()
    database_url = f"sqlite:///{tmp_path / 'namlog_test.db'}"
    repo = Repository(database_url)
    repo.initialize_database()
    yield repo, database_url
    DatabaseManager.reset_instance()


def test_truck_validation_rejects_negative_capacity() -> None:
    with pytest.raises(ValueError):
        Truck("N 999 WB", -2.0, "Walvis Bay")


def test_database_manager_uses_singleton_instance(repository) -> None:
    _repo, database_url = repository
    first = DatabaseManager(database_url)
    second = DatabaseManager("sqlite:///another.db")
    assert first is second
    assert first.database_url == database_url


def test_truck_is_created_and_persisted(repository) -> None:
    repo, _database_url = repository
    truck = repo.create_truck(Truck("N 123 WB", 28.0, "Walvis Bay"))

    saved = repo.get_truck(truck.id)

    assert saved is not None
    assert saved.registration == "N 123 WB"
    assert saved.capacity_tonnes == 28.0


def test_delivery_is_created_with_assigned_truck(repository) -> None:
    repo, _database_url = repository
    truck = repo.create_truck(Truck("N 555 WB", 18.0, "Walvis Bay"))

    delivery = repo.create_delivery(Delivery("Walvis Bay", "Gaborone", 4500, truck.id))

    assert delivery.id is not None
    assert delivery.assigned_truck_id == truck.id
    assert delivery.status == "Pending"


def test_delivery_status_update_validates_allowed_values(repository) -> None:
    repo, _database_url = repository
    delivery = repo.create_delivery(Delivery("Walvis Bay", "Lusaka", 2400))

    updated = repo.update_delivery_status(delivery.id, "In Transit")

    assert updated is not None
    assert updated.status == "In Transit"
    with pytest.raises(ValueError):
        repo.update_delivery_status(delivery.id, "Lost")


def test_api_get_trucks_returns_json_list(tmp_path) -> None:
    DatabaseManager.reset_instance()
    database_url = f"sqlite:///{tmp_path / 'api_test.db'}"
    app = create_app(database_url=database_url, seed_data=False)
    repo = app.extensions["repository"]
    repo.create_truck(Truck("N 222 WHK", 25.0, "Windhoek"))

    response = app.test_client().get("/api/trucks")

    assert response.status_code == 200
    assert response.is_json
    assert response.get_json()[0]["registration"] == "N 222 WHK"
    DatabaseManager.reset_instance()


def test_api_create_and_update_delivery(tmp_path) -> None:
    DatabaseManager.reset_instance()
    database_url = f"sqlite:///{tmp_path / 'api_delivery_test.db'}"
    app = create_app(database_url=database_url, seed_data=False)
    repo = app.extensions["repository"]
    truck = repo.create_truck(Truck("N 777 KAT", 30.0, "Katima Mulilo"))
    client = app.test_client()

    create_response = client.post(
        "/api/deliveries",
        json={
            "origin": "Walvis Bay",
            "destination": "Harare",
            "weight_kg": 6100,
            "assigned_truck_id": truck.id,
        },
    )
    delivery_id = create_response.get_json()["id"]
    update_response = client.put(f"/api/deliveries/{delivery_id}", json={"status": "Delivered"})

    assert create_response.status_code == 201
    assert update_response.status_code == 200
    assert update_response.get_json()["status"] == "Delivered"
    DatabaseManager.reset_instance()
