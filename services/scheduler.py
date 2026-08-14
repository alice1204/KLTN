import re

# Ham hieu thoi gian
def parse_time(time_text: str):
    pattern = r"^T(\d+)\((\d+)-(\d+)\)$"

    match = re.match(
        pattern,
        time_text
    )

    if match is None:
        raise ValueError(
            f"Thời gian không hợp lệ: {time_text}"
        )

    day = int(match.group(1))
    start_period = int(match.group(2))
    end_period = int(match.group(3))

    return day, start_period, end_period

#Kiem tra buoi trung
def times_conflict(
    time_a: str,
    time_b: str
) -> bool:

    day_a, start_a, end_a = parse_time(time_a)
    day_b, start_b, end_b = parse_time(time_b)

    # Khác ngày thì chắc chắn không trùng
    if day_a != day_b:
        return False

    # Cùng ngày -> kiểm tra khoảng tiết giao nhau
    return (
        start_a <= end_b
        and start_b <= end_a
    )

#Mot lop co the co nhieu buoi
def classes_conflict(
    class_a: dict,
    class_b: dict
) -> bool:

    for time_a in class_a["times"]:
        for time_b in class_b["times"]:

            if times_conflict(
                time_a,
                time_b
            ):
                return True

    return False

#Kiem tra mot lop moi voi lich dang co
def can_add_class(
    schedule: list,
    new_item: dict
) -> bool:

    for existing_item in schedule:

        if classes_conflict(
            existing_item,
            new_item
        ):
            return False

    return True

#Backtracking de tim lich hoc
def create_schedule(
    candidates: list,
    target_credits: int = 18,
    min_credits: int = 15,
    max_credits: int = 25,
):

    best_schedule = None
    best_score = None

    def evaluate(schedule, total_credits):

        if not (
            min_credits
            <= total_credits
            <= max_credits
        ):
            return None

        retake_count = sum(
            1
            for item in schedule
            if item["reason"] == "retake"
        )

        early_count = sum(
            1
            for item in schedule
            if item["reason"] == "early"
        )

        normal_count = sum(
            1
            for item in schedule
            if item["reason"] == "normal"
        )

        school_days = set()

        for item in schedule:
            for time_text in item["times"]:

                day, _, _ = parse_time(
                    time_text
                )

                school_days.add(day)

        # Tuple nhỏ hơn = lịch tốt hơn
        return (
            -retake_count,
            abs(target_credits - total_credits),
            early_count,
            len(school_days),
            -normal_count,
        )

    def backtrack(
        index: int,
        current_schedule: list,
        current_credits: int,
    ):

        nonlocal best_schedule
        nonlocal best_score

        # Vượt giới hạn tín chỉ -> dừng nhánh
        if current_credits > max_credits:
            return

        # Đánh giá lịch hiện tại
        score = evaluate(
            current_schedule,
            current_credits
        )

        if score is not None:

            if (
                best_score is None
                or score < best_score
            ):
                best_score = score
                best_schedule = (
                    current_schedule.copy()
                )

        # Đã xét hết môn
        if index >= len(candidates):
            return

        course = candidates[index]

        # PHƯƠNG ÁN 1:
        # thử chọn môn này
        for class_info in course["classes"]:

            item = {
                "course_code": course["code"],
                "course_name": course["name"],
                "credits": course["credits"],
                "reason": course["reason"],
                "class_id": class_info["id"],
                "times": class_info["times"],
            }

            if can_add_class(
                current_schedule,
                item
            ):

                current_schedule.append(item)

                backtrack(
                    index + 1,
                    current_schedule,
                    current_credits
                    + course["credits"],
                )

                current_schedule.pop()

        # PHƯƠNG ÁN 2:
        # không chọn môn này
        backtrack(
            index + 1,
            current_schedule,
            current_credits,
        )

    backtrack(
        index=0,
        current_schedule=[],
        current_credits=0,
    )

    if best_schedule is None:

        return {
            "success": False,
            "schedule": [],
            "total_credits": 0,
            "message":
                "Không tìm được lịch đáp ứng điều kiện.",
        }

    total_credits = sum(
        item["credits"]
        for item in best_schedule
    )

    return {
        "success": True,
        "schedule": best_schedule,
        "total_credits": total_credits,
    }