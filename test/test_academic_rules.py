from services.academic_rules import (
    get_student,
    prerequisites_satisfied,
    get_candidate_courses,
)


def test_get_existing_student():

    student = get_student("671234")

    assert student is not None
    assert student["current_semester"] == 4


def test_get_nonexistent_student():

    student = get_student("999999")

    assert student is None


def test_prerequisites_satisfied():

    course = {
        "prerequisites": [
            "TH01001",
            "TH01002",
        ]
    }

    completed = {
        "TH01001",
        "TH01002",
    }

    result = prerequisites_satisfied(
        course,
        completed,
    )

    assert result is True


def test_prerequisites_not_satisfied():

    course = {
        "prerequisites": [
            "TH01001",
            "TH01002",
        ]
    }

    completed = {
        "TH01001",
    }

    result = prerequisites_satisfied(
        course,
        completed,
    )

    assert result is False


def test_completed_courses_are_not_candidates():

    student = get_student("671234")

    completed = set(
        student.get("completed", [])
    )

    candidates = get_candidate_courses(
        "671234"
    )

    candidate_codes = {
        course["code"]
        for course in candidates
    }

    assert completed.isdisjoint(
        candidate_codes
    )


def test_failed_course_is_retake():

    candidates = get_candidate_courses(
        "671234"
    )

    course = next(
        item
        for item in candidates
        if item["code"] == "TH01007"
    )

    assert course["reason"] == "retake"
    assert course["priority"] == 1


def test_early_course_when_allowed():

    candidates = get_candidate_courses(
        "671234",
        allow_early=True,
    )

    early_courses = [
        course
        for course in candidates
        if course["reason"] == "early"
    ]

    assert len(early_courses) > 0


def test_no_early_course_when_disabled():

    candidates = get_candidate_courses(
        "671234",
        allow_early=False,
    )

    early_courses = [
        course
        for course in candidates
        if course["reason"] == "early"
    ]

    assert len(early_courses) == 0