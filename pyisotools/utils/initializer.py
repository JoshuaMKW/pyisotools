from abc import ABC, abstractmethod
from typing import Any, Callable, Optional

from pyisotools.utils import A_Serializable


_ByteInitializer = bytes | bytearray | A_Serializable | Callable[[
], bytes | bytearray | A_Serializable]


class A_Initializer(ABC):
    def __init__(self) -> None:
        super().__init__()

    @ abstractmethod
    def get_name(self) -> str:
        """
        Returns the name of the data to be initialized
        """
        ...

    @ abstractmethod
    def get_identity(self) -> Any:
        """
        Returns a default "initialized" state of data
        """
        ...


class SerialInitializer(A_Initializer):
    def __init__(self, serializer: Optional[type[A_Serializable]]) -> None:
        super().__init__()
        self._serialCls = serializer

    def get_name(self) -> str:
        return self._serialCls.__name__

    def get_identity(self) -> A_Serializable:
        return self._serialCls()

    def get_serializer(self) -> type[A_Serializable]:
        return self._serialCls

    def set_serializer(self, serializer: type[A_Serializable]):
        self._serialCls = serializer


class FileInitializer(A_Initializer):
    def __init__(self, name: str, initializer: _ByteInitializer = b"") -> None:
        super().__init__()
        self._name = name
        self._initializer = initializer

    def get_name(self) -> str:
        return self._name

    def get_identity(self) -> bytes | bytearray:
        if isinstance(self._initializer, (bytes, bytearray)):
            return self._initializer
        if isinstance(self._initializer, A_Serializable):
            return self._initializer.to_bytes()

        initializer = self._initializer()

        if isinstance(initializer, (bytes, bytearray)):
            return initializer
        if isinstance(initializer, A_Serializable):
            return initializer.to_bytes()

        raise ValueError("Proper file identity could not be initialized")

    def get_initializer(self) -> _ByteInitializer:
        return self._initializer

    def set_initializer(self, initializer: _ByteInitializer):
        self._initializer = initializer
