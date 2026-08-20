from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


class ScheduleRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid"
    )

    target_credits: int = Field(
        default=18,
        ge=15,
        le=25,
    )

    allow_early: bool = True


class ExplainScheduleRequest(BaseModel):
    schedule_result: dict