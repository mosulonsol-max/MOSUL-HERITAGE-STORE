import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "generate_artwork.py"
SPEC = importlib.util.spec_from_file_location("generate_artwork", MODULE_PATH)
ARTWORK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ARTWORK)

CPU_MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "generate_cpu.py"
CPU_SPEC = importlib.util.spec_from_file_location("generate_cpu", CPU_MODULE_PATH)
CPU = importlib.util.module_from_spec(CPU_SPEC)
CPU_SPEC.loader.exec_module(CPU)


class BackendTests(unittest.TestCase):
    def test_cpu_reference_rejects_unapproved_hosts_before_network_access(self):
        with self.assertRaisesRegex(ValueError, "Library of Congress"):
            CPU.download_reference("https://example.com/untrusted.jpg")

    def test_cpu_backend_invokes_bounded_generator(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "out.png"

            def fake_run(command, **kwargs):
                self.assertTrue(str(command[1]).endswith("generate_cpu.py"))
                Image.new("RGB", (512, 512), "navy").save(output)
                return type("Done", (), {"stdout": json.dumps({
                    "model": "segmind/small-sd", "model_revision": "pinned", "seed": 7
                })})()

            with patch.dict(os.environ, {"ARTWORK_BACKEND": "cpu-free"}, clear=False), \
                 patch.object(ARTWORK.subprocess, "run", side_effect=fake_run):
                raw = ARTWORK.get_png("safe architectural art", output)
            self.assertTrue(raw.startswith(b"\x89PNG\r\n\x1a\n"))
            self.assertEqual(ARTWORK.GENERATION_DETAILS["seed"], 7)

    def test_visual_quality_rejects_uniform_image(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "flat.png"
            Image.new("RGB", (512, 512), "navy").save(output)
            with self.assertRaisesRegex(ValueError, "visual-quality"):
                ARTWORK.validate_visual_quality(output.read_bytes())

    def test_visual_quality_accepts_varied_image(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "varied.png"
            image = Image.new("RGB", (512, 512))
            image.putdata([
                (x // 2, y // 2, (x + y) // 4)
                for y in range(512) for x in range(512)
            ])
            image.save(output)
            result = ARTWORK.validate_visual_quality(output.read_bytes())
            self.assertEqual(result["status"], "passed")

    def test_unknown_backend_fails_closed(self):
        with tempfile.TemporaryDirectory() as folder, \
             patch.dict(os.environ, {"ARTWORK_BACKEND": "unknown"}, clear=False):
            with self.assertRaisesRegex(ValueError, "cpu-free"):
                ARTWORK.get_png("prompt", Path(folder) / "out.png")


if __name__ == "__main__":
    unittest.main()
