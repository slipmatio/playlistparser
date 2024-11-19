# Changelog

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
