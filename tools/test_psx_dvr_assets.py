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

    def test_crt_tv_asset_metadata_and_budget(self):
        self.assertIn("crt_tv", self.assets)
        crt = self.assets["crt_tv"]
        self.assertEqual(crt["texture_size"], [256, 256])
        self.assertGreaterEqual(crt["triangles"], 900)
        self.assertLessEqual(crt["triangles"], 1800)
        self.assertTrue((ROOT / crt["glb"]).exists())
        self.assertTrue((ROOT / crt["texture"]).exists())
        self.assertTrue((ROOT / crt["preview"]).exists())

    def test_integrated_set_is_blender_importable_glb(self):
        self.assertIn("psx_dvr_crt_set", self.assets)
        asset_set = self.assets["psx_dvr_crt_set"]
        self.assertEqual(asset_set["blender_import"], "Import GLB in Blender")
        self.assertEqual(asset_set["contains"], ["psx_dvr_console", "psx_dvr_disc", "crt_tv"])
        self.assertTrue((ROOT / asset_set["glb"]).exists())
        self.assertTrue((ROOT / asset_set["preview"]).exists())


if __name__ == "__main__":
    unittest.main()
