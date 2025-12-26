from sqlalchemy import text
from app.common.app_common.db.session import engine


def get_current_static_hash() -> str | None:
    """
    Returns current static hash from gtfs_meta (id=1),
    or None if not set yet.
    """
    with engine.connect() as conn:
        return conn.execute(
            text("SELECT current_hash FROM gtfs_meta WHERE id = 1")
        ).scalar_one_or_none()


def set_current_static_hash(new_hash: str) -> None:
    """
    Inserts or updates current static hash in gtfs_meta (id=1).
    """
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO gtfs_meta (id, current_hash)
                VALUES (1, :h)
                ON CONFLICT (id) DO UPDATE
                SET current_hash = EXCLUDED.current_hash,
                    updated_at = now()
                """
            ),
            {"h": new_hash}
        )
