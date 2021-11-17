from abc import ABC, abstractmethod
from enum import IntEnum
from dataclasses import dataclass

from pyisotools.security.signature import Signature

class KeyType(IntEnum):
    RSA4096 = 0
    RSA2048 = 1
    ECCB233 = 2

@dataclass(init=True, eq=True)
class CertificateHeader():
    keyType: KeyType
    name: str
    id: int

    def __len__(self) -> int:
        return 0x48

class Certificate(ABC):
    def __init__(
        self,
        signature: Signature,
        header: CertificateHeader,
    ):
        self.signature = signature
        self.header = header

    @classmethod
    def root(cls) -> "Certificate":
        cert = cls()

    @abstractmethod
    def size(self) -> int: ...

    def __len__(self) -> int:
        return self.size()


class CertificateRSA4096(Certificate):
    """
    Abstraction of sign verification data on Wii discs
    """

    def size(self) -> int:
        return len(self.signature) + len(self.header) + 0x138


class CertificateRSA2048(Certificate):
    """
    Abstraction of sign verification data on Wii discs
    """

    def size(self) -> int:
        return len(self.signature) + len(self.header) + 0x138


class CertificateECCB233(Certificate):
    """
    Abstraction of sign verification data on Wii discs
    """

    def size(self) -> int:
        return len(self.signature) + len(self.header) + 0x78


def get_key_length(type: KeyType) -> int:
    if type == KeyType.RSA4096:
        return 0x23C
    if type == KeyType.RSA2048:
        return 0x13C
    if type == KeyType.ECCB233:
        return 0x78
    return -1