from fastapi import FastAPI, HTTPException

from models.schemas import ScheduleRequest

from services.academic_rules import (
    get_candidate_courses,
)

from services.scheduler import (
    create_schedule,
)


app = FastAPI(
    title="Student Scheduler API",
    version="1.0.0",
)


@app.get("/")
def root():

    return {
        "message":
            "Student Scheduler API is running"
    }


@app.post("/schedule")
def generate_schedule(
    request: ScheduleRequest
):

    try:

        candidates = get_candidate_courses(
            student_id=request.student_id,
            allow_early=request.allow_early,
        )

    except ValueError as error:

        raise HTTPException(
            status_code=404,
            detail=str(error),
        )

    result = create_schedule(
        candidates=candidates,
        target_credits=request.target_credits,
    )

    return result

from models.schemas import (
    ScheduleRequest,
    ExplainScheduleRequest,
)

from services.ai_service import (
    explain_schedule,
)

@app.post("/schedule/explain")
def explain_generated_schedule(
    request: ExplainScheduleRequest
):

    explanation = explain_schedule(
        request.schedule_result
    )

    return {
        "explanation": explanation
    }