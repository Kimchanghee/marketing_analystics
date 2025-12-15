from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine

from app.auth import auth_manager
from app.config import get_settings
from app.database import get_session
from app.main import app
from app.models import User, UserRole


TEST_PASSWORD = "Passw0rd!"

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


def override_get_session():
    with Session(engine) as session:
        yield session


app.dependency_overrides[get_session] = override_get_session


@pytest.fixture(autouse=True)
def prepare_database():
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    yield
    SQLModel.metadata.drop_all(engine)


def seed_user(email: str, role: UserRole) -> None:
    with Session(engine) as session:
        user = User(
            email=email,
            hashed_password=auth_manager.hash_password(TEST_PASSWORD),
            role=role,
            is_email_verified=True,
            password_login_enabled=True,
        )
        session.add(user)
        session.commit()


def perform_login(client: TestClient, email: str):
    return client.post(
        "/login",
        data={"email": email, "password": TEST_PASSWORD},
        allow_redirects=False,
    )


def test_creator_login_redirects_to_creator_dashboard():
    client = TestClient(app)
    seed_user("creator@example.com", UserRole.CREATOR)

    response = perform_login(client, "creator@example.com")

    assert response.status_code == 303
    assert response.headers["location"] == "/dashboard"


def test_manager_login_redirects_to_manager_dashboard():
    client = TestClient(app)
    seed_user("manager@example.com", UserRole.MANAGER)

    response = perform_login(client, "manager@example.com")

    assert response.status_code == 303
    assert response.headers["location"] == "/manager/dashboard"


def test_super_admin_login_redirects_to_super_admin_console():
    client = TestClient(app)
    seed_user("super@example.com", UserRole.SUPER_ADMIN)

    response = perform_login(client, "super@example.com")

    settings = get_settings()
    assert response.status_code == 303
    assert response.headers["location"] == f"/super-admin?admin_token={settings.super_admin_access_token}"
