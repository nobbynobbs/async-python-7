import dataclasses
from typing import Tuple

MIN_LAT: float = -90  # south pole
MAX_LAT: float = +90  # north pole
MIN_LNG: float = -180  # west
MAX_LNG: float = +180  # east


@dataclasses.dataclass
class Bus:
    busId: str
    route: str
    lat: float
    lng: float

    @property
    def position(self) -> Tuple[float, float]:
        return self.lat, self.lng


@dataclasses.dataclass
class WindowBounds:
    south_lat: float = MIN_LAT
    north_lat: float = MAX_LAT
    west_lng: float = MIN_LNG
    east_lng: float = MAX_LNG

    def update(
            self,
            south_lat: float,
            north_lat: float,
            west_lng: float,
            east_lng: float
    ) -> None:
        self.south_lat = south_lat
        self.north_lat = north_lat
        self.west_lng = west_lng
        self.east_lng = east_lng

    def contains(self, lat: float, lng: float) -> bool:
        return (self.south_lat < lat < self.north_lat
                and self.west_lng < lng < self.east_lng)
