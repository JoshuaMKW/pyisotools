from abc import ABC, abstractmethod
from enum import IntEnum
from typing import Union

from Crypto.PublicKey import RSA
from Crypto.Hash import SHA1, SHA256, SHA512


class SigType(IntEnum):
    RSA4096 = 0x10000
    RSA2048 = 0x10001
    ECCB233 = 0x10002

class Signature(ABC):
    """
    Abstract class representing a Wii verification signature
    """

    def __init__(self, signature: bytes, publickey: RSA.RsaKey, privatekey: RSA.RsaKey, name: str):
        assert len(signature) == Signature.get_length_of(self.type)
        self._signature = signature
        self.publickey = publickey
        self.privatekey = privatekey
        self.name = name

    @abstractmethod
    def size() -> int: ...

    @abstractmethod
    def sign_off(self, data: bytes): ...

    @staticmethod
    def get_length_of(type: SigType) -> int:
        if type == SigType.RSA4096:
            return 0x200
        if type == SigType.RSA2048:
            return 0x100
        if type == SigType.ECCB233:
            return 0x3C
        return -1

    

    def __len__(self) -> int:
        return self.size()

class SignatureRSA4096(Signature):
    def size() -> int:
        return 0x280

    @property
    def signature(self, data: bytes):
        return 

    @signature.setter
    def signature(self, sig: Union[str, bytes]):
        ...

    def get_raw_signature(self) -> bytes:
        """
        Returns the decrypted signature
        """
        decodedSig = pow(self._signature, self.publickey.d, self.publickey.n)
        return decodedSig.to_bytes(Signature.get_length_of(SigType.RSA4096), "big", signed=False)


    def set_raw_signature(self, sig: Union[str, bytes]):
        """
        Sets the signature by encrypting `sig`
        """
        shaHash = SHA512.new(sig) # 0x200 bytes long
        hashedBytes = shaHash.digest()

        rsaKey = RSA.generate(2048)

        signature = pow(int.from_bytes(hashedBytes, "big", signed=False), rsaKey.d, rsaKey.n)
        self._signature = signature

class SignatureRSA2048(Signature):
    def size() -> int:
        return 0x180

class SignatureECCB233(Signature):
    def size() -> int:
        return 0xC0