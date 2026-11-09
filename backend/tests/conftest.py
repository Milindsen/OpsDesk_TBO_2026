import uuid
from collections.abc import Generator
from datetime import datetime, time, timezone
from typing import Dict

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models.agency import Agency
from app.models.user import User
from app.services.auth_service import create_access_token, get_password_hash

# In-memory SQLite with StaticPool for test isolation
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
)


@pytest.fixture(scope="session", autouse=True)
def setup_database() -> Generator[None, None, None]:
    Base.metadata.create_all(bind=test_engine, checkfirst=True)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def test_client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
def seed_agencies(db_session: Session) -> Dict[str, Agency]:
    agencies = {
        "horizons": Agency(id=uuid.uuid4(), name="Horizons Travel", region="IN-West"),
        "sunrise": Agency(id=uuid.uuid4(), name="Sunrise Tours", region="IN-East"),
        "peak": Agency(id=uuid.uuid4(), name="Peak Adventures", region="ME"),
    }
    for ag in agencies.values():
        db_session.add(ag)
    db_session.flush()
    return agencies


@pytest.fixture
def seed_users(db_session: Session, seed_agencies: Dict[str, Agency]) -> Dict[str, User]:
    hashed_pw = get_password_hash("Demo@1234")
    now = datetime.now(timezone.utc)

    users = {
        "agent1": User(
            id=uuid.uuid4(),
            email="agent1@tbo.com",
            full_name="Agent One",
            hashed_password=hashed_pw,
            role="agent",
            region="IN-West",
            shift_start=time(9, 0),
            shift_end=time(18, 0),
            availability=True,
            current_load=0,
            created_at=now,
        ),
        "agent2": User(
            id=uuid.uuid4(),
            email="agent2@tbo.com",
            full_name="Agent Two",
            hashed_password=hashed_pw,
            role="agent",
            region="IN-East",
            shift_start=time(9, 0),
            shift_end=time(18, 0),
            availability=True,
            current_load=0,
            created_at=now,
        ),
        "em": User(
            id=uuid.uuid4(),
            email="em@tbo.com",
            full_name="Escalation Manager",
            hashed_password=hashed_pw,
            role="escalation_manager",
            region="IN-West",
            availability=True,
            current_load=0,
            created_at=now,
        ),
        "lead": User(
            id=uuid.uuid4(),
            email="lead@tbo.com",
            full_name="Team Lead",
            hashed_password=hashed_pw,
            role="lead",
            availability=True,
            current_load=0,
            created_at=now,
        ),
        "requester_a": User(
            id=uuid.uuid4(),
            email="agency_a@horizons.com",
            full_name="Requester A",
            hashed_password=hashed_pw,
            role="requester",
            agency_id=seed_agencies["horizons"].id,
            region="IN-West",
            availability=True,
            current_load=0,
            created_at=now,
        ),
        "requester_b": User(
            id=uuid.uuid4(),
            email="agency_b@sunrise.com",
            full_name="Requester B",
            hashed_password=hashed_pw,
            role="requester",
            agency_id=seed_agencies["sunrise"].id,
            region="IN-East",
            availability=True,
            current_load=0,
            created_at=now,
        ),
    }

    for u in users.values():
        db_session.add(u)
    db_session.flush()
    return users


def get_token_for(user: User) -> str:
    return create_access_token(
        data={
            "sub": user.email,
            "user_id": str(user.id),
            "role": user.role,
            "agency_id": str(user.agency_id) if user.agency_id else None,
        }
    )


@pytest.fixture
def auth_headers(seed_users: Dict[str, User]) -> Dict[str, Dict[str, str]]:
    return {
        key: {"Authorization": f"Bearer {get_token_for(usr)}"}
        for key, usr in seed_users.items()
    }
