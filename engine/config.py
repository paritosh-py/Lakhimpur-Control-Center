from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field

ROOT = Path(__file__).resolve().parents[1]


class BasecampConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    plus_code: str = Field(min_length=1)
    address: str = Field(min_length=1)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    graph_node_id: str = Field(min_length=1)


class DistrictConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    district: str = Field(min_length=1)
    state: str = Field(min_length=1)
    country: str = Field(min_length=1)
    hazard: Literal["flood"]
    display_timezone: Literal["Asia/Kolkata"]
    target_road_segments: int = Field(ge=300, le=1000)
    target_settlements: int = Field(ge=15, le=40)
    target_shelters: int = Field(ge=5, le=10)
    basecamp: BasecampConfig | None = None


def load_district(path: Path = ROOT / "config/district.yaml") -> DistrictConfig:
    with path.open(encoding="utf-8") as stream:
        return DistrictConfig.model_validate(yaml.safe_load(stream))

