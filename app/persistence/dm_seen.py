"""Persistence helpers for tracking processed Reddit DM message IDs."""

from __future__ import annotations

import json
from pathlib import Path
from threading import Lock
from typing import Iterable

_DM_FILE = Path("seen_dm_ids.json")
_LOCK = Lock()


def _load_ids() -> set[str]:
    try:
        with _DM_FILE.open("r") as fh:
            data = json.load(fh)
        if isinstance(data, list):
            return {str(item) for item in data}
        return set()
    except FileNotFoundError:
        return set()
    except Exception as exc:
        print(f"⚠️ Failed to load seen DM ids: {exc}")
        return set()


_SEEN_DM_IDS: set[str] | None = None


def _ensure_loaded() -> set[str]:
    global _SEEN_DM_IDS
    if _SEEN_DM_IDS is None:
        _SEEN_DM_IDS = _load_ids()
    return _SEEN_DM_IDS


def has_processed(message_id: str | None) -> bool:
    """Return True if the DM with ``message_id`` was already handled."""
    if not message_id:
        return False
    with _LOCK:
        seen = _ensure_loaded()
        return message_id in seen


def record_processed(message_id: str | None) -> None:
    """Persist that a DM ``message_id`` has been handled."""
    if not message_id:
        return
    with _LOCK:
        seen = _ensure_loaded()
        if message_id in seen:
            return
        seen.add(message_id)
        try:
            with _DM_FILE.open("w") as fh:
                json.dump(sorted(seen), fh)
        except Exception as exc:
            print(f"⚠️ Failed to persist seen DM id {message_id}: {exc}")


def record_many(message_ids: Iterable[str]) -> None:
    """Persist multiple DM ``message_ids`` as processed."""
    with _LOCK:
        seen = _ensure_loaded()
        updated = False
        for mid in message_ids:
            if not mid or mid in seen:
                continue
            seen.add(mid)
            updated = True
        if not updated:
            return
        try:
            with _DM_FILE.open("w") as fh:
                json.dump(sorted(seen), fh)
        except Exception as exc:
            print(f"⚠️ Failed to persist seen DM ids: {exc}")
