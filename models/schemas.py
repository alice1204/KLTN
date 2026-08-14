from pydantic import BaseModel, Field


class ScheduleRequest(BaseModel):

    student_id: str

    target_credits: int = Field(
        default=18,
        ge=15,
        le=25,
    )

    allow_early: bool = True

class ExplainScheduleRequest(BaseModel):
    schedule_result: dict