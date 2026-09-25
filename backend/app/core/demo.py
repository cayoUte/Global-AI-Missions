"""Demo accounts (SHARED_CONTEXT §7, PD-018, PD-023). DEMO-ONLY credentials.

Imported by the seed (backend/seed) and by GET /api/config (listed only when DEMO_MODE=true).
The password below is a published demo password for local runs and the evaluation demo, not a
secret: it must never be reused for a real account. The admin user is a test fixture only and
is deliberately not listed here.
"""

from dataclasses import dataclass
from typing import Literal

DEMO_PASSWORD = "LastTrain2026!"  # demo-only, shown on the check-in screen in demo mode

Role = Literal["student", "teacher", "admin"]


@dataclass(frozen=True)
class DemoAccount:
    email: str
    display_name: str
    role: Role
    purpose: str


NEW_STUDENT = DemoAccount(
    email="new@globalai.test",
    display_name="Ana",
    role="student",
    purpose="First meeting with Maya.",
)
VETERAN = DemoAccount(
    email="veteran@globalai.test",
    display_name="Leo",
    role="student",
    purpose="Returning student: history, memory and progress trend.",
)
TEACHER = DemoAccount(
    email="teacher@globalai.test",
    display_name="Ms. Clarke",
    role="teacher",
    purpose="Teacher of a class with both students (roles demo).",
)

# The order GET /api/config lists them in.
DEMO_ACCOUNTS: tuple[DemoAccount, ...] = (NEW_STUDENT, VETERAN, TEACHER)

# The teacher's class; both demo students are members.
DEMO_CLASS_NAME = "Evening B1"
DEMO_CLASS_STUDENTS: tuple[DemoAccount, ...] = (NEW_STUDENT, VETERAN)

# Veteran history (seed only): simulator profile, fixed seeds and how many days ago each
# submitted attempt happened (spread over the last 14 days, oldest first).
VETERAN_PROFILE = "A2_weak_listening"
VETERAN_SEEDS: tuple[int, ...] = (3, 11, 19, 27)
VETERAN_DAYS_AGO: tuple[int, ...] = (13, 9, 5, 2)
