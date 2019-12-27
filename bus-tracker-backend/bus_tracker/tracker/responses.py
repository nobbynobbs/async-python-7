from dataclasses import dataclass, field
from typing import List

from bus_tracker.tracker.entities import Bus
from bus_tracker.tracker.json_encoder import dumps


@dataclass
class BaseMessage:
    # not ClassVar cuz we need it in json representation
    msgType: str = field(default="", init=False, repr=False)

    def json(self) -> str:
        return dumps(self)


@dataclass
class ErrorMessage(BaseMessage):
    msgType: str = field(default="Error", init=False, repr=False)
    errors: List[str]


@dataclass
class BusesMessage(BaseMessage):
    msgType: str = field(default="Buses", init=False, repr=False)
    buses: List[Bus]
