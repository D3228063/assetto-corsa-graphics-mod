# Assetto Corsa Graphics Mod

A Content Manager-selectable post-processing filter for Assetto Corsa, alongside a configurable shader foundation featuring metallic-roughness PBR, shadow-map PCF, SSAO, an atmospheric sky, and a post-processing composite. It also includes quality and lighting presets plus utilities for validation, profiling, texture optimization, and installation.

> **What works in-game:** `content-manager/assetto-corsa-graphics-mod.ini` is an AC post-processing filter that Content Manager can select. It uses the game's YEBIS post-processing options for exposure, color grading, glare/bloom, chromatic aberration, and vignette. The GLSL ES shaders in `shaders/` are separate reference sources: AC/CSP does not load them directly, so the PBR, SSAO, and custom shader composite are not activated by installing the filter.

## Project layout

- `shaders/` — standalone GLSL ES 3.00 shader stages and effects.
- `configs/` — Low, Medium, High, and Ultra quality presets plus sunrise, midday, golden-hour, and night lighting examples.
- `content-manager/` — Content Manager-compatible AC post-processing filter.
- `scripts/validate.py` — validates presets and performs shader source checks; uses `glslangValidator` when installed.
- `scripts/benchmark.py` — times repeated CPU-side validation runs (not GPU frame-time measurement).
- `scripts/optimize_texture.py` — losslessly recompresses PNGs while retaining their metadata and color profiles.
- `scripts/setup.py` — stages a source bundle or installs the filter into an Assetto Corsa game root.
- `tests/` — dependency-free unit tests.

## Requirements

- Python 3.9 or later for the utilities and tests.
- An OpenGL ES 3.0-capable shader runtime is required only to use the standalone GLSL ES sources.
- Optional: `glslangValidator` on `PATH` for compiler-backed shader validation.

The installed filter does not require a custom shader runtime. The standalone GLSL ES shaders target a different interface from Assetto Corsa and CSP; using them in-game requires porting them to the target renderer and providing its framebuffers, textures, uniforms, and pass scheduling.

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

## Install and select in Content Manager

Install the filter directly into the game's post-processing filters directory:

```sh
python3 scripts/setup.py --game-root "/path/to/assettocorsa"
```

The installer checks for `acs.exe` or `acs_x86.exe`, then copies the filter to `system/cfg/ppfilters/assetto-corsa-graphics-mod.ini`. It refuses to overwrite an existing copy unless `--force` is specified.

In Content Manager, enable post-processing and choose **assetto-corsa-graphics-mod** from Assetto Corsa's post-processing filter list. Restart the session if Content Manager does not refresh the filter list. To remove the mod, delete that single `.ini` file from `system/cfg/ppfilters`.

To stage a portable source bundle instead, run:

```sh
python3 scripts/setup.py --destination /path/to/mods
```

This creates or updates an `assetto-corsa-graphics-mod` subfolder and does not modify the game installation.

## Limitations and next steps

The Content Manager filter uses the built-in YEBIS effects; it does not load the GLSL ES sources. Those shaders remain renderer-independent examples and are not yet ported to CSP's native shader format. The toolkit also does not implement a live adjustment UI, GPU profiling, bloom generation, motion-vector generation, refraction, texture baking, or DDS optimization. The included CPU benchmark is intentionally labeled to avoid implying GPU profiling. Test any shader port against its target compiler and a backed-up game installation.
