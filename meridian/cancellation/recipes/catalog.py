from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass(frozen=True)
class Recipe:
    merchant: str
    aliases: tuple[str, ...]
    channel: str
    steps: tuple[str, ...]
    last_verified: date | None

    @property
    def executable(self) -> bool:
        return self.last_verified is not None and self.last_verified <= date.today() and bool(self.steps)


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()


def load_catalog(directory: str | Path) -> tuple[Recipe, ...]:
    root = Path(directory)
    recipes: list[Recipe] = []
    for path in sorted(root.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        verified = payload.get("last_verified")
        recipes.append(Recipe(
            merchant=payload["merchant"],
            aliases=tuple(payload.get("aliases", [])),
            channel=payload["channel"],
            steps=tuple(payload.get("steps", [])),
            last_verified=date.fromisoformat(verified) if verified else None,
        ))
    return tuple(recipes)


def match_recipe(merchant: str, catalog: tuple[Recipe, ...]) -> Recipe | None:
    normalized = _normalize(merchant)
    for recipe in catalog:
        if normalized in {_normalize(recipe.merchant), *(_normalize(alias) for alias in recipe.aliases)}:
            return recipe
    return None
