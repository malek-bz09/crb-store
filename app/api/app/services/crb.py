"""The CRB page: next match, fixtures and results, the league table and season
numbers, built from saved TheSportsDB answers (kept up to date by crb_refresh.py),
plus the ticket links admins add for upcoming matches.

Pages never wait for the API: everything here reads the football_cache table.
"""

from collections import Counter
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.models.football import FootballCache, MatchTicket
from app.services import football_api

FORM_LENGTH = 5
MAX_ROUNDS = 40  # how many league rounds to look for (a season has 30)
# The free key only gives the top of the table
FREE_TABLE_ROWS = 5

NOT_READY = "Match data is still loading. Please try again in a few minutes."

# TheSportsDB's match statuses (short codes, sometimes written out), grouped into
# what the page needs to know. Anything unknown counts as upcoming.
LIVE = {"1H", "HT", "2H", "ET", "BT", "P", "SUSP", "INT", "LIVE", "In Progress"}
FINISHED = {"FT", "AET", "PEN", "AWD", "WO", "Match Finished"}
POSTPONED = {"PST", "Postponed"}
CANCELLED = {"CANC", "ABD", "Cancelled", "Abandoned"}

STATUS_TEXT = {
    "NS": "Not started",
    "TBD": "Time to be confirmed",
    "FT": "Full time",
    "AET": "After extra time",
    "PEN": "After penalties",
    "AWD": "Awarded",
    "WO": "Walkover",
    "PST": "Postponed",
    "CANC": "Cancelled",
    "ABD": "Abandoned",
    "1H": "First half",
    "HT": "Half time",
    "2H": "Second half",
    "ET": "Extra time",
    "P": "Penalties",
    "SUSP": "Suspended",
    "INT": "Interrupted",
}

# Matches people can still buy tickets for
OPEN_STATUSES = ("upcoming", "live", "postponed")
# A match still marked "not started" this long after kick-off is out-of-date data
STALE_AFTER = timedelta(hours=3)


def current_season(today: date | None = None) -> int:
    """Seasons run from August to June and are named after the year they start in."""
    today = today or datetime.now(ZoneInfo(get_settings().shop_timezone)).date()
    return today.year if today.month >= 7 else today.year - 1


def season_start() -> int:
    return get_settings().football_season or current_season()


def season_name() -> str:
    """TheSportsDB's name for the season: "2026-2027"."""
    start = season_start()
    return f"{start}-{start + 1}"


def status_of(event: dict) -> str:
    status = event.get("strStatus") or ""
    if status in LIVE:
        return "live"
    if status in FINISHED:
        return "finished"
    if status in POSTPONED or event.get("strPostponed") == "yes":
        return "postponed"
    if status in CANCELLED:
        return "cancelled"
    # No status, but a score: played
    if event.get("intHomeScore") not in (None, "") and event.get("intAwayScore") not in (None, ""):
        return "finished"
    return "upcoming"


def number(value) -> int | None:
    return int(value) if value not in (None, "") else None


def badge(url: str | None) -> str | None:
    # TheSportsDB serves smaller copies of its images at <url>/small
    return f"{url}/small" if url and not url.endswith(("/tiny", "/small", "/medium")) else url


def kickoff(event: dict) -> tuple[datetime, bool]:
    """When the match starts (TheSportsDB times are UTC), and whether the time is fixed."""
    time = event.get("strTime") or ""
    confirmed = bool(time) and time != "00:00:00"
    stamp = event.get("strTimestamp") or f"{event['dateEvent']}T{time or '00:00:00'}"
    moment = datetime.fromisoformat(stamp)
    return (moment if moment.tzinfo else moment.replace(tzinfo=UTC)), confirmed


def match_of(event: dict, team_id: int, league_id: int, tickets: dict[int, str]) -> dict:
    status = status_of(event)
    is_home = number(event["idHomeTeam"]) == team_id
    home_goals, away_goals = number(event.get("intHomeScore")), number(event.get("intAwayScore"))

    result = None
    if status == "finished" and home_goals is not None and away_goals is not None:
        ours, theirs = (home_goals, away_goals) if is_home else (away_goals, home_goals)
        result = "W" if ours > theirs else "L" if ours < theirs else "D"

    starts, confirmed = kickoff(event)
    match_id = int(event["idEvent"])
    league = number(event.get("idLeague"))
    round_number = number(event.get("intRound"))
    raw_status = event.get("strStatus") or ""
    return {
        "id": match_id,
        "date": starts,
        "kickoff_confirmed": confirmed,
        "status": status,
        "status_text": STATUS_TEXT.get(raw_status, raw_status or "Not started"),
        "competition": {
            "id": league or 0,
            "name": event.get("strLeague") or "Other",
            "logo": badge(event.get("strLeagueBadge")),
        },
        # Round numbers mean match days in the league; in cups they're codes
        "round": f"Matchday {round_number}" if league == league_id and round_number else None,
        "venue": event.get("strVenue") or None,
        "home": {
            "id": number(event["idHomeTeam"]),
            "name": event["strHomeTeam"],
            "logo": badge(event.get("strHomeTeamBadge")),
            "goals": home_goals,
        },
        "away": {
            "id": number(event["idAwayTeam"]),
            "name": event["strAwayTeam"],
            "logo": badge(event.get("strAwayTeamBadge")),
            "goals": away_goals,
        },
        "is_home": is_home,
        "result": result,
        "ticket_url": tickets.get(match_id) if status in OPEN_STATUSES else None,
    }


def crb_events(db: Session) -> list[dict]:
    """Every saved CRB match this season: from the league rounds, plus the "next" and
    "last" answers, which also cover CAF and cup matches."""
    settings = get_settings()
    team, league, season = str(settings.crb_team_id), settings.crb_league_id, season_name()
    by_id = {}
    for round_number in range(1, MAX_ROUNDS + 1):
        body = football_api.cached(db, "/eventsround.php", {"id": league, "r": round_number, "s": season})
        if body is None or not body.get("events"):
            break
        for event in body["events"]:
            if team in (event.get("idHomeTeam"), event.get("idAwayTeam")):
                by_id[event["idEvent"]] = event
    # The rounds are the better source for a match they include: "next" can lag behind
    # (it still lists a postponed match as next after it's been moved)
    for path, key in (("/eventsnext.php", "events"), ("/eventslast.php", "results")):
        body = football_api.cached(db, path, {"id": settings.crb_team_id}) or {}
        for event in body.get(key) or []:
            if event.get("strSeason") in (None, season):
                by_id.setdefault(event["idEvent"], event)
    return list(by_id.values())


def load_matches(db: Session) -> tuple[dict, list[dict]]:
    """CRB's team and every saved match of the season, oldest first."""
    settings = get_settings()
    events = crb_events(db)
    if not events:
        raise AppError(503, NOT_READY)
    tickets = dict(db.execute(select(MatchTicket.fixture_id, MatchTicket.url)).all())
    matches = sorted(
        (match_of(e, settings.crb_team_id, settings.crb_league_id, tickets) for e in events),
        key=lambda m: m["date"],
    )
    crb = next(m["home" if m["is_home"] else "away"] for m in matches)
    team = {"id": crb["id"], "name": crb["name"], "logo": crb["logo"]}
    return team, matches


def season_stats(matches: list[dict]) -> dict:
    """Totals over the finished matches (oldest first)."""
    played = [m for m in matches if m["result"]]
    results = Counter(m["result"] for m in played)
    scored = [m["home" if m["is_home"] else "away"]["goals"] for m in played]
    conceded = [m["away" if m["is_home"] else "home"]["goals"] for m in played]
    return {
        "played": len(played),
        "wins": results["W"],
        "draws": results["D"],
        "losses": results["L"],
        "goals_for": sum(scored),
        "goals_against": sum(conceded),
        "clean_sheets": conceded.count(0),
        "failed_to_score": scored.count(0),
        "form": [m["result"] for m in played[-FORM_LENGTH:]],
    }


def league_table(db: Session) -> list[dict] | None:
    """The league table rows (the top 5 with the free key), or None if not saved yet."""
    settings = get_settings()
    body = football_api.cached(db, "/lookuptable.php", {"l": settings.crb_league_id, "s": season_name()})
    if body is None:
        return None
    return [
        {
            "rank": int(row["intRank"]),
            "team": {"id": int(row["idTeam"]), "name": row["strTeam"], "logo": badge(row.get("strBadge"))},
            "played": int(row["intPlayed"]),
            "wins": int(row["intWin"]),
            "draws": int(row["intDraw"]),
            "losses": int(row["intLoss"]),
            "goals_for": int(row["intGoalsFor"]),
            "goals_against": int(row["intGoalsAgainst"]),
            "goal_diff": int(row["intGoalDifference"]),
            "points": int(row["intPoints"]),
            "form": row.get("strForm") or None,
            "description": row.get("strDescription") or None,
            "is_crb": int(row["idTeam"]) == settings.crb_team_id,
        }
        for row in body.get("table") or []
    ]


def still_to_play(matches: list[dict]) -> list[dict]:
    """Live and upcoming matches by date, then postponed ones. An "upcoming" match
    whose kick-off is long past is left out (its result isn't in the data yet)."""
    now = datetime.now(UTC)
    playing = [
        m
        for m in matches
        if m["status"] == "live" or (m["status"] == "upcoming" and m["date"] > now - STALE_AFTER)
    ]
    # Postponed matches go last: their old date is meaningless until they're moved
    return playing + [m for m in matches if m["status"] == "postponed"]


def overview(db: Session) -> dict:
    settings = get_settings()
    team, matches = load_matches(db)

    upcoming = still_to_play(matches)
    live = [m for m in upcoming if m["status"] == "live"]
    scheduled = [m for m in upcoming if m["status"] == "upcoming"]
    next_match = (live or scheduled or [None])[0]

    # Competitions in the order CRB first played in them
    competitions = {}
    for match in matches:
        competitions.setdefault(match["competition"]["id"], match["competition"])

    rows = league_table(db)
    competition_overviews = []
    for competition_id, competition in competitions.items():
        standings = []
        if competition_id == settings.crb_league_id and rows:
            standings = [{"name": None, "rows": rows, "top_only": len(rows) <= FREE_TABLE_ROWS}]
        competition_overviews.append(
            {
                **competition,
                "stats": season_stats([m for m in matches if m["competition"]["id"] == competition_id]),
                "standings": standings,
            }
        )

    return {
        "team": team,
        "season": season_start(),
        "updated_at": db.scalar(select(func.max(FootballCache.fetched_at))),
        "next_match": next_match,
        "upcoming": upcoming,
        "results": [m for m in reversed(matches) if m["status"] == "finished"],
        "stats": season_stats(matches),
        "competitions": competition_overviews,
        "unavailable": ["standings"] if rows is None else [],
    }


# ---------- Ticket links (admin) ----------


def open_matches(db: Session) -> list[dict]:
    """Upcoming matches, the ones that can have a ticket link."""
    _, matches = load_matches(db)
    return still_to_play(matches)


def set_ticket(db: Session, fixture_id: int, url: str) -> dict:
    match = next((m for m in open_matches(db) if m["id"] == fixture_id), None)
    if match is None:
        raise AppError(404, "This isn't one of CRB's upcoming matches.")
    db.execute(
        insert(MatchTicket)
        .values(fixture_id=fixture_id, url=url)
        .on_conflict_do_update(index_elements=["fixture_id"], set_={"url": url, "updated_at": func.now()})
    )
    db.commit()
    return match | {"ticket_url": url}


def remove_ticket(db: Session, fixture_id: int) -> None:
    db.execute(delete(MatchTicket).where(MatchTicket.fixture_id == fixture_id))
    db.commit()
