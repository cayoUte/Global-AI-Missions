"""Maya's reference register: ASSESSMENT_SPEC §7 text plus the memory phrases of the mock.

Used by the deterministic mock (the demo default and every fallback) and shown to the LLM as the
register to imitate. All of it is A2-readable and free of the words banned by MAYA.md §8.
"""

# PD-010: the challenge skill -> the catalog mission that trains it.
MISSION_FOR_SKILL: dict[str, str] = {
    "grammar": "the-interview",
    "vocabulary": "dinner-for-two",
    "reading": "campus-day",
    "listening": "night-radio",
}

# ASSESSMENT_SPEC §7.2: can-do statement per suggested level.
CAN_DO: dict[str, str] = {
    "PRE_A1": "You can understand some very common words and numbers when people speak slowly "
    "and clearly.",
    "A1": "You can understand simple signs, numbers and short questions, like asking the way in "
    "a station.",
    "A2": "You can read short notices and messages and do simple travel tasks, like buying the "
    "right ticket.",
    "B1": "You can follow clear announcements and explain what happened to you, even when plans "
    "change.",
    "B2": "You can understand what people mean even when they don't say it directly, and talk "
    "about what could have happened.",
}

# ASSESSMENT_SPEC §7.3: (strong >= 75, developing 50-74, focus < 50).
SKILL_BANDS: dict[str, tuple[str, str, str]] = {
    "grammar": (
        "You build clear sentences, even with tricky verb forms.",
        "Your sentences mostly work. Some verb forms still need care.",
        "Verb forms are slowing you down. Short, clear sentences come first.",
    ),
    "listening": (
        "You catch numbers and details in announcements.",
        "You get the main idea when people speak. Some details slip past.",
        "Conversations are moving faster than you are.",
    ),
    "reading": (
        "You read signs, notices and messages quickly and well.",
        'You understand most of what you read. Small details, like times and "if", can trip you '
        "up.",
        "Written notices are hard for now. Read slowly and look for the key words.",
    ),
    "vocabulary": (
        "You recognize common vocabulary quickly.",
        "You know many everyday words. Phrases with two meanings are still tricky.",
        "New words are your next step. Learn travel words in small groups.",
    ),
}

# ASSESSMENT_SPEC §7.4: recommendation per challenge skill.
RECOMMENDATIONS: dict[str, str] = {
    "grammar": "Say one sentence about your day each evening, and check the verb.",
    "listening": "Listen for numbers first, then names. Play short announcements twice.",
    "reading": 'Read the whole notice once, then look for times and the word "if".',
    "vocabulary": 'Learn words in pairs that go together, like "single" and "return".',
}

# Memory phrases (MAYA.md §4-§6): what Maya says she noticed, per skill.
DOES_WELL_WITH: dict[str, str] = {
    "grammar": "building clear sentences",
    "listening": "announcements",
    "reading": "signs and messages",
    "vocabulary": "vocabulary",
}
STILL_HESITATES: dict[str, str] = {
    "grammar": "You still slow down on tricky verb forms.",
    "listening": "You still hesitate when someone speaks quickly.",
    "reading": "You still lose small details, like times, in long notices.",
    "vocabulary": "You still pause on words with two meanings.",
}
# (what was hard last time, tonight's tip) for the next greeting.
GREETING_TIPS: dict[str, tuple[str, str]] = {
    "grammar": ("some verb forms were tricky", "let's take each sentence slowly"),
    "listening": ("the announcements were fast", "listen for the numbers first"),
    "reading": ("the small details in notices were tricky", "look for the times first"),
    "vocabulary": ("some travel words were new", "watch for words with two meanings"),
}
NUMBER_WORDS: dict[int, str] = {
    2: "Two",
    3: "Three",
    4: "Four",
    5: "Five",
    6: "Six",
    7: "Seven",
    8: "Eight",
    9: "Nine",
    10: "Ten",
}


def cefr_label(code: str) -> str:
    return "Pre-A1" if code == "PRE_A1" else code


def band_line(skill: str, pct: int) -> str:
    strong, developing, focus = SKILL_BANDS[skill]
    return strong if pct >= 75 else developing if pct >= 50 else focus
