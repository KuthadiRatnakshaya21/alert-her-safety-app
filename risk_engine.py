"""Shared risk scoring and crowd-story memory for Alert Her."""

from __future__ import annotations

RISK_ZONES: dict[str, str] = {
    "Sultanpuri": "red",
    "Prem Nagar": "red",
    "Nihal Vihar": "red",
    "Anand Parbat": "red",
    "ITO": "red",
    "Jama Masjid": "red",
    "Govindpuri": "red",
    "Dwarka Mor": "red",
    "Uttam Nagar": "red",
    "Shadipur": "red",
    "Chandni Chowk": "red",
    "Kashmere Gate": "red",
    "Dhaula Kuan": "yellow",
    "Vasant Vihar": "yellow",
    "Mehrauli": "yellow",
    "Malviya Nagar": "yellow",
    "Paharganj": "yellow",
    "Karol Bagh": "yellow",
    "Chanakyapuri": "green",
    "Lutyens Delhi": "green",
    "Connaught Place": "green",
}

ZONE_COORDS: dict[str, tuple[float, float]] = {
    "Sultanpuri": (28.7031, 77.0750),
    "Prem Nagar": (28.6703, 77.0812),
    "Nihal Vihar": (28.6674, 77.0661),
    "Anand Parbat": (28.6582, 77.1724),
    "ITO": (28.6289, 77.2410),
    "Jama Masjid": (28.6507, 77.2334),
    "Govindpuri": (28.5304, 77.2641),
    "Dwarka Mor": (28.6193, 77.0333),
    "Uttam Nagar": (28.6210, 77.0550),
    "Shadipur": (28.6516, 77.1583),
    "Chandni Chowk": (28.6506, 77.2303),
    "Kashmere Gate": (28.6676, 77.2289),
    "Dhaula Kuan": (28.5950, 77.1610),
    "Vasant Vihar": (28.5572, 77.1571),
    "Mehrauli": (28.5210, 77.1780),
    "Malviya Nagar": (28.5362, 77.2110),
    "Paharganj": (28.6448, 77.2167),
    "Karol Bagh": (28.6517, 77.1909),
    "Chanakyapuri": (28.5934, 77.1888),
    "Lutyens Delhi": (28.6139, 77.2090),
    "Connaught Place": (28.6315, 77.2167),
}

ZONE_POINTS = {"red": 40, "yellow": 20, "green": 0}
UNKNOWN_POINTS = 15
CROWD_STORY_POINTS = 15

# Seed memory copied into st.session_state.stories on first run.
CROWD_STORIES: list[dict] = [
    {
        "id": "seed-ito-1",
        "timestamp": "2026-09-16 22:41",
        "location": "ITO",
        "description": "Dark stretch near the underpass; streetlights were out.",
        "avatar_label": "I",
        "avatar_color": "#e53e3e",
    },
    {
        "id": "seed-paharganj-1",
        "timestamp": "2026-09-17 00:12",
        "location": "Paharganj",
        "description": "Heavy crowding and catcalling near the station exit.",
        "avatar_label": "P",
        "avatar_color": "#dd8c2b",
    },
    {
        "id": "seed-cp-1",
        "timestamp": "2026-09-17 19:05",
        "location": "Connaught Place",
        "description": "Large unmanaged crowd at the inner circle after office hours.",
        "avatar_label": "C",
        "avatar_color": "#2f9e44",
    },
    {
        "id": "seed-kashmere-1",
        "timestamp": "2026-09-17 21:18",
        "location": "Kashmere Gate",
        "description": "Isolated walkway behind metro gate 2 felt unsafe.",
        "avatar_label": "K",
        "avatar_color": "#e53e3e",
    },
]


def _is_night(hour: int) -> bool:
    return hour >= 21 or hour < 5


def _is_late_night(hour: int) -> bool:
    return hour >= 23 or hour < 4


def _level_from_score(score: int) -> str:
    if score <= 30:
        return "Low"
    if score <= 60:
        return "Moderate"
    return "High"


def _active_stories() -> list[dict]:
    try:
        import streamlit as st

        stories = st.session_state.get("stories")
        if isinstance(stories, list):
            return stories
    except Exception:
        pass
    return CROWD_STORIES


def matching_stories(destination: str) -> list[dict]:
    dest = (destination or "").strip().lower()
    if not dest:
        return []
    return [
        story
        for story in _active_stories()
        if (story.get("location") or "").strip().lower() == dest
    ]


def calculate_risk(destination: str, hour: int, is_weekend: bool) -> dict:
    """Return score (0-100), level, and plain-language reasons."""
    hour = int(hour) % 24
    dest = (destination or "").strip()
    zone = RISK_ZONES.get(dest)

    score = 0
    reasons: list[str] = []

    if zone == "red":
        score += ZONE_POINTS["red"]
        reasons.append("Flagged high-incident area (+40)")
    elif zone == "yellow":
        score += ZONE_POINTS["yellow"]
        reasons.append("Moderate-incident area — extra caution (+20)")
    elif zone == "green":
        reasons.append("Lower-incident area (no extra zone points)")
    else:
        score += UNKNOWN_POINTS
        reasons.append("Unknown area — default caution (+15)")

    if _is_night(hour):
        score += 30
        reasons.append("Late night travel (+30)")

    if _is_late_night(hour):
        score += 10
        reasons.append("Very late / early-morning hours (+10)")

    if is_weekend and _is_night(hour):
        score += 10
        reasons.append("Weekend night (+10)")

    for _story in matching_stories(dest):
        score += CROWD_STORY_POINTS
        reasons.append("Active user-reported hazard flagged at this location (+15)")

    score = max(0, min(100, score))
    return {"score": score, "level": _level_from_score(score), "reasons": reasons}


def hourly_scores(destination: str, is_weekend: bool) -> list[int]:
    return [calculate_risk(destination, h, is_weekend)["score"] for h in range(24)]


def best_upcoming_hour(
    destination: str,
    current_hour: int,
    is_weekend: bool,
    window: int = 6,
) -> tuple[int, dict, dict]:
    """Lowest-score hour in the next `window` hours (not including now)."""
    current = calculate_risk(destination, current_hour, is_weekend)
    best_hour = (int(current_hour) + 1) % 24
    best = calculate_risk(destination, best_hour, is_weekend)
    for offset in range(1, window + 1):
        hour = (int(current_hour) + offset) % 24
        result = calculate_risk(destination, hour, is_weekend)
        if result["score"] < best["score"]:
            best_hour = hour
            best = result
    return best_hour, current, best
