from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import os


class PlaylistParserError(Exception):
    pass


class UnknownFormatError(PlaylistParserError):
    def __init__(self, path: str | os.PathLike[str], supported: list[str] | None = None) -> None:
        self.path = path
        self.supported = supported or [".nml", ".txt", ".csv"]
        exts = ", ".join(self.supported)
        super().__init__(
            f"Cannot determine playlist format for '{path}'. "
            f"Supported extensions: {exts}. "
            "Use the as_type= parameter to override detection.",
        )


class MalformedPlaylistError(PlaylistParserError):
    def __init__(
        self,
        message: str,
        path: str | os.PathLike[str] | None = None,
        line: int | None = None,
    ) -> None:
        self.path = path
        self.line = line
        detail = f" (file: {path}" + (f", line: {line}" if line is not None else "") + ")" if path else ""
        super().__init__(f"{message}{detail}")


class MissingFieldError(PlaylistParserError):
    def __init__(
        self,
        field: str,
        line: int | None = None,
        track_title: str | None = None,
    ) -> None:
        self.field = field
        self.line = line
        self.track_title = track_title
        parts = [f"Required field '{field}' is missing"]
        if track_title:
            parts.append(f"track: {track_title!r}")
        if line is not None:
            parts.append(f"line: {line}")
        super().__init__(", ".join(parts))
