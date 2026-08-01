import argparse
import dataclasses
import json
import sys

from playlistparser import PlaylistParser, PlaylistParserError, PlaylistType

FORMAT_NAMES = {
    PlaylistType.ENGINE: "Engine DJ",
    PlaylistType.REKORDBOX: "Rekordbox",
    PlaylistType.SERATO: "Serato",
    PlaylistType.TRAKTOR: "Traktor",
    PlaylistType.VIRTUALDJ: "VirtualDJ",
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="playlistparser", description="Parse DJ software playlists.")
    commands = parser.add_subparsers(dest="command", required=True)
    parse_command = commands.add_parser("parse", help="print the tracks in a playlist file")
    parse_command.add_argument("file", help="playlist file (.nml, .txt or .csv)")
    parse_command.add_argument("--json", action="store_true", help="output JSON instead of text")
    args = parser.parse_args(argv)

    try:
        playlist = PlaylistParser(args.file)
        tracks = playlist.to_list()
    except (PlaylistParserError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    if args.json:
        json.dump(
            {
                "tracks": [dataclasses.asdict(track) for track in tracks],
                "summary": {
                    "playlist_type": playlist.playlist_type.name,
                    "track_count": len(tracks),
                },
            },
            sys.stdout,
            indent=2,
            ensure_ascii=False,
        )
        print()
    else:
        for number, track in enumerate(tracks, start=1):
            print(f"{number}. {track.artist} - {track.title}")
        print()
        print(f"{FORMAT_NAMES[playlist.playlist_type]} · {len(tracks)} tracks")

    return 0
