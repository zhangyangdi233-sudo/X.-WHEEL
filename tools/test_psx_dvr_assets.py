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
        self.assertEqual(crt["front_style"], "large_bezel_box_crt")
        self.assertEqual(crt["screen_material"], "convex_black_glass")
        self.assertEqual(crt["control_layout"], "bottom_button_row")
        self.assertGreaterEqual(crt["triangles"], 900)
        self.assertLessEqual(crt["triangles"], 2200)
        self.assertGreater(crt["dimensions"][0], self.assets["psx_dvr_console"]["dimensions"][0] * 0.6)
        self.assertIn("crt_bottom_button_00", crt["source_parts"])
        self.assertIn("crt_large_black_glass_panel", crt["source_parts"])
        self.assertIn("crt_boxy_side_depth", crt["source_parts"])
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

    def test_beanbag_chair_is_player_sittable_room_asset(self):
        self.assertIn("beanbag_chair", self.assets)
        beanbag = self.assets["beanbag_chair"]
        self.assertEqual(beanbag["seat_role"], "player_sittable")
        self.assertEqual(beanbag["shape_construction"], "single_sculpted_body")
        self.assertEqual(beanbag["fabric_style"], "sculpted_green_velour")
        self.assertEqual(beanbag["texture_size"], [256, 256])
        self.assertGreaterEqual(beanbag["triangles"], 900)
        self.assertLessEqual(beanbag["triangles"], 2200)
        self.assertGreater(beanbag["dimensions"][0], self.assets["crt_tv"]["dimensions"][0] * 0.75)
        self.assertGreater(beanbag["dimensions"][1], self.assets["crt_tv"]["dimensions"][1] * 0.75)
        self.assertIn("beanbag_sculpted_body", beanbag["source_parts"])
        self.assertIn("beanbag_center_sink", beanbag["source_parts"])
        self.assertNotIn("beanbag_left_arm_cushion", beanbag["source_parts"])
        self.assertNotIn("beanbag_back_cushion", beanbag["source_parts"])
        self.assertTrue((ROOT / beanbag["glb"]).exists())
        self.assertTrue((ROOT / beanbag["texture"]).exists())
        self.assertTrue((ROOT / beanbag["preview"]).exists())

    def test_disc_rug_is_generated_as_round_floor_asset(self):
        self.assertIn("disc_rug", self.assets)
        rug = self.assets["disc_rug"]
        self.assertEqual(rug["surface_role"], "floor_rug")
        self.assertEqual(rug["rug_style"], "green_disc_rug")
        self.assertEqual(rug["texture_size"], [256, 256])
        self.assertGreaterEqual(rug["triangles"], 250)
        self.assertLessEqual(rug["triangles"], 1200)
        self.assertGreater(rug["dimensions"][0], self.assets["beanbag_chair"]["dimensions"][0])
        self.assertLessEqual(rug["dimensions"][2], 0.08)
        self.assertIn("disc_rug_outer_round_mat", rug["source_parts"])
        self.assertIn("disc_rug_center_label", rug["source_parts"])
        self.assertTrue((ROOT / rug["glb"]).exists())
        self.assertTrue((ROOT / rug["texture"]).exists())
        self.assertTrue((ROOT / rug["preview"]).exists())


if __name__ == "__main__":
    unittest.main()
