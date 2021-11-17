from enum import Enum, IntEnum
from typing import Union


class IDKind(IntEnum):
    SYSTEM = 0x00001
    DISC = 0x10000
    VIRTUAL = 0x10001
    CHANNEL = 0x10001
    SYSTEM_CHANNEL = 0x10002
    DLC = 0x10005
    HIDDEN = 0x10008


def __construct_title_id(__kind: IDKind, __id: Union[int, bytes]) -> int:
    """
    Returns a complete title ID as an int
    """
    __kind <<= 32
    if isinstance(id, bytes):
        return __kind | int.from_bytes(id, "big", signed=False)
    return __kind | id
    

def __cmp_ord_at(__num: int, __idx: int, __chr: str) -> bool:
    """
    Check if the ordinal of __chr matches the byte at __idx of __int
    """
    assert len(__chr) == 1, "__chr isn't ord() compatible!"
    return (__num >> (__idx * 8)) == ord(__chr)


class RegionCode(Enum):
    ALL_REGIONS = "A"
    WIIWARE_B = "B"
    CHINA_EMU = "C"
    DVDX_V7 = "C"
    GERMAN = "D"
    NTSC = "E"
    FRENCH = "F"
    ITALIAN = "I"
    HOMEBREW = "I"
    JAPAN = "J"
    KOREA = "K"
    JAPAN_EU = "L"
    USA_EU = "M"
    JAPAN_USA = "N"
    PAL = "P"
    KOREA_JP = "Q"
    SPANISH = "S"
    KOREA_USA = "T"
    WIIWARE_U = "U"
    TAIWAN = "W"
    WIIWARE_X = "X"
    DVDX_OLD = "X"
    HOMEBREW_OLD = "X"


class SystemCode(Enum):
    COMMODORE_64 = "C"
    DEMO_DISC = "D"
    ARCADE = "E"
    NEOGEO = "E"
    NES = "F"
    GAMECUBE_DISC = "G"
    GENERAL_CHANNEL = "H"
    SNES = "J"
    MASTER_SYSTEM = "L"
    MEGADRIVE = "M"
    N64 = "N"
    PROMO_DISC = "P"
    TURBOGRAFX = "P"
    TURBOGRAFX_CD = "Q"
    WII_DISC_OLD = "R"
    WII_DISC_NEW = "S"
    WIIWARE = "W"
    WIIWARE_DEMO = "X"
    MSX = "X"


class SystemTitleID(Enum):
    """
    IDs that fall under 0x10000
    """
    BOOT2 = __construct_title_id(IDKind.SYSTEM, 0x00000001)
    SYSTEM_MENU = __construct_title_id(IDKind.SYSTEM, 0x00000002)
    BC = __construct_title_id(IDKind.SYSTEM, 0x00000100)
    MIOS = __construct_title_id(IDKind.SYSTEM, 0x00000101)
    BC_NAND = __construct_title_id(IDKind.SYSTEM, 0x00000200)
    BC_WFS = __construct_title_id(IDKind.SYSTEM, 0x00000201)


class DiscTitleID(Enum):
    """
    IDs that fall under 0x10001
    """
    BOOT2_UPDATER = __construct_title_id(IDKind.DISC, b"0000")
    DATACHK = __construct_title_id(IDKind.DISC, b"0002")
    FACTORY_TITLE = __construct_title_id(IDKind.DISC, b"0003")
    UPDATE_PARTITION = __construct_title_id(IDKind.DISC, b".UPE")
    CHANNEL_INSTALLER = __construct_title_id(IDKind.DISC, b".INS")
    PHOTO_CHANNEL = __construct_title_id(IDKind.DISC, b"HAZA")


class SystemChannelID(Enum):
    """
    IDs that fall under 0x10002 (WII_MESSAGE_BOARD is the exception)
    """
    PHOTO_CHANNEL_1 = __construct_title_id(IDKind.SYSTEM_CHANNEL, b"HAAA")
    SHOPPING_CHANNEL = __construct_title_id(IDKind.SYSTEM_CHANNEL, b"HABA")
    SHOPPING_CHANNEL_K = __construct_title_id(IDKind.SYSTEM_CHANNEL, b"HABK")
    MII_CHANNEL = __construct_title_id(IDKind.SYSTEM_CHANNEL, b"HACA")
    MII_CHANNEL_K = __construct_title_id(IDKind.SYSTEM_CHANNEL, b"HACK")
    WEATHER_CHANNEL = __construct_title_id(IDKind.SYSTEM_CHANNEL, b"HAFA")
    NEWS_CHANNEL = __construct_title_id(IDKind.SYSTEM_CHANNEL, b"HAGA")
    PHOTO_CHANNEL_2 = __construct_title_id(IDKind.SYSTEM_CHANNEL, b"HAYA")
    PHOTO_CHANNEL_2_K = __construct_title_id(IDKind.SYSTEM_CHANNEL, b"HAYK")
    WII_MESSAGE_BOARD = __construct_title_id(IDKind.CHANNEL, b"HAEA")


class GameChannelID(Enum):
    """
    IDs that fall under 0x10004
    """
    WII_FIT_CHANNEL_U = __construct_title_id(IDKind.SYSTEM_CHANNEL, b"RFNU")
    WII_FIT_CHANNEL_J = __construct_title_id(IDKind.SYSTEM_CHANNEL, b"RFNJ")
    WII_FIT_CHANNEL_P = __construct_title_id(IDKind.SYSTEM_CHANNEL, b"RFNP")
    WII_FIT_CHANNEL_K = __construct_title_id(IDKind.SYSTEM_CHANNEL, b"RFNK")
    WII_FIT_PLUS_CHANNEL_U = __construct_title_id(
        IDKind.SYSTEM_CHANNEL, b"RFPU")
    WII_FIT_PLUS_CHANNEL_J = __construct_title_id(
        IDKind.SYSTEM_CHANNEL, b"RFPJ")
    WII_FIT_PLUS_CHANNEL_P = __construct_title_id(
        IDKind.SYSTEM_CHANNEL, b"RFPP")
    WII_FIT_PLUS_CHANNEL_K = __construct_title_id(
        IDKind.SYSTEM_CHANNEL, b"RFPK")
    MARIO_KART_CHANNEL_U = __construct_title_id(IDKind.SYSTEM_CHANNEL, b"RMCU")
    MARIO_KART_CHANNEL_J = __construct_title_id(IDKind.SYSTEM_CHANNEL, b"RMCJ")
    MARIO_KART_CHANNEL_P = __construct_title_id(IDKind.SYSTEM_CHANNEL, b"RMCP")
    MARIO_KART_CHANNEL_K = __construct_title_id(IDKind.SYSTEM_CHANNEL, b"RMCK")
    RABBIDS_CHANNEL = __construct_title_id(IDKind.CHANNEL, b"RGWX")


class HiddenChannelID(Enum):
    """
    IDs that fall under 0x10008
    """
    PERSONAL_DATA_CHANNEL = __construct_title_id(IDKind.HIDDEN, b"HCCJ")
    EULA_U = __construct_title_id(IDKind.HIDDEN, b"HAKU")
    EULA_J = __construct_title_id(IDKind.HIDDEN, b"HAKJ")
    EULA_P = __construct_title_id(IDKind.HIDDEN, b"HAKP")
    EULA_K = __construct_title_id(IDKind.HIDDEN, b"HAKK")
    REGION_SELECT_U = __construct_title_id(IDKind.HIDDEN, b"HALU")
    REGION_SELECT_J = __construct_title_id(IDKind.HIDDEN, b"HALJ")
    REGION_SELECT_P = __construct_title_id(IDKind.HIDDEN, b"HALP")
    REGION_SELECT_K = __construct_title_id(IDKind.HIDDEN, b"HALK")
    MYSTERY_CHANNEL_U = __construct_title_id(IDKind.HIDDEN, b"HCZU")
    MYSTERY_CHANNEL_J = __construct_title_id(IDKind.HIDDEN, b"HCZJ")
    MYSTERY_CHANNEL_P = __construct_title_id(IDKind.HIDDEN, b"HCZP")
    MYSTERY_CHANNEL_K = __construct_title_id(IDKind.HIDDEN, b"HCZK")


class TitleIDInfo():
    """
    `title` methods work upon the upper 32 bits of a title id

    `id` methods work opon the lower 32 bits of a title id
    """
    @staticmethod
    def predict_id_region(id: int) -> RegionCode:
        try:
            return RegionCode(chr(id & 0xFF))
        except ValueError:
            return None

    @staticmethod
    def is_title_system(id: int) -> bool:
        return (id >> 32) == IDKind.SYSTEM

    @staticmethod
    def is_title_disc(id: int) -> bool:
        return (id >> 32) == IDKind.DISC

    @staticmethod
    def is_title_virtual(id: int) -> bool:
        return (id >> 32) == IDKind.VIRTUAL

    @staticmethod
    def is_title_channel(id: int) -> bool:
        return (id >> 32) == IDKind.CHANNEL

    @staticmethod
    def is_title_system_channel(id: int) -> bool:
        return (id >> 32) == IDKind.SYSTEM_CHANNEL

    @staticmethod
    def is_title_dlc(id: int) -> bool:
        return (id >> 32) == IDKind.DLC

    @staticmethod
    def is_title_hidden(id: int) -> bool:
        return (id >> 32) == IDKind.HIDDEN

    @staticmethod
    def is_id_arcade(id: int) -> bool:
        return TitleIDInfo.is_title_virtual() and __cmp_ord_at(id, 3, 'E') and not __cmp_ord_at(id, 2, 'A')

    @staticmethod
    def is_id_neogeo(id: int) -> bool:
        return TitleIDInfo.is_title_virtual() and __cmp_ord_at(id, 3, 'E') and __cmp_ord_at(id, 2, 'A')

    @staticmethod
    def is_id_nes(id: int) -> bool:
        return TitleIDInfo.is_title_virtual() and __cmp_ord_at(id, 3, 'F')

    @staticmethod
    def is_id_channel(id: int) -> bool:
        return TitleIDInfo.is_title_virtual() and __cmp_ord_at(id, 3, 'H')

    @staticmethod
    def is_id_snes(id: int) -> bool:
        return TitleIDInfo.is_title_virtual() and __cmp_ord_at(id, 3, 'J')

    @staticmethod
    def is_id_master_system(id: int) -> bool:
        return TitleIDInfo.is_title_virtual() and __cmp_ord_at(id, 3, 'L')

    @staticmethod
    def is_id_genesis(id: int) -> bool:
        return TitleIDInfo.is_title_virtual() and __cmp_ord_at(id, 3, 'M')

    @staticmethod
    def is_id_n64(id: int) -> bool:
        return TitleIDInfo.is_title_virtual() and __cmp_ord_at(id, 3, 'N')

    @staticmethod
    def is_id_turbografx_16(id: int) -> bool:
        return TitleIDInfo.is_title_virtual() and __cmp_ord_at(id, 3, 'P')

    @staticmethod
    def is_id_turbografx_cd(id: int) -> bool:
        return TitleIDInfo.is_title_virtual() and __cmp_ord_at(id, 3, 'Q')

    @staticmethod
    def is_id_wiiware(id: int) -> bool:
        return TitleIDInfo.is_title_virtual() and __cmp_ord_at(id, 3, 'W')

    @staticmethod
    def is_id_msx(id: int) -> bool:
        return TitleIDInfo.is_title_virtual() and __cmp_ord_at(id, 3, 'X') and not __cmp_ord_at(id, 2, 'H')

    @staticmethod
    def is_id_wiiware_demo(id: int) -> bool:
        return TitleIDInfo.is_title_virtual() and __cmp_ord_at(id, 3, 'X') and __cmp_ord_at(id, 2, 'H')

    @staticmethod
    def construct_title_id(kind: IDKind, id: Union[int, bytes]) -> int:
        """
        Returns a complete title ID as an int
        """
        return __construct_title_id(kind, id)
