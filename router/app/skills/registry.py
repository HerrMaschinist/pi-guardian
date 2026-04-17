from __future__ import annotations

from collections.abc import Iterable

from app.skills.base import BaseSkill


class SkillRegistry:
    def __init__(self) -> None:
        self._skills: dict[str, BaseSkill] = {}

    def register(self, skill: BaseSkill) -> None:
        name = skill.name.strip()
        if not name:
            raise ValueError("Skill-Name darf nicht leer sein")
        if name in self._skills:
            raise ValueError(f"Skill bereits registriert: {name}")
        self._skills[name] = skill

    def get(self, skill_name: str) -> BaseSkill | None:
        return self._skills.get(skill_name)

    def list_skills(self) -> list[BaseSkill]:
        return [self._skills[name] for name in sorted(self._skills)]

    def names(self) -> list[str]:
        return sorted(self._skills)

    def ensure_allowed(self, allowed_skills: Iterable[str]) -> list[str]:
        normalized: list[str] = []
        for name in allowed_skills:
            stripped = name.strip()
            if not stripped:
                raise ValueError("allowed_skills enthält leere Einträge")
            if stripped not in self._skills:
                raise ValueError(f"Unbekannter Skill: {stripped}")
            if stripped not in normalized:
                normalized.append(stripped)
        return normalized


registry = SkillRegistry()


def register_skill(skill: BaseSkill) -> None:
    registry.register(skill)


def get_skill(skill_name: str) -> BaseSkill | None:
    return registry.get(skill_name)


def list_skills() -> list[BaseSkill]:
    return registry.list_skills()


def list_skill_names() -> list[str]:
    return registry.names()


from app.skills import standard as _standard_skills  # noqa: E402,F401
