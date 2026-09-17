from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ForbiddenBehaviour(BaseModel):
    trace: list[str] = Field(default_factory=list)
    reason: str = ""
    requirement: str = ""


class Transition(BaseModel):
    source: str
    event: str
    guard: str = ""
    action: str = ""
    target: str
    requirement: str = ""


class FSMOutput(BaseModel):
    states: list[str]
    initial_state: str
    events: list[str]
    transitions: list[Transition]
    forbidden_behaviours: list[ForbiddenBehaviour] = Field(default_factory=list)


def fsm_json_schema() -> dict[str, Any]:
    return FSMOutput.model_json_schema()
