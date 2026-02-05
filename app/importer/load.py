import csv
import zipfile
from collections.abc import Generator, Iterable
from pathlib import Path
from typing import Any

from sqlalchemy import delete
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.common.db.models import CurrentRoute, CurrentShape, CurrentStop, CurrentStopTime, CurrentTrip
from app.common.gtfs.timeparse import parse_gtfs_time_to_seconds

BATCH_SIZE = 5000


def load_gtfs_zip(session: Session, zip_path: Path, agency_id: str) -> None:
    """
    Load GTFS static data from ZIP file into current_* tables in DB. Clears existing data and loads fresh.
    """
    with zipfile.ZipFile(zip_path, "r") as zf:
        session.execute(delete(CurrentStopTime))
        session.execute(delete(CurrentShape))
        session.execute(delete(CurrentTrip))
        session.execute(delete(CurrentStop))
        session.execute(delete(CurrentRoute))
        session.flush()

        _load_routes(session, zf, agency_id)
        _load_stops(session, zf)
        _load_trips(session, zf)
        _load_stop_times(session, zf)
        _load_shapes(session, zf, agency_id)


def batch_iterator(iterable: Iterable[Any], batch_size: int = BATCH_SIZE) -> Generator[list[Any]]:
    batch = []
    for item in iterable:
        batch.append(item)
        if len(batch) >= batch_size:
            yield batch
            batch = []
    if batch:
        yield batch


def _load_routes(session: Session, zf: zipfile.ZipFile, agency_id: str) -> None:
    with zf.open("routes.txt") as f:
        reader = csv.DictReader(line.decode("utf-8-sig") for line in f)
        rows_gen = (
            {"route_id": row["route_id"], "agency_id": agency_id, "route_short_name": row["route_short_name"]}
            for row in reader
        )

        for batch in batch_iterator(rows_gen):
            stmt = insert(CurrentRoute).values(batch)
            stmt = stmt.on_conflict_do_update(
                index_elements=[CurrentRoute.route_id],
                set_={"agency_id": stmt.excluded.agency_id, "route_short_name": stmt.excluded.route_short_name},
            )
            session.execute(stmt)


def _load_stops(session: Session, zf: zipfile.ZipFile) -> None:
    with zf.open("stops.txt") as f:
        reader = csv.DictReader(line.decode("utf-8-sig") for line in f)
        rows_gen = (
            {
                "stop_id": row["stop_id"],
                "stop_name": row["stop_name"],
                "stop_code": row["stop_code"],
                "stop_desc": row["stop_desc"],
                "stop_lat": float(row["stop_lat"]),
                "stop_lon": float(row["stop_lon"]),
            }
            for row in reader
        )

        for batch in batch_iterator(rows_gen):
            stmt = insert(CurrentStop).values(batch)
            stmt = stmt.on_conflict_do_update(
                index_elements=[CurrentStop.stop_id],
                set_={
                    "stop_name": stmt.excluded.stop_name,
                    "stop_code": stmt.excluded.stop_code,
                    "stop_desc": stmt.excluded.stop_desc,
                    "stop_lat": stmt.excluded.stop_lat,
                    "stop_lon": stmt.excluded.stop_lon,
                },
            )
            session.execute(stmt)


def _load_trips(session: Session, zf: zipfile.ZipFile) -> None:
    with zf.open("trips.txt") as f:
        reader = csv.DictReader(line.decode("utf-8-sig") for line in f)
        rows_gen = (
            {
                "trip_id": row["trip_id"],
                "route_id": row["route_id"],
                "service_id": row["service_id"],
                "direction_id": int(row["direction_id"]),
                "headsign": row["trip_headsign"],
                "shape_id": row["shape_id"],
            }
            for row in reader
        )

        for batch in batch_iterator(rows_gen):
            stmt = insert(CurrentTrip).values(batch)
            stmt = stmt.on_conflict_do_update(
                index_elements=[CurrentTrip.trip_id],
                set_={
                    "route_id": stmt.excluded.route_id,
                    "service_id": stmt.excluded.service_id,
                    "direction_id": stmt.excluded.direction_id,
                    "headsign": stmt.excluded.headsign,
                    "shape_id": stmt.excluded.shape_id,
                },
            )
            session.execute(stmt)


def _load_stop_times(session: Session, zf: zipfile.ZipFile) -> None:
    with zf.open("stop_times.txt") as f:
        reader = csv.DictReader(line.decode("utf-8-sig") for line in f)
        rows_gen = (
            {
                "trip_id": row["trip_id"],
                "stop_sequence": int(row["stop_sequence"]),
                "stop_id": row["stop_id"],
                "arrival_seconds": parse_gtfs_time_to_seconds(row["arrival_time"]),
                "departure_seconds": parse_gtfs_time_to_seconds(row["departure_time"]),
            }
            for row in reader
        )

        for batch in batch_iterator(rows_gen):
            stmt = insert(CurrentStopTime).values(batch)
            stmt = stmt.on_conflict_do_nothing(index_elements=[CurrentStopTime.trip_id, CurrentStopTime.stop_sequence])
            session.execute(stmt)


def _load_shapes(session: Session, zf: zipfile.ZipFile, agency_id: str) -> None:
    with zf.open("shapes.txt") as f:
        reader = csv.DictReader(line.decode("utf-8-sig") for line in f)
        rows_gen = (
            {
                "agency_id": agency_id,
                "shape_id": row["shape_id"],
                "shape_pt_lat": float(row["shape_pt_lat"]),
                "shape_pt_lon": float(row["shape_pt_lon"]),
                "shape_pt_sequence": int(row["shape_pt_sequence"]),
            }
            for row in reader
        )

        for batch in batch_iterator(rows_gen):
            session.execute(insert(CurrentShape).values(batch))
