#!/usr/bin/env python3
"""Measure CPU time for repeated config and shader validation."""

import argparse
import statistics
import time

from validate import validate_presets, validate_scenarios, validate_shaders


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iterations", type=int, default=20)
    args = parser.parse_args()
    if args.iterations < 1 or args.iterations > 10000:
        parser.error("--iterations must be between 1 and 10000")

    durations = []
    for _ in range(args.iterations):
        start = time.perf_counter()
        validate_presets()
        validate_scenarios()
        validate_shaders()
        durations.append(time.perf_counter() - start)

    print(
        f"CPU validation: {args.iterations} iterations, "
        f"mean {statistics.mean(durations) * 1000:.2f} ms, "
        f"median {statistics.median(durations) * 1000:.2f} ms "
        "(not GPU or in-game performance)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
