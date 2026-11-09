"""Load a local user profile without committing personal data."""

import json
from pathlib import Path

from kaggle_scout.user_profile import UserProfile

_REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PROFILE_PATH = _REPO_ROOT / "data" / "user_profile.json"
EXAMPLE_PROFILE_PATH = _REPO_ROOT / "data" / "user_profile.example.json"


def load_user_profile(path: Path | None = None) -> UserProfile:
    """Read a JSON profile and validate it as ``UserProfile``."""
    profile_path = Path(path) if path is not None else DEFAULT_PROFILE_PATH
    if not profile_path.is_file():
        raise FileNotFoundError(
            f"User profile not found at {profile_path}. "
            "Copy data/user_profile.example.json to data/user_profile.json "
            "and edit it with your skills and interests."
        )

    try:
        raw = json.loads(profile_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"User profile is not valid JSON: {profile_path}") from error

    if not isinstance(raw, dict):
        raise TypeError("User profile must be a JSON object")

    return UserProfile(**raw)
