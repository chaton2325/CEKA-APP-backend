from difflib import SequenceMatcher
from unicodedata import category, normalize

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.user import User


def normalize_search_text(value: str) -> str:
    without_accents = "".join(
        char
        for char in normalize("NFKD", value.lower().strip())
        if category(char) != "Mn"
    )
    return "".join(char for char in without_accents if char.isalnum())


def score_profile_match(query: str, user: User) -> float:
    normalized_query = normalize_search_text(query)
    normalized_username = normalize_search_text(user.username)
    normalized_bio = normalize_search_text(user.bio or "")

    if not normalized_query:
        return 0.0

    username_ratio = SequenceMatcher(
        None, normalized_query, normalized_username
    ).ratio()
    bio_ratio = SequenceMatcher(None, normalized_query, normalized_bio).ratio() * 0.35

    if normalized_username.startswith(normalized_query):
        username_ratio += 0.45
    elif normalized_query in normalized_username:
        username_ratio += 0.3

    return min(max(username_ratio, bio_ratio), 1.0)


def search_profiles(db: Session, query: str, limit: int = 10) -> list[tuple[User, float]]:
    users = list(db.scalars(select(User)))
    scored_users = [
        (user, score_profile_match(query, user))
        for user in users
    ]
    matches = [
        (user, score)
        for user, score in scored_users
        if score >= 0.35
    ]
    matches.sort(key=lambda item: (item[1], item[0].created_at), reverse=True)
    return matches[:limit]
