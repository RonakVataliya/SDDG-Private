from typing import Literal

from pydantic import BaseModel, Field, field_validator

ItemCategory = Literal["actor", "entity", "process", "data_flow", "data_store", "interaction", "relationship"]
DiagramType = Literal["use_case", "class", "activity", "sequence", "dfd", "component", "state"]


class ConsentCreate(BaseModel):
    policy_version: str


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class ItemUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class InputCreate(BaseModel):
    text: str = Field(min_length=1)

    @field_validator("text")
    @classmethod
    def text_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Requirement text must not be blank.")
        return value


class SuggestionDecision(BaseModel):
    decision: Literal["approved", "rejected"]


class GenerationCreate(BaseModel):
    diagram_types: list[DiagramType] = Field(min_length=1)


class RevisionCreate(BaseModel):
    instruction: str = Field(min_length=1, max_length=500)
