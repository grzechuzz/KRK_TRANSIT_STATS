import csv
import io
import logging
import zipfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy import delete, select, text
from sqlalchemy.orm import Session

from app.common.db.models import CurrentRoute, CurrentShape, CurrentStop, CurrentStopTime, CurrentTrip
from app.common.gtfs.timeparse import parse_gtfs_time_to_seconds

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TableMapping:
    """Configuration for loading a GTFS file into a database table."""

    gtfs_file: str
    table_name: str
    columns: list[str]
    row_transformer: Callable[[dict[str, str], str], list[Any]]


def _routes_transformer(row: dict[str, str], agency_id: str) -> list[Any]:
    return [row["route_id"], agency_id, row["route_short_name"]]


def _stops_transformer(row: dict[str, str], agency_id: str) -> list[Any]:
    return [row["stop_id"], row["stop_name"], row["stop_code"], row["stop_desc"], row["stop_lat"], row["stop_lon"]]


def _trips_transformer(row: dict[str, str], agency_id: str) -> list[Any]:
    return [
        row["trip_id"],
        row["route_id"],
        row["service_id"],
        row["direction_id"],
        row["trip_headsign"],
        row["shape_id"],
    ]


def _stop_times_transformer(row: dict[str, str], agency_id: str) -> list[Any]:
    return [
        row["trip_id"],
        row["stop_sequence"],
        row["stop_id"],
        parse_gtfs_time_to_seconds(row["arrival_time"]),
        parse_gtfs_time_to_seconds(row["departure_time"]),
    ]


def _shapes_transformer(row: dict[str, str], agency_id: str) -> list[Any]:
    return [agency_id, row["shape_id"], row["shape_pt_lat"], row["shape_pt_lon"], row["shape_pt_sequence"]]


TABLE_MAPPINGS = [
    TableMapping("routes.txt", "current_routes", ["route_id", "agency_id", "route_short_name"], _routes_transformer),
    TableMapping(
        "stops.txt",
        "current_stops",
        ["stop_id", "stop_name", "stop_code", "stop_desc", "stop_lat", "stop_lon"],
        _stops_transformer,
    ),
    TableMapping(
        "trips.txt",
        "current_trips",
        ["trip_id", "route_id", "service_id", "direction_id", "headsign", "shape_id"],
        _trips_transformer,
    ),
    TableMapping(
        "stop_times.txt",
        "current_stop_times",
        ["trip_id", "stop_sequence", "stop_id", "arrival_seconds", "departure_seconds"],
        _stop_times_transformer,
    ),
    TableMapping(
        "shapes.txt",
        "current_shapes",
        ["agency_id", "shape_id", "shape_pt_lat", "shape_pt_lon", "shape_pt_sequence"],
        _shapes_transformer,
    ),
]


def _delete_agency_data(session: Session, agency_id: str) -> None:
    """Delete all GTFS static data for agency"""
    logger.info(f"[{agency_id}] Deleting old data...")

    route_ids = [
        r[0] for r in session.execute(select(CurrentRoute.route_id).where(CurrentRoute.agency_id == agency_id)).all()
    ]

    if not route_ids:
        logger.info(f"[{agency_id}] No existing data")
        return

    trip_ids = [
        t[0] for t in session.execute(select(CurrentTrip.trip_id).where(CurrentTrip.route_id.in_(route_ids))).all()
    ]

    stop_ids = [
        s[0]
        for s in session.execute(
            select(CurrentStopTime.stop_id).where(CurrentStopTime.trip_id.in_(trip_ids)).distinct()
        ).all()
    ]

    if trip_ids:
        session.execute(delete(CurrentStopTime).where(CurrentStopTime.trip_id.in_(trip_ids)))

        session.execute(delete(CurrentTrip).where(CurrentTrip.trip_id.in_(trip_ids)))

    session.execute(delete(CurrentRoute).where(CurrentRoute.route_id.in_(route_ids)))

    session.execute(delete(CurrentShape).where(CurrentShape.agency_id == agency_id))

    if stop_ids:
        session.execute(delete(CurrentStop).where(CurrentStop.stop_id.in_(stop_ids)))

    session.flush()

    logger.info(f"[{agency_id}] Delete complete")


def _copy_to_table(session: Session, table_name: str, columns: list[str], data: io.StringIO) -> None:
    """
    Previously I used simple batch insert but it was sooooo slow, now using COPY
    """
    raw_conn = session.connection().connection.dbapi_connection
    if raw_conn is None:
        raise RuntimeError("No database connection available")

    cursor = raw_conn.cursor()
    data.seek(0)

    with cursor.copy(f"COPY {table_name} ({','.join(columns)}) FROM STDIN WITH (FORMAT CSV)") as copy:
        copy.write(data.getvalue())


def _upsert_via_copy(
    session: Session, table_name: str, columns: list[str], data: io.StringIO, pk_columns: list[str]
) -> None:
    raw_conn = session.connection().connection.dbapi_connection
    if raw_conn is None:
        raise RuntimeError("No database connection available")

    cursor = raw_conn.cursor()
    temp_table = f"tmp_{table_name}"
    session.execute(
        text(f"CREATE TEMP TABLE IF NOT EXISTS {temp_table} (LIKE {table_name} INCLUDING DEFAULTS) ON COMMIT DROP")
    )
    session.execute(text(f"TRUNCATE {temp_table}"))

    data.seek(0)
    columns_fmt = ",".join(columns)

    with cursor.copy(f"COPY {temp_table} ({columns_fmt}) FROM STDIN WITH (FORMAT CSV)") as copy:
        copy.write(data.getvalue())

    update_set = ", ".join([f"{col} = EXCLUDED.{col}" for col in columns if col not in pk_columns])
    conflict_target = ", ".join(pk_columns)

    sql = f"""
        INSERT INTO {table_name} ({columns_fmt})
        SELECT {columns_fmt} FROM {temp_table}
        ON CONFLICT ({conflict_target})
        DO UPDATE SET {update_set}
    """
    session.execute(text(sql))


def _load_table(session: Session, zf: zipfile.ZipFile, mapping: TableMapping, agency_id: str) -> None:
    logger.info(f"[{agency_id}] Loading {mapping.gtfs_file}...")

    buf = io.StringIO()
    writer = csv.writer(buf)
    seen_ids = set()

    with zf.open(mapping.gtfs_file) as f:
        reader = csv.DictReader(line.decode("utf-8-sig") for line in f)
        for row in reader:
            transformed_row = mapping.row_transformer(row, agency_id)
            row_id = transformed_row[0]

            if row_id in seen_ids:
                continue

            seen_ids.add(row_id)
            writer.writerow(transformed_row)

    if mapping.table_name == "current_stops":
        _upsert_via_copy(session, mapping.table_name, mapping.columns, buf, pk_columns=["stop_id"])
    elif mapping.table_name == "current_routes":
        _upsert_via_copy(session, mapping.table_name, mapping.columns, buf, pk_columns=["route_id"])
    else:
        _copy_to_table(session, mapping.table_name, mapping.columns, buf)


def load_gtfs_zip(session: Session, zip_path: Path, agency_id: str) -> None:
    """Load GTFS static data."""
    logger.info(f"[{agency_id}] Opening ZIP: {zip_path}")

    with zipfile.ZipFile(zip_path, "r") as zf:
        _delete_agency_data(session, agency_id)

        for mapping in TABLE_MAPPINGS:
            _load_table(session, zf, mapping, agency_id)

        logger.info(f"[{agency_id}] All data loaded, committing...")
