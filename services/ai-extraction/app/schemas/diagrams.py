"""Shared request and response contracts for deterministic diagram generation."""
from typing import Literal

from pydantic import BaseModel, Field


DiagramType = Literal["dfd", "class", "sequence", "activity", "component", "state"]
ItemCategory = Literal["actor", "entity", "process", "data_flow", "data_store", "interaction", "relationship"]


class DiagramItem(BaseModel):
    id: str
    category: ItemCategory
    name: str
    description: str | None = None
    source_refs: list[str] = Field(default_factory=list)
    source_id: str | None = None
    target_id: str | None = None
    relation_type: str | None = None


class DiagramGenerationRequest(BaseModel):
    diagram_type: DiagramType
    system_name: str
    items: list[DiagramItem] = Field(default_factory=list)


class DiagramGenerationResult(BaseModel):
    plantuml_source: str
    svg: str
    render_duration_seconds: float
