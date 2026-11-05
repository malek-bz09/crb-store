"""Keeps the saved CRB match data up to date, in the background.

Every few minutes, the answers that are too old are asked for again, one request
at a time (see football_api.py). Finished rounds hardly ever change, so after the
first run only a handful of requests are made each hour.
"""

import logging
import threading
from datetime import UTC, datetime, timedelta

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import SessionLocal, engine
from app.services import football_api
from app.services.crb import FINISHED, MAX_ROUNDS, season_name
from app.services.football_api import FootballDataError

logger = logging.getLogger(__name__)

REFRESH_EVERY = timedelta(minutes=5)
TABLE_MAX_AGE = timedelta(hours=3)
NEXT_LAST_MAX_AGE = timedelta(hours=1)
ROUND_IN_PLAY_MAX_AGE = timedelta(hours=1)  # has matches today or recently
# Every match more than a week away, or no matches: fixtures can still be added
ROUND_LATER_MAX_AGE = timedelta(hours=12)
ROUND_DONE_MAX_AGE = timedelta(days=7)  # every match finished

# Only one process refreshes at a time (several API workers, or --reload restarts)
LOCK_ID = 727_001


def event_time(event: dict) -> datetime | None:
    stamp = event.get("strTimestamp")
    if not stamp:
        return None
    moment = datetime.fromisoformat(stamp)
    return moment if moment.tzinfo else moment.replace(tzinfo=UTC)


def round_max_age(body: dict) -> timedelta:
    events = body.get("events") or []
    if not events:
        return ROUND_LATER_MAX_AGE
    if all(event.get("strStatus") in FINISHED for event in events):
        return ROUND_DONE_MAX_AGE
    week_ahead = datetime.now(UTC) + timedelta(days=7)
    times = [event_time(e) for e in events]
    if all(t is not None and t > week_ahead for t in times):
        return ROUND_LATER_MAX_AGE
    return ROUND_IN_PLAY_MAX_AGE


def refresh_once(db: Session) -> None:
    """Asks the API again for every saved answer that's too old. Stops at the first
    failure (usually "too many requests"); the next run carries on."""
    settings = get_settings()
    season = season_name()
    league, team = settings.crb_league_id, settings.crb_team_id

    football_api.get(db, "/eventsnext.php", {"id": team}, NEXT_LAST_MAX_AGE)
    football_api.get(db, "/eventslast.php", {"id": team}, NEXT_LAST_MAX_AGE)
    football_api.get(db, "/lookuptable.php", {"l": league, "s": season}, TABLE_MAX_AGE)
    for number in range(1, MAX_ROUNDS + 1):
        body = football_api.get(
            db, "/eventsround.php", {"id": league, "r": number, "s": season}, round_max_age
        )
        if not body.get("events"):
            break  # past the last round


def run_once() -> None:
    """One refresh, unless another process is already doing it."""
    # The lock belongs to this connection, so it's held on its own connection while
    # the session below commits after each answer
    with engine.connect() as lock_conn:
        if not lock_conn.scalar(text("SELECT pg_try_advisory_lock(:id)"), {"id": LOCK_ID}):
            return
        try:
            with SessionLocal() as db:
                refresh_once(db)
        except FootballDataError as exc:
            logger.warning("CRB match data refresh stopped: %s", exc)
        finally:
            lock_conn.execute(text("SELECT pg_advisory_unlock(:id)"), {"id": LOCK_ID})
            lock_conn.commit()


def start() -> threading.Event:
    """Starts refreshing in a background thread. Set the returned event to stop it."""
    stop = threading.Event()

    def loop() -> None:
        while not stop.is_set():
            try:
                run_once()
            except Exception:
                # Never let one bad run (database down, ...) end the thread
                logger.exception("CRB match data refresh failed")
            stop.wait(REFRESH_EVERY.total_seconds())

    threading.Thread(target=loop, name="crb-refresh", daemon=True).start()
    return stop
