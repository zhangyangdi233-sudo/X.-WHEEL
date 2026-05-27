import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "assets" / "3d" / "psx_dvr_assets_manifest.json"


class PsxDvrAssetsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run(
            [sys.executable, str(ROOT / "tools" / "create_psx_dvr_assets.py")],
            cwd=ROOT,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        cls.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        cls.assets = cls.manifest["assets"]

    def test_manifest_declares_shared_palette(self):
        self.assertEqual(self.manifest["palette"]["primary"], ["#3FA943", "#E8F8E4", "#0C1725"])

    def test_crt_tv_asset_metadata_budget_and_black_glass_screen(self):
        self.assertIn("crt_tv", self.assets)
        crt = self.assets["crt_tv"]
        self.assertEqual(crt["texture_size"], [256, 256])
        self.assertEqual(crt["screen_state"], "black_glass")
        self.assertGreaterEqual(crt["triangles"], 900)
        self.assertLessEqual(crt["triangles"], 1800)
        self.assertGreater(crt["dimensions"][0], self.assets["psx_dvr_console"]["dimensions"][0] * 0.6)
        self.assertTrue((ROOT / crt["glb"]).exists())
        self.assertTrue((ROOT / crt["texture"]).exists())
        self.assertTrue((ROOT / crt["preview"]).exists())

    def test_no_integrated_set_asset_is_generated(self):
        self.assertNotIn("psx_dvr_crt_set", self.assets)
        self.assertFalse((ROOT / "assets" / "3d" / "psx_dvr_crt_set" / "psx_dvr_crt_set.glb").exists())
        self.assertFalse((ROOT / "assets" / "3d" / "psx_dvr_crt_set" / "psx_dvr_crt_set_texture.png").exists())
        self.assertFalse((ROOT / "assets" / "3d" / "psx_dvr_crt_set" / "psx_dvr_crt_set_preview.png").exists())

    def test_bookshelf_and_desk_assets_are_larger_than_crt(self):
        self.assertIn("bookshelf", self.assets)
        self.assertIn("desk", self.assets)
        crt = self.assets["crt_tv"]
        bookshelf = self.assets["bookshelf"]
        desk = self.assets["desk"]
        self.assertGreater(bookshelf["dimensions"][2], crt["dimensions"][2])
        self.assertGreater(bookshelf["dimensions"][0], crt["dimensions"][0])
        self.assertGreater(desk["dimensions"][0], crt["dimensions"][0])
        self.assertGreater(desk["dimensions"][1], crt["dimensions"][1])
        for asset in (bookshelf, desk):
            self.assertEqual(asset["texture_size"], [256, 256])
            self.assertGreaterEqual(asset["triangles"], 900)
            self.assertLessEqual(asset["triangles"], 1800)
            self.assertTrue((ROOT / asset["glb"]).exists())
            self.assertTrue((ROOT / asset["texture"]).exists())
            self.assertTrue((ROOT / asset["preview"]).exists())


if __name__ == "__main__":
    unittest.main()
