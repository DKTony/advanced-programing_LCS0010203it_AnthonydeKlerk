from __future__ import annotations

import threading
import time
from typing import Any, Optional

from flask import Flask, jsonify, request
from sqlalchemy.exc import SQLAlchemyError

from models import Delivery, Repository, Truck


database_write_lock = threading.Lock()


def create_app(database_url: str = "sqlite:///namlog.db", seed_data: bool = True) -> Flask:
    app = Flask(__name__)
    repository = Repository(database_url)
    repository.initialize_database()
    app.extensions["repository"] = repository

    if seed_data and not repository.list_trucks():
        seed_default_trucks(repository)

    @app.get("/api/trucks")
    def get_trucks() -> tuple[Any, int]:
        try:
            trucks = [truck.to_dict() for truck in repository.list_trucks()]
            return jsonify(trucks), 200
        except SQLAlchemyError as exc:
            return jsonify({"error": "Database error while loading trucks.", "details": str(exc)}), 500

    @app.get("/api/trucks/<int:truck_id>")
    def get_truck(truck_id: int) -> tuple[Any, int]:
        try:
            truck = repository.get_truck(truck_id)
            if truck is None:
                return jsonify({"error": "Truck not found."}), 404
            return jsonify(truck.to_dict()), 200
        except SQLAlchemyError as exc:
            return jsonify({"error": "Database error while loading truck.", "details": str(exc)}), 500

    @app.delete("/api/trucks/<int:truck_id>")
    def delete_truck(truck_id: int) -> tuple[Any, int]:
        try:
            with database_write_lock:
                deleted = repository.delete_truck(truck_id)
            if not deleted:
                return jsonify({"error": "Truck not found."}), 404
            return jsonify({}), 204
        except SQLAlchemyError as exc:
            return jsonify({"error": "Database error while deleting truck.", "details": str(exc)}), 500

    @app.get("/api/deliveries")
    def get_deliveries() -> tuple[Any, int]:
        try:
            deliveries = [delivery.to_dict() for delivery in repository.list_deliveries()]
            return jsonify(deliveries), 200
        except SQLAlchemyError as exc:
            return jsonify({"error": "Database error while loading deliveries.", "details": str(exc)}), 500

    @app.post("/api/deliveries")
    def create_delivery() -> tuple[Any, int]:
        payload = request.get_json(silent=True) or {}
        try:
            delivery = Delivery(
                origin=str(payload.get("origin", "")),
                destination=str(payload.get("destination", "")),
                weight_kg=float(payload.get("weight_kg", 0)),
                assigned_truck_id=_optional_int(payload.get("assigned_truck_id")),
                status=str(payload.get("status", "Pending")),
            )
            with database_write_lock:
                created = repository.create_delivery(delivery)
            return jsonify(created.to_dict()), 201
        except (TypeError, ValueError) as exc:
            return jsonify({"error": str(exc)}), 400
        except SQLAlchemyError as exc:
            return jsonify({"error": "Database error while creating delivery.", "details": str(exc)}), 500

    @app.put("/api/deliveries/<int:delivery_id>")
    def update_delivery(delivery_id: int) -> tuple[Any, int]:
        payload = request.get_json(silent=True) or {}
        status = str(payload.get("status", ""))
        try:
            with database_write_lock:
                delivery = repository.update_delivery_status(delivery_id, status)
            if delivery is None:
                return jsonify({"error": "Delivery not found."}), 404
            return jsonify(delivery.to_dict()), 200
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        except SQLAlchemyError as exc:
            return jsonify({"error": "Database error while updating delivery.", "details": str(exc)}), 500

    return app


def _optional_int(value: Any) -> Optional[int]:
    if value in (None, ""):
        return None
    return int(value)


def seed_default_trucks(repository: Repository) -> None:
    default_trucks = [
        Truck("N 123 WB", 28.0, "Walvis Bay", True),
        Truck("N 456 WHK", 20.0, "Windhoek", True),
        Truck("N 789 KAT", 32.0, "Katima Mulilo", False),
    ]
    with database_write_lock:
        for truck in default_trucks:
            repository.create_truck(truck)


def process_manifest(repository: Repository, records: Optional[list[dict[str, Any]]] = None) -> int:
    sample_records = records or [
        {
            "origin": "Walvis Bay",
            "destination": "Gaborone",
            "weight_kg": 7600,
            "assigned_truck_id": 1,
        },
        {
            "origin": "Walvis Bay",
            "destination": "Lusaka",
            "weight_kg": 12400,
            "assigned_truck_id": 2,
        },
    ]
    created_count = 0

    for record in sample_records:
        time.sleep(2.0)
        print(
            f"[manifest-worker] importing {record['origin']} -> {record['destination']}",
            flush=True,
        )
        delivery = Delivery(
            origin=str(record["origin"]),
            destination=str(record["destination"]),
            weight_kg=float(record["weight_kg"]),
            assigned_truck_id=_optional_int(record.get("assigned_truck_id")),
        )
        # Without this Lock, the Flask request thread and manifest worker could
        # commit delivery writes at the same time. In NamLog, that race could
        # double-book a truck or leave a delivery partially committed in SQLite.
        with database_write_lock:
            repository.create_delivery(delivery)
        created_count += 1
        print(f"[manifest-worker] imported delivery #{created_count}", flush=True)

    return created_count


def start_manifest_worker(repository: Repository) -> threading.Thread:
    worker = threading.Thread(
        target=process_manifest,
        args=(repository,),
        name="manifest-worker",
        daemon=True,
    )
    worker.start()
    print(f"[main] started background thread: {worker.name}", flush=True)
    return worker


def run_api_server(host: str = "127.0.0.1", port: int = 5000) -> None:
    app = create_app()
    app.run(host=host, port=port, debug=False, use_reloader=False)


if __name__ == "__main__":
    run_api_server()
