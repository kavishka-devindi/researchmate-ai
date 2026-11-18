import json
import os
import time

from src.config import BASE_DIR

HISTORY_PATH = os.path.join(BASE_DIR, "data", "history.json")
MAX_ENTRIES = 200


def load_history():
    """Return the saved activity list (oldest first). Empty list if none."""
    try:
        with open(HISTORY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return []


def add_entry(kind, text):
    """Save one activity. kind: 'question', 'summary', 'comparison' or 'upload'."""
    entries = load_history()
    entries.append({"time": time.time(), "kind": kind, "text": text})
    try:
        os.makedirs(os.path.dirname(HISTORY_PATH), exist_ok=True)
        with open(HISTORY_PATH, "w", encoding="utf-8") as f:
            json.dump(entries[-MAX_ENTRIES:], f)
    except OSError:
        pass  # history is a nice-to-have, never crash the app because of it


def time_ago(timestamp):
    seconds = int(time.time() - timestamp)
    if seconds < 60:
        return "just now"
    if seconds < 3600:
        return f"{seconds // 60} min ago"
    if seconds < 86400:
        return f"{seconds // 3600} h ago"
    return f"{seconds // 86400} d ago"