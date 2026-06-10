from pathlib import Path


def test_alembic_initial_migration_exists():
    migration = Path("migrations/versions/0001_initial_saas_schema.py")
    retention_migration = Path("migrations/versions/0002_retention_artifacts.py")

    assert Path("alembic.ini").exists()
    assert Path("migrations/env.py").exists()
    assert migration.exists()
    assert retention_migration.exists()

    text = migration.read_text()
    for table in (
        "users",
        "organizations",
        "organization_memberships",
        "sessions",
        "messages",
        "events",
    ):
        assert f'"{table}"' in text


def test_alembic_initial_migration_has_operational_indexes():
    text = Path("migrations/versions/0001_initial_saas_schema.py").read_text()

    for index_name in (
        "ix_sessions_user_id",
        "ix_sessions_organization_id",
        "ix_sessions_status",
        "ix_sessions_created_at",
        "ix_messages_session_id",
        "ix_events_session_id",
        "ix_events_event",
        "ix_events_created_at",
    ):
        assert index_name in text


def test_alembic_retention_migration_has_artifacts_and_deleted_at():
    text = Path("migrations/versions/0002_retention_artifacts.py").read_text()

    for expected in (
        "deleted_at",
        "artifacts",
        "artifact_id",
        "artifact_type",
        "storage_path",
        "expires_at",
        "ix_artifacts_session_id",
        "ix_artifacts_expires_at",
    ):
        assert expected in text
