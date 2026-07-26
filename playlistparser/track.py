import dataclasses
import re
from datetime import timedelta
from unicodedata import normalize

YEAR_RE = re.compile(r"\d{4}")


def normalize_text(text: str) -> str:
    """NFC-normalize *text*, skipping the syscall for pure-ASCII strings."""
    stripped = text.strip()
    if stripped.isascii():
        return stripped
    return normalize("NFC", stripped)


def clean_year(raw: str | int) -> int:
    """Extract a four-digit year from *raw*, return 0 on failure."""
    if isinstance(raw, int):
        return raw
    match = YEAR_RE.search(raw)
    if match:
        try:
            return int(match.group())
        except ValueError:
            return 0
    return 0


@dataclasses.dataclass(frozen=True, slots=True, init=False)
class Track:
    """An immutable, hashable representation of a single playlist track.

    ``year`` accepts both ``str`` (parsed from raw playlist data) and ``int``
    (clean values); it is always stored and exposed as ``int``.
    """

    title: str
    artist: str
    album: str
    key: str
    duration: int
    year: int
    bpm: float
    file_path: str
    vendor_id: str

    def __init__(  # noqa: PLR0913 -- keyword-only arguments mirror the stable Track data model
        self,
        *,
        title: str,
        artist: str,
        album: str = "",
        key: str = "",
        duration: int = 0,
        year: str | int = 0,
        bpm: float = 0.0,
        file_path: str = "",
        vendor_id: str = "",
    ) -> None:
        object.__setattr__(self, "title", normalize_text(title))
        object.__setattr__(self, "artist", normalize_text(artist))
        object.__setattr__(self, "album", normalize_text(album))
        object.__setattr__(self, "key", normalize_text(key))
        object.__setattr__(self, "duration", duration)
        object.__setattr__(self, "year", clean_year(year))
        object.__setattr__(self, "bpm", round(float(bpm), 1))
        object.__setattr__(self, "file_path", file_path)
        object.__setattr__(self, "vendor_id", vendor_id.strip())

    def __str__(self) -> str:
        return f"{self.artist} - {self.title}"

    def duration_str(self) -> str:
        if not self.duration:
            return "0:00"
        string = str(timedelta(seconds=self.duration))
        # '0:00:12' → '00:12'
        string = string.removeprefix("0:")
        # '00:12' → '0:12'
        if string.startswith("00:"):
            string = "0:" + string[3:]
        # '01:12' → '1:12'
        if string.startswith("0") and not string.startswith("0:"):
            string = string[1:]
        return string

    def as_dict(self, *, no_meta: bool = False) -> dict[str, str | int | float]:
        song: dict[str, str | int | float] = {"title": self.title, "artist": self.artist}
        if no_meta:
            return song
        all_fields = dataclasses.asdict(self)
        for key in ("album", "key", "duration", "year", "bpm", "file_path", "vendor_id"):
            if all_fields[key]:
                song[key] = all_fields[key]
        if self.duration:
            song["duration_str"] = self.duration_str()
        return song
