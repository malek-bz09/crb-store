"""The CRB page (next match, fixtures, tables, players) and its ticket links."""

from fastapi import APIRouter, Response

from app.api.deps import AdminOnly, DbSession, StaffOrAdmin
from app.schemas.crb import CrbOverview, Match, TicketLink
from app.services import crb as service

router = APIRouter(tags=["crb"])


@router.get("/crb")
def crb_overview(db: DbSession) -> CrbOverview:
    """Everything the CRB page shows, for the current season."""
    return CrbOverview.model_validate(service.overview(db))


# ---------- Admin: ticket links for upcoming matches ----------

admin_router = APIRouter(prefix="/admin/crb", tags=["crb (admin)"], dependencies=[StaffOrAdmin])


@admin_router.get("/matches")
def upcoming_matches(db: DbSession) -> list[Match]:
    """CRB's upcoming matches, with their ticket links."""
    return [Match.model_validate(m) for m in service.open_matches(db)]


@admin_router.put("/matches/{fixture_id}/ticket", dependencies=[AdminOnly])
def set_ticket(fixture_id: int, data: TicketLink, db: DbSession) -> Match:
    """Sets (or replaces) where to buy tickets for a match, e.g. its Digiticket page."""
    return Match.model_validate(service.set_ticket(db, fixture_id, data.url))


@admin_router.delete("/matches/{fixture_id}/ticket", status_code=204, dependencies=[AdminOnly])
def remove_ticket(fixture_id: int, db: DbSession) -> Response:
    service.remove_ticket(db, fixture_id)
    return Response(status_code=204)
