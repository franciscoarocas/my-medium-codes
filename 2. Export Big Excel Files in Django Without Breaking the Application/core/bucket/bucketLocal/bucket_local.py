from pathlib import Path
from typing import BinaryIO
from uuid import uuid4

from django.conf import settings

from core.bucket.bucketBase import BucketBase, StoredFile


class BucketLocal(BucketBase):
    def __init__(self):
        self.root = (
            Path(settings.BASE_DIR) / 'core' / 'bucket' / 'bucketLocal' / 'files'
        )
        self.root.mkdir(parents=True, exist_ok=True)

    def create_file(self, filename: str) -> StoredFile:
        key = f'{uuid4().hex}_{Path(filename).name}'
        return StoredFile(key=key, path=self.root / key)

    def open(self, key: str) -> BinaryIO:
        return self._path_for(key).open('rb')

    def delete(self, key: str) -> None:
        self._path_for(key).unlink(missing_ok=True)

    def _path_for(self, key: str) -> Path:
        path = (self.root / key).resolve()
        if path.parent != self.root.resolve():
            raise ValueError('Invalid bucket key.')
        return path
