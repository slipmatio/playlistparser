# Changelog

## 4.0.0 (2026-05-26)

- Breaking: removed `parse()`, `get_tracks()`, `verbose=`, and the five individual `require_*`
  booleans from `PlaylistParser`. Use `require=[...]` instead.
- Breaking: all parsers are now streaming generators; the `parser()` wrappers are removed.
- Feat: top-level `parse()`, `iter_tracks()`, and `detect_format()` convenience functions.
- Feat: `FieldName` type alias and full exception hierarchy (`PlaylistParserError`,
  `UnknownFormatError`, `MalformedPlaylistError`, `MissingFieldError`) exported from package root.
- Feat: `PlaylistParser` accepts `str | os.PathLike`, exposes `path`, `as_type`, `playlist_type`,
  lazy `tracks` property, and supports `iter()` and `len()`.
- Fix: all `require=` fields now correctly raise `MissingFieldError` across all parsers.
- Fix: Traktor yields `duration=0` when `PLAYTIME` is absent instead of crashing.
- Perf: Rekordbox streams via `io.TextIOWrapper`; Traktor uses `lxml.etree.iterparse`; CSV parsers
  use `csv.reader` with a header-index map.
- Refactor: `Track` is now a frozen, slotted dataclass with equality, hash, and repr.
- Refactor: explicit `encoding=` on every `open()` call; `logging` replaces `print()`.

## 3.0.0-beta.11 (2026-05-21)

- docs: document installing
- refactor: use uv build backend
- ci: added Renovate config
- tooling: added `ty`
- chore: bump dev deps

## 3.0.0-beta.10 (2024-11-19)

- Fix: keep quiet when `verbose=False`.
- Refactor: use `uv` for packaging.

## 3.0.0-beta.9 (2022-04-04)

- Refactor: use IntEnum instead of Enum for playlist_type.

## 3.0.0-beta.8 (2022-04-04)

- Feat: implemented playlist_type as importable Enum class. (In #10)
- Fix: added typings to PlaylistParser arguments.

## 3.0.0-beta.7 (2022-03-29)

- Feat: added default artist name. (Fixes #8, in #9)
- Feat: added ability to require title, duration, year, bpm, and file_path (In #6 and #7)

## 3.0.0-beta.6 (2022-03-25)

- Feat: added ability to parse file paths from Rekordbox and Engine playlists. (In #5)

## 3.0.0-beta.5 (2022-03-22)

- Fix: clean track title and artist. (In #4)

## 3.0.0-beta.4 (2022-03-22)

- Feat: added support for VirtualDJ.

## 3.0.0-beta.3 (2022-03-16)

- Fixed: added normalization to Track artist and title. (Fixes #2)

## 3.0.0-beta.2 (2022-03-16)

- Fixed: added missing files to the distribution.

## 3.0.0-beta.1 (2022-03-15)

- Initial version, fully rewritten for the second time since the original from 2013.
