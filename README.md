# Assetto Corsa Graphics Mod — shader foundation

A configurable graphics-mod reference implementation featuring a metallic-roughness PBR material shader, shadow-map PCF, SSAO, an atmospheric sky, and a post-processing composite. It also includes quality presets and small Python utilities for validation, profiling, and staging the files.

> **Runtime compatibility:** Assetto Corsa does not load GLSL ES shaders directly. These shaders target GLSL ES 3.00 and need a compatible renderer/adapter (for example, a custom integration) to supply the documented inputs and render passes. This project does not patch the game, install a CSP extension, or claim that copying these files into the game makes them active. Treat this as a working shader/tooling foundation, not a drop-in replacement for an established AC renderer.

## Project layout

- `shaders/` — standalone GLSL ES 3.00 shader stages and effects.
- `configs/` — Low, Medium, High, and Ultra quality presets plus sunrise, midday, golden-hour, and night lighting examples.
- `scripts/validate.py` — validates presets and performs shader source checks; uses `glslangValidator` when installed.
- `scripts/benchmark.py` — times repeated CPU-side validation runs (not GPU frame-time measurement).
- `scripts/optimize_texture.py` — losslessly recompresses PNGs while retaining their metadata and color profiles.
- `scripts/setup.py` — stages shaders and presets into a destination directory without modifying game files.
- `tests/` — dependency-free unit tests.

## Requirements

- Python 3.9 or later for the utilities and tests.
- An OpenGL ES 3.0-capable shader runtime for the GLSL ES shader sources.
- Optional: `glslangValidator` on `PATH` for compiler-backed shader validation.

Assetto Corsa's renderer and modding interfaces are not GLSL ES 3.0 interfaces. Before using these shaders in-game, a runtime adapter must translate or load the shader code, create the framebuffers/textures, bind uniforms, and invoke the passes in the order below. The exact adapter depends on the user's AC/CSP setup.

## Validate and test

From the repository root:

```sh
python3 scripts/validate.py
python3 -m unittest discover -s tests -v
```

When available, `validate.py` also compiles each shader with `glslangValidator`. Without it, source checks catch common structural mistakes but do not replace compilation on the target renderer.

## Configure

`configs/presets.json` contains complete named presets. Copy a preset as the starting point for a runtime adapter; the `quality` value is metadata, while the settings are the values an adapter should apply. Increase quality gradually and profile on the target machine. `shadow_map_size`, SSAO sampling, and post-process passes can have significant GPU cost.

`configs/lighting-scenarios.json` provides example sun and sky values for four times of day. A runtime can interpolate these values using `time_of_day_hours`; this repository does not include a game clock or interpolation runtime.

Losslessly recompress a PNG texture (the source file is never overwritten):

```sh
python3 scripts/optimize_texture.py input.png
```

The tool writes `input.optimized.png` beside the source, preserves image pixels and metadata, and refuses to overwrite an existing output unless `--force` is provided. It currently supports PNG only, not Assetto Corsa DDS textures.

Run the CPU-side validator benchmark with:

```sh
python3 scripts/benchmark.py --iterations 20
```

This reports validation throughput only; it does not represent game or shader GPU performance.

## Render-pass integration contract

1. Render opaque geometry using `pbr.vert` + `pbr.frag`; provide linear material textures, camera/light matrices, a depth-comparison shadow map, and an environment cubemap.
2. Optionally run `ssao.frag` against a linear depth texture and provide its occlusion texture to the lighting/composite adapter. SSAO is a separate pass; this starter does not include a blur pass.
3. Render the sky with `sky.vert` + `sky.frag` where the scene has no geometry.
4. Composite the scene using `postprocess.vert` + `postprocess.frag`, supplying a bloom texture and screen-space velocity texture. Generate bloom and velocity in the host renderer; the composite shader consumes but does not generate them.

All color textures passed to the lighting and post-processing stages should use a consistent linear color-space convention. The adapter is responsible for depth conventions, framebuffer formats, texture filtering, exposure values, and any required color-space conversions.

## Staging files

To prepare a portable bundle in a chosen directory (it creates/updates a `assetto-corsa-graphics-mod` subfolder):

```sh
python3 scripts/setup.py --destination /path/to/mods
```

This stages source assets only. It does not modify an Assetto Corsa installation. Back up game/mod files and follow the chosen adapter's own installation instructions before integrating anything.

## Limitations and next steps

The included shaders are modular building blocks, not a complete renderer. Real-time adjustment UI, GPU profiling, bloom generation, motion-vector generation, refraction, texture baking, DDS optimization, and a game-specific installer require a host runtime and are not implemented here. The included CPU benchmark is intentionally labeled to avoid implying GPU profiling. Test any adapter changes against its own shader compiler and a backed-up game installation.
