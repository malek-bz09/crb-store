"""What the CRB page endpoints return, and the ticket link admins send."""

from datetime import datetime
from typing import Annotated, Literal
from urllib.parse import urlsplit

from pydantic import AfterValidator, Field

from app.schemas.common import CamelModel

Result = Literal["W", "D", "L"]


class Team(CamelModel):
    id: int
    name: str
    logo: str | None = None


class Side(Team):
    goals: int | None = None


class Competition(CamelModel):
    id: int
    name: str
    logo: str | None = None


class Match(CamelModel):
    id: int
    date: datetime
    kickoff_confirmed: bool  # false: only the day is known, not the time
    status: Literal["upcoming", "live", "finished", "postponed", "cancelled"]
    status_text: str  # the API's own wording, e.g. "Match Finished"
    competition: Competition
    round: str | None
    venue: str | None
    home: Side
    away: Side
    is_home: bool
    result: Result | None  # CRB's result, once the match is finished
    ticket_url: str | None


class SeasonStats(CamelModel):
    played: int
    wins: int
    draws: int
    losses: int
    goals_for: int
    goals_against: int
    clean_sheets: int
    failed_to_score: int
    form: list[Result]  # the last 5 results, oldest first


class StandingRow(CamelModel):
    rank: int
    team: Team
    played: int
    wins: int
    draws: int
    losses: int
    goals_for: int
    goals_against: int
    goal_diff: int
    points: int
    form: str | None
    description: str | None  # e.g. "CAF Champions League" next to the top places
    is_crb: bool


class StandingGroup(CamelModel):
    name: str | None
    rows: list[StandingRow]
    top_only: bool  # only the top of the table (the free data stops there)


class CompetitionOverview(Competition):
    stats: SeasonStats
    standings: list[StandingGroup]  # empty for cups without a table


class CrbOverview(CamelModel):
    team: Team
    season: int  # the year the season starts in: 2026 = 2026/27
    updated_at: datetime | None  # when the newest data was fetched
    next_match: Match | None
    upcoming: list[Match]
    results: list[Match]  # newest first
    stats: SeasonStats  # all competitions together
    competitions: list[CompetitionOverview]
    # Parts that aren't available yet: "standings"
    unavailable: list[str]


def check_ticket_url(value: str) -> str:
    # Must be a full https:// address: it's opened from the shop, so "javascript:..."
    # or a plain-http page must never get in
    parts = urlsplit(value)
    if parts.scheme != "https" or not parts.hostname:
        raise ValueError("Enter the full ticket page address, starting with https://")
    return value


class TicketLink(CamelModel):
    url: Annotated[str, Field(min_length=1, max_length=500), AfterValidator(check_ticket_url)]
