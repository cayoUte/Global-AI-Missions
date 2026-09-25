"""Demo users and the teacher's class (values from app/core/demo.py; demo-only password)."""

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import demo
from app.models import ClassMember, SchoolClass, User
from app.repositories import users as users_repo

_hasher = PasswordHasher()


def _password_matches(password_hash: str, password: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False


def upsert_user(session: Session, account: demo.DemoAccount, password: str) -> User:
    """Create the user, or bring name and role back to the demo values. The hash is only
    recomputed when the stored one does not match (argon2 salts differ on every hash)."""
    user = users_repo.get_user_by_email(session, account.email)
    if user is None:
        user = User(
            email=users_repo.normalize_email(account.email),
            password_hash=_hasher.hash(password),
            display_name=account.display_name,
            role=account.role,
        )
        session.add(user)
    else:
        user.display_name = account.display_name
        user.role = account.role
        if not _password_matches(user.password_hash, password):
            user.password_hash = _hasher.hash(password)
    session.flush()
    return user


def seed_demo_users(session: Session) -> dict[str, User]:
    users = {a.email: upsert_user(session, a, demo.DEMO_PASSWORD) for a in demo.DEMO_ACCOUNTS}
    teacher = users[demo.TEACHER.email]
    school_class = session.scalar(
        select(SchoolClass).where(
            SchoolClass.teacher_id == teacher.id, SchoolClass.name == demo.DEMO_CLASS_NAME
        )
    )
    if school_class is None:
        school_class = SchoolClass(name=demo.DEMO_CLASS_NAME, teacher_id=teacher.id)
        session.add(school_class)
        session.flush()
    for account in demo.DEMO_CLASS_STUDENTS:
        student = users[account.email]
        if session.get(ClassMember, (school_class.id, student.id)) is None:
            session.add(ClassMember(class_id=school_class.id, user_id=student.id))
    session.flush()
    return users
