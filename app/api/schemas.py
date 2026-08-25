from __future__ import annotations

from pydantic import BaseModel


class JobCreateTask(BaseModel):
    operation: str = "convert"
    input: str
    outputFormat: str
    options: dict | None = None


class JobCreateInput(BaseModel):
    tasks: list[JobCreateTask]
