from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import Any, Optional

from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, relationship


class DeclarativeABCMeta(type(DeclarativeBase), ABCMeta):
    """Combines SQLAlchemy's declarative metaclass with ABC enforcement."""


class Base(DeclarativeBase, metaclass=DeclarativeABCMeta):
    pass


class User(Base):
    """Abstract base user mapped with SQLAlchemy polymorphic inheritance."""

    __tablename__ = "users"

    __id = Column("id", Integer, primary_key=True)
    __name = Column("name", String(80), nullable=False)
    __email = Column("email", String(120), nullable=False, unique=True)
    __role = Column("role", String(20), nullable=False)

    __mapper_args__ = {
        "polymorphic_on": __role,
        "polymorphic_identity": "user",
    }

    def __init__(self, name: str, email: str, role: str) -> None:
        self.name = name
        self.email = email
        self.role = role

    @property
    def id(self) -> Optional[int]:
        return self.__id

    @property
    def name(self) -> str:
        return self.__name

    @name.setter
    def name(self, value: str) -> None:
        if not value or not value.strip():
            raise ValueError("User name is required.")
        self.__name = value.strip()

    @property
    def email(self) -> str:
        return self.__email

    @email.setter
    def email(self, value: str) -> None:
        if "@" not in value:
            raise ValueError("A valid email address is required.")
        self.__email = value.strip().lower()

    @property
    def role(self) -> str:
        return self.__role

    @role.setter
    def role(self, value: str) -> None:
        allowed_roles = {"admin", "guest"}
        if value not in allowed_roles:
            raise ValueError(f"Role must be one of: {', '.join(sorted(allowed_roles))}.")
        self.__role = value

    @abstractmethod
    def get_permissions(self) -> list[str]:
        """Return the permissions granted to this user type."""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "permissions": self.get_permissions(),
        }


class Admin(User):
    """Administrative user with full freight-tracking permissions."""

    __mapper_args__ = {"polymorphic_identity": "admin"}

    def __init__(self, name: str, email: str) -> None:
        # The subclass delegates shared validation and role assignment to User.
        super().__init__(name, email, "admin")

    def get_permissions(self) -> list[str]:
        return ["create", "read", "update", "delete"]


class Guest(User):
    """Read-only user for staff who should not modify freight data."""

    __mapper_args__ = {"polymorphic_identity": "guest"}

    def __init__(self, name: str, email: str) -> None:
        # The subclass delegates shared validation and role assignment to User.
        super().__init__(name, email, "guest")

    def get_permissions(self) -> list[str]:
        return ["read"]


class Truck(Base):
    __tablename__ = "trucks"

    __id = Column("id", Integer, primary_key=True)
    __registration = Column("registration", String(30), nullable=False, unique=True)
    __capacity_tonnes = Column("capacity_tonnes", Float, nullable=False)
    __current_location = Column("current_location", String(80), nullable=False)
    __is_available = Column("is_available", Boolean, nullable=False, default=True)

    deliveries = relationship(
        "Delivery",
        back_populates="assigned_truck",
        cascade="all, delete-orphan",
    )

    def __init__(
        self,
        registration: str,
        capacity_tonnes: float,
        current_location: str,
        is_available: bool = True,
    ) -> None:
        self.registration = registration
        self.capacity_tonnes = capacity_tonnes
        self.current_location = current_location
        self.is_available = is_available

    @property
    def id(self) -> Optional[int]:
        return self.__id

    @property
    def registration(self) -> str:
        return self.__registration

    @registration.setter
    def registration(self, value: str) -> None:
        if not value or not value.strip():
            raise ValueError("Truck registration is required.")
        self.__registration = value.strip().upper()

    @property
    def capacity_tonnes(self) -> float:
        return self.__capacity_tonnes

    @capacity_tonnes.setter
    def capacity_tonnes(self, value: float) -> None:
        if value <= 0:
            raise ValueError("Truck capacity must be greater than zero tonnes.")
        self.__capacity_tonnes = float(value)

    @property
    def current_location(self) -> str:
        return self.__current_location

    @current_location.setter
    def current_location(self, value: str) -> None:
        if not value or not value.strip():
            raise ValueError("Current location is required.")
        self.__current_location = value.strip()

    @property
    def is_available(self) -> bool:
        return self.__is_available

    @is_available.setter
    def is_available(self, value: bool) -> None:
        self.__is_available = bool(value)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "registration": self.registration,
            "capacity_tonnes": self.capacity_tonnes,
            "current_location": self.current_location,
            "is_available": self.is_available,
        }


class Delivery(Base):
    __tablename__ = "deliveries"

    VALID_STATUSES = {"Pending", "In Transit", "Delivered", "Cancelled"}

    __id = Column("id", Integer, primary_key=True)
    __origin = Column("origin", String(80), nullable=False)
    __destination = Column("destination", String(80), nullable=False)
    __weight_kg = Column("weight_kg", Float, nullable=False)
    __assigned_truck_id = Column(
        "assigned_truck_id",
        Integer,
        ForeignKey("trucks.id"),
        nullable=True,
    )
    __status = Column("status", String(30), nullable=False, default="Pending")

    assigned_truck = relationship("Truck", back_populates="deliveries")

    def __init__(
        self,
        origin: str,
        destination: str,
        weight_kg: float,
        assigned_truck_id: Optional[int] = None,
        status: str = "Pending",
    ) -> None:
        self.origin = origin
        self.destination = destination
        self.weight_kg = weight_kg
        self.assigned_truck_id = assigned_truck_id
        self.status = status

    @property
    def id(self) -> Optional[int]:
        return self.__id

    @property
    def origin(self) -> str:
        return self.__origin

    @origin.setter
    def origin(self, value: str) -> None:
        if not value or not value.strip():
            raise ValueError("Delivery origin is required.")
        self.__origin = value.strip()

    @property
    def destination(self) -> str:
        return self.__destination

    @destination.setter
    def destination(self, value: str) -> None:
        if not value or not value.strip():
            raise ValueError("Delivery destination is required.")
        self.__destination = value.strip()

    @property
    def weight_kg(self) -> float:
        return self.__weight_kg

    @weight_kg.setter
    def weight_kg(self, value: float) -> None:
        if value <= 0:
            raise ValueError("Delivery weight must be greater than zero kilograms.")
        self.__weight_kg = float(value)

    @property
    def assigned_truck_id(self) -> Optional[int]:
        return self.__assigned_truck_id

    @assigned_truck_id.setter
    def assigned_truck_id(self, value: Optional[int]) -> None:
        if value is not None and value <= 0:
            raise ValueError("Assigned truck id must be a positive integer.")
        self.__assigned_truck_id = value

    @property
    def status(self) -> str:
        return self.__status

    @status.setter
    def status(self, value: str) -> None:
        if value not in self.VALID_STATUSES:
            raise ValueError(f"Status must be one of: {', '.join(sorted(self.VALID_STATUSES))}.")
        self.__status = value

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "origin": self.origin,
            "destination": self.destination,
            "weight_kg": self.weight_kg,
            "assigned_truck_id": self.assigned_truck_id,
            "status": self.status,
        }


class DatabaseManager:
    """Singleton wrapper around the SQLAlchemy engine.

    SQLite is file-based and sensitive to concurrent writers. Sharing one engine
    configuration keeps the desktop app, Flask API, and worker thread pointed at
    the same database instead of opening competing connection managers.
    """

    _instance: Optional["DatabaseManager"] = None

    def __new__(cls, database_url: str = "sqlite:///namlog.db") -> "DatabaseManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialise(database_url)
        return cls._instance

    def _initialise(self, database_url: str) -> None:
        self.__database_url = database_url
        self.__engine = create_engine(
            database_url,
            echo=False,
            future=True,
            connect_args={"check_same_thread": False}
            if database_url.startswith("sqlite")
            else {},
        )

    @property
    def engine(self) -> Engine:
        return self.__engine

    @property
    def database_url(self) -> str:
        return self.__database_url

    def create_tables(self) -> None:
        Base.metadata.create_all(self.__engine)

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton for isolated unit tests."""
        cls._instance = None


class Repository:
    def __init__(self, database_url: str = "sqlite:///namlog.db") -> None:
        self.__database_manager = DatabaseManager(database_url)
        self.__engine = self.__database_manager.engine

    def initialize_database(self) -> None:
        self.__database_manager.create_tables()

    def create_user(self, user: User) -> User:
        with Session(self.__engine) as session:
            session.add(user)
            session.commit()
            session.refresh(user)
            return user

    def create_truck(self, truck: Truck) -> Truck:
        with Session(self.__engine) as session:
            session.add(truck)
            session.commit()
            session.refresh(truck)
            return truck

    def list_trucks(self) -> list[Truck]:
        with Session(self.__engine) as session:
            return list(session.query(Truck).order_by(Truck._Truck__id).all())

    def get_truck(self, truck_id: int) -> Optional[Truck]:
        with Session(self.__engine) as session:
            truck = session.get(Truck, truck_id)
            if truck is not None:
                session.expunge(truck)
            return truck

    def update_truck(self, truck_id: int, **changes: Any) -> Optional[Truck]:
        with Session(self.__engine) as session:
            truck = session.get(Truck, truck_id)
            if truck is None:
                return None
            for field, value in changes.items():
                if hasattr(type(truck), field):
                    setattr(truck, field, value)
            session.commit()
            session.refresh(truck)
            session.expunge(truck)
            return truck

    def delete_truck(self, truck_id: int) -> bool:
        with Session(self.__engine) as session:
            truck = session.get(Truck, truck_id)
            if truck is None:
                return False
            session.delete(truck)
            session.commit()
            return True

    def create_delivery(self, delivery: Delivery) -> Delivery:
        with Session(self.__engine) as session:
            if delivery.assigned_truck_id is not None:
                truck = session.get(Truck, delivery.assigned_truck_id)
                if truck is None:
                    raise ValueError("Assigned truck does not exist.")
                if delivery.weight_kg > truck.capacity_tonnes * 1000:
                    raise ValueError("Delivery weight exceeds assigned truck capacity.")
            session.add(delivery)
            session.commit()
            session.refresh(delivery)
            return delivery

    def list_deliveries(self) -> list[Delivery]:
        with Session(self.__engine) as session:
            return list(session.query(Delivery).order_by(Delivery._Delivery__id).all())

    def get_delivery(self, delivery_id: int) -> Optional[Delivery]:
        with Session(self.__engine) as session:
            delivery = session.get(Delivery, delivery_id)
            if delivery is not None:
                session.expunge(delivery)
            return delivery

    def update_delivery_status(self, delivery_id: int, status: str) -> Optional[Delivery]:
        with Session(self.__engine) as session:
            delivery = session.get(Delivery, delivery_id)
            if delivery is None:
                return None
            delivery.status = status
            session.commit()
            session.refresh(delivery)
            session.expunge(delivery)
            return delivery

    def delete_delivery(self, delivery_id: int) -> bool:
        with Session(self.__engine) as session:
            delivery = session.get(Delivery, delivery_id)
            if delivery is None:
                return False
            session.delete(delivery)
            session.commit()
            return True
