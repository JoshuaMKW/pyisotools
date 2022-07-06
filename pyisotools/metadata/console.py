from enum import Enum, IntEnum, auto


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


class Platform(IntEnum):
    GAMECUBEDISC = 0,
    WIIDISC = 1
    WIIWAD = 2
    ELFORDOL = 3
    NUMBEROFPLATFORMS = 4

    def is_disc(self) -> bool:
        """
        Is this platform type a disc?
        """
        return self == Platform.GAMECUBEDISC or self == Platform.WIIDISC

    def is_gcn(self) -> bool:
        """
        Is this platform type a Gamecube disc?
        """
        return self == Platform.GAMECUBEDISC

    def is_wii(self) -> bool:
        """
        Is this platform type a wii disc/wad?
        """
        return self == Platform.WIIDISC or self == Platform.WIIWAD