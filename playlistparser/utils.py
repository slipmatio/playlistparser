import io
from contextlib import contextmanager
from typing import TYPE_CHECKING

from playlistparser.exceptions import MissingFieldError

if TYPE_CHECKING:
    from collections.abc import Iterator
    from typing import BinaryIO

    from playlistparser import FieldName


@contextmanager
def decoded_text(
    file: BinaryIO,
    *,
    encoding: str,
    errors: str | None = None,
) -> Iterator[io.TextIOWrapper]:
    """Decode *file* without taking ownership of the binary stream."""
    text = io.TextIOWrapper(file, encoding=encoding, errors=errors, newline="")
    try:
        yield text
    finally:
        text.detach()


def time_str_to_seconds(time: str) -> int:
    """Convert a time string to seconds.

    0:01:00 -> 60
    """
    try:
        secs = sum(
            multiplier * int(part) for multiplier, part in zip([1, 60, 3600], reversed(time.split(":")), strict=False)
        )
    except ValueError, TypeError, AttributeError:
        secs = 0
    return secs


def csv_field(
    row: list[str],
    columns: dict[str, int],
    name: str,
    default: str = "",
) -> str:
    position = columns.get(name)
    if position is None or position >= len(row):
        return default
    return row[position].strip()


def required[T](
    value: T,
    field: FieldName,
    require: frozenset[FieldName],
    *,
    line: int,
    track_title: str = "",
) -> T:
    """Return *value*, raising MissingFieldError when it is empty and *field* was required."""
    if not value and field in require:
        raise MissingFieldError(field, line=line, track_title=track_title or None)
    return value
