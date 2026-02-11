from fastapi import APIRouter, Response

from app.api.db import DbSession
from app.api.schemas import Period, PeriodQuery
from app.api.service import StatsService

router = APIRouter(prefix="/lines", tags=["statistics"])

JSON = "application/json"


@router.get("/{line_number}/stats/max-delay-between-stops")
def get_max_delay_between_stops(
    line_number: str,
    db: DbSession,
    period: PeriodQuery = Period.TODAY,
) -> Response:
    raw = StatsService(db).max_delay_between_stops(line_number, period)
    return Response(content=raw, media_type=JSON)


@router.get("/{line_number}/stats/route-delay")
def get_route_delay(
    line_number: str,
    db: DbSession,
    period: PeriodQuery = Period.TODAY,
) -> Response:
    raw = StatsService(db).route_delay(line_number, period)
    return Response(content=raw, media_type=JSON)


@router.get("/stats/summary")
def get_lines_summary(
    db: DbSession,
    period: PeriodQuery = Period.TODAY,
) -> Response:
    raw = StatsService(db).lines_summary(period)
    return Response(content=raw, media_type=JSON)


@router.get("/{line_number}/stats/punctuality")
def get_punctuality(
    line_number: str,
    db: DbSession,
    period: PeriodQuery = Period.TODAY,
) -> Response:
    raw = StatsService(db).punctuality(line_number, period)
    return Response(content=raw, media_type=JSON)


@router.get("/{line_number}/stats/trend")
def get_trend(
    line_number: str,
    db: DbSession,
    period: PeriodQuery = Period.MONTH,
) -> Response:
    raw = StatsService(db).trend(line_number, period)
    return Response(content=raw, media_type=JSON)
