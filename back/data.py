import json
import re
import functools
from pathlib import Path

DATA_PATH = Path(__file__).parent / "timetable_2026_1.json"

EXCLUDED_TOPS = {
    "교양",
    "매치업 집중이수제",
    "연계전공",
    "융합교과목",
    "창업 교과목",
    "다학년 다학기 프로젝트",
    "군사학",
}

_DAY_CHARS = "월화수목금토일"
_TOKEN_RE = re.compile(rf"([{_DAY_CHARS}])((?:\d+(?:,\d+)*)?)")

def _parse_grade(course_code: str):
    parts = course_code.split("-")
    if len(parts) >= 2 and parts[1].isdigit():
        return int(parts[1])
    return None

def _parse_family(course_code: str):
    parts = course_code.split("-")
    if len(parts) >= 3:
        return parts[2]
    return course_code

def _parse_time_slots(class_time):
    if not class_time:
        return None
    slots = []
    for day, periods in _TOKEN_RE.findall(class_time):
        if not periods:
            return None
        for p in periods.split(","):
            slots.append((day, int(p)))
    if not slots:
        return None
    return frozenset(slots)

def _is_remote(remarks):
    return bool(remarks) and "원격수업" in remarks

class TimetableStore:
    def __init__(self, raw: dict):
        self.raw = raw
        self.dept_to_college: dict[str, str] = {}
        self.departments: list[str] = []
        self.major_pool: dict[tuple[str, int], dict[int, list[dict]]] = {}
        self.gen_ed_pool: dict[int, dict[int, list[dict]]] = {}

        self._build()

    def _tag_course(self, course: dict, category: str) -> dict:
        c = dict(course)
        c["grade"] = _parse_grade(c["course_code"])
        c["category"] = category
        c["_family"] = _parse_family(c["course_code"])
        c["_is_remote"] = _is_remote(c.get("remarks"))
        c["_slots"] = _parse_time_slots(c.get("class_time"))
        return c

    def _build(self):
        major_by_college: dict[str, dict[str, list[dict]]] = {}
        common_by_college: dict[str, list[dict]] = {}

        for top, subs in self.raw.items():
            if top in EXCLUDED_TOPS:
                continue
            major_by_college.setdefault(top, {})
            for sub, block in subs.items():
                tagged = [self._tag_course(c, "전공" if sub != "공통" else "공통") for c in block["courses"]]
                if sub == "공통":
                    common_by_college[top] = tagged
                else:
                    self.dept_to_college[sub] = top
                    major_by_college[top][sub] = tagged

        self.departments = sorted(self.dept_to_college.keys())

        for dept, college in self.dept_to_college.items():
            dept_courses = major_by_college.get(college, {}).get(dept, [])
            common_courses = common_by_college.get(college, [])
            pool = dept_courses + common_courses
            for grade in range(1, 6):
                by_credit: dict[int, list[dict]] = {}
                for c in pool:
                    if c["grade"] == grade:
                        by_credit.setdefault(c["credits"], []).append(c)
                self.major_pool[(dept, grade)] = by_credit

        gen_ed_flat = []
        for sub, block in self.raw.get("교양", {}).items():
            gen_ed_flat.extend(self._tag_course(c, "교양") for c in block["courses"])
        for grade in range(1, 6):
            by_credit: dict[int, list[dict]] = {}
            for c in gen_ed_flat:
                if c["grade"] == grade:
                    by_credit.setdefault(c["credits"], []).append(c)
            self.gen_ed_pool[grade] = by_credit

    def get_major_pool(self, department: str, grade: int) -> dict[int, list[dict]]:
        return self.major_pool.get((department, grade), {})

    def get_gen_ed_pool(self, grade: int) -> dict[int, list[dict]]:
        return self.gen_ed_pool.get(grade, {})

@functools.lru_cache(maxsize=1)
def get_store() -> TimetableStore:
    with open(DATA_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    return TimetableStore(raw)

@functools.lru_cache(maxsize=1)
def get_departments() -> list[str]:
    return get_store().departments

@functools.lru_cache(maxsize=256)
def get_college(department: str):
    return get_store().dept_to_college.get(department)
