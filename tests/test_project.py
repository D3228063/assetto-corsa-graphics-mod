import configparser
import json
import struct
import tempfile
import unittest
from pathlib import Path
import zlib

from scripts.optimize_texture import make_chunk, optimize_png
from scripts.validate import validate_presets, validate_scenarios, validate_shaders
from scripts.setup import install, stage


class PresetValidationTests(unittest.TestCase):
    def test_repository_presets_are_valid(self):
        presets = validate_presets()
        self.assertEqual(set(presets["presets"]), {"Low", "Medium", "High", "Ultra"})

    def test_rejects_out_of_range_preset_value(self):
        presets = json.loads((Path(__file__).parents[1] / "configs" / "presets.json").read_text())
        presets["presets"]["Low"]["exposure"] = -1
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "presets.json"
            config.write_text(json.dumps(presets))
            with self.assertRaisesRegex(ValueError, "exposure"):
                validate_presets(config)

    def test_repository_lighting_scenarios_are_valid(self):
        scenarios = validate_scenarios()
        self.assertEqual(set(scenarios["scenarios"]), {"Sunrise", "Midday", "Golden hour", "Night"})


class ShaderValidationTests(unittest.TestCase):
    def test_repository_shaders_pass_source_checks(self):
        self.assertEqual(validate_shaders(), 7)

    def test_rejects_unbalanced_shader(self):
        with tempfile.TemporaryDirectory() as directory:
            shader = Path(directory) / "broken.frag"
            shader.write_text("#version 300 es\nvoid main() {\n")
            with self.assertRaisesRegex(ValueError, "unbalanced"):
                validate_shaders(directory)


class SetupTests(unittest.TestCase):
    def test_stages_shader_and_config_files(self):
        with tempfile.TemporaryDirectory() as directory:
            bundle = stage(directory)
            self.assertTrue((bundle / "shaders" / "pbr.frag").is_file())
            self.assertTrue((bundle / "configs" / "presets.json").is_file())
            self.assertTrue((bundle / "content-manager" / "assetto-corsa-graphics-mod.ini").is_file())

    def test_content_manager_filter_has_supported_sections(self):
        config = configparser.ConfigParser()
        config.read(Path(__file__).parents[1] / "content-manager" / "assetto-corsa-graphics-mod.ini")
        self.assertTrue(config.getboolean("YEBIS", "ENABLED"))
        self.assertTrue(config.getboolean("AUTO_EXPOSURE", "ENABLED"))
        self.assertAlmostEqual(config.getfloat("COLOR", "CONTRAST"), 1.04)

    def test_installs_post_processing_filter_to_game_root(self):
        with tempfile.TemporaryDirectory() as directory:
            game_root = Path(directory)
            (game_root / "acs.exe").touch()
            installed = install(game_root)
            self.assertEqual(installed, game_root / "system" / "cfg" / "ppfilters" / "assetto-corsa-graphics-mod.ini")
            self.assertTrue(installed.is_file())

    def test_requires_game_root_marker_and_protects_existing_filter(self):
        with tempfile.TemporaryDirectory() as directory:
            game_root = Path(directory)
            with self.assertRaisesRegex(ValueError, "game root"):
                install(game_root)
            (game_root / "acs.exe").touch()
            destination = game_root / "system" / "cfg" / "ppfilters" / "assetto-corsa-graphics-mod.ini"
            destination.parent.mkdir(parents=True)
            destination.write_text("user version")
            with self.assertRaises(FileExistsError):
                install(game_root)
            self.assertEqual(destination.read_text(), "user version")


class TextureOptimizationTests(unittest.TestCase):
    def test_recompresses_png_without_changing_pixels_or_metadata(self):
        raw_pixels = b"\x00\xff\x00\x00"
        png = (
            b"\x89PNG\r\n\x1a\n"
            + make_chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
            + make_chunk(b"IDAT", zlib.compress(raw_pixels, level=1))
            + make_chunk(b"tEXt", b"Description\x00test")
            + make_chunk(b"IEND", b"")
        )
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.png"
            destination = Path(directory) / "optimized.png"
            source.write_bytes(png)
            optimize_png(source, destination)
            result = destination.read_bytes()

        offset = len(b"\x89PNG\r\n\x1a\n")
        chunks = []
        compressed = bytearray()
        while offset < len(result):
            length = struct.unpack_from(">I", result, offset)[0]
            chunk_type = result[offset + 4:offset + 8]
            payload = result[offset + 8:offset + 8 + length]
            chunks.append(chunk_type)
            if chunk_type == b"IDAT":
                compressed.extend(payload)
            offset += length + 12
        self.assertEqual(zlib.decompress(compressed), raw_pixels)
        self.assertIn(b"tEXt", chunks)
        self.assertLess(chunks.index(b"IDAT"), chunks.index(b"tEXt"))
        self.assertLess(chunks.index(b"tEXt"), chunks.index(b"IEND"))

    def test_refuses_to_overwrite_output_by_default(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.png"
            destination = Path(directory) / "existing.png"
            source.write_bytes(b"not a png")
            destination.write_bytes(b"preserve")
            with self.assertRaises(FileExistsError):
                optimize_png(source, destination)
            self.assertEqual(destination.read_bytes(), b"preserve")


if __name__ == "__main__":
    unittest.main()
