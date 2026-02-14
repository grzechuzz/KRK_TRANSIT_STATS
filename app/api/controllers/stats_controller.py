from typing import Annotated

from fastapi import APIRouter, Depends, Response

from app.api.db import DbSession
from app.api.schemas import EndDateQuery, StartDateQuery
from app.api.services.stats_service import StatsService

router = APIRouter(prefix="/lines", tags=["statistics"])

JSON = "application/json"


def _get_service(db: DbSession) -> StatsService:
    return StatsService(db)


Stats = Annotated[StatsService, Depends(_get_service)]


@router.get("/{line_number}/stats/max-delay")
def get_max_delay_between_stops(
    line_number: str,
    service: Stats,
    start_date: StartDateQuery,
    end_date: EndDateQuery,
) -> Response:
    return Response(content=service.max_delay_between_stops(line_number, start_date, end_date), media_type=JSON)


@router.get("/{line_number}/stats/route-delay")
def get_route_delay(
    line_number: str,
    service: Stats,
    start_date: StartDateQuery,
    end_date: EndDateQuery,
) -> Response:
    return Response(content=service.route_delay(line_number, start_date, end_date), media_type=JSON)


@router.get("/{line_number}/stats/punctuality")
def get_punctuality(
    line_number: str,
    service: Stats,
    start_date: StartDateQuery,
    end_date: EndDateQuery,
) -> Response:
    return Response(content=service.punctuality(line_number, start_date, end_date), media_type=JSON)


@router.get("/{line_number}/stats/trend")
def get_trend(
    line_number: str,
    service: Stats,
    start_date: StartDateQuery,
    end_date: EndDateQuery,
) -> Response:
    return Response(content=service.trend(line_number, start_date, end_date), media_type=JSON)
