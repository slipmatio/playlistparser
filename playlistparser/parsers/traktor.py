import logging
from typing import TYPE_CHECKING

from lxml import etree  # type: ignore[import-untyped]  # ty:ignore[unresolved-import]

from playlistparser.exceptions import MissingFieldError
from playlistparser.track import Track

if TYPE_CHECKING:
    from collections.abc import Iterator

    from playlistparser import FieldName

logger = logging.getLogger(__name__)


def iter_tracks(  # noqa: C901, PLR0912 -- many branches needed for optional NML fields
    file_path: str,
    *,
    require: frozenset[FieldName] = frozenset(),
    default_artist: str = "Unknown Artist",
    logger: logging.Logger | None = None,
) -> Iterator[Track]:
    """Traktor NML supports: title, artist, year, duration, bpm.

    Only COLLECTION ENTRYs (those with a ``TITLE`` attribute) are processed;
    playlist-reference ENTRYs are silently skipped.

    Yields one :class:`~playlistparser.track.Track` per ENTRY.
    """
    log = logger or logging.getLogger(__name__)
    context = etree.iterparse(file_path, events=("end",), tag="ENTRY")

    for lineno, (event, elem) in enumerate(context, start=1):
        del event  # iterparse event string; only "end" is used here
        # Playlist reference entries have no TITLE attribute — skip them.
        if "TITLE" not in elem.attrib:
            elem.clear()
            continue
        try:
            track_title = (elem.get("TITLE") or "").strip()
            if not track_title and "title" in require:
                raise MissingFieldError("title", line=lineno)

            track_artist = (elem.get("ARTIST") or "").strip() or default_artist

            playtime = 0
            year = ""
            meta = elem.find("INFO")
            if meta is not None:
                raw_playtime = (meta.get("PLAYTIME") or "").strip()
                if raw_playtime:
                    try:
                        playtime = int(raw_playtime)
                    except ValueError:
                        playtime = 0
                if playtime == 0 and "duration" in require:
                    raise MissingFieldError("duration", line=lineno, track_title=track_title or None)

                year = meta.get("RELEASE_DATE") or ""
                if not year and "year" in require:
                    raise MissingFieldError("year", line=lineno, track_title=track_title or None)
            elif "duration" in require:
                raise MissingFieldError("duration", line=lineno, track_title=track_title or None)
            elif "year" in require:
                raise MissingFieldError("year", line=lineno, track_title=track_title or None)

            bpm = 0
            tempometa = elem.find("TEMPO")
            if tempometa is not None:
                try:
                    bpm = int(float(tempometa.get("BPM") or 0))
                except ValueError, TypeError:
                    bpm = 0
            if bpm == 0 and "bpm" in require:
                raise MissingFieldError("bpm", line=lineno, track_title=track_title or None)

            yield Track(
                title=track_title,
                artist=track_artist,
                year=year,
                duration=playtime,
                bpm=bpm,
            )
        except MissingFieldError:
            raise
        except (AttributeError, ValueError, TypeError) as exc:
            log.debug("Skipping entry %d: %s", lineno, exc)
        finally:
            elem.clear()
