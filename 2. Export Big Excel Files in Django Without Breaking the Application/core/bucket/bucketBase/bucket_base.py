from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO


@dataclass(frozen=True)
class StoredFile:
    key: str
    path: Path


class BucketBase(ABC):
    @abstractmethod
    def create_file(self, filename: str) -> StoredFile:
        raise NotImplementedError

    @abstractmethod
    def open(self, key: str) -> BinaryIO:
        raise NotImplementedError

    @abstractmethod
    def delete(self, key: str) -> None:
        raise NotImplementedError
