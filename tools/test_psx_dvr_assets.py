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
        self.assertEqual(self.manifest["scale_reference"]["character"], "five_head_chibi_1_40m")
        self.assertEqual(self.manifest["style"]["detail_level"], "higher_detail_lowpoly")
        self.assertEqual(self.manifest["style"]["color_policy"], "preserve_existing_palette")

    def test_crt_tv_asset_metadata_budget_and_black_glass_screen(self):
        self.assertIn("crt_tv", self.assets)
        crt = self.assets["crt_tv"]
        self.assertEqual(crt["texture_size"], [256, 256])
        self.assertEqual(crt["screen_state"], "black_glass")
        self.assertEqual(crt["front_style"], "large_bezel_box_crt")
        self.assertEqual(crt["screen_material"], "convex_black_glass")
        self.assertEqual(crt["control_layout"], "bottom_button_row")
        self.assertEqual(crt["scale_reference"], "five_head_chibi_1_40m")
        self.assertGreaterEqual(crt["triangles"], 2200)
        self.assertLessEqual(crt["triangles"], 5200)
        self.assertLessEqual(crt["dimensions"][0], 0.80)
        self.assertLessEqual(crt["dimensions"][2], 0.70)
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
        self.assertAlmostEqual(desk["dimensions"][2], 0.72, delta=0.05)
        self.assertLessEqual(bookshelf["dimensions"][2], 1.75)
        for asset in (bookshelf, desk):
            self.assertEqual(asset["texture_size"], [256, 256])
            self.assertEqual(asset["scale_reference"], "five_head_chibi_1_40m")
            self.assertGreaterEqual(asset["triangles"], 1800)
            self.assertLessEqual(asset["triangles"], 5200)
            self.assertTrue((ROOT / asset["glb"]).exists())
            self.assertTrue((ROOT / asset["texture"]).exists())
            self.assertTrue((ROOT / asset["preview"]).exists())

    def test_beanbag_chair_is_player_sittable_room_asset(self):
        self.assertIn("beanbag_chair", self.assets)
        beanbag = self.assets["beanbag_chair"]
        self.assertEqual(beanbag["seat_role"], "player_sittable")
        self.assertEqual(beanbag["shape_construction"], "single_sculpted_body")
        self.assertEqual(beanbag["sculpt_base"], "uv_sphere")
        self.assertEqual(beanbag["fabric_style"], "sculpted_green_velour")
        self.assertEqual(beanbag["texture_size"], [256, 256])
        self.assertEqual(beanbag["scale_reference"], "five_head_chibi_1_40m")
        self.assertGreaterEqual(beanbag["triangles"], 2200)
        self.assertLessEqual(beanbag["triangles"], 5600)
        self.assertGreater(beanbag["dimensions"][0], self.assets["crt_tv"]["dimensions"][0] * 0.75)
        self.assertGreater(beanbag["dimensions"][1], self.assets["crt_tv"]["dimensions"][1] * 0.75)
        self.assertLessEqual(beanbag["dimensions"][2], 0.70)
        self.assertIn("beanbag_uv_sphere_sculpted_body", beanbag["source_parts"])
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
        self.assertEqual(rug["scale_reference"], "five_head_chibi_1_40m")
        self.assertGreaterEqual(rug["triangles"], 1200)
        self.assertLessEqual(rug["triangles"], 3200)
        self.assertGreater(rug["dimensions"][0], self.assets["beanbag_chair"]["dimensions"][0])
        self.assertLessEqual(rug["dimensions"][2], 0.08)
        self.assertIn("disc_rug_outer_round_mat", rug["source_parts"])
        self.assertIn("disc_rug_center_label", rug["source_parts"])
        self.assertTrue((ROOT / rug["glb"]).exists())
        self.assertTrue((ROOT / rug["texture"]).exists())
        self.assertTrue((ROOT / rug["preview"]).exists())

    def test_emi_room_scene_includes_requested_layout(self):
        self.assertIn("emi_room", self.assets)
        room = self.assets["emi_room"]
        self.assertEqual(room["scene_role"], "character_room")
        self.assertEqual(room["room_owner"], "emi")
        self.assertEqual(room["texture_size"], [512, 512])
        self.assertEqual(room["scale_reference"], "five_head_chibi_1_40m")
        self.assertGreaterEqual(room["triangles"], 22000)
        self.assertLessEqual(room["triangles"], 62000)
        self.assertLessEqual(room["dimensions"][0], 4.50)
        self.assertLessEqual(room["dimensions"][2], 2.70)
        self.assertGreaterEqual(room["poster_count"], 10)
        self.assertLessEqual(room["poster_count"], 15)
        self.assertEqual(room["disc_count_on_desk"], 3)
        self.assertGreaterEqual(room["floor_book_count"], 5)
        self.assertGreaterEqual(room["floor_cd_case_count"], 4)
        for key in (
            "bookshelf",
            "desk",
            "crt_tv",
            "psx_dvr_console",
            "psx_dvr_disc",
            "disc_rug",
            "poster",
            "draft_paper",
            "table_lamp",
            "pencil",
            "eraser",
            "potted_plant",
            "wheeled_lounge_chair",
            "floor_book",
            "cd_case",
        ):
            self.assertIn(key, room["included_assets"])
        for part in (
            "emi_room_back_wall",
            "emi_room_desk_cluster",
            "emi_room_poster_00",
            "emi_room_table_lamp",
            "emi_room_wheeled_lounge_chair",
            "emi_room_bookshelf_planter",
            "emi_room_floor_book_00",
            "emi_room_floor_cd_case_00",
        ):
            self.assertIn(part, room["source_parts"])
        self.assertTrue((ROOT / room["glb"]).exists())
        self.assertTrue((ROOT / room["texture"]).exists())
        self.assertTrue((ROOT / room["preview"]).exists())

    def test_existing_core_assets_have_higher_detail_and_chibi_scale(self):
        expectations = {
            "psx_dvr_console": ((1800, 4200), (0.50, 0.50, 0.20)),
            "psx_dvr_disc": ((700, 1800), (0.16, 0.16, 0.04)),
        }
        for name, (triangle_range, max_dimensions) in expectations.items():
            asset = self.assets[name]
            self.assertEqual(asset["scale_reference"], "five_head_chibi_1_40m")
            self.assertGreaterEqual(asset["triangles"], triangle_range[0])
            self.assertLessEqual(asset["triangles"], triangle_range[1])
            for value, max_value in zip(asset["dimensions"], max_dimensions):
                self.assertLessEqual(value, max_value)

    def test_room_clutter_is_packaged_as_individual_assets(self):
        expected_assets = {
            "poster": "wall_decor",
            "draft_paper": "desk_clutter",
            "table_lamp": "desk_lighting",
            "pencil": "desk_clutter",
            "eraser": "desk_clutter",
            "potted_plant": "shelf_decor",
            "wheeled_lounge_chair": "player_seat",
            "floor_book": "floor_clutter",
            "cd_case": "floor_clutter",
        }
        for name, role in expected_assets.items():
            self.assertIn(name, self.assets)
            asset = self.assets[name]
            self.assertEqual(asset["asset_role"], role)
            self.assertEqual(asset["scale_reference"], "five_head_chibi_1_40m")
            self.assertGreaterEqual(asset["triangles"], 80)
            self.assertLessEqual(asset["triangles"], 1800)
            self.assertTrue((ROOT / asset["glb"]).exists())
            self.assertTrue((ROOT / asset["texture"]).exists())
            self.assertTrue((ROOT / asset["preview"]).exists())


if __name__ == "__main__":
    unittest.main()
