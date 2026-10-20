#!/usr/bin/env python3
"""Validate graphics-mod presets and perform basic GLSL ES checks."""

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRESETS_PATH = ROOT / "configs" / "presets.json"
SCENARIOS_PATH = ROOT / "configs" / "lighting-scenarios.json"
SHADER_DIR = ROOT / "shaders"
EXPECTED_PRESETS = {"Low", "Medium", "High", "Ultra"}
NUMERIC_RANGES = {
    "shadow_map_size": (512, 16384),
    "shadow_pcf_samples": (1, 25),
    "ssao_samples": (1, 16),
    "exposure": (0.0, 8.0),
    "contrast": (0.0, 4.0),
    "saturation": (0.0, 4.0),
    "film_grain": (0.0, 0.1),
    "chromatic_aberration": (0.0, 0.02),
}
BOOLEAN_FIELDS = {
    "ssao_enabled",
    "bloom_enabled",
    "motion_blur_enabled",
}


def validate_presets(path=PRESETS_PATH):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("schema_version") != 1 or set(data.get("presets", {})) != EXPECTED_PRESETS:
        raise ValueError("Expected schema_version 1 and Low/Medium/High/Ultra presets")

    required = set(NUMERIC_RANGES) | BOOLEAN_FIELDS | {"quality"}
    for name, preset in data["presets"].items():
        if set(preset) != required:
            raise ValueError(f"{name} preset has missing or unexpected settings")
        if preset["quality"] != name:
            raise ValueError(f"{name} preset quality value must match its name")
        for key, (minimum, maximum) in NUMERIC_RANGES.items():
            value = preset[key]
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not minimum <= value <= maximum:
                raise ValueError(f"{name}.{key} must be a number between {minimum} and {maximum}")
        for key in BOOLEAN_FIELDS:
            if not isinstance(preset[key], bool):
                raise ValueError(f"{name}.{key} must be a boolean")
    return data


def validate_scenarios(path=SCENARIOS_PATH):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    scenarios = data.get("scenarios", {})
    if data.get("schema_version") != 1 or not scenarios:
        raise ValueError("Expected schema_version 1 and at least one lighting scenario")
    vector_fields = ("sun_direction", "sun_color", "ambient_color", "horizon_color", "zenith_color")
    for name, scenario in scenarios.items():
        if set(scenario) != set(vector_fields) | {"time_of_day_hours", "atmosphere_density"}:
            raise ValueError(f"{name} scenario has missing or unexpected settings")
        hour = scenario["time_of_day_hours"]
        if isinstance(hour, bool) or not isinstance(hour, (int, float)) or not 0 <= hour < 24:
            raise ValueError(f"{name}.time_of_day_hours must be between 0 (inclusive) and 24")
        density = scenario["atmosphere_density"]
        if isinstance(density, bool) or not isinstance(density, (int, float)) or not 0.01 <= density <= 10:
            raise ValueError(f"{name}.atmosphere_density must be between 0.01 and 10")
        for key in vector_fields:
            vector = scenario[key]
            if not isinstance(vector, list) or len(vector) != 3:
                raise ValueError(f"{name}.{key} must contain three numeric components")
            for component in vector:
                minimum, maximum = (-1, 1) if key == "sun_direction" else (0, 4)
                if isinstance(component, bool) or not isinstance(component, (int, float)) or not minimum <= component <= maximum:
                    raise ValueError(f"{name}.{key} components must be between {minimum} and {maximum}")
        direction_length = sum(component * component for component in scenario["sun_direction"])
        if not 0.98 <= direction_length <= 1.02:
            raise ValueError(f"{name}.sun_direction must be normalized")
    return data


def validate_shaders(shader_dir=SHADER_DIR, compiler=None):
    files = sorted(Path(shader_dir).glob("*"))
    if not files:
        raise ValueError(f"No shaders found in {shader_dir}")

    for path in files:
        source = path.read_text(encoding="utf-8")
        if not source.startswith("#version 300 es\n"):
            raise ValueError(f"{path.name} must begin with #version 300 es")
        if source.count("{") != source.count("}"):
            raise ValueError(f"{path.name} has unbalanced braces")
        if "void main()" not in source:
            raise ValueError(f"{path.name} is missing void main()")
        if compiler:
            result = subprocess.run(
                [compiler, "-S", path.suffix.lstrip("."), str(path)],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode:
                raise ValueError(f"{path.name} failed glslangValidator:\n{result.stdout}{result.stderr}")
    return len(files)


def main():
    try:
        validate_presets()
        validate_scenarios()
        compiler = shutil.which("glslangValidator")
        shader_count = validate_shaders(compiler=compiler)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Validation failed: {error}", file=sys.stderr)
        return 1
    suffix = " (glslangValidator)" if compiler else " (source checks; install glslangValidator for compilation)"
    print(f"Validated four presets, lighting scenarios, and {shader_count} shaders{suffix}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
