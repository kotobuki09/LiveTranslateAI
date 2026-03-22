from enum import Enum, auto


class AppState(Enum):
    IDLE = auto()
    STARTING = auto()
    LISTENING = auto()
    RECONNECTING = auto()
    ERROR = auto()
