import os
import json
from typing import Generator, Any


def load_routes(directory_path: str = 'routes') -> Generator[Any, None, None]:
    # TODO: add good typing for yield type
    filenames = (f for f in os.listdir(directory_path) if f.endswith(".json"))
    for filename in filenames:
        filepath = os.path.join(directory_path, filename)
        with open(filepath, 'r', encoding='utf8') as file:
            yield json.load(file)


def generate_bus_id(route_id: str, bus_index: int = None) -> str:
    if bus_index is None:
        return route_id
    return f"{route_id}-{bus_index}"
