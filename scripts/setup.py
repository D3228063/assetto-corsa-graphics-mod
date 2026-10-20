#!/usr/bin/env python3
"""Stage shader and preset source assets into a portable bundle directory."""

import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILTER_NAME = "assetto-corsa-graphics-mod.ini"
GAME_EXECUTABLES = ("acs.exe", "acs_x86.exe")


def stage(destination):
    destination = Path(destination).expanduser().resolve() / "assetto-corsa-graphics-mod"
    destination.mkdir(parents=True, exist_ok=True)
    for folder in ("shaders", "configs", "content-manager"):
        shutil.copytree(ROOT / folder, destination / folder, dirs_exist_ok=True)
    return destination


def install(game_root, force=False):
    game_root = Path(game_root).expanduser().resolve()
    if not game_root.is_dir() or not any((game_root / name).is_file() for name in GAME_EXECUTABLES):
        raise ValueError("game root must contain acs.exe or acs_x86.exe")
    filter_directory = game_root / "system" / "cfg" / "ppfilters"
    filter_directory.mkdir(parents=True, exist_ok=True)
    if not filter_directory.resolve().is_relative_to(game_root):
        raise ValueError("post-processing filter directory resolves outside the game root")
    destination = filter_directory / FILTER_NAME
    if destination.exists() and not force:
        raise FileExistsError(f"{destination} already exists; pass --force to replace it")
    if not destination.resolve().is_relative_to(game_root):
        raise ValueError("post-processing filter file resolves outside the game root")
    shutil.copy2(ROOT / "content-manager" / FILTER_NAME, destination)
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--destination", help="directory in which to create the staged source bundle")
    target.add_argument("--game-root", help="Assetto Corsa installation root")
    parser.add_argument("--force", action="store_true", help="replace an existing installed filter")
    args = parser.parse_args()
    try:
        if args.game_root:
            installed = install(args.game_root, args.force)
            print(f"Installed Content Manager post-processing filter at {installed}")
        else:
            bundle = stage(args.destination)
            print(f"Staged source assets in {bundle}")
    except (OSError, ValueError) as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
