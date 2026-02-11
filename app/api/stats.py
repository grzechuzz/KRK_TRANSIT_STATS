from typing import Any

from fastapi import APIRouter, HTTPException, Response, status

from app.api import cache
from app.api.db import DbSession
from app.api.repository import StatsRepository, resolve_date_range
from app.api.schemas import (
    LineSummary,
    LineSummaryResponse,
    MaxDelayBetweenStops,
    MaxDelayBetweenStopsResponse,
    Period,
    PeriodQuery,
    PunctualityResponse,
    RouteDelay,
    RouteDelayResponse,
    TrendDay,
    TrendResponse,
)

router = APIRouter(prefix="/lines", tags=["statistics"])

JSON = "application/json"


def _to_str(row: dict[str, Any]) -> dict[str, Any]:
    return {k: str(v) if not isinstance(v, (str, int, float)) else v for k, v in row.items()}


def _check_line_exists(trips: int, line_number: str, period: Period) -> None:
    if not trips:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Line {line_number} not found in {period.value} period",
        )


def _from_cache(endpoint: str, period: Period, line_number: str = "") -> Response | None:
    raw = cache.get_cached(endpoint, period, line_number)
    if raw is not None:
        return Response(content=raw, media_type=JSON)
    return None


@router.get("/{line_number}/stats/max-delay-between-stops")
def get_max_delay_between_stops(
    line_number: str,
    db: DbSession,
    period: PeriodQuery = Period.TODAY,
) -> Response:
    cached = _from_cache("max-delay-between-stops", period, line_number)
    if cached:
        return cached

    start, end = resolve_date_range(period)
    repo = StatsRepository(db)

    trips = repo.trips_count(line_number, start, end)
    _check_line_exists(trips, line_number, period)

    rows = repo.max_delay_between_stops(line_number, start, end)

    result = MaxDelayBetweenStopsResponse(
        line_number=line_number,
        period=period.value,
        max_delay=[MaxDelayBetweenStops(**_to_str(row)) for row in rows],
        trips_analyzed=trips,
    )
    raw = cache.set_cached("max-delay-between-stops", period, result, line_number)
    return Response(content=raw, media_type=JSON)


@router.get("/{line_number}/stats/route-delay")
def get_route_delay(
    line_number: str,
    db: DbSession,
    period: PeriodQuery = Period.TODAY,
) -> Response:
    cached = _from_cache("route-delay", period, line_number)
    if cached:
        return cached

    start, end = resolve_date_range(period)
    repo = StatsRepository(db)

    trips = repo.trips_count(line_number, start, end)
    _check_line_exists(trips, line_number, period)

    rows = repo.max_route_delay(line_number, start, end)

    result = RouteDelayResponse(
        line_number=line_number,
        period=period.value,
        max_route_delay=[RouteDelay(**_to_str(row)) for row in rows],
        trips_analyzed=trips,
    )
    raw = cache.set_cached("route-delay", period, result, line_number)
    return Response(content=raw, media_type=JSON)


@router.get("/stats/summary")
def get_lines_summary(
    db: DbSession,
    period: PeriodQuery = Period.TODAY,
) -> Response:
    cached = _from_cache("summary", period)
    if cached:
        return cached

    start, end = resolve_date_range(period)
    repo = StatsRepository(db)

    rows = repo.lines_summary(start, end)

    result = LineSummaryResponse(
        period=period.value,
        lines=[LineSummary(**_to_str(r)) for r in rows],
    )
    raw = cache.set_cached("summary", period, result)
    return Response(content=raw, media_type=JSON)


@router.get("/{line_number}/stats/punctuality")
def get_punctuality(
    line_number: str,
    db: DbSession,
    period: PeriodQuery = Period.TODAY,
) -> Response:
    cached = _from_cache("punctuality", period, line_number)
    if cached:
        return cached

    start, end = resolve_date_range(period)
    repo = StatsRepository(db)

    trips = repo.trips_count(line_number, start, end)
    _check_line_exists(trips, line_number, period)

    row = repo.punctuality(line_number, start, end)
    total = row["total"]

    result = PunctualityResponse(
        line_number=line_number,
        period=period.value,
        total_trips=total,
        on_time_count=row["on_time"],
        on_time_percent=round(row["on_time"] / total * 100, 1) if total else 0.0,
        slightly_delayed_count=row["slightly_delayed"],
        slightly_delayed_percent=round(row["slightly_delayed"] / total * 100, 1) if total else 0.0,
        delayed_count=row["delayed"],
        delayed_percent=round(row["delayed"] / total * 100, 1) if total else 0.0,
    )
    raw = cache.set_cached("punctuality", period, result, line_number)
    return Response(content=raw, media_type=JSON)


@router.get("/{line_number}/stats/trend")
def get_trend(
    line_number: str,
    db: DbSession,
    period: PeriodQuery = Period.MONTH,
) -> Response:
    cached = _from_cache("trend", period, line_number)
    if cached:
        return cached

    start, end = resolve_date_range(period)
    repo = StatsRepository(db)

    trips = repo.trips_count(line_number, start, end)
    _check_line_exists(trips, line_number, period)

    rows = repo.trend(line_number, start, end)

    result = TrendResponse(
        line_number=line_number,
        period=period.value,
        days=[TrendDay(**_to_str(r)) for r in rows],
    )
    raw = cache.set_cached("trend", period, result, line_number)
    return Response(content=raw, media_type=JSON)
