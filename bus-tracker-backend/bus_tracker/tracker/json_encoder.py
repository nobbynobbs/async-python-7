import functools
import json
import dataclasses
from typing import Any, Callable


class DataclassEncoder(json.JSONEncoder):
    """custom encoder supporting dataclasses instances"""
    def default(self, o: Any) -> Any:
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)


dumps: Callable[[Any], str] = functools.partial(
    json.dumps, cls=DataclassEncoder
)
