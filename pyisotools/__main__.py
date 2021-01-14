from argparse import ArgumentParser
from pathlib import Path

from pyisotools.iso import GamecubeISO
from pyisotools import __version__

if __name__ == "__main__":
    parser = ArgumentParser(f"pyisotools {__version__}", description="ISO tool for extracting/building Gamecube ISOs", allow_abbrev=False)

    parser.add_argument("src", help="ISO/root to build/extract with")
    parser.add_argument("job",
                        choices=["B", "E"],
                        help="Job to do")
    parser.add_argument("--newinfo",
                        help="Overwrite original information with custom info (build only)",
                        action="store_true")
    parser.add_argument("--dest",
                        help="Directory (extract)/ISO (build) to store data")

    args = parser.parse_args()

    src = Path(args.src).resolve()
    iso = GamecubeISO()
    if args.job == "E":
        iso.extract(src, args.dest)
    elif args.job == "B":
        iso.build(src, args.dest, genNewInfo=args.newinfo)
    else:
        parser.print_help()