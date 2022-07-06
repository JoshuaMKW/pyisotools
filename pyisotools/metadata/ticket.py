import json
from dataclasses import dataclass
from enum import Enum, IntEnum
from io import BytesIO
from typing import List, Union

from Crypto.Cipher import AES

from pyisotools.security import COMMON_AES_KEY
from pyisotools.gui.workpathing import resource_path
from pyisotools.metadata.console import ConsoleKind
from pyisotools.metadata.region import RegionCode, SystemCode
from pyisotools.security.certificate import Certificate
from pyisotools.security.signature import Signature, SignatureRSA2048, SigType
from pyisotools.tools import bytes_to_string


class CommonKey(IntEnum):
    DEFAULT = 0
    KOREAN = 1
    V_WII = 2


class TicketID(IntEnum):
    SYSTEM = 0x00001
    DISC = 0x10000
    VIRTUAL = 0x10001
    CHANNEL = 0x10001
    SYSTEM_CHANNEL = 0x10002
    GAME_CHANNEL = 0x10004
    DLC = 0x10005
    HIDDEN = 0x10008


def __cmp_ord_at(__num: int, __idx: int, __chr: str) -> bool:
    """
    Check if the ordinal of __chr matches the byte at __idx of __int
    """
    assert len(__chr) == 1, "__chr isn't ord() compatible!"
    return (__num >> (__idx * 8)) == ord(__chr)


class TitleID(int):
    """
    `title` methods work upon the upper 32 bits of a title id

    `id` methods work opon the lower 32 bits of a title id
    """
    @classmethod
    def construct_title_id(cls, kind: TicketID, id: Union[int, bytes]) -> int:
        """
        Returns a complete title ID as an int
        """
        kind <<= 32
        if isinstance(id, bytes):
            return kind | int.from_bytes(id, "big", signed=False)
        return cls(kind | id)

    @classmethod
    def lookup_title_id(cls, name: str, local: bool = False) -> "TitleID":
        if local:
            with open(resource_path("data/title_db.json"), "r") as f:
                database: dict = json.load(f)

            for key, value in database.items():
                if value == name.strip():
                    return cls(key)
            return None
        else:
            raise NotImplementedError(
                "Database downloading not implemented yet!")

    def is_title_system(self) -> bool:
        return (self >> 32) == TicketID.SYSTEM

    def is_title_disc(self) -> bool:
        return (self >> 32) == TicketID.DISC

    def is_title_virtual(self) -> bool:
        return (self >> 32) == TicketID.VIRTUAL

    def is_title_channel(self) -> bool:
        return (self >> 32) == TicketID.CHANNEL

    def is_title_system_channel(self) -> bool:
        return (self >> 32) == TicketID.SYSTEM_CHANNEL

    def is_title_dlc(self) -> bool:
        return (self >> 32) == TicketID.DLC

    def is_title_hidden(self) -> bool:
        return (self >> 32) == TicketID.HIDDEN

    def is_id_arcade(self) -> bool:
        return self.is_title_virtual() and __cmp_ord_at(self, 3, SystemCode.ARCADE) and not __cmp_ord_at(self, 2, 'A')

    def is_id_neogeo(self) -> bool:
        return self.is_title_virtual() and __cmp_ord_at(self, 3, SystemCode.NEOGEO) and __cmp_ord_at(self, 2, 'A')

    def is_id_nes(self) -> bool:
        return self.is_title_virtual() and __cmp_ord_at(self, 3, SystemCode.NES)

    def is_id_channel(self) -> bool:
        return self.is_title_virtual() and __cmp_ord_at(self, 3, SystemCode.GENERAL_CHANNEL)

    def is_id_snes(self) -> bool:
        return self.is_title_virtual() and __cmp_ord_at(self, 3, SystemCode.SNES)

    def is_id_master_system(self) -> bool:
        return self.is_title_virtual() and __cmp_ord_at(self, 3, SystemCode.MASTER_SYSTEM)

    def is_id_genesis(self) -> bool:
        return self.is_title_virtual() and __cmp_ord_at(self, 3, SystemCode.GENESIS)

    def is_id_n64(self) -> bool:
        return self.is_title_virtual() and __cmp_ord_at(self, 3, SystemCode.N64)

    def is_id_turbografx_16(self) -> bool:
        return self.is_title_virtual() and __cmp_ord_at(self, 3, SystemCode.TURBOGRAFX)

    def is_id_turbografx_cd(self) -> bool:
        return self.is_title_virtual() and __cmp_ord_at(self, 3, SystemCode.TURBOGRAFX_CD)

    def is_id_wiiware(self) -> bool:
        return self.is_title_virtual() and __cmp_ord_at(self, 3, SystemCode.WIIWARE)

    def is_id_msx(self) -> bool:
        return self.is_title_virtual() and __cmp_ord_at(self, 3, SystemCode.MSX) and not __cmp_ord_at(self, 2, 'H')

    def is_id_wiiware_demo(self) -> bool:
        return self.is_title_virtual() and __cmp_ord_at(self, 3, SystemCode.WIIWARE_DEMO) and __cmp_ord_at(self, 2, 'H')

    def predict_id_region(self) -> RegionCode:
        try:
            return RegionCode(chr(self & 0xFF))
        except ValueError:
            return None

    def lookup_name(self, local: bool = True) -> str:
        if local:
            with open(resource_path("data/title_db.json"), "r") as f:
                database: dict = json.load(f)

            try:
                return database[str(self)]
            except KeyError:
                return None
        else:
            raise NotImplementedError(
                "Database downloading not implemented yet!")

    def __str__(self) -> str:
        rawID = self.to_bytes(4, "big", signed=False)
        titleID = bytes_to_string(rawID) if rawID.isalnum() else f"{self:08X}"
        return f"{self >> 32:08X}-{titleID}"


class TitleEnum(TitleID, Enum):
    """
    Special Enum describing pre-defined TitleIDs
    """


class SystemTitleID(TitleEnum):
    """
    IDs that fall under 0x10000
    """
    BOOT2 = TitleID.construct_title_id(TicketID.SYSTEM, 0x00000001)
    SYSTEM_MENU = TitleID.construct_title_id(TicketID.SYSTEM, 0x00000002)
    BC = TitleID.construct_title_id(TicketID.SYSTEM, 0x00000100)
    MIOS = TitleID.construct_title_id(TicketID.SYSTEM, 0x00000101)
    BC_NAND = TitleID.construct_title_id(TicketID.SYSTEM, 0x00000200)
    BC_WFS = TitleID.construct_title_id(TicketID.SYSTEM, 0x00000201)


class DiscTitleID(TitleEnum):
    """
    IDs that fall under 0x10001
    """
    BOOT2_UPDATER = TitleID.construct_title_id(TicketID.DISC, b"0000")
    DATACHK = TitleID.construct_title_id(TicketID.DISC, b"0002")
    FACTORY_TITLE = TitleID.construct_title_id(TicketID.DISC, b"0003")
    UPDATE_PARTITION = TitleID.construct_title_id(TicketID.DISC, b".UPE")
    CHANNEL_INSTALLER = TitleID.construct_title_id(TicketID.DISC, b".INS")
    PHOTO_CHANNEL = TitleID.construct_title_id(TicketID.DISC, b"HAZA")


class SystemChannelID(TitleEnum):
    """
    IDs that fall under 0x10002 (WII_MESSAGE_BOARD is the exception)
    """
    PHOTO_CHANNEL_1 = TitleID.construct_title_id(TicketID.SYSTEM_CHANNEL, b"HAAA")
    SHOPPING_CHANNEL = TitleID.construct_title_id(TicketID.SYSTEM_CHANNEL, b"HABA")
    SHOPPING_CHANNEL_K = TitleID.construct_title_id(TicketID.SYSTEM_CHANNEL, b"HABK")
    MII_CHANNEL = TitleID.construct_title_id(TicketID.SYSTEM_CHANNEL, b"HACA")
    MII_CHANNEL_K = TitleID.construct_title_id(TicketID.SYSTEM_CHANNEL, b"HACK")
    WEATHER_CHANNEL = TitleID.construct_title_id(TicketID.SYSTEM_CHANNEL, b"HAFA")
    NEWS_CHANNEL = TitleID.construct_title_id(TicketID.SYSTEM_CHANNEL, b"HAGA")
    PHOTO_CHANNEL_2 = TitleID.construct_title_id(TicketID.SYSTEM_CHANNEL, b"HAYA")
    PHOTO_CHANNEL_2_K = TitleID.construct_title_id(TicketID.SYSTEM_CHANNEL, b"HAYK")
    WII_MESSAGE_BOARD = TitleID.construct_title_id(TicketID.CHANNEL, b"HAEA")


class GameChannelID(TitleEnum):
    """
    IDs that fall under 0x10004
    """
    WII_FIT_CHANNEL_U = TitleID.construct_title_id(TicketID.SYSTEM_CHANNEL, b"RFNU")
    WII_FIT_CHANNEL_J = TitleID.construct_title_id(TicketID.SYSTEM_CHANNEL, b"RFNJ")
    WII_FIT_CHANNEL_P = TitleID.construct_title_id(TicketID.SYSTEM_CHANNEL, b"RFNP")
    WII_FIT_CHANNEL_K = TitleID.construct_title_id(TicketID.SYSTEM_CHANNEL, b"RFNK")
    WII_FIT_PLUS_CHANNEL_U = TitleID.construct_title_id(
        TicketID.SYSTEM_CHANNEL, b"RFPU")
    WII_FIT_PLUS_CHANNEL_J = TitleID.construct_title_id(
        TicketID.SYSTEM_CHANNEL, b"RFPJ")
    WII_FIT_PLUS_CHANNEL_P = TitleID.construct_title_id(
        TicketID.SYSTEM_CHANNEL, b"RFPP")
    WII_FIT_PLUS_CHANNEL_K = TitleID.construct_title_id(
        TicketID.SYSTEM_CHANNEL, b"RFPK")
    MARIO_KART_CHANNEL_U = TitleID.construct_title_id(
        TicketID.SYSTEM_CHANNEL, b"RMCU")
    MARIO_KART_CHANNEL_J = TitleID.construct_title_id(
        TicketID.SYSTEM_CHANNEL, b"RMCJ")
    MARIO_KART_CHANNEL_P = TitleID.construct_title_id(
        TicketID.SYSTEM_CHANNEL, b"RMCP")
    MARIO_KART_CHANNEL_K = TitleID.construct_title_id(
        TicketID.SYSTEM_CHANNEL, b"RMCK")
    RABBIDS_CHANNEL = TitleID.construct_title_id(TicketID.CHANNEL, b"RGWX")


class HiddenChannelID(TitleEnum):
    """
    IDs that fall under 0x10008
    """
    PERSONAL_DATA_CHANNEL = TitleID.construct_title_id(TicketID.HIDDEN, b"HCCJ")
    EULA_U = TitleID.construct_title_id(TicketID.HIDDEN, b"HAKU")
    EULA_J = TitleID.construct_title_id(TicketID.HIDDEN, b"HAKJ")
    EULA_P = TitleID.construct_title_id(TicketID.HIDDEN, b"HAKP")
    EULA_K = TitleID.construct_title_id(TicketID.HIDDEN, b"HAKK")
    REGION_SELECT_U = TitleID.construct_title_id(TicketID.HIDDEN, b"HALU")
    REGION_SELECT_J = TitleID.construct_title_id(TicketID.HIDDEN, b"HALJ")
    REGION_SELECT_P = TitleID.construct_title_id(TicketID.HIDDEN, b"HALP")
    REGION_SELECT_K = TitleID.construct_title_id(TicketID.HIDDEN, b"HALK")
    MYSTERY_CHANNEL_U = TitleID.construct_title_id(TicketID.HIDDEN, b"HCZU")
    MYSTERY_CHANNEL_J = TitleID.construct_title_id(TicketID.HIDDEN, b"HCZJ")
    MYSTERY_CHANNEL_P = TitleID.construct_title_id(TicketID.HIDDEN, b"HCZP")
    MYSTERY_CHANNEL_K = TitleID.construct_title_id(TicketID.HIDDEN, b"HCZK")


@dataclass
class TimeLimit():
    enabled: bool = False
    seconds: int = 0


class TicketFlags(IntEnum):
    # All official titles have this flag set.
    DEFAULT = 0x1
    # Unknown.
    UNK_0x4 = 0x4
    # Used for DLC titles.
    DATA = 0x8
    # Unknown.
    UNK_0x10 = 0x10
    # Appears to be used for WFS titles.
    WFS = 0x20
    # Unknown.
    CT = 0x40


@dataclass
class TicketView():
    issuer: str
    titleKey: bytes  # Encrypted
    ticketID: bytes
    consoleID: ConsoleKind
    titleID: TitleID  # IV for AES-CBC encryption (8 bytes long)
    permittedTitlesMask: int
    # Disc title ANDed with inverse of this checked against permittedTitlesMask
    permitMask: int
    titleExportAllowed: bool
    commonKeyIndex: CommonKey
    # bit list for each content (0x40 bytes long)
    contentAccessWhiteList: bytes
    enableTimeLimit: bool = False
    timeLimits: List[TimeLimit] = [TimeLimit()]


class Ticket():
    def __init__(self, signature: SignatureRSA2048, view: TicketView):
        self.signature = signature
        self.view = view

    @classmethod
    def from_bytes(cls, data: Union[bytes, BytesIO]) -> "Ticket":
        """
        Build a ticket from the raw bytes provided
        """
        if isinstance(data, bytes):
            data = BytesIO(data)

        signature = SignatureRSA2048(data.read(0x100))

    def to_bytes(self) -> bytes:
        ...

    def get_title_key(self, consoleKind: ConsoleKind = ConsoleKind.RETAIL) -> bytes:
        """
        Return the decrypted title key extracted from this ticket
        """
        aesIV = self.view.titleID.to_bytes(8, "big", signed=False) + (b"\x00" * 8)
        return AES.new(COMMON_AES_KEY[consoleKind], AES.MODE_CBC, aesIV).digest()