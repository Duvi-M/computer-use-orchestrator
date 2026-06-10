from pathlib import Path


def test_alembic_initial_migration_exists():
    migration = Path("migrations/versions/0001_initial_saas_schema.py")

    assert Path("alembic.ini").exists()
    assert Path("migrations/env.py").exists()
    assert migration.exists()

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
