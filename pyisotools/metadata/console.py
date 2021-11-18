from enum import Enum, IntEnum


class ConsoleMagic(IntEnum):
    """
    Identifies the console type for a disc
    """
    GCN = 0xC2339F3D
    WII = 0x5D1C9EA3


class ConsoleKind(Enum):
    """
    Used for picking Kind specific data, like the common AES key
    """
    RETAIL = "Retail"
    KOREAN = "Korean"
    DEBUG = "Debug"
