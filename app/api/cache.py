import msgspec
import redis

from app.api.schemas import Period
from app.common.constants import CACHE_TTL_MONTH, CACHE_TTL_TODAY, CACHE_TTL_WEEK
from app.common.redis.connection import get_client

_TTL: dict[Period, int] = {
    Period.TODAY: CACHE_TTL_TODAY,
    Period.WEEK: CACHE_TTL_WEEK,
    Period.MONTH: CACHE_TTL_MONTH,
}


def _key(endpoint: str, period: Period, line_number: str = "") -> str:
    if line_number:
        return f"stats:{endpoint}:{line_number}:{period.value}"
    return f"stats:{endpoint}:{period.value}"


def get_cached(endpoint: str, period: Period, line_number: str = "") -> bytes | None:
    try:
        client = get_client()
        return client.get(_key(endpoint, period, line_number))  # type: ignore
    except redis.RedisError:
        return None


def set_cached(endpoint: str, period: Period, data: msgspec.Struct, line_number: str = "") -> bytes:
    raw = msgspec.json.encode(data)
    try:
        client = get_client()
        client.setex(_key(endpoint, period, line_number), _TTL[period], raw)
    except redis.RedisError:
        pass
    return raw
