from __future__ import annotations
from abc import ABC, abstractmethod
import array
import ctypes
import mmap
import pickle
import sys
from typing import Any, BinaryIO, Callable, Dict, List, Optional, Protocol, Type, TypeAlias, TypeVar, Union


JSYSTEM_PADDING_TEXT = "This is padding data to alignment....."


class classproperty(property):
    def __get__(self, __obj: Any, __type: type | None = None) -> Any:
        return classmethod(self.fget).__get__(None, __type)() # type: ignore


class SupportsDunderLT(Protocol):
    def __lt__(self, __other: Any) -> bool: ...


class SupportsDunderGT(Protocol):
    def __gt__(self, __other: Any) -> bool: ...


class SupportsDunderLE(Protocol):
    def __le__(self, __other: Any) -> bool: ...


class SupportsDunderGE(Protocol):
    def __ge__(self, __other: Any) -> bool: ...


class SupportsAllComparisons(SupportsDunderLT, SupportsDunderGT, SupportsDunderLE, SupportsDunderGE, Protocol): ...


SupportsRichComparison: TypeAlias = SupportsDunderLT | SupportsDunderGT
SupportsRichComparisonT = TypeVar("SupportsRichComparisonT", bound=SupportsRichComparison)  # noqa: Y001

ReadOnlyBuffer: TypeAlias = bytes  # stable
WriteableBuffer: TypeAlias = bytearray | memoryview | mmap.mmap  # stable
ReadableBuffer: TypeAlias = ReadOnlyBuffer | WriteableBuffer  # stable

VariadicArgs = Any
VariadicKwargs = Any

clamp: Callable[[SupportsAllComparisons, SupportsAllComparisons, SupportsAllComparisons],
                SupportsAllComparisons] = lambda x, min_, max_: min_ if x < min_ else max_ if x > max_ else x
clamp01: Callable[[SupportsAllComparisons], SupportsAllComparisons] = lambda x: clamp(x, 0, 1)
sign: Callable[[SupportsAllComparisons], SupportsAllComparisons] = lambda x: 1 if x >= 0 else -1


def write_jsystem_padding(f: BinaryIO, multiple: int) -> None:
    next_aligned = (f.tell() + (multiple - 1)) & ~(multiple - 1)

    diff = next_aligned - f.tell()

    for i in range(diff):
        pos = i % len(JSYSTEM_PADDING_TEXT)
        f.write(JSYSTEM_PADDING_TEXT[pos:pos+1].encode())


class A_Serializable(ABC):
    """
    Interface that ensures compatibility with generic object streaming
    """
    @classmethod
    @abstractmethod
    def from_bytes(cls, data: BinaryIO, *args: VariadicArgs, **
                   kwargs: VariadicKwargs) -> Optional[A_Serializable]: ...

    @abstractmethod
    def to_bytes(self) -> bytes: ...


class A_Clonable(ABC):
    """
    Interface that ensures this object supports deep copying
    """
    @abstractmethod
    def copy(self, *, deep: bool = False) -> A_Clonable: ...