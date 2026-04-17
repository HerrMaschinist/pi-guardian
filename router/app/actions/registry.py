from __future__ import annotations

from collections.abc import Iterable

from app.actions.base import BaseAction


class ActionRegistry:
    def __init__(self) -> None:
        self._actions: dict[str, BaseAction] = {}

    def register(self, action: BaseAction) -> None:
        name = action.name.strip()
        if not name:
            raise ValueError("Action-Name darf nicht leer sein")
        if name in self._actions:
            raise ValueError(f"Action bereits registriert: {name}")
        self._actions[name] = action

    def get(self, action_name: str) -> BaseAction | None:
        return self._actions.get(action_name)

    def list_actions(self) -> list[BaseAction]:
        return [self._actions[name] for name in sorted(self._actions)]

    def names(self) -> list[str]:
        return sorted(self._actions)

    def ensure_allowed(self, allowed_actions: Iterable[str]) -> list[str]:
        normalized: list[str] = []
        for name in allowed_actions:
            stripped = name.strip()
            if not stripped:
                raise ValueError("allowed_actions enthält leere Einträge")
            if stripped not in self._actions:
                raise ValueError(f"Unbekannte Action: {stripped}")
            if stripped not in normalized:
                normalized.append(stripped)
        return normalized


registry = ActionRegistry()


def register_action(action: BaseAction) -> None:
    registry.register(action)


def get_action(action_name: str) -> BaseAction | None:
    return registry.get(action_name)


def list_actions() -> list[BaseAction]:
    return registry.list_actions()


def list_action_names() -> list[str]:
    return registry.names()


from app.actions import standard as _standard_actions  # noqa: E402,F401
