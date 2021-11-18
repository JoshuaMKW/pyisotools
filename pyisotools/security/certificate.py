from abc import ABC, abstractmethod
from enum import IntEnum
from dataclasses import dataclass
from typing import Union
from io import BytesIO
from Crypto.PublicKey import RSA

from pyisotools.security.signature import Signature, SignatureRSA2048
from pyisotools.tools import read_string, read_uint32


class KeyType(IntEnum):
    RSA4096 = 0
    RSA2048 = 1
    ECCB233 = 2


@dataclass(init=True, eq=True)
class CertificateData():
    issuer: str
    keyType: KeyType
    keyName: str
    keyID: int
    publicKey: bytes

    def __len__(self) -> int:
        return 0x48


class Certificate(ABC):
    def __init__(
        self,
        signature: Signature,
        data: CertificateData,
    ):
        self.signature = signature
        self.data = data

    @classmethod
    def root(cls) -> "Certificate":
        cert = cls()

    @abstractmethod
    @classmethod
    def from_bytes(cls, data: Union[bytes, BytesIO]) -> "Certificate": ...

    @abstractmethod
    def to_bytes(self) -> bytes: ...

    @abstractmethod
    def size(self) -> int: ...


    def __len__(self) -> int:
        return self.size()


class CertificateRSA4096(Certificate):
    """
    Abstraction of sign verification data on Wii discs
    """

    @classmethod
    def from_bytes(cls, data: Union[bytes, BytesIO]) -> "Certificate": ...

    def to_bytes(self) -> bytes: ...

    def size(self) -> int:
        return len(self.signature) + len(self.header) + 0x138



class CertificateRSA2048(Certificate):
    """
    Abstraction of sign verification data on Wii discs
    """

    @classmethod
    def from_bytes(cls, data: Union[bytes, BytesIO]) -> "Certificate":
        if isinstance(data, bytes):
            data = BytesIO(data)

        # Skip the signature type, it is known here
        data.seek(4, 1)

        sigdata = data.read(0x100)
        issuer = read_string(data, maxlen=0x40)

        # Certificate data
        keyType = KeyType(read_uint32(data))
        keyName = read_string(data, maxlen=0x40)
        keyID = read_uint32(data)
        publicKey = data.read(0x100)
        certheader = CertificateData(issuer, keyType, keyName, keyID, publicKey)

        data.seek(0x38, 1) # Skip padding

        # Signature
        signature = SignatureRSA2048(sigdata, publickey=publicKey, name=issuer)

        # Build the certificate
        cert = cls(signature, certheader)
        return cert

    def to_bytes(self) -> bytes: ...


    def size(self) -> int:
        return len(self.signature) + len(self.header) + 0x138


class CertificateECCB233(Certificate):
    """
    Abstraction of sign verification data on Wii discs
    """

    @classmethod
    def from_bytes(cls, data: Union[bytes, BytesIO]) -> "Certificate": ...

    def to_bytes(self) -> bytes: ...

    def size(self) -> int:
        return len(self.signature) + len(self.header) + 0x78


class CertificateChain(list):
    """
    Accessor object for a chain of certificates
    """
    def __init__(self, rootCert: Certificate):
        self.chain = {"ROOT": rootCert}

    def __iter__(self): ...
    

def get_key_length(type: KeyType) -> int:
    if type == KeyType.RSA4096:
        return 0x23C
    if type == KeyType.RSA2048:
        return 0x13C
    if type == KeyType.ECCB233:
        return 0x78
    return -1