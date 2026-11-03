from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from ponto_fora_api.bootstrap import (
    BOOTSTRAP_KEY,
    CONFIRMATION_PHRASE,
    BootstrapAlreadyCompleted,
    BootstrapError,
    bootstrap_first_admin,
    require_postgresql,
)
from ponto_fora_api.db import Base
from ponto_fora_api.models import (
    AuthorizationEvent,
    ExternalIdentity,
    Permission,
    Role,
    RolePermission,
    SystemBootstrap,
    User,
    UserRole,
)


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as session:
        yield session
    engine.dispose()


def seed_platform_admin_role(db: Session) -> Role:
    role = Role(
        key="PLATFORM_ADMIN",
        description="Gestão técnica da plataforma.",
        is_active=True,
    )
    db.add(role)
    db.flush()
    for key in ("identity.manage", "roles.manage"):
        permission = Permission(key=key, description=key, is_active=True)
        db.add(permission)
        db.flush()
        db.add(RolePermission(role_id=role.id, permission_id=permission.id))
    db.commit()
    return role


def run_bootstrap(db: Session, **overrides):
    values = {
        "issuer": "https://identity.example.test/",
        "expected_issuer": "https://identity.example.test/",
        "subject": "oidc-subject-001",
        "display_name": "Administrador inicial",
        "email": "admin@example.test",
        "reason": "Bootstrap inicial aprovado pelo responsável da plataforma.",
        "confirmation": CONFIRMATION_PHRASE,
    }
    values.update(overrides)
    return bootstrap_first_admin(db, **values)


def test_bootstrap_creates_user_identity_role_marker_and_audit_atomically(db) -> None:
    seed_platform_admin_role(db)

    user = run_bootstrap(db)

    assert user.status == "ACTIVE"
    assert user.email == "admin@example.test"
    identity = db.scalar(select(ExternalIdentity).where(
        ExternalIdentity.user_id == user.id
    ))
    assert identity is not None
    assert identity.issuer == "https://identity.example.test/"
    assert identity.subject == "oidc-subject-001"

    assignment = db.scalar(select(UserRole).where(UserRole.user_id == user.id))
    assert assignment is not None
    assert assignment.status == "ACTIVE"
    assert assignment.scope_type is None
    role = db.get(Role, assignment.role_id)
    assert role is not None and role.key == "PLATFORM_ADMIN"

    marker = db.get(SystemBootstrap, BOOTSTRAP_KEY)
    assert marker is not None and marker.user_id == user.id
    event = db.scalar(select(AuthorizationEvent).where(
        AuthorizationEvent.event_type == "BOOTSTRAP_COMPLETED"
    ))
    assert event is not None
    assert event.actor_id == "bootstrap:cli"
    assert event.role_key == "PLATFORM_ADMIN"


def test_bootstrap_can_only_run_once(db) -> None:
    seed_platform_admin_role(db)
    first_user = run_bootstrap(db)

    with pytest.raises(BootstrapAlreadyCompleted):
        run_bootstrap(db, subject="second-subject")

    assert db.scalar(select(User).where(User.id == first_user.id)) is not None
    assert len(db.scalars(select(User)).all()) == 1
    assert len(db.scalars(select(AuthorizationEvent)).all()) == 1


def test_bootstrap_requires_exact_confirmation(db) -> None:
    seed_platform_admin_role(db)

    with pytest.raises(ValueError, match="Confirmação explícita"):
        run_bootstrap(db, confirmation="yes")

    assert db.scalar(select(User)) is None
    assert db.get(SystemBootstrap, BOOTSTRAP_KEY) is None


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("issuer", "http://identity.example.test/"),
        ("issuer", "https://user:pass@identity.example.test/"),
        ("issuer", "https://identity.example.test/?next=unsafe"),
        ("issuer", "https://identity.example.test/#fragment"),
        ("expected_issuer", "https://other.example.test/"),
        ("subject", ""),
        ("subject", "x" * 513),
        ("display_name", ""),
        ("display_name", "x" * 241),
    ],
)
def test_bootstrap_rejects_invalid_identity_input(db, field: str, value: str) -> None:
    seed_platform_admin_role(db)

    with pytest.raises(ValueError):
        run_bootstrap(db, **{field: value})

    assert db.scalar(select(User)) is None


def test_bootstrap_refuses_if_platform_admin_assignment_already_exists(db) -> None:
    role = seed_platform_admin_role(db)
    existing_user = User(
        id=uuid4(),
        display_name="Admin legado",
        status="ACTIVE",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db.add(existing_user)
    db.flush()
    db.add(UserRole(
        user_id=existing_user.id,
        role_id=role.id,
        status="REVOKED",
        valid_from=datetime.now(UTC),
        granted_by="legacy",
        granted_at=datetime.now(UTC),
    ))
    db.commit()

    with pytest.raises(BootstrapAlreadyCompleted):
        run_bootstrap(db)

    assert len(db.scalars(select(User)).all()) == 1
    assert db.get(SystemBootstrap, BOOTSTRAP_KEY) is None


def test_bootstrap_requires_expected_technical_permissions(db) -> None:
    role = Role(
        key="PLATFORM_ADMIN",
        description="Admin sem permissões completas.",
        is_active=True,
    )
    db.add(role)
    permission = Permission(
        key="roles.manage",
        description="Gestão de papéis.",
        is_active=True,
    )
    db.add(permission)
    db.flush()
    db.add(RolePermission(role_id=role.id, permission_id=permission.id))
    db.commit()

    with pytest.raises(BootstrapError, match="permissões técnicas mínimas"):
        run_bootstrap(db)

    assert db.scalar(select(User)) is None


def test_cli_bootstrap_guard_rejects_sqlite(db) -> None:
    with pytest.raises(BootstrapError, match="exige PostgreSQL"):
        require_postgresql(db)
