import random
from data import get_store

def _fill(pool_by_credit: dict, target_credits: int, prefer_remote: bool, prefer_required: bool,
          selected: list, used_families: set, occupied_slots: set, total: int) -> int:
    for credit in sorted(pool_by_credit.keys(), reverse=True):
        if total >= target_credits:
            break
        if credit <= 0 or total + credit > target_credits:
            continue

        candidates = [c for c in pool_by_credit[credit] if c["_family"] not in used_families]
        random.shuffle(candidates)
        if prefer_required and prefer_remote:
            required_remote = [c for c in candidates if c["course_type"] == "전필" and c["_is_remote"]]
            required_other = [c for c in candidates if c["course_type"] == "전필" and not c["_is_remote"]]
            other_remote = [c for c in candidates if c["course_type"] != "전필" and c["_is_remote"]]
            other_rest = [c for c in candidates if c["course_type"] != "전필" and not c["_is_remote"]]
            candidates = required_remote + required_other + other_remote + other_rest
        elif prefer_required:
            required = [c for c in candidates if c["course_type"] == "전필"]
            non_required = [c for c in candidates if c["course_type"] != "전필"]
            candidates = required + non_required
        elif prefer_remote:
            remote = [c for c in candidates if c["_is_remote"]]
            non_remote = [c for c in candidates if not c["_is_remote"]]
            candidates = remote + non_remote

        for c in candidates:
            if total >= target_credits:
                break
            if total + c["credits"] > target_credits:
                continue
            if c["_family"] in used_families:
                continue
            if c["_slots"] is not None and occupied_slots & c["_slots"]:
                continue

            selected.append(c)
            used_families.add(c["_family"])
            if c["_slots"] is not None:
                occupied_slots.update(c["_slots"])
            total += c["credits"]

    return total

def recommend(department: str, grade: int, target_credits: int, prefer_remote: bool, prefer_required: bool):
    store = get_store()

    selected: list[dict] = []
    used_families: set[str] = set()
    occupied_slots: set[tuple] = set()
    total = 0

    major_pool = store.get_major_pool(department, grade)
    total = _fill(major_pool, target_credits, prefer_remote, prefer_required, selected, used_families, occupied_slots, total)

    if total < target_credits:
        gen_ed_pool = store.get_gen_ed_pool(grade)
        total = _fill(gen_ed_pool, target_credits, prefer_remote, prefer_required, selected, used_families, occupied_slots, total)

    if total >= target_credits:
        message = f"목표 {target_credits}학점 중 {total}학점을 추천했습니다."
    else:
        message = (
            f"학과/단과대학 공통/교양 과목을 모두 확인했지만 {total}학점만 채웠습니다"
            f"(목표 {target_credits}학점). 학년/학과/학점 조건을 바꿔보세요."
        )

    courses_out = [
        {
            "course_code": c["course_code"],
            "course_name": c["course_name"],
            "section": c.get("section"),
            "course_type": c.get("course_type"),
            "credits": c["credits"],
            "hours": c.get("hours"),
            "professor": c.get("professor"),
            "class_time": c.get("class_time"),
            "remarks": c.get("remarks"),
            "category": c["category"],
        }
        for c in selected
    ]

    return courses_out, total, message
