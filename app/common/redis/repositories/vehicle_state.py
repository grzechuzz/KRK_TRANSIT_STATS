import redis

from app.common.constants import REDIS_VEHICLE_STATE_TTL
from app.common.redis import serializer
from app.common.redis.schemas import VehicleState


class VehicleStateRepository:
    def __init__(self, client: redis.Redis):
        self._redis = client

    @staticmethod
    def _key(agency: str, license_plate: str) -> str:
        return f"vs:{agency}:{license_plate}"

    def get(self, agency: str, license_plate: str) -> VehicleState | None:
        data: bytes | None = self._redis.get(self._key(agency, license_plate))  # type: ignore[assignment]
        if data is None:
            return None
        try:
            return serializer.decode_vehicle_state(data)
        except Exception:
            return None

    def save(self, state: VehicleState) -> None:
        key = self._key(state.agency, state.license_plate)
        self._redis.setex(key, REDIS_VEHICLE_STATE_TTL, serializer.encode(state))

    def delete(self, agency: str, license_plate: str) -> None:
        self._redis.delete(self._key(agency, license_plate))
