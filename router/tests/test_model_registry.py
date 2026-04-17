from sqlmodel import Session, SQLModel, create_engine, select

from app.models.model_registry import ModelCreate, ModelRecord, ModelUpdate
from app.router.model_registry import (
    create_registered_model,
    delete_registered_model,
    sync_model_registry,
    update_registered_model,
)


def _session():
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def test_sync_model_registry_seeds_default_and_large_models(monkeypatch):
    monkeypatch.setattr("app.router.model_registry.settings.DEFAULT_MODEL", "fast-a")
    monkeypatch.setattr("app.router.model_registry.settings.LARGE_MODEL", "deep-b")

    with _session() as session:
        sync_model_registry(session)
        records = session.exec(select(ModelRecord).order_by(ModelRecord.role)).all()

    assert [record.name for record in records] == ["fast-a", "deep-b"]
    assert [record.role for record in records] == ["default", "large"]


def test_registered_model_crud_roundtrip():
    with _session() as session:
        created = create_registered_model(
            session,
            ModelCreate(name="qwen3-mini", description="Testmodell", enabled=True),
        )
        assert created.name == "qwen3-mini"
        assert created.role == "registered"

        updated = update_registered_model(
            session,
            created.id,
            ModelUpdate(description="Aktualisierte Beschreibung", enabled=False),
        )
        assert updated.description == "Aktualisierte Beschreibung"
        assert updated.enabled is False

        delete_registered_model(session, created.id)
        assert session.get(ModelRecord, created.id) is None


def test_sync_model_registry_promotes_registered_model_to_large_without_renaming(monkeypatch):
    monkeypatch.setattr("app.router.model_registry.settings.DEFAULT_MODEL", "qwen2.5-coder:1.5b")
    monkeypatch.setattr("app.router.model_registry.settings.LARGE_MODEL", "gemma3:4b")

    with _session() as session:
        session.add(
            ModelRecord(
                name="qwen2.5-coder:1.5b",
                description="fast",
                role="default",
                enabled=True,
            )
        )
        session.add(
            ModelRecord(
                name="qwen2.5-coder:3b",
                description="deep",
                role="large",
                enabled=True,
            )
        )
        session.add(
            ModelRecord(
                name="gemma3:4b",
                description="registered",
                role="registered",
                enabled=True,
            )
        )
        session.commit()

        sync_model_registry(session)
        records = session.exec(select(ModelRecord).order_by(ModelRecord.id)).all()

    assert [(record.name, record.role) for record in records] == [
        ("qwen2.5-coder:1.5b", "default"),
        ("qwen2.5-coder:3b", "registered"),
        ("gemma3:4b", "large"),
    ]


def test_sync_model_registry_swaps_core_roles_without_duplicate_names(monkeypatch):
    monkeypatch.setattr("app.router.model_registry.settings.DEFAULT_MODEL", "gemma3:4b")
    monkeypatch.setattr("app.router.model_registry.settings.LARGE_MODEL", "qwen2.5-coder:3b")

    with _session() as session:
        session.add(
            ModelRecord(
                name="qwen2.5-coder:1.5b",
                description="fast",
                role="default",
                enabled=True,
            )
        )
        session.add(
            ModelRecord(
                name="qwen2.5-coder:3b",
                description="deep",
                role="large",
                enabled=True,
            )
        )
        session.add(
            ModelRecord(
                name="gemma3:4b",
                description="registered",
                role="registered",
                enabled=True,
            )
        )
        session.commit()

        sync_model_registry(session)
        records = session.exec(select(ModelRecord).order_by(ModelRecord.name)).all()

    assert [(record.name, record.role) for record in records] == [
        ("gemma3:4b", "default"),
        ("qwen2.5-coder:1.5b", "registered"),
        ("qwen2.5-coder:3b", "large"),
    ]
