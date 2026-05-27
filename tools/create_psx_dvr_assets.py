"""Generate low-poly PSX DVR-inspired GLB assets with no third-party deps."""

from __future__ import annotations

import argparse
import binascii
import json
import math
import os
import struct
import zlib
from dataclasses import dataclass, field
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = ROOT / "assets" / "3d"
MANIFEST_PATH = ASSET_ROOT / "psx_dvr_assets_manifest.json"


FONT_5X7 = {
    " ": ["00000", "00000", "00000", "00000", "00000", "00000", "00000"],
    "+": ["00000", "00100", "00100", "11111", "00100", "00100", "00000"],
    "-": ["00000", "00000", "00000", "11111", "00000", "00000", "00000"],
    ".": ["00000", "00000", "00000", "00000", "00000", "01100", "01100"],
    "/": ["00001", "00010", "00100", "01000", "10000", "00000", "00000"],
    "0": ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00010", "00100", "01000", "11111"],
    "3": ["11110", "00001", "00001", "01110", "00001", "00001", "11110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "10000", "11110", "00001", "00001", "11110"],
    "6": ["00110", "01000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00010", "11100"],
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "C": ["01111", "10000", "10000", "10000", "10000", "10000", "01111"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "G": ["01111", "10000", "10000", "10011", "10001", "10001", "01111"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["11111", "00100", "00100", "00100", "00100", "00100", "11111"],
    "J": ["00111", "00010", "00010", "00010", "00010", "10010", "01100"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "Q": ["01110", "10001", "10001", "10001", "10101", "10010", "01101"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    "W": ["10001", "10001", "10001", "10101", "10101", "10101", "01010"],
    "X": ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    "Y": ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
    "Z": ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
}


@dataclass
class Material:
    name: str
    color: tuple[float, float, float, float]
    roughness: float = 0.85
    metallic: float = 0.0
    alpha_mode: str = "OPAQUE"


@dataclass
class Primitive:
    name: str
    material_index: int
    positions: list[tuple[float, float, float]]
    normals: list[tuple[float, float, float]]
    uvs: list[tuple[float, float]]
    colors: list[tuple[float, float, float, float]]
    indices: list[int]

    @property
    def triangle_count(self) -> int:
        return len(self.indices) // 3


@dataclass
class Asset:
    name: str
    output_dir: Path
    texture_size: tuple[int, int]
    texture_pixels: list[tuple[int, int, int, int]]
    materials: list[Material]
    primitives: list[Primitive] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def export_primitives(self) -> list[Primitive]:
        return [primitive for primitive in self.primitives if not primitive.name.startswith("col_")]

    @property
    def triangle_count(self) -> int:
        return sum(primitive.triangle_count for primitive in self.export_primitives)

    @property
    def material_count(self) -> int:
        return len(self.materials)

    @property
    def glb_path(self) -> Path:
        return self.output_dir / f"{self.name}.glb"

    @property
    def texture_path(self) -> Path:
        return self.output_dir / f"{self.name}_texture.png"

    @property
    def preview_path(self) -> Path:
        return self.output_dir / f"{self.name}_preview.png"


def clamp_byte(value: int) -> int:
    return max(0, min(255, int(value)))


def rgb_to_rgba(color: tuple[int, int, int], alpha: int = 255) -> tuple[int, int, int, int]:
    return (clamp_byte(color[0]), clamp_byte(color[1]), clamp_byte(color[2]), clamp_byte(alpha))


def float_color_to_rgba(color: tuple[float, float, float, float]) -> tuple[int, int, int, int]:
    return tuple(clamp_byte(channel * 255) for channel in color)  # type: ignore[return-value]


def make_canvas(width: int, height: int, color: tuple[int, int, int, int]) -> list[tuple[int, int, int, int]]:
    return [color for _ in range(width * height)]


def set_pixel(
    pixels: list[tuple[int, int, int, int]],
    width: int,
    height: int,
    x: int,
    y: int,
    color: tuple[int, int, int, int],
) -> None:
    if 0 <= x < width and 0 <= y < height:
        pixels[y * width + x] = color


def draw_rect(
    pixels: list[tuple[int, int, int, int]],
    width: int,
    height: int,
    x0: int,
    y0: int,
    x1: int,
    y1: int,
    color: tuple[int, int, int, int],
) -> None:
    xa, xb = sorted((max(0, x0), min(width - 1, x1)))
    ya, yb = sorted((max(0, y0), min(height - 1, y1)))
    for y in range(ya, yb + 1):
        base = y * width
        for x in range(xa, xb + 1):
            pixels[base + x] = color


def draw_line(
    pixels: list[tuple[int, int, int, int]],
    width: int,
    height: int,
    x0: int,
    y0: int,
    x1: int,
    y1: int,
    color: tuple[int, int, int, int],
) -> None:
    dx = abs(x1 - x0)
    sx = 1 if x0 < x1 else -1
    dy = -abs(y1 - y0)
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    x, y = x0, y0
    while True:
        set_pixel(pixels, width, height, x, y, color)
        if x == x1 and y == y1:
            break
        twice = 2 * err
        if twice >= dy:
            err += dy
            x += sx
        if twice <= dx:
            err += dx
            y += sy


def draw_text(
    pixels: list[tuple[int, int, int, int]],
    width: int,
    height: int,
    x: int,
    y: int,
    text: str,
    color: tuple[int, int, int, int],
    scale: int = 1,
) -> None:
    cursor = x
    for char in text.upper():
        glyph = FONT_5X7.get(char, FONT_5X7[" "])
        for row, bits in enumerate(glyph):
            for col, bit in enumerate(bits):
                if bit == "1":
                    for sy in range(scale):
                        for sx in range(scale):
                            set_pixel(pixels, width, height, cursor + col * scale + sx, y + row * scale + sy, color)
        cursor += 6 * scale


def write_png(path: Path, width: int, height: int, pixels: list[tuple[int, int, int, int]]) -> bytes:
    if len(pixels) != width * height:
        raise ValueError(f"Expected {width * height} pixels, got {len(pixels)}")

    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", binascii.crc32(kind + data) & 0xFFFFFFFF)

    raw_rows = bytearray()
    for y in range(height):
        raw_rows.append(0)
        for r, g, b, a in pixels[y * width : (y + 1) * width]:
            raw_rows.extend((r, g, b, a))

    png = bytearray(b"\x89PNG\r\n\x1a\n")
    png.extend(chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)))
    png.extend(chunk(b"IDAT", zlib.compress(bytes(raw_rows), level=9)))
    png.extend(chunk(b"IEND", b""))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(bytes(png))
    return bytes(png)


class MeshBuilder:
    def __init__(self, asset: Asset):
        self.asset = asset

    def add_primitive(
        self,
        name: str,
        material_index: int,
        positions: list[tuple[float, float, float]],
        normals: list[tuple[float, float, float]],
        uvs: list[tuple[float, float]],
        indices: list[int],
    ) -> None:
        color = self.asset.materials[material_index].color
        self.asset.primitives.append(
            Primitive(
                name=name,
                material_index=material_index,
                positions=positions,
                normals=normals,
                uvs=uvs,
                colors=[color for _ in positions],
                indices=indices,
            )
        )

    def add_box(
        self,
        name: str,
        center: tuple[float, float, float],
        size: tuple[float, float, float],
        material_index: int,
        uv_rect: tuple[float, float, float, float] = (0.02, 0.02, 0.18, 0.18),
    ) -> None:
        cx, cy, cz = center
        sx, sy, sz = (size[0] / 2, size[1] / 2, size[2] / 2)
        corners = {
            "lbf": (cx - sx, cy - sy, cz - sz),
            "rbf": (cx + sx, cy - sy, cz - sz),
            "rtf": (cx + sx, cy - sy, cz + sz),
            "ltf": (cx - sx, cy - sy, cz + sz),
            "lbb": (cx - sx, cy + sy, cz - sz),
            "rbb": (cx + sx, cy + sy, cz - sz),
            "rtb": (cx + sx, cy + sy, cz + sz),
            "ltb": (cx - sx, cy + sy, cz + sz),
        }
        faces = [
            (("lbf", "rbf", "rtf", "ltf"), (0.0, -1.0, 0.0)),
            (("rbb", "lbb", "ltb", "rtb"), (0.0, 1.0, 0.0)),
            (("lbb", "lbf", "ltf", "ltb"), (-1.0, 0.0, 0.0)),
            (("rbf", "rbb", "rtb", "rtf"), (1.0, 0.0, 0.0)),
            (("ltf", "rtf", "rtb", "ltb"), (0.0, 0.0, 1.0)),
            (("lbb", "rbb", "rbf", "lbf"), (0.0, 0.0, -1.0)),
        ]
        u0, v0, u1, v1 = uv_rect
        face_uv = [(u0, v1), (u1, v1), (u1, v0), (u0, v0)]
        positions: list[tuple[float, float, float]] = []
        normals: list[tuple[float, float, float]] = []
        uvs: list[tuple[float, float]] = []
        indices: list[int] = []
        for face_names, normal in faces:
            base = len(positions)
            for idx, corner_name in enumerate(face_names):
                positions.append(corners[corner_name])
                normals.append(normal)
                uvs.append(face_uv[idx])
            indices.extend((base, base + 1, base + 2, base, base + 2, base + 3))
        self.add_primitive(name, material_index, positions, normals, uvs, indices)

    def add_cylinder_z(
        self,
        name: str,
        center: tuple[float, float, float],
        radius: float,
        depth: float,
        sides: int,
        material_index: int,
        hole_radius: float = 0.0,
        uv_rect: tuple[float, float, float, float] = (0.22, 0.02, 0.38, 0.18),
    ) -> None:
        cx, cy, cz = center
        top_z = cz + depth / 2
        bottom_z = cz - depth / 2
        positions: list[tuple[float, float, float]] = []
        normals: list[tuple[float, float, float]] = []
        uvs: list[tuple[float, float]] = []
        indices: list[int] = []
        u0, v0, u1, v1 = uv_rect

        def uv_for(x: float, y: float) -> tuple[float, float]:
            return (u0 + (x / radius + 1.0) * 0.5 * (u1 - u0), v0 + (y / radius + 1.0) * 0.5 * (v1 - v0))

        for i in range(sides):
            a0 = (i / sides) * math.tau
            a1 = ((i + 1) / sides) * math.tau
            cos0, sin0 = math.cos(a0), math.sin(a0)
            cos1, sin1 = math.cos(a1), math.sin(a1)
            outer0 = (cx + radius * cos0, cy + radius * sin0)
            outer1 = (cx + radius * cos1, cy + radius * sin1)
            inner0 = (cx + hole_radius * cos0, cy + hole_radius * sin0)
            inner1 = (cx + hole_radius * cos1, cy + hole_radius * sin1)

            if hole_radius > 0:
                base = len(positions)
                ring_vertices = [
                    (outer0[0], outer0[1], top_z),
                    (outer1[0], outer1[1], top_z),
                    (inner1[0], inner1[1], top_z),
                    (inner0[0], inner0[1], top_z),
                    (outer1[0], outer1[1], bottom_z),
                    (outer0[0], outer0[1], bottom_z),
                    (inner0[0], inner0[1], bottom_z),
                    (inner1[0], inner1[1], bottom_z),
                ]
                positions.extend(ring_vertices)
                normals.extend([(0.0, 0.0, 1.0)] * 4 + [(0.0, 0.0, -1.0)] * 4)
                uvs.extend([uv_for(px - cx, py - cy) for px, py, _ in ring_vertices])
                indices.extend((base, base + 1, base + 2, base, base + 2, base + 3))
                indices.extend((base + 4, base + 5, base + 6, base + 4, base + 6, base + 7))

                base = len(positions)
                outer_vertices = [
                    (outer1[0], outer1[1], top_z),
                    (outer0[0], outer0[1], top_z),
                    (outer0[0], outer0[1], bottom_z),
                    (outer1[0], outer1[1], bottom_z),
                ]
                positions.extend(outer_vertices)
                normal_outer = (math.cos((a0 + a1) / 2), math.sin((a0 + a1) / 2), 0.0)
                normals.extend([normal_outer] * 4)
                uvs.extend(((u0, v0), (u1, v0), (u1, v1), (u0, v1)))
                indices.extend((base, base + 1, base + 2, base, base + 2, base + 3))

                base = len(positions)
                inner_vertices = [
                    (inner0[0], inner0[1], top_z),
                    (inner1[0], inner1[1], top_z),
                    (inner1[0], inner1[1], bottom_z),
                    (inner0[0], inner0[1], bottom_z),
                ]
                positions.extend(inner_vertices)
                normal_inner = (-math.cos((a0 + a1) / 2), -math.sin((a0 + a1) / 2), 0.0)
                normals.extend([normal_inner] * 4)
                uvs.extend(((u0, v0), (u1, v0), (u1, v1), (u0, v1)))
                indices.extend((base, base + 1, base + 2, base, base + 2, base + 3))
            else:
                base = len(positions)
                top_center = (cx, cy, top_z)
                bottom_center = (cx, cy, bottom_z)
                sector_vertices = [
                    top_center,
                    (outer0[0], outer0[1], top_z),
                    (outer1[0], outer1[1], top_z),
                    bottom_center,
                    (outer1[0], outer1[1], bottom_z),
                    (outer0[0], outer0[1], bottom_z),
                ]
                positions.extend(sector_vertices)
                normals.extend([(0.0, 0.0, 1.0)] * 3 + [(0.0, 0.0, -1.0)] * 3)
                uvs.extend([uv_for(px - cx, py - cy) for px, py, _ in sector_vertices])
                indices.extend((base, base + 1, base + 2, base + 3, base + 4, base + 5))

                base = len(positions)
                side_vertices = [
                    (outer1[0], outer1[1], top_z),
                    (outer0[0], outer0[1], top_z),
                    (outer0[0], outer0[1], bottom_z),
                    (outer1[0], outer1[1], bottom_z),
                ]
                positions.extend(side_vertices)
                normal_side = (math.cos((a0 + a1) / 2), math.sin((a0 + a1) / 2), 0.0)
                normals.extend([normal_side] * 4)
                uvs.extend(((u0, v0), (u1, v0), (u1, v1), (u0, v1)))
                indices.extend((base, base + 1, base + 2, base, base + 2, base + 3))

        self.add_primitive(name, material_index, positions, normals, uvs, indices)

    def add_cylinder_y(
        self,
        name: str,
        center: tuple[float, float, float],
        radius: float,
        depth: float,
        sides: int,
        material_index: int,
    ) -> None:
        cx, cy, cz = center
        temp_asset = Asset("_temp", Path("."), (1, 1), [(255, 255, 255, 255)], self.asset.materials)
        temp_builder = MeshBuilder(temp_asset)
        temp_builder.add_cylinder_z(name, (0.0, 0.0, 0.0), radius, depth, sides, material_index)
        primitive = temp_asset.primitives[0]
        rotated_positions = [(cx + x, cy + z, cz + y) for x, y, z in primitive.positions]
        rotated_normals = [(x, z, y) for x, y, z in primitive.normals]
        self.add_primitive(name, material_index, rotated_positions, rotated_normals, primitive.uvs, primitive.indices)


def console_materials() -> list[Material]:
    return [
        Material("mat_warm_ivory_plastic", (0.86, 0.83, 0.73, 1.0)),
        Material("mat_plastic_shadow", (0.62, 0.60, 0.53, 1.0)),
        Material("mat_recess_black", (0.035, 0.038, 0.042, 1.0)),
        Material("mat_port_dark_gray", (0.12, 0.13, 0.14, 1.0)),
        Material("mat_muted_red_light", (0.76, 0.08, 0.055, 1.0)),
        Material("mat_muted_green_light", (0.10, 0.62, 0.25, 1.0)),
        Material("mat_dull_metal", (0.63, 0.66, 0.66, 1.0), metallic=0.15),
        Material("mat_label_blue_gray", (0.20, 0.27, 0.34, 1.0)),
        Material("mat_collision_proxy", (0.15, 0.7, 0.95, 0.12), alpha_mode="BLEND"),
    ]


def disc_materials() -> list[Material]:
    return [
        Material("mat_silver_disc", (0.72, 0.76, 0.78, 1.0), metallic=0.2),
        Material("mat_disc_shadow", (0.42, 0.45, 0.47, 1.0), metallic=0.1),
        Material("mat_label_blue_gray", (0.17, 0.24, 0.33, 1.0)),
        Material("mat_center_clear", (0.91, 0.93, 0.92, 1.0)),
        Material("mat_collision_proxy", (0.15, 0.7, 0.95, 0.12), alpha_mode="BLEND"),
    ]


def build_console_texture() -> list[tuple[int, int, int, int]]:
    w = h = 256
    pixels = make_canvas(w, h, rgb_to_rgba((219, 212, 188)))
    ink = rgb_to_rgba((24, 25, 27))
    red = rgb_to_rgba((166, 30, 24))
    green = rgb_to_rgba((38, 150, 68))
    blue = rgb_to_rgba((45, 62, 76))
    gray = rgb_to_rgba((148, 148, 140))
    light = rgb_to_rgba((238, 234, 212))
    draw_rect(pixels, w, h, 8, 8, 118, 58, light)
    draw_rect(pixels, w, h, 12, 64, 224, 86, ink)
    draw_rect(pixels, w, h, 14, 66, 222, 68, gray)
    draw_rect(pixels, w, h, 132, 8, 244, 58, blue)
    draw_text(pixels, w, h, 142, 20, "XW-03", light, 2)
    draw_text(pixels, w, h, 140, 42, "HDD+GAME", rgb_to_rgba((192, 203, 207)), 1)
    draw_rect(pixels, w, h, 8, 96, 118, 148, rgb_to_rgba((104, 102, 94)))
    draw_text(pixels, w, h, 20, 110, "MEMORY", light, 1)
    draw_text(pixels, w, h, 20, 126, "I/O", light, 1)
    draw_rect(pixels, w, h, 132, 96, 244, 148, rgb_to_rgba((36, 37, 39)))
    draw_text(pixels, w, h, 144, 108, "REC", red, 1)
    draw_text(pixels, w, h, 144, 126, "READY", green, 1)
    for x in range(14, 230, 13):
        draw_line(pixels, w, h, x, 177, x + 8, 172, rgb_to_rgba((178, 172, 150)))
    for i in range(18):
        x = 20 + i * 12
        draw_rect(pixels, w, h, x, 202, x + 5, 224, ink)
    for x, y in ((35, 239), (78, 232), (162, 241), (209, 233)):
        draw_rect(pixels, w, h, x, y, x + 18, y + 3, rgb_to_rgba((188, 181, 156)))
    return pixels


def build_disc_texture() -> list[tuple[int, int, int, int]]:
    w = h = 128
    pixels = make_canvas(w, h, rgb_to_rgba((190, 195, 198)))
    cx = cy = 64
    for y in range(h):
        for x in range(w):
            dx = x - cx
            dy = y - cy
            radius = math.sqrt(dx * dx + dy * dy)
            if radius < 10:
                pixels[y * w + x] = rgb_to_rgba((230, 233, 232))
            elif radius < 32:
                pixels[y * w + x] = rgb_to_rgba((34, 46, 60))
            elif radius < 61:
                shade = 178 + int(35 * math.sin((x + y) * 0.18))
                pixels[y * w + x] = rgb_to_rgba((shade, shade + 3, shade + 8))
            else:
                pixels[y * w + x] = rgb_to_rgba((0, 0, 0), 0)
    draw_text(pixels, w, h, 37, 49, "DISC", rgb_to_rgba((224, 230, 230)), 1)
    draw_text(pixels, w, h, 43, 64, "03", rgb_to_rgba((224, 230, 230)), 1)
    draw_line(pixels, w, h, 18, 80, 110, 50, rgb_to_rgba((240, 245, 247)))
    draw_line(pixels, w, h, 20, 84, 112, 54, rgb_to_rgba((126, 134, 141)))
    return pixels


def build_console_asset() -> Asset:
    asset = Asset(
        name="psx_dvr_console",
        output_dir=ASSET_ROOT / "psx_dvr_console",
        texture_size=(256, 256),
        texture_pixels=build_console_texture(),
        materials=console_materials(),
        notes=["Generated as one GLB mesh/node for clean Blender import; source geometry is reproducible from tools/create_psx_dvr_assets.py."],
    )
    b = MeshBuilder(asset)
    b.add_box("console_main_body", (0.0, 0.0, 0.42), (3.12, 3.22, 0.78), 0)
    b.add_box("console_bottom_shadow", (0.0, 0.02, 0.055), (3.18, 3.28, 0.11), 1)
    b.add_box("console_top_step", (-0.10, 0.38, 0.88), (2.32, 2.08, 0.15), 0)
    b.add_box("console_top_step_shadow_edge", (-0.10, -0.68, 0.815), (2.36, 0.045, 0.07), 1)
    b.add_box("console_front_tray_slot", (-0.40, -1.635, 0.51), (1.42, 0.055, 0.14), 2)
    b.add_box("console_front_tray_highlight", (-0.40, -1.672, 0.59), (1.34, 0.018, 0.025), 6)
    b.add_box("console_front_lower_band", (0.0, -1.655, 0.19), (2.84, 0.046, 0.055), 3)
    b.add_box("console_front_memory_slot_l", (-1.05, -1.666, 0.34), (0.42, 0.042, 0.10), 2)
    b.add_box("console_front_memory_slot_r", (1.05, -1.666, 0.34), (0.42, 0.042, 0.10), 2)
    b.add_box("console_front_usb_slot", (1.34, -1.668, 0.48), (0.22, 0.045, 0.09), 2)
    b.add_box("console_front_memory_stick_slot", (-1.28, -1.668, 0.49), (0.36, 0.045, 0.075), 2)
    b.add_cylinder_y("console_controller_port_l", (-0.55, -1.70, 0.255), 0.17, 0.075, 14, 2)
    b.add_cylinder_y("console_controller_port_r", (0.55, -1.70, 0.255), 0.17, 0.075, 14, 2)
    b.add_cylinder_y("console_controller_socket_l", (-0.55, -1.745, 0.255), 0.095, 0.035, 10, 3)
    b.add_cylinder_y("console_controller_socket_r", (0.55, -1.745, 0.255), 0.095, 0.035, 10, 3)
    b.add_box("console_power_button", (1.37, -1.675, 0.64), (0.16, 0.045, 0.16), 6)
    b.add_box("console_red_status_light", (1.13, -1.682, 0.64), (0.075, 0.035, 0.075), 4)
    b.add_box("console_green_status_light", (1.25, -1.682, 0.64), (0.075, 0.035, 0.075), 5)
    b.add_box("console_top_label_plate", (0.72, -0.52, 0.972), (0.82, 0.42, 0.025), 7)
    b.add_box("console_top_label_line_1", (0.72, -0.63, 0.989), (0.58, 0.024, 0.012), 6)
    b.add_box("console_top_label_line_2", (0.72, -0.52, 0.989), (0.38, 0.024, 0.012), 6)
    b.add_box("console_top_label_line_3", (0.72, -0.41, 0.989), (0.52, 0.024, 0.012), 6)
    b.add_box("console_top_lid_seam_front", (-0.72, -0.54, 0.97), (0.92, 0.035, 0.018), 1)
    b.add_box("console_top_lid_seam_left", (-1.18, -0.16, 0.971), (0.035, 0.78, 0.018), 1)
    b.add_box("console_top_lid_seam_right", (-0.26, -0.16, 0.971), (0.035, 0.78, 0.018), 1)
    for idx, x in enumerate([-.98, -.78, -.58, -.38, -.18, .02, .22, .42, .62, .82, 1.02, 1.22]):
        b.add_box(f"console_top_vent_a_{idx:02d}", (x, 0.78, 0.973), (0.055, 0.56, 0.024), 3)
    for idx, y in enumerate([-1.08, -0.88, -0.68, -0.48, -0.28, -0.08, 0.12, 0.32, 0.52, 0.72, 0.92]):
        b.add_box(f"console_left_side_vent_{idx:02d}", (-1.585, y, 0.49), (0.045, 0.085, 0.31), 3)
        b.add_box(f"console_right_side_vent_{idx:02d}", (1.585, y, 0.49), (0.045, 0.085, 0.31), 3)
    for idx, x in enumerate([-1.15, -0.85, -0.55, -0.25, 0.05, 0.35, 0.65, 0.95, 1.25]):
        b.add_box(f"console_rear_cable_shadow_{idx:02d}", (x, 1.64, 0.39), (0.17, 0.05, 0.12), 2)
    for idx, (x, y) in enumerate([(-1.22, -1.18), (1.22, -1.18), (-1.22, 1.18), (1.22, 1.18)]):
        b.add_cylinder_z(f"console_rubber_foot_{idx}", (x, y, 0.015), 0.18, 0.03, 10, 2)
    for idx, (x, y) in enumerate([(-1.26, -0.72), (1.26, -0.72), (-1.26, 0.92), (1.26, 0.92)]):
        b.add_cylinder_z(f"console_top_screw_{idx}", (x, y, 0.973), 0.055, 0.018, 8, 6)
    for idx, x in enumerate([-1.42, -0.96, -0.50, -0.04, 0.42, 0.88, 1.34]):
        b.add_box(f"console_front_pixel_scuff_{idx}", (x, -1.682, 0.755), (0.12, 0.018, 0.018), 1)
    return asset


def build_disc_asset() -> Asset:
    asset = Asset(
        name="psx_dvr_disc",
        output_dir=ASSET_ROOT / "psx_dvr_disc",
        texture_size=(128, 128),
        texture_pixels=build_disc_texture(),
        materials=disc_materials(),
        notes=["Generated as one GLB mesh/node for clean Blender import; source geometry is reproducible from tools/create_psx_dvr_assets.py."],
    )
    b = MeshBuilder(asset)
    b.add_cylinder_z("disc_outer_silver_ring", (0.0, 0.0, 0.035), 0.48, 0.055, 24, 0, hole_radius=0.075)
    b.add_cylinder_z("disc_printed_label_ring", (0.0, 0.0, 0.069), 0.30, 0.018, 24, 2, hole_radius=0.11)
    b.add_cylinder_z("disc_inner_clear_ring", (0.0, 0.0, 0.083), 0.14, 0.022, 12, 3, hole_radius=0.075)
    for idx, angle in enumerate([0, math.pi * 0.5, math.pi, math.pi * 1.5]):
        x = math.cos(angle) * 0.25
        y = math.sin(angle) * 0.25
        b.add_box(f"disc_pixel_label_tick_{idx}", (x, y, 0.095), (0.11, 0.018, 0.01), 1)
    return asset


def pack_floats(values: list[float]) -> bytes:
    return struct.pack("<" + "f" * len(values), *values)


def pack_uint16(values: list[int]) -> bytes:
    return struct.pack("<" + "H" * len(values), *values)


def flatten_vec3(values: list[tuple[float, float, float]]) -> list[float]:
    return [component for value in values for component in value]


def flatten_vec2(values: list[tuple[float, float]]) -> list[float]:
    return [component for value in values for component in value]


def flatten_vec4(values: list[tuple[float, float, float, float]]) -> list[float]:
    return [component for value in values for component in value]


def min_max_vec3(values: list[tuple[float, float, float]]) -> tuple[list[float], list[float]]:
    return (
        [min(value[i] for value in values) for i in range(3)],
        [max(value[i] for value in values) for i in range(3)],
    )


class GlbWriter:
    def __init__(self, asset: Asset, image_bytes: bytes):
        self.asset = asset
        self.image_bytes = image_bytes
        self.binary = bytearray()
        self.buffer_views: list[dict] = []
        self.accessors: list[dict] = []

    def append_blob(self, data: bytes, target: int | None = None) -> int:
        while len(self.binary) % 4:
            self.binary.append(0)
        offset = len(self.binary)
        self.binary.extend(data)
        view = {"buffer": 0, "byteOffset": offset, "byteLength": len(data)}
        if target is not None:
            view["target"] = target
        self.buffer_views.append(view)
        return len(self.buffer_views) - 1

    def add_accessor(
        self,
        data: bytes,
        component_type: int,
        count: int,
        accessor_type: str,
        target: int,
        mins: list[float] | None = None,
        maxs: list[float] | None = None,
    ) -> int:
        view_index = self.append_blob(data, target)
        accessor = {
            "bufferView": view_index,
            "byteOffset": 0,
            "componentType": component_type,
            "count": count,
            "type": accessor_type,
        }
        if mins is not None and maxs is not None:
            accessor["min"] = mins
            accessor["max"] = maxs
        self.accessors.append(accessor)
        return len(self.accessors) - 1

    def build(self) -> bytes:
        mesh_primitives = []
        for primitive in self.asset.export_primitives:
            mins, maxs = min_max_vec3(primitive.positions)
            position_accessor = self.add_accessor(
                pack_floats(flatten_vec3(primitive.positions)),
                5126,
                len(primitive.positions),
                "VEC3",
                34962,
                mins,
                maxs,
            )
            normal_accessor = self.add_accessor(
                pack_floats(flatten_vec3(primitive.normals)),
                5126,
                len(primitive.normals),
                "VEC3",
                34962,
            )
            uv_accessor = self.add_accessor(
                pack_floats(flatten_vec2(primitive.uvs)),
                5126,
                len(primitive.uvs),
                "VEC2",
                34962,
            )
            color_accessor = self.add_accessor(
                pack_floats(flatten_vec4(primitive.colors)),
                5126,
                len(primitive.colors),
                "VEC4",
                34962,
            )
            index_accessor = self.add_accessor(
                pack_uint16(primitive.indices),
                5123,
                len(primitive.indices),
                "SCALAR",
                34963,
            )
            mesh_primitives.append(
                {
                    "attributes": {
                        "POSITION": position_accessor,
                        "NORMAL": normal_accessor,
                        "TEXCOORD_0": uv_accessor,
                        "COLOR_0": color_accessor,
                    },
                    "indices": index_accessor,
                    "material": primitive.material_index,
                    "mode": 4,
                    "extras": {"source_part": primitive.name},
                }
            )

        meshes = [{"name": self.asset.name, "primitives": mesh_primitives}]
        nodes = [{"name": self.asset.name, "mesh": 0}]

        image_view = self.append_blob(self.image_bytes)
        materials = []
        for material in self.asset.materials:
            entry = {
                "name": material.name,
                "pbrMetallicRoughness": {
                    "baseColorFactor": [1.0, 1.0, 1.0, material.color[3]],
                    "metallicFactor": material.metallic,
                    "roughnessFactor": material.roughness,
                },
            }
            if material.alpha_mode != "OPAQUE":
                entry["alphaMode"] = material.alpha_mode
                entry["doubleSided"] = True
            materials.append(entry)

        document = {
            "asset": {
                "version": "2.0",
                "generator": "tools/create_psx_dvr_assets.py",
                "copyright": "Logo-free original asset generated for X. WHEEL",
            },
            "scene": 0,
            "scenes": [{"name": self.asset.name, "nodes": [0]}],
            "nodes": nodes,
            "meshes": meshes,
            "materials": materials,
            "buffers": [{"byteLength": 0}],
            "bufferViews": self.buffer_views,
            "accessors": self.accessors,
            "images": [{"name": f"{self.asset.name}_texture", "bufferView": image_view, "mimeType": "image/png"}],
            "samplers": [{"magFilter": 9728, "minFilter": 9728, "wrapS": 33071, "wrapT": 33071}],
            "textures": [{"name": f"{self.asset.name}_texture", "sampler": 0, "source": 0}],
        }

        while len(self.binary) % 4:
            self.binary.append(0)
        document["buffers"][0]["byteLength"] = len(self.binary)

        json_bytes = json.dumps(document, separators=(",", ":")).encode("utf-8")
        while len(json_bytes) % 4:
            json_bytes += b" "
        total_length = 12 + 8 + len(json_bytes) + 8 + len(self.binary)
        return (
            b"glTF"
            + struct.pack("<II", 2, total_length)
            + struct.pack("<I4s", len(json_bytes), b"JSON")
            + json_bytes
            + struct.pack("<I4s", len(self.binary), b"BIN\x00")
            + bytes(self.binary)
        )


def write_glb(asset: Asset, image_bytes: bytes) -> None:
    asset.output_dir.mkdir(parents=True, exist_ok=True)
    asset.glb_path.write_bytes(GlbWriter(asset, image_bytes).build())


def transform_point(point: tuple[float, float, float]) -> tuple[float, float, float]:
    x, y, z = point
    yaw = math.radians(-36)
    cy = math.cos(yaw)
    sy = math.sin(yaw)
    x1 = cy * x - sy * y
    y1 = sy * x + cy * y
    pitch = math.radians(58)
    cp = math.cos(pitch)
    sp = math.sin(pitch)
    y2 = cp * y1 - sp * z
    z2 = sp * y1 + cp * z
    return (x1, z2, y2)


def edge(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float]) -> float:
    return (c[0] - a[0]) * (b[1] - a[1]) - (c[1] - a[1]) * (b[0] - a[0])


def shaded_color(color: tuple[float, float, float, float], normal: tuple[float, float, float]) -> tuple[int, int, int, int]:
    light = (0.25, -0.45, 0.86)
    length = math.sqrt(sum(channel * channel for channel in normal)) or 1.0
    n = tuple(channel / length for channel in normal)
    dot = max(0.0, sum(n[i] * light[i] for i in range(3)))
    shade = 0.58 + 0.42 * dot
    return (
        clamp_byte(color[0] * shade * 255),
        clamp_byte(color[1] * shade * 255),
        clamp_byte(color[2] * shade * 255),
        clamp_byte(color[3] * 255),
    )


def draw_triangle(
    pixels: list[tuple[int, int, int, int]],
    zbuffer: list[float],
    width: int,
    height: int,
    points: list[tuple[float, float, float]],
    color: tuple[int, int, int, int],
) -> None:
    pts2 = [(points[0][0], points[0][1]), (points[1][0], points[1][1]), (points[2][0], points[2][1])]
    min_x = max(0, int(math.floor(min(p[0] for p in pts2))))
    max_x = min(width - 1, int(math.ceil(max(p[0] for p in pts2))))
    min_y = max(0, int(math.floor(min(p[1] for p in pts2))))
    max_y = min(height - 1, int(math.ceil(max(p[1] for p in pts2))))
    area = edge(pts2[0], pts2[1], pts2[2])
    if abs(area) < 0.0001:
        return
    for y in range(min_y, max_y + 1):
        for x in range(min_x, max_x + 1):
            p = (x + 0.5, y + 0.5)
            w0 = edge(pts2[1], pts2[2], p) / area
            w1 = edge(pts2[2], pts2[0], p) / area
            w2 = edge(pts2[0], pts2[1], p) / area
            if w0 >= -0.0001 and w1 >= -0.0001 and w2 >= -0.0001:
                depth = w0 * points[0][2] + w1 * points[1][2] + w2 * points[2][2]
                idx = y * width + x
                if depth < zbuffer[idx]:
                    zbuffer[idx] = depth
                    pixels[idx] = color


def render_preview(asset: Asset, path: Path, width: int = 960, height: int = 720) -> None:
    bg = rgb_to_rgba((34, 36, 39))
    pixels = make_canvas(width, height, bg)
    zbuffer = [float("inf")] * (width * height)
    transformed: list[tuple[Primitive, list[tuple[float, float, float]]]] = []
    all_points: list[tuple[float, float, float]] = []
    for primitive in asset.primitives:
        points = [transform_point(point) for point in primitive.positions]
        transformed.append((primitive, points))
        all_points.extend(points)
    min_x = min(point[0] for point in all_points)
    max_x = max(point[0] for point in all_points)
    min_y = min(point[1] for point in all_points)
    max_y = max(point[1] for point in all_points)
    scale = min((width * 0.72) / (max_x - min_x), (height * 0.68) / (max_y - min_y))
    ox = width * 0.5 - (min_x + max_x) * 0.5 * scale
    oy = height * 0.54 - (min_y + max_y) * 0.5 * scale

    for primitive, points in transformed:
        material = asset.materials[primitive.material_index]
        if primitive.name.startswith("col_") or material.color[3] < 0.2:
            continue
        for i in range(0, len(primitive.indices), 3):
            ids = primitive.indices[i : i + 3]
            tri = [(points[index][0] * scale + ox, height - (points[index][1] * scale + oy), points[index][2]) for index in ids]
            normal = primitive.normals[ids[0]]
            draw_triangle(pixels, zbuffer, width, height, tri, shaded_color(material.color, normal))

    text_color = rgb_to_rgba((235, 232, 214))
    draw_text(pixels, width, height, 28, 28, asset.name.upper(), text_color, 2)
    draw_text(pixels, width, height, 30, 58, f"{asset.triangle_count} TRIS", rgb_to_rgba((166, 174, 178)), 1)
    write_png(path, width, height, pixels)


def generate_assets() -> list[Asset]:
    assets = [build_console_asset(), build_disc_asset()]
    manifest = {
        "generator": "tools/create_psx_dvr_assets.py",
        "source_note": "GLB geometry is generated reproducibly by script, then imported into assets/3d/psx_dvr_assets.blend as two Blender assets.",
        "assets": {},
    }
    for asset in assets:
        image_bytes = write_png(asset.texture_path, asset.texture_size[0], asset.texture_size[1], asset.texture_pixels)
        write_glb(asset, image_bytes)
        render_preview(asset, asset.preview_path)
        manifest["assets"][asset.name] = {
            "glb": str(asset.glb_path.relative_to(ROOT)).replace(os.sep, "/"),
            "texture": str(asset.texture_path.relative_to(ROOT)).replace(os.sep, "/"),
            "preview": str(asset.preview_path.relative_to(ROOT)).replace(os.sep, "/"),
            "triangles": asset.triangle_count,
            "materials": asset.material_count,
            "texture_size": list(asset.texture_size),
            "objects": [asset.name],
            "source_parts": [primitive.name for primitive in asset.export_primitives],
            "notes": asset.notes,
        }
        print(f"{asset.name}: {asset.triangle_count} triangles, {asset.material_count} materials")
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return assets


def read_glb(path: Path) -> tuple[dict, bytes]:
    data = path.read_bytes()
    if data[:4] != b"glTF":
        raise ValueError(f"{path}: invalid magic")
    version, total_length = struct.unpack_from("<II", data, 4)
    if version != 2:
        raise ValueError(f"{path}: expected GLB version 2, got {version}")
    if total_length != len(data):
        raise ValueError(f"{path}: header length {total_length} != actual {len(data)}")
    json_len, json_type = struct.unpack_from("<I4s", data, 12)
    if json_type != b"JSON":
        raise ValueError(f"{path}: missing JSON chunk")
    json_start = 20
    document = json.loads(data[json_start : json_start + json_len].decode("utf-8"))
    bin_header = json_start + json_len
    bin_len, bin_type = struct.unpack_from("<I4s", data, bin_header)
    if bin_type != b"BIN\x00":
        raise ValueError(f"{path}: missing BIN chunk")
    bin_start = bin_header + 8
    return document, data[bin_start : bin_start + bin_len]


def verify_glb(path: Path) -> str:
    document, binary = read_glb(path)
    if document.get("asset", {}).get("version") != "2.0":
        raise ValueError(f"{path}: asset.version is not 2.0")
    if not document.get("meshes"):
        raise ValueError(f"{path}: no meshes")
    if not document.get("materials"):
        raise ValueError(f"{path}: no materials")
    if not document.get("images"):
        raise ValueError(f"{path}: no embedded image")
    for index, view in enumerate(document.get("bufferViews", [])):
        if view.get("byteOffset", 0) % 4 != 0:
            raise ValueError(f"{path}: bufferView {index} is not 4-byte aligned")
        if view.get("byteOffset", 0) + view.get("byteLength", 0) > len(binary):
            raise ValueError(f"{path}: bufferView {index} exceeds BIN chunk")
    return f"{path.relative_to(ROOT)}: valid GLB, {len(document['meshes'])} meshes, {len(document['materials'])} materials"


def verify_outputs() -> None:
    expected = [
        ASSET_ROOT / "psx_dvr_console" / "psx_dvr_console.glb",
        ASSET_ROOT / "psx_dvr_disc" / "psx_dvr_disc.glb",
    ]
    for path in expected:
        print(verify_glb(path))


def report_outputs() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    console = manifest["assets"]["psx_dvr_console"]
    disc = manifest["assets"]["psx_dvr_disc"]
    if not (900 <= console["triangles"] <= 1800):
        raise ValueError(f"psx_dvr_console triangle count outside budget: {console['triangles']}")
    if console["texture_size"] != [256, 256]:
        raise ValueError(f"psx_dvr_console texture size mismatch: {console['texture_size']}")
    if not (200 <= disc["triangles"] <= 700):
        raise ValueError(f"psx_dvr_disc triangle count outside budget: {disc['triangles']}")
    if disc["texture_size"] != [128, 128]:
        raise ValueError(f"psx_dvr_disc texture size mismatch: {disc['texture_size']}")
    print("psx_dvr_console: triangles between 900 and 1800, texture 256x256")
    print("psx_dvr_disc: triangles between 200 and 700, texture 128x128")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate PSX DVR-style low-poly GLB assets.")
    parser.add_argument("--verify", action="store_true", help="Verify generated GLB structure.")
    parser.add_argument("--report", action="store_true", help="Report generated metadata and enforce budgets.")
    args = parser.parse_args()
    if args.verify:
        verify_outputs()
    elif args.report:
        report_outputs()
    else:
        generate_assets()


if __name__ == "__main__":
    main()
