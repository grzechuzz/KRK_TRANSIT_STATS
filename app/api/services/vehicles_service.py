import msgspec

from app.api.repositories.vehicles_repository import fetch_all_positions, load_trip_info
from app.api.schemas import LiveVehicle, LiveVehicleResponse


def get_live_vehicles() -> bytes:
    positions = fetch_all_positions()
    trip_info = load_trip_info()

    vehicles: list[LiveVehicle] = []
    for vp in positions:
        if not vp.has_position or not vp.license_plate:
            continue

        info = trip_info.get(vp.trip_id)
        if not info:
            continue

        vehicles.append(
            LiveVehicle(
                license_plate=vp.license_plate,
                line_number=info[0],
                headsign=info[1],
                latitude=vp.latitude,
                longitude=vp.longitude,
                bearing=vp.bearing,
                timestamp=vp.timestamp.isoformat(),
            )
        )

    return msgspec.json.encode(LiveVehicleResponse(count=len(vehicles), vehicles=vehicles))
