"""Tables for the CRB page: saved API-Football answers and the ticket links."""

from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, DateTime, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class FootballCache(Base):
    """The last answer API-Football gave for each request. The free plan only
    allows 100 requests a day, so answers are reused (see services/football_api.py)."""

    __tablename__ = "football_cache"

    # The request it answers, e.g. "/fixtures?season=2026&team=1234"
    key: Mapped[str] = mapped_column(String(300), primary_key=True)
    data: Mapped[Any] = mapped_column(JSONB)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class MatchTicket(TimestampMixin, Base):
    """Where to buy tickets for a match (its Digiticket page), set by an admin."""

    __tablename__ = "match_tickets"

    # API-Football's id for the match
    fixture_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    url: Mapped[str] = mapped_column(String(500))
