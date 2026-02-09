from datetime import date

import redis

from app.common.constants import REDIS_SAVED_SEQS_TTL


class SavedSequencesRepository:
    def __init__(self, client: redis.Redis):
        self._redis = client

    @staticmethod
    def _key(agency: str, trip_id: str, service_date: date) -> str:
        return f"saved:{agency}:{trip_id}:{service_date.isoformat()}"

    def is_saved(self, agency: str, trip_id: str, service_date: date, stop_sequence: int) -> bool:
        return bool(self._redis.sismember(self._key(agency, trip_id, service_date), str(stop_sequence)))

    def mark_saved(self, agency: str, trip_id: str, service_date: date, stop_sequence: int) -> None:
        key = self._key(agency, trip_id, service_date)
        self._redis.sadd(key, str(stop_sequence))
        self._redis.expire(key, REDIS_SAVED_SEQS_TTL)
