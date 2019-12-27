from typing import Dict, Any, Mapping

from bus_tracker.tracker.entities import Bus, WindowBounds
from bus_tracker.tracker.exceptions import ValidationError


def validate_bus_data(bus: Dict[str, Any]) -> None:
    ex = ValidationError("invalid bus data")
    if not isinstance(bus, Mapping):
        raise ex
    try:
        _ = Bus(**bus)  # if it's stupid but it works it's not stupid :)
    except TypeError:
        raise ex


def validate_bounds_message(message: Dict[str, Any]) -> None:
    required_keys = {"msgType", "data"}
    if message.keys() != required_keys:
        sorted_keys = sorted(required_keys)
        raise ValidationError(f"Unexpected keys, {sorted_keys} expected")
    if message["msgType"] != "newBounds":
        raise ValidationError("Unsupported msgType")
    validate_bounds_data(message["data"])


def validate_bounds_data(bounds: Dict[str, float]) -> None:
    ex = ValidationError("invalid bounds data")
    if not isinstance(bounds, Mapping):
        raise ex
    try:
        _ = WindowBounds(**bounds)
    except TypeError:
        raise ex
