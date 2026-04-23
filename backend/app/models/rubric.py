from pydantic import BaseModel, Field


class RubricCriterion(BaseModel):
    name: str = Field(min_length=1)
    max_points: float = Field(gt=0)
    description: str = Field(min_length=1)


class RubricCreateRequest(BaseModel):
    criteria: list[RubricCriterion] = Field(min_length=1)


class RubricRecord(RubricCreateRequest):
    rubric_id: str
