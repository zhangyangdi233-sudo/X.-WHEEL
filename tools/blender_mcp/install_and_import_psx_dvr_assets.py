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
OUTPUT_BLEND = ROOT / "assets" / "3d" / "psx_dvr_assets.blend"
REPORT_PATH = ROOT / "assets" / "3d" / "psx_dvr_blender_import_report.json"


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
    console_objects: list[bpy.types.Object],
    disc_objects: list[bpy.types.Object],
    crt_objects: list[bpy.types.Object],
    bookshelf_objects: list[bpy.types.Object],
    desk_objects: list[bpy.types.Object],
    beanbag_objects: list[bpy.types.Object],
    rug_objects: list[bpy.types.Object],
) -> dict:
    mesh_objects = [obj for obj in bpy.data.objects if obj.type == "MESH"]
    return {
        "addon_module": addon_module,
        "blend": str(OUTPUT_BLEND),
        "source_glbs": [str(CONSOLE_GLB), str(DISC_GLB), str(CRT_GLB), str(BOOKSHELF_GLB), str(DESK_GLB), str(BEANBAG_GLB), str(RUG_GLB)],
        "collections": {
            "psx_dvr_console": [obj.name for obj in console_objects],
            "psx_dvr_disc": [obj.name for obj in disc_objects],
            "crt_tv": [obj.name for obj in crt_objects],
            "bookshelf": [obj.name for obj in bookshelf_objects],
            "desk": [obj.name for obj in desk_objects],
            "beanbag_chair": [obj.name for obj in beanbag_objects],
            "disc_rug": [obj.name for obj in rug_objects],
        },
        "mesh_object_count": len(mesh_objects),
        "material_count": len(bpy.data.materials),
        "image_count": len(bpy.data.images),
        "asset_marked_objects": [obj.name for obj in bpy.data.objects if obj.asset_data is not None],
    }


def main() -> None:
    addon_module = install_blender_mcp_addon()
    clear_scene()
    console_objects = import_glb(CONSOLE_GLB, "psx_dvr_console", -5.0)
    disc_objects = import_glb(DISC_GLB, "psx_dvr_disc", -2.8)
    crt_objects = import_glb(CRT_GLB, "crt_tv", -0.7)
    bookshelf_objects = import_glb(BOOKSHELF_GLB, "bookshelf", 2.0)
    desk_objects = import_glb(DESK_GLB, "desk", 5.0)
    beanbag_objects = import_glb(BEANBAG_GLB, "beanbag_chair", 7.8)
    rug_objects = import_glb(RUG_GLB, "disc_rug", 10.2)
    make_scene_usable()

    OUTPUT_BLEND.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT_BLEND))

    report = collect_report(addon_module, console_objects, disc_objects, crt_objects, bookshelf_objects, desk_objects, beanbag_objects, rug_objects)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
