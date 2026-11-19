"""Tier maps: which privilege tier each benchmark role belongs to."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, ValidationError, field_validator

from privilege_drift.data.errors import DataError
from privilege_drift.schema import Tier

TOOLPRIVBENCH_TIERS_PATH = Path("configs/tiers/toolprivbench_tiers.yaml")


class RoleTierMap(BaseModel):
    """A benchmark's role names mapped to tiers, as written in ``configs/tiers/*.yaml``.

    The map must be one-to-one: converting a scenario back to its raw form relies on every tier
    naming exactly one role.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    source: str
    role_to_tier: Mapping[str, Tier]

    @field_validator("role_to_tier", mode="before")
    @classmethod
    def _parse_tier_names(cls, value: Any) -> Any:
        if not isinstance(value, Mapping):
            return value
        parsed: dict[str, Tier] = {}
        for role, name in value.items():
            try:
                parsed[role] = Tier[str(name).upper()]
            except KeyError:
                valid = ", ".join(t.name.lower() for t in Tier)
                raise ValueError(f"unknown tier {name!r}; valid tiers: {valid}") from None
        return parsed

    @field_validator("role_to_tier")
    @classmethod
    def _one_to_one(cls, value: Mapping[str, Tier]) -> Mapping[str, Tier]:
        if len(set(value.values())) != len(value):
            raise ValueError("two roles map to the same tier; the map must be one-to-one")
        return value

    def tier_to_role(self) -> dict[Tier, str]:
        return {tier: role for role, tier in self.role_to_tier.items()}


def load_role_tier_map(path: Path | str = TOOLPRIVBENCH_TIERS_PATH) -> RoleTierMap:
    """Parse and validate a tier-map YAML file."""
    try:
        data = yaml.safe_load(Path(path).read_text())
        return RoleTierMap.model_validate(data)
    except (OSError, yaml.YAMLError, ValidationError) as exc:
        raise DataError(f"cannot load tier map {path}: {exc}") from exc
