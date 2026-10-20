#!/usr/bin/env python3
"""Stage shader and preset source assets into a portable bundle directory."""

import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def stage(destination):
    destination = Path(destination).expanduser().resolve() / "assetto-corsa-graphics-mod"
    destination.mkdir(parents=True, exist_ok=True)
    for folder in ("shaders", "configs"):
        shutil.copytree(ROOT / folder, destination / folder, dirs_exist_ok=True)
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", required=True, help="directory in which to create the staged bundle")
    args = parser.parse_args()
    bundle = stage(args.destination)
    print(f"Staged source assets in {bundle}")
    print("These files are not installed into or loaded by Assetto Corsa.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
