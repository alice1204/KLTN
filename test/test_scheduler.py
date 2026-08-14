from services.academic_rules import (
    get_candidate_courses,
)

from services.scheduler import (
    parse_time,
    times_conflict,
    classes_conflict,
    create_schedule,
)

def test_parse_time():

    result = parse_time(
        "T2(4-5)"
    )

    assert result == (2, 4, 5)

#Test trung lich
def test_same_day_overlapping_times_conflict():

    assert times_conflict(
        "T2(4-5)",
        "T2(5-7)",
    ) is True

def test_same_day_non_overlapping_times():

    assert times_conflict(
        "T2(4-5)",
        "T2(6-8)",
    ) is False

def test_different_days_do_not_conflict():

    assert times_conflict(
        "T2(4-5)",
        "T3(4-5)",
    ) is False

#Test lop co nhieu buoi
def test_classes_with_one_overlapping_session_conflict():

    class_a = {
        "times": [
            "T2(1-3)",
            "T5(1-3)",
        ]
    }

    class_b = {
        "times": [
            "T5(2-4)",
        ]
    }

    assert classes_conflict(
        class_a,
        class_b,
    ) is True

#Test kha nang tao lich
def test_scheduler_can_create_schedule():

    candidates = get_candidate_courses(
        "671234"
    )

    result = create_schedule(
        candidates=candidates,
        target_credits=18,
    )

    assert result["success"] is True
    assert len(result["schedule"]) > 0

#Test tong tin chi
def test_schedule_credit_limit():

    candidates = get_candidate_courses(
        "671234"
    )

    result = create_schedule(
        candidates=candidates,
        target_credits=18,
    )

    total_credits = result[
        "total_credits"
    ]

    assert 15 <= total_credits <= 25

def test_schedule_reaches_target_18():

    candidates = get_candidate_courses(
        "671234"
    )

    result = create_schedule(
        candidates=candidates,
        target_credits=18,
    )

    assert result["total_credits"] == 18

#Test xung dot
def test_generated_schedule_has_no_conflicts():

    candidates = get_candidate_courses(
        "671234"
    )

    result = create_schedule(
        candidates=candidates,
        target_credits=18,
    )

    schedule = result["schedule"]

    for i in range(len(schedule)):

        for j in range(
            i + 1,
            len(schedule)
        ):

            class_a = schedule[i]
            class_b = schedule[j]

            assert not classes_conflict(
                class_a,
                class_b,
            )

#Test mon trung
def test_no_duplicate_courses():

    candidates = get_candidate_courses(
        "671234"
    )

    result = create_schedule(
        candidates=candidates,
        target_credits=18,
    )

    codes = [
        item["course_code"]
        for item in result["schedule"]
    ]

    assert len(codes) == len(set(codes))

#Test mon hoc lai