"""Install Blender MCP addon and build a usable PSX DVR Blender asset scene."""

from __future__ import annotations

import json
from pathlib import Path

import bpy


ROOT = Path(r"D:\游戏制作\X. WHEEL")
ADDON_PATH = ROOT / "tools" / "blender_mcp" / "addon.py"
CONSOLE_GLB = ROOT / "assets" / "3d" / "psx_dvr_console" / "psx_dvr_console.glb"
DISC_GLB = ROOT / "assets" / "3d" / "psx_dvr_disc" / "psx_dvr_disc.glb"
CRT_GLB = ROOT / "assets" / "3d" / "crt_tv" / "crt_tv.glb"
BOOKSHELF_GLB = ROOT / "assets" / "3d" / "bookshelf" / "bookshelf.glb"
DESK_GLB = ROOT / "assets" / "3d" / "desk" / "desk.glb"
BEANBAG_GLB = ROOT / "assets" / "3d" / "beanbag_chair" / "beanbag_chair.glb"
RUG_GLB = ROOT / "assets" / "3d" / "disc_rug" / "disc_rug.glb"
EMI_ROOM_GLB = ROOT / "assets" / "3d" / "emi_room" / "emi_room.glb"
POSTER_GLB = ROOT / "assets" / "3d" / "poster" / "poster.glb"
DRAFT_PAPER_GLB = ROOT / "assets" / "3d" / "draft_paper" / "draft_paper.glb"
TABLE_LAMP_GLB = ROOT / "assets" / "3d" / "table_lamp" / "table_lamp.glb"
PENCIL_GLB = ROOT / "assets" / "3d" / "pencil" / "pencil.glb"
ERASER_GLB = ROOT / "assets" / "3d" / "eraser" / "eraser.glb"
POTTED_PLANT_GLB = ROOT / "assets" / "3d" / "potted_plant" / "potted_plant.glb"
WHEELED_LOUNGE_CHAIR_GLB = ROOT / "assets" / "3d" / "wheeled_lounge_chair" / "wheeled_lounge_chair.glb"
FLOOR_BOOK_GLB = ROOT / "assets" / "3d" / "floor_book" / "floor_book.glb"
CD_CASE_GLB = ROOT / "assets" / "3d" / "cd_case" / "cd_case.glb"
OUTPUT_BLEND = ROOT / "assets" / "3d" / "psx_dvr_assets.blend"
REPORT_PATH = ROOT / "assets" / "3d" / "psx_dvr_blender_import_report.json"

ASSET_SPECS = [
    ("psx_dvr_console", CONSOLE_GLB),
    ("psx_dvr_disc", DISC_GLB),
    ("crt_tv", CRT_GLB),
    ("bookshelf", BOOKSHELF_GLB),
    ("desk", DESK_GLB),
    ("beanbag_chair", BEANBAG_GLB),
    ("disc_rug", RUG_GLB),
    ("poster", POSTER_GLB),
    ("draft_paper", DRAFT_PAPER_GLB),
    ("table_lamp", TABLE_LAMP_GLB),
    ("pencil", PENCIL_GLB),
    ("eraser", ERASER_GLB),
    ("potted_plant", POTTED_PLANT_GLB),
    ("wheeled_lounge_chair", WHEELED_LOUNGE_CHAIR_GLB),
    ("floor_book", FLOOR_BOOK_GLB),
    ("cd_case", CD_CASE_GLB),
    ("emi_room", EMI_ROOM_GLB),
]


def install_blender_mcp_addon() -> str:
    if not ADDON_PATH.exists():
        raise FileNotFoundError(f"Missing Blender MCP addon: {ADDON_PATH}")

    bpy.ops.preferences.addon_install(filepath=str(ADDON_PATH), overwrite=True)

    # Single-file addons use the source filename as the module name.
    module_name = ADDON_PATH.stem
    bpy.ops.preferences.addon_enable(module=module_name)

    addon = bpy.context.preferences.addons.get(module_name)
    if addon and hasattr(addon.preferences, "telemetry_consent"):
        addon.preferences.telemetry_consent = False

    bpy.ops.wm.save_userpref()
    return module_name


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def import_glb(filepath: Path, collection_name: str, x_offset: float) -> list[bpy.types.Object]:
    if not filepath.exists():
        raise FileNotFoundError(f"Missing GLB: {filepath}")

    collection = bpy.data.collections.new(collection_name)
    bpy.context.scene.collection.children.link(collection)

    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(filepath))
    imported = [obj for obj in bpy.data.objects if obj not in before]
    mesh_imports = [obj for obj in imported if obj.type == "MESH"]
    if len(mesh_imports) != 1:
        raise RuntimeError(f"{collection_name}: expected 1 mesh object from GLB, got {len(mesh_imports)}")

    for obj in imported:
        for linked_collection in list(obj.users_collection):
            linked_collection.objects.unlink(obj)
        collection.objects.link(obj)
        obj.location.x += x_offset
        obj.asset_mark()
        obj.asset_data.description = f"Low-poly PSX DVR asset: {collection_name}"

        if obj.type == "MESH":
            obj.name = collection_name
            obj.data.asset_mark()
            obj.data.name = f"{collection_name}_mesh"
            for polygon in obj.data.polygons:
                polygon.use_smooth = False

    return imported


def make_scene_usable() -> None:
    bpy.context.scene.unit_settings.system = "METRIC"

    camera_data = bpy.data.cameras.new("cam_psx_dvr_asset_preview")
    camera = bpy.data.objects.new("cam_psx_dvr_asset_preview", camera_data)
    bpy.context.scene.collection.objects.link(camera)
    camera.location = (7.4, -10.2, 5.2)
    camera.rotation_euler = (1.05, 0.0, 0.62)
    camera.data.lens = 32
    bpy.context.scene.camera = camera

    light_data = bpy.data.lights.new("key_area_light", "AREA")
    light = bpy.data.objects.new("key_area_light", light_data)
    bpy.context.scene.collection.objects.link(light)
    light.location = (1.8, -3.2, 4.0)
    light.data.energy = 450
    light.data.size = 4.0

    empty = bpy.data.objects.new("asset_origin_reference", None)
    bpy.context.scene.collection.objects.link(empty)
    empty.empty_display_type = "PLAIN_AXES"
    empty.empty_display_size = 0.45

    bpy.context.scene.render.engine = "BLENDER_EEVEE_NEXT"
    bpy.context.scene.eevee.taa_render_samples = 32
    bpy.context.scene.view_settings.view_transform = "Standard"
    bpy.context.scene.view_settings.look = "Medium High Contrast"
    bpy.context.scene.world.color = (0.035, 0.037, 0.04)


def collect_report(
    addon_module: str,
    imported_by_asset: dict[str, list[bpy.types.Object]],
) -> dict:
    mesh_objects = [obj for obj in bpy.data.objects if obj.type == "MESH"]
    return {
        "addon_module": addon_module,
        "blend": str(OUTPUT_BLEND),
        "source_glbs": [str(path) for _, path in ASSET_SPECS],
        "collections": {name: [obj.name for obj in objects] for name, objects in imported_by_asset.items()},
        "mesh_object_count": len(mesh_objects),
        "material_count": len(bpy.data.materials),
        "image_count": len(bpy.data.images),
        "asset_marked_objects": [obj.name for obj in bpy.data.objects if obj.asset_data is not None],
    }


def main() -> None:
    addon_module = install_blender_mcp_addon()
    clear_scene()
    imported_by_asset = {}
    for index, (name, path) in enumerate(ASSET_SPECS):
        imported_by_asset[name] = import_glb(path, name, -8.0 + index * 1.15)
    make_scene_usable()

    OUTPUT_BLEND.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT_BLEND))

    report = collect_report(addon_module, imported_by_asset)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
