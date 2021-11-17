from dataclasses import dataclass
from enum import IntEnum
from pyisotools.security.signature import SigType, Signature

@dataclass
class TimeLimit():
    enabled: bool = False
    seconds: int = 0

class TicketType(IntEnum):
    SYSTEM = 0x00000001
    GAME = 0x00010000
    CHANNEL = 0x00010001
    SYSTEMCHANNEL = 0x00010002
    GAMEWITHCHANNEL = 0x00010004
    DLC = 0x00010005
    HIDDENCHANNEL = 0x00010008

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

class TicketView():
    ...


class Ticket():
    def __init__(self, sigtype: SigType, signature: bytes, view: bytes):
        assert len(signature) == Signature.get_length_of(sigtype)
        assert len(view) == 415
        self.sigtype = sigtype
        self.signature = signature
        self.view = view
