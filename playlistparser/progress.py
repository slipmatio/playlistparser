import io
from collections.abc import Buffer, Callable

type ProgressCallback = Callable[[int, int | None, int, int], None]
type ByteReadCallback = Callable[[int], None]


class CountingReader(io.RawIOBase):
    """Read-only binary stream wrapper that counts bytes consumed."""

    def __init__(self, source: io.FileIO, on_read: ByteReadCallback | None = None) -> None:
        super().__init__()
        self.source = source
        self.on_read = on_read
        self.bytes_read = 0

    def readable(self) -> bool:
        return self.source.readable()

    def seekable(self) -> bool:
        return self.source.seekable()

    def fileno(self) -> int:
        return self.source.fileno()

    def tell(self) -> int:
        return self.source.tell()

    def seek(self, offset: int, whence: int = io.SEEK_SET) -> int:
        return self.source.seek(offset, whence)

    def readinto(self, buffer: Buffer) -> int | None:
        count = self.source.readinto(buffer)
        if count:
            self.bytes_read += count
            if self.on_read is not None:
                self.on_read(self.bytes_read)
        return count
