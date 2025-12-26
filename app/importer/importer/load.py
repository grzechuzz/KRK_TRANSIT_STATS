from __future__ import annotations

from pathlib import Path
from sqlalchemy import text
from app.common.app_common.db.session import engine


class LoadError(RuntimeError):
    pass


def load_static_gtfs(base_dir: str | Path) -> None:
    base_dir = Path(base_dir)

    for name in ("routes.txt", "stops.txt", "trips.txt", "stop_times.txt"):
        p = base_dir / name
        if not p.exists():
            raise LoadError(f"Missing file for load: {p}")

    with engine.begin() as conn:
        conn.execute(text("TRUNCATE current_stop_times"))
        conn.execute(text("TRUNCATE current_trips"))
        conn.execute(text("TRUNCATE current_stops"))
        conn.execute(text("TRUNCATE current_routes"))

        _copy(conn, "current_routes", base_dir / "routes.txt",
              ["route_id", "route_short_name"])

        _copy(conn, "current_stops", base_dir / "stops.txt",
              ["stop_id", "stop_name", "stop_code", "stop_desc", "stop_lat", "stop_lon"])

        _copy(conn, "current_trips", base_dir / "trips.txt",
              ["trip_id", "route_id", "direction_id", "headsign"])

        _copy(conn, "current_stop_times", base_dir / "stop_times.txt",
              ["trip_id", "stop_sequence", "stop_id", "arrival_seconds", "departure_seconds"])


def _copy(conn, table: str, file: Path, columns: list[str]) -> None:
    cols = ", ".join(columns)
    sql = f"COPY {table} ({cols}) FROM STDIN WITH (FORMAT CSV, HEADER TRUE)"

    try:
        raw = conn.connection
        with raw.cursor() as cur, open(file, "r", encoding="utf-8", newline="") as f:
            cur.copy_expert(sql, f)
    except OSError as e:
        raise LoadError(f"Failed to read {file}: {e}") from e
    except Exception as e:
        raise LoadError(f"COPY into {table} failed from {file}: {e}") from e
