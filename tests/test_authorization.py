from datetime import timedelta

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from ponto_fora_api.auth import AuthenticatedPrincipal
from ponto_fora_api.authorization import (
    InactiveUser,
    PermissionDenied,
    UnknownIdentity,
    grant_role,
    link_external_identity,
    resolve_active_user,
    revoke_role,
    user_has_permission,
)
from ponto_fora_api.db import Base
from ponto_fora_api.models import (
    AuthorizationEvent,
    ExternalIdentity,
    Permission,
    Role,
    RolePermission,
    User,
    UserRole,
    utc_now,
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


def create_user(db: Session, status: str = "ACTIVE") -> User:
    user = User(status=status, created_at=utc_now(), updated_at=utc_now())
    db.add(user)
    db.flush()
    return user


def create_role(db: Session, key: str) -> Role:
    role = Role(key=key, description=key, is_active=True)
    db.add(role)
    db.flush()
    return role


def grant_permission_to_role(db: Session, role: Role, key: str) -> None:
    permission = db.scalar(select(Permission).where(Permission.key == key))
    if permission is None:
        permission = Permission(key=key, description=key, is_active=True)
        db.add(permission)
        db.flush()
    db.add(RolePermission(role_id=role.id, permission_id=permission.id))
    db.flush()


def make_admin(db: Session) -> User:
    admin = create_user(db)
    role = create_role(db, "PLATFORM_ADMIN")
    grant_permission_to_role(db, role, "identity.manage")
    grant_permission_to_role(db, role, "roles.manage")
    db.add(UserRole(
        user_id=admin.id,
        role_id=role.id,
        status="ACTIVE",
        valid_from=utc_now(),
        granted_by="bootstrap",
        granted_at=utc_now(),
    ))
    db.flush()
    return admin


def test_identity_resolution_uses_issuer_and_subject_not_email(db) -> None:
    user = create_user(db)
    db.add(ExternalIdentity(
        user_id=user.id,
        issuer="https://id.example.test/",
        subject="subject-123",
        created_at=utc_now(),
    ))
    db.commit()

    principal = AuthenticatedPrincipal(
        issuer="https://id.example.test/",
        subject="subject-123",
        email="different@example.test",
    )

    assert resolve_active_user(db, principal).id == user.id


def test_unknown_oidc_identity_is_not_auto_provisioned(db) -> None:
    principal = AuthenticatedPrincipal(
        issuer="https://id.example.test/",
        subject="unknown-subject",
    )

    with pytest.raises(UnknownIdentity):
        resolve_active_user(db, principal)

    assert db.scalar(select(User)) is None


def test_disabled_user_cannot_resolve(db) -> None:
    user = create_user(db, status="DISABLED")
    db.add(ExternalIdentity(
        user_id=user.id,
        issuer="https://id.example.test/",
        subject="disabled-subject",
        created_at=utc_now(),
    ))
    db.commit()

    with pytest.raises(InactiveUser):
        resolve_active_user(db, AuthenticatedPrincipal(
            issuer="https://id.example.test/",
            subject="disabled-subject",
        ))


def test_permission_requires_active_global_role_and_active_user(db) -> None:
    user = create_user(db)
    role = create_role(db, "EDITORIAL_DIRECTOR")
    grant_permission_to_role(db, role, "editorial.decide")
    db.add(UserRole(
        user_id=user.id,
        role_id=role.id,
        status="ACTIVE",
        valid_from=utc_now() - timedelta(minutes=1),
        granted_by="bootstrap",
        granted_at=utc_now(),
    ))
    db.commit()

    assert user_has_permission(db, user.id, "editorial.decide") is True
    assert user_has_permission(db, user.id, "roles.manage") is False


def test_expired_and_revoked_roles_do_not_grant_permissions(db) -> None:
    user = create_user(db)
    role = create_role(db, "EDITORIAL_DIRECTOR")
    grant_permission_to_role(db, role, "editorial.decide")
    db.add(UserRole(
        user_id=user.id,
        role_id=role.id,
        status="ACTIVE",
        valid_from=utc_now() - timedelta(days=2),
        valid_until=utc_now() - timedelta(days=1),
        granted_by="bootstrap",
        granted_at=utc_now() - timedelta(days=2),
    ))
    db.commit()

    assert user_has_permission(db, user.id, "editorial.decide") is False


def test_role_grant_requires_authorized_actor_and_is_audited(db) -> None:
    admin = make_admin(db)
    target = create_user(db)
    create_role(db, "WRITER")
    db.commit()

    assignment = grant_role(
        db,
        user_id=target.id,
        role_key="WRITER",
        actor_user_id=admin.id,
        reason="Integração de redator autorizado.",
    )

    assert assignment.status == "ACTIVE"
    event = db.scalar(select(AuthorizationEvent).where(
        AuthorizationEvent.event_type == "ROLE_GRANTED"
    ))
    assert event is not None
    assert event.actor_id == f"user:{admin.id}"


def test_role_grant_denies_actor_without_management_permission(db) -> None:
    actor = create_user(db)
    target = create_user(db)
    create_role(db, "WRITER")
    db.commit()

    with pytest.raises(PermissionDenied):
        grant_role(
            db,
            user_id=target.id,
            role_key="WRITER",
            actor_user_id=actor.id,
            reason="Tentativa sem privilégio.",
        )


def test_revoked_role_stops_granting_permission(db) -> None:
    admin = make_admin(db)
    target = create_user(db)
    writer = create_role(db, "WRITER")
    grant_permission_to_role(db, writer, "artifacts.write")
    db.commit()

    grant_role(
        db,
        user_id=target.id,
        role_key="WRITER",
        actor_user_id=admin.id,
        reason="Atribuição inicial.",
    )
    assert user_has_permission(db, target.id, "artifacts.write") is True

    revoke_role(
        db,
        user_id=target.id,
        role_key="WRITER",
        actor_user_id=admin.id,
        reason="Fim da colaboração.",
    )
    assert user_has_permission(db, target.id, "artifacts.write") is False


def test_identity_linking_requires_admin_and_is_audited(db) -> None:
    admin = make_admin(db)
    target = create_user(db)
    db.commit()

    identity = link_external_identity(
        db,
        user_id=target.id,
        issuer="https://id.example.test/",
        subject="new-subject",
        actor_user_id=admin.id,
        reason="Associação validada pelo administrador.",
    )

    assert identity.user_id == target.id
    assert db.scalar(select(AuthorizationEvent).where(
        AuthorizationEvent.event_type == "IDENTITY_LINKED"
    )) is not None


def test_identity_linking_rejects_duplicate_issuer_subject(db) -> None:
    admin = make_admin(db)
    first = create_user(db)
    second = create_user(db)
    db.add(ExternalIdentity(
        user_id=first.id,
        issuer="https://id.example.test/",
        subject="same-subject",
        created_at=utc_now(),
    ))
    db.commit()

    with pytest.raises(ValueError, match="já está associada"):
        link_external_identity(
            db,
            user_id=second.id,
            issuer="https://id.example.test/",
            subject="same-subject",
            actor_user_id=admin.id,
            reason="Tentativa de associação duplicada.",
        )
