"""The CRB page, its background refresh and its ticket links, with a fake
TheSportsDB instead of the real one."""

import io
from datetime import UTC, datetime, timedelta
from urllib.error import HTTPError

import pytest
from sqlalchemy import select, text, update

from app.core.config import get_settings
from app.db.session import SessionLocal, engine
from app.models.football import FootballCache
from app.services import crb, crb_refresh, football_api
from app.services.football_api import FootballDataError

CRB, LIGUE_1, CAF = 139278, 4753, 4720
PAGE = "/api/v1/crb"
MATCHES = "/api/v1/admin/crb/matches"
SEASON = "2026-2027"

ME = (CRB, "CR Belouizdad")
MCA, USMA, ESS, CSC, AHLY = (1, "MC Alger"), (2, "USM Alger"), (3, "ES Sétif"), (4, "CS Constantine"), (5, "Al Ahly")


def stamp(days: float) -> str:
    """A kick-off time `days` from now, as TheSportsDB writes it (UTC, no zone)."""
    return (datetime.now(UTC) + timedelta(days=days)).strftime("%Y-%m-%dT%H:00:00")


def event(id, days, home, away, status="NS", score=(None, None), league=LIGUE_1, round=1, time="17:00:00"):
    return {
        "idEvent": str(id), "strTimestamp": stamp(days), "dateEvent": stamp(days)[:10], "strTime": time,
        "idLeague": str(league), "strLeague": {LIGUE_1: "Algerian Ligue 1", CAF: "CAF Champions League"}[league],
        "strLeagueBadge": "https://img/league.png", "strSeason": SEASON, "intRound": str(round),
        "idHomeTeam": str(home[0]), "strHomeTeam": home[1], "strHomeTeamBadge": f"https://img/{home[0]}.png",
        "idAwayTeam": str(away[0]), "strAwayTeam": away[1], "strAwayTeamBadge": f"https://img/{away[0]}.png",
        "intHomeScore": None if score[0] is None else str(score[0]),
        "intAwayScore": None if score[1] is None else str(score[1]),
        "strStatus": status, "strVenue": "Stade 5 Juillet 1962", "strPostponed": "no",
    }


ROUNDS = {
    1: [event(11, -30, ME, MCA, "FT", (2, 0)), event(91, -30, USMA, ESS, "FT", (1, 1))],
    2: [event(12, -23, USMA, ME, "FT", (1, 1))],
    3: [event(14, -9, ESS, ME, "FT", (0, 2), round=3)],
    # Postponed, then moved to a new date: the round has the new date, "next" still the old one
    4: [event(15, 3, ME, CSC, "NS", round=4)],
    5: [event(16, 10, MCA, ME, "NS", round=5, time="00:00:00"),  # time not fixed yet
        event(18, -20, ME, USMA, "PST", round=5)],  # postponed, no new date yet
    6: [event(17, -1, ME, ESS, "NS", round=6)],  # kick-off long past, no result yet
}
NEXT = {"events": [event(15, 1, ME, CSC, "PST", round=4)]}
LAST = {"results": [event(13, -16, AHLY, ME, "FT", (3, 1), league=CAF, round=125)]}


def table_row(rank, side, points):
    return {"intRank": str(rank), "idTeam": str(side[0]), "strTeam": side[1], "strBadge": "https://img/t.png/tiny",
            "intPlayed": "3", "intWin": "2", "intDraw": "1", "intLoss": "0", "intGoalsFor": "5",
            "intGoalsAgainst": "2", "intGoalDifference": "3", "intPoints": str(points), "strForm": "WDW",
            "strDescription": "Promotion - CAF Champions League" if rank == 1 else ""}


TABLE = {"table": [table_row(1, ME, 7), table_row(2, USMA, 5), table_row(3, MCA, 4), table_row(4, ESS, 4),
                   table_row(5, CSC, 3)]}


class FakeApi:
    def __init__(self):
        self.calls = []
        self.fail = False

    def __call__(self, path, params):
        self.calls.append((path, params.get("r")))
        if self.fail:
            raise FootballDataError("HTTP Error 429: Too Many Requests")
        if path == "/eventsround.php":
            assert params["s"] == SEASON
            return {"events": ROUNDS.get(params["r"])}
        return {"/eventsnext.php": NEXT, "/eventslast.php": LAST, "/lookuptable.php": TABLE}[path]


@pytest.fixture
def api(monkeypatch):
    fake = FakeApi()
    monkeypatch.setattr(football_api, "request", fake)
    monkeypatch.setattr(get_settings(), "football_season", 2026)
    return fake


@pytest.fixture
def loaded(api):
    """The data as after the first background refresh."""
    crb_refresh.run_once()
    return api


def make_old(days=1):
    with SessionLocal() as db:
        db.execute(update(FootballCache).values(fetched_at=datetime.now(UTC) - timedelta(days=days)))
        db.commit()


# ---------- The page ----------


def test_page_says_loading_before_the_first_refresh(client, api):
    response = client.get(PAGE)
    assert response.status_code == 503
    assert response.json()["detail"]["message"] == crb.NOT_READY


def test_page_shows_the_season(client, loaded):
    page = client.get(PAGE).json()

    assert page["team"] == {"id": CRB, "name": "CR Belouizdad", "logo": f"https://img/{CRB}.png/small"}
    assert page["season"] == 2026
    assert page["updatedAt"] is not None

    # The rescheduled date from the round wins over "next", which still says postponed
    assert page["nextMatch"]["id"] == 15
    assert page["nextMatch"]["status"] == "upcoming"
    assert page["nextMatch"]["round"] == "Matchday 4"
    assert page["nextMatch"]["venue"] == "Stade 5 Juillet 1962"
    assert page["nextMatch"]["kickoffConfirmed"] is True
    # Match 17's kick-off is long past without a result: not listed as upcoming.
    # Postponed match 18 comes last, whatever its old date.
    assert [(m["id"], m["kickoffConfirmed"]) for m in page["upcoming"]] == [(15, True), (16, False), (18, True)]

    # The CAF match comes from "last"; another club's match in round 1 isn't CRB's
    assert [(m["id"], m["result"]) for m in page["results"]] == [(14, "W"), (13, "L"), (12, "D"), (11, "W")]
    assert page["results"][1]["round"] is None  # cup round codes aren't match days

    assert page["stats"] == {"played": 4, "wins": 2, "draws": 1, "losses": 1, "goalsFor": 6,
                             "goalsAgainst": 4, "cleanSheets": 2, "failedToScore": 0,
                             "form": ["W", "D", "L", "W"]}

    competitions = {c["id"]: c for c in page["competitions"]}
    assert list(competitions) == [LIGUE_1, CAF]
    assert competitions[LIGUE_1]["stats"]["played"] == 3
    assert competitions[CAF]["standings"] == []
    [table] = competitions[LIGUE_1]["standings"]
    assert table["topOnly"] is True
    assert [(r["rank"], r["team"]["name"], r["isCrb"]) for r in table["rows"]][:2] == [
        (1, "CR Belouizdad", True), (2, "USM Alger", False)]
    assert table["rows"][0]["team"]["logo"] == "https://img/t.png/tiny"  # already a small copy
    assert page["unavailable"] == []


def test_page_without_the_table_yet(client, loaded):
    with SessionLocal() as db:
        db.execute(FootballCache.__table__.delete().where(FootballCache.key.like("/lookuptable%")))
        db.commit()
    page = client.get(PAGE).json()
    assert page["unavailable"] == ["standings"]
    assert all(c["standings"] == [] for c in page["competitions"])


def test_page_never_calls_the_api(client, loaded):
    calls = len(loaded.calls)
    make_old(days=30)
    assert client.get(PAGE).status_code == 200
    assert len(loaded.calls) == calls


def test_season_switches_in_july():
    assert crb.current_season(datetime(2027, 6, 30).date()) == 2026
    assert crb.current_season(datetime(2027, 7, 1).date()) == 2027


# ---------- The background refresh ----------


def test_refresh_asks_for_every_round_until_an_empty_one(loaded):
    rounds = [r for path, r in loaded.calls if path == "/eventsround.php"]
    assert rounds == [1, 2, 3, 4, 5, 6, 7]  # 7 is empty: the season stops there
    assert {path for path, _ in loaded.calls} == {"/eventsround.php", "/eventsnext.php", "/eventslast.php",
                                                   "/lookuptable.php"}


def test_refresh_only_asks_again_for_old_answers(loaded):
    loaded.calls.clear()
    crb_refresh.run_once()
    assert loaded.calls == []

    # A day later: finished rounds are kept for a week, the rest is asked for again
    make_old(days=1)
    crb_refresh.run_once()
    assert sorted(r or 0 for path, r in loaded.calls) == [0, 0, 0, 4, 5, 6, 7]


def test_round_max_age():
    finished = {"events": [event(1, -10, ME, MCA, "FT", (1, 0)), event(2, -10, USMA, ESS, "AET", (2, 1))]}
    soon = {"events": [event(1, -10, ME, MCA, "FT", (1, 0)), event(2, 2, USMA, ESS)]}
    later = {"events": [event(1, 20, ME, MCA), event(2, 21, USMA, ESS)]}
    assert crb_refresh.round_max_age(finished) == crb_refresh.ROUND_DONE_MAX_AGE
    assert crb_refresh.round_max_age({"events": None}) == crb_refresh.ROUND_LATER_MAX_AGE
    assert crb_refresh.round_max_age(soon) == crb_refresh.ROUND_IN_PLAY_MAX_AGE
    assert crb_refresh.round_max_age(later) == crb_refresh.ROUND_LATER_MAX_AGE


def test_a_failed_refresh_keeps_the_saved_data(client, loaded):
    make_old()
    loaded.fail = True
    loaded.calls.clear()
    crb_refresh.run_once()  # logs a warning, doesn't raise
    assert len(loaded.calls) == 1  # stopped at the first failure
    assert client.get(PAGE).json()["nextMatch"]["id"] == 15


def test_only_one_process_refreshes_at_a_time(api):
    with engine.connect() as other:
        other.execute(text("SELECT pg_advisory_lock(:id)"), {"id": crb_refresh.LOCK_ID})
        crb_refresh.run_once()
        assert api.calls == []
        other.execute(text("SELECT pg_advisory_unlock(:id)"), {"id": crb_refresh.LOCK_ID})
    crb_refresh.run_once()
    assert api.calls


# ---------- Ticket links ----------

DIGITICKET = "https://digiticket.example/events/crb-csc"


def test_admin_adds_a_ticket_link_that_the_page_shows(client, admin_client, loaded):
    response = admin_client.put(f"{MATCHES}/15/ticket", json={"url": DIGITICKET})
    assert response.status_code == 200
    assert response.json()["ticketUrl"] == DIGITICKET
    assert client.get(PAGE).json()["nextMatch"]["ticketUrl"] == DIGITICKET

    # Replacing it, then removing it
    admin_client.put(f"{MATCHES}/15/ticket", json={"url": DIGITICKET + "?v=2"})
    assert [m["ticketUrl"] for m in admin_client.get(MATCHES).json() if m["id"] == 15] == [DIGITICKET + "?v=2"]
    assert admin_client.delete(f"{MATCHES}/15/ticket").status_code == 204
    assert client.get(PAGE).json()["nextMatch"]["ticketUrl"] is None


@pytest.mark.parametrize("url", ["http://digiticket.example/x", "javascript:alert(1)", "digiticket.example", "https://"])
def test_ticket_link_must_be_an_https_address(admin_client, loaded, url):
    response = admin_client.put(f"{MATCHES}/15/ticket", json={"url": url})
    assert response.status_code == 422
    assert "https://" in response.json()["detail"]["fieldErrors"]["url"]


def test_only_upcoming_matches_get_ticket_links(admin_client, loaded):
    assert admin_client.put(f"{MATCHES}/11/ticket", json={"url": DIGITICKET}).status_code == 404  # finished
    assert admin_client.put(f"{MATCHES}/17/ticket", json={"url": DIGITICKET}).status_code == 404  # long past
    assert admin_client.put(f"{MATCHES}/999/ticket", json={"url": DIGITICKET}).status_code == 404  # unknown


def test_staff_can_see_but_not_change_ticket_links(client, staff_client, loaded):
    assert [m["id"] for m in staff_client.get(MATCHES).json()] == [15, 16, 18]
    assert staff_client.put(f"{MATCHES}/15/ticket", json={"url": DIGITICKET}).status_code == 403
    assert staff_client.delete(f"{MATCHES}/15/ticket").status_code == 403
    assert client.put(f"{MATCHES}/15/ticket", json={"url": DIGITICKET}).status_code == 401
    assert client.get(MATCHES).status_code == 401


# ---------- The request itself ----------


@pytest.fixture
def http(monkeypatch):
    """Replaces the network: set `.body` (bytes) or `.error`, read `.url`."""

    class Http:
        body, error, url = b"{}", None, None

        def urlopen(self, req, timeout):
            self.url = req.full_url
            if self.error:
                raise self.error
            return io.BytesIO(self.body)

    fake = Http()
    monkeypatch.setattr(football_api, "urlopen", fake.urlopen)
    monkeypatch.setattr(football_api, "MIN_INTERVAL_SECONDS", 0)
    return fake


def test_request_uses_the_key_in_the_address(http):
    http.body = b'{"events": [1]}'
    assert football_api.request("/eventsnext.php", {"id": CRB}) == {"events": [1]}
    assert http.url == f"https://www.thesportsdb.com/api/v1/json/123/eventsnext.php?id={CRB}"


def test_request_fails_on_too_many_requests_and_bad_answers(http):
    http.error = HTTPError("https://x", 429, "Too Many Requests", {}, None)
    with pytest.raises(FootballDataError):
        football_api.request("/eventsnext.php", {"id": CRB})
    http.error, http.body = None, b"<html>Slow down</html>"
    with pytest.raises(FootballDataError):
        football_api.request("/eventsnext.php", {"id": CRB})


def test_get_saves_the_answer(http):
    http.body = b'{"table": []}'
    with SessionLocal() as db:
        football_api.get(db, "/lookuptable.php", {"l": LIGUE_1, "s": SEASON}, timedelta(hours=1))
        assert db.scalar(select(FootballCache.key)) == f"/lookuptable.php?l={LIGUE_1}&s={SEASON}"
        assert football_api.cached(db, "/lookuptable.php", {"s": SEASON, "l": LIGUE_1}) == {"table": []}
