"""Talks to TheSportsDB and saves every answer in the football_cache table.

The free key allows about 30 requests a minute, so requests are only made by the
background refresh (services/crb_refresh.py), spaced out, and only for answers
older than the `max_age` the caller asks for. Pages read the saved answers only.
"""

import json
import logging
import threading
import time
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.football import FootballCache

logger = logging.getLogger(__name__)

TIMEOUT_SECONDS = 15
# At least this long between two requests: about 24 a minute, under the free limit
MIN_INTERVAL_SECONDS = 2.5
USER_AGENT = "crb-store/1.0"


class FootballDataError(Exception):
    """The API couldn't answer (no connection, too many requests, a bad answer)."""


_pace_lock = threading.Lock()
_last_request_at = 0.0


def _wait_for_turn() -> None:
    global _last_request_at
    with _pace_lock:
        wait = _last_request_at + MIN_INTERVAL_SECONDS - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        _last_request_at = time.monotonic()


def cache_key(path: str, params: dict) -> str:
    return f"{path}?{urlencode(sorted(params.items()))}"


def request(path: str, params: dict) -> dict:
    """One real request to the API. Returns the JSON answer."""
    settings = get_settings()
    _wait_for_turn()
    req = Request(
        f"{settings.sportsdb_api_url}/{settings.sportsdb_api_key.get_secret_value()}{path}?{urlencode(params)}",
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    try:
        with urlopen(req, timeout=TIMEOUT_SECONDS) as response:
            body = json.load(response)
    # URLError includes HTTP errors such as 429 Too Many Requests;
    # ValueError is an answer that isn't JSON
    except (URLError, TimeoutError, ValueError) as exc:
        raise FootballDataError(f"{path}: {exc}") from exc
    if not isinstance(body, dict):
        raise FootballDataError(f"{path}: unexpected answer")
    return body


def cached(db: Session, path: str, params: dict) -> Any | None:
    """The saved answer for path?params, however old, or None. Never asks the API."""
    row = db.get(FootballCache, cache_key(path, params))
    return row.data if row is not None else None


MaxAge = timedelta | Callable[[Any], timedelta]


def get(db: Session, path: str, params: dict, max_age: MaxAge) -> Any:
    """The answer for path?params: the saved one if it's recent enough, otherwise a
    fresh one (saved for next time). max_age can depend on the saved answer, e.g.
    a round of finished matches can be kept longer than one still being played."""
    key = cache_key(path, params)
    row = db.get(FootballCache, key)
    now = datetime.now(UTC)
    if row is not None:
        limit = max_age(row.data) if callable(max_age) else max_age
        if now - row.fetched_at < limit:
            return row.data

    body = request(path, params)
    db.execute(
        insert(FootballCache)
        .values(key=key, data=body, fetched_at=now)
        .on_conflict_do_update(index_elements=["key"], set_={"data": body, "fetched_at": now})
    )
    db.commit()
    return body
