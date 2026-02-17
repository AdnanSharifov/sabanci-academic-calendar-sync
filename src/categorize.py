# Made by canadaaww
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class Category:
    name: str
    emoji: str
    color_id: str
    reminder_minutes: int | None


# Google Calendar supports colorId strings "1".."11" (calendar colors differ from event colors, but event colorId uses these)
CATEGORIES: List[Category] = [
    Category(
        name="Admissions, Applications, and Program Entry",
        emoji="📝",
        color_id="9",
        reminder_minutes=24 * 60,  # 1 day
    ),
    Category(
        name="Registration, Enrollment, and Administrative Procedures",
        emoji="🧾",
        color_id="6",
        reminder_minutes=24 * 60,  # 1 day
    ),
    Category(
        name="Academic Term Activities (Teaching Cycle)",
        emoji="📚",
        color_id="2",
        reminder_minutes=None,
    ),
    Category(
        name="Exams, Assessments, and Academic Evaluation",
        emoji="🧪",
        color_id="11",
        reminder_minutes=24 * 60,  # 1 day
    ),
    Category(
        name="Orientation, Ceremonies, and University Events",
        emoji="🎓",
        color_id="5",
        reminder_minutes=None,
    ),
    Category(
        name="Holidays and Official Breaks",
        emoji="🏖️",
        color_id="10",
        reminder_minutes=None,
    ),
]

FALLBACK = CATEGORIES[1]  # admin/procedures


_KEYWORDS: List[Tuple[Category, List[re.Pattern]]] = [
    (CATEGORIES[0], [re.compile(p, re.I) for p in [
        r"\bapplication\b", r"\bapply\b", r"\badmission\b", r"\btransfer\b",
        r"\bentry\b", r"\bdeclaration\b", r"\bmajor\b", r"\bminor\b",
        r"\bdouble\s+major\b", r"\bprogram\b", r"\bexchange\s+students?\b",
        r"\binternational\s+students?\b",
    ]]),
    (CATEGORIES[1], [re.compile(p, re.I) for p in [
        r"\benrollment\b", r"\bregistration\b", r"\badd[-\s]?drop\b", r"\bwithdraw(al)?\b",
        r"\btuition\b", r"\bfee\b", r"\bpayment\b", r"\bsubstitution\b",
        r"\bleave\s+of\s+absence\b", r"\bI\s+grades?\b", r"\bconvert(ing)?\b",
        r"\bsingle\s+course\s+exam\s+application\b",
    ]]),
    (CATEGORIES[2], [re.compile(p, re.I) for p in [
        r"\bfirst\s+day\s+of\s+classes\b", r"\blast\s+day\s+of\s+classes\b",
        r"\binternship\b", r"\bmake[-\s]?up\s+class\b",
    ]]),
    (CATEGORIES[3], [re.compile(p, re.I) for p in [
        r"\bexam\b", r"\bfinal\b", r"\bmake[-\s]?up\s+exam\b", r"\bassessment\b",
        r"\bgrade\s+submission\b", r"\bresults?\b", r"\bELAE\b",
    ]]),
    (CATEGORIES[4], [re.compile(p, re.I) for p in [
        r"\borientation\b", r"\bcommencement\b", r"\bceremony\b", r"\bawards?\b",
        r"\bfamily\s+campus\s+day\b", r"\bfest\b",
    ]]),
    (CATEGORIES[5], [re.compile(p, re.I) for p in [
        r"\bholiday\b", r"\bbreak\b", r"\brepublic\b", r"\bvictory\b",
        r"\bramadan\b", r"\bsacrifice\b", r"\bnew\s+year\b",
        r"\bdemocracy\b", r"\bnational\s+unity\b", r"\blabou?r\b",
        r"\byouth\b", r"\bsports\s+day\b",
    ]]),
]


def categorize(title: str) -> Category:
    for cat, pats in _KEYWORDS:
        for pat in pats:
            if pat.search(title):
                return cat
    return FALLBACK