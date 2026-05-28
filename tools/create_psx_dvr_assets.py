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

PALETTE = {"green": "#3FA943", "pale": "#E8F8E4", "deep": "#0C1725"}
PALETTE_PRIMARY = [PALETTE["green"], PALETTE["pale"], PALETTE["deep"]]
SCALE_REFERENCE = "five_head_chibi_1_40m"
DETAIL_LEVEL = "higher_detail_lowpoly"
COLOR_POLICY = "preserve_existing_palette"


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
    dimensions: tuple[float, float, float] | None = None
    manifest_extra: dict[str, object] = field(default_factory=dict)
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


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    raw = value.lstrip("#")
    return (int(raw[0:2], 16), int(raw[2:4], 16), int(raw[4:6], 16))


def hex_to_rgba(value: str, alpha: int = 255) -> tuple[int, int, int, int]:
    return rgb_to_rgba(hex_to_rgb(value), alpha)


def hex_to_float_color(value: str, alpha: float = 1.0) -> tuple[float, float, float, float]:
    r, g, b = hex_to_rgb(value)
    return (r / 255.0, g / 255.0, b / 255.0, alpha)


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

    def add_box_z_rotated(
        self,
        name: str,
        center: tuple[float, float, float],
        size: tuple[float, float, float],
        angle: float,
        material_index: int,
        uv_rect: tuple[float, float, float, float] = (0.02, 0.02, 0.18, 0.18),
    ) -> None:
        temp_asset = Asset("_temp", Path("."), (1, 1), [(255, 255, 255, 255)], self.asset.materials)
        temp_builder = MeshBuilder(temp_asset)
        temp_builder.add_box(name, (0.0, 0.0, 0.0), size, material_index, uv_rect)
        primitive = temp_asset.primitives[0]
        cx, cy, cz = center
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        rotated_positions = [
            (cx + cos_a * x - sin_a * y, cy + sin_a * x + cos_a * y, cz + z)
            for x, y, z in primitive.positions
        ]
        rotated_normals = [
            (cos_a * x - sin_a * y, sin_a * x + cos_a * y, z)
            for x, y, z in primitive.normals
        ]
        self.add_primitive(name, material_index, rotated_positions, rotated_normals, primitive.uvs, primitive.indices)

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

    def add_elliptical_cylinder_z(
        self,
        name: str,
        center: tuple[float, float, float],
        radius_x: float,
        radius_y: float,
        depth: float,
        sides: int,
        material_index: int,
        hole_radius: float = 0.0,
    ) -> None:
        temp_asset = Asset("_temp", Path("."), (1, 1), [(255, 255, 255, 255)], self.asset.materials)
        temp_builder = MeshBuilder(temp_asset)
        temp_builder.add_cylinder_z(name, (0.0, 0.0, 0.0), 1.0, depth, sides, material_index, hole_radius)
        primitive = temp_asset.primitives[0]
        cx, cy, cz = center
        scaled_positions = [(cx + x * radius_x, cy + y * radius_y, cz + z) for x, y, z in primitive.positions]
        scaled_normals = []
        for nx, ny, nz in primitive.normals:
            sx = nx / max(radius_x, 0.001)
            sy = ny / max(radius_y, 0.001)
            length = math.sqrt(sx * sx + sy * sy + nz * nz) or 1.0
            scaled_normals.append((sx / length, sy / length, nz / length))
        self.add_primitive(name, material_index, scaled_positions, scaled_normals, primitive.uvs, primitive.indices)

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


def fit_asset_to_dimensions(asset: Asset, target: tuple[float, float, float]) -> None:
    all_positions = [position for primitive in asset.primitives for position in primitive.positions]
    if not all_positions:
        asset.dimensions = target
        return
    min_x = min(position[0] for position in all_positions)
    max_x = max(position[0] for position in all_positions)
    min_y = min(position[1] for position in all_positions)
    max_y = max(position[1] for position in all_positions)
    min_z = min(position[2] for position in all_positions)
    max_z = max(position[2] for position in all_positions)
    source = (max_x - min_x, max_y - min_y, max_z - min_z)
    sx = target[0] / source[0] if source[0] else 1.0
    sy = target[1] / source[1] if source[1] else 1.0
    sz = target[2] / source[2] if source[2] else 1.0
    cx = (min_x + max_x) * 0.5
    cy = (min_y + max_y) * 0.5

    for primitive in asset.primitives:
        primitive.positions = [((x - cx) * sx, (y - cy) * sy, (z - min_z) * sz) for x, y, z in primitive.positions]
        transformed_normals = []
        for nx, ny, nz in primitive.normals:
            ax = nx / max(sx, 0.0001)
            ay = ny / max(sy, 0.0001)
            az = nz / max(sz, 0.0001)
            length = math.sqrt(ax * ax + ay * ay + az * az) or 1.0
            transformed_normals.append((ax / length, ay / length, az / length))
        primitive.normals = transformed_normals
    asset.dimensions = target


def finalize_asset(asset: Asset, target_dimensions: tuple[float, float, float] | None = None) -> Asset:
    if target_dimensions is not None:
        fit_asset_to_dimensions(asset, target_dimensions)
    asset.manifest_extra.setdefault("scale_reference", SCALE_REFERENCE)
    asset.manifest_extra.setdefault("detail_level", DETAIL_LEVEL)
    asset.manifest_extra.setdefault("color_policy", COLOR_POLICY)
    return asset


def console_materials() -> list[Material]:
    return [
        Material("mat_pale_plastic", hex_to_float_color(PALETTE["pale"])),
        Material("mat_pale_shadow", (0.58, 0.67, 0.58, 1.0)),
        Material("mat_deep_recess", hex_to_float_color(PALETTE["deep"])),
        Material("mat_deep_panel", (0.06, 0.12, 0.19, 1.0)),
        Material("mat_green_status_dim", (0.16, 0.48, 0.24, 1.0)),
        Material("mat_green_status", hex_to_float_color(PALETTE["green"])),
        Material("mat_pale_metal", (0.78, 0.86, 0.80, 1.0), metallic=0.12),
        Material("mat_green_label", (0.18, 0.42, 0.25, 1.0)),
        Material("mat_collision_proxy", (0.15, 0.7, 0.95, 0.12), alpha_mode="BLEND"),
    ]


def disc_materials() -> list[Material]:
    return [
        Material("mat_pale_disc", (0.74, 0.86, 0.78, 1.0), metallic=0.12),
        Material("mat_disc_shadow", (0.20, 0.30, 0.28, 1.0), metallic=0.08),
        Material("mat_deep_label", hex_to_float_color(PALETTE["deep"])),
        Material("mat_center_pale", hex_to_float_color(PALETTE["pale"])),
        Material("mat_collision_proxy", (0.15, 0.7, 0.95, 0.12), alpha_mode="BLEND"),
    ]


def crt_materials() -> list[Material]:
    return [
        Material("mat_crt_deep_shell", (0.035, 0.075, 0.110, 1.0)),
        Material("mat_crt_deep_edge", (0.018, 0.040, 0.065, 1.0)),
        Material("mat_crt_black_glass", (0.006, 0.014, 0.024, 1.0), roughness=0.24, metallic=0.08),
        Material("mat_crt_glass_scanline", (0.025, 0.13, 0.075, 1.0), roughness=0.35),
        Material("mat_crt_panel_green_dark", (0.13, 0.35, 0.20, 1.0)),
        Material("mat_crt_control_dark", (0.04, 0.09, 0.14, 1.0)),
        Material("mat_crt_glass_reflection", (0.55, 0.78, 0.60, 1.0), roughness=0.18, metallic=0.04),
        Material("mat_collision_proxy", (0.15, 0.7, 0.95, 0.12), alpha_mode="BLEND"),
    ]


def bookshelf_materials() -> list[Material]:
    return [
        Material("mat_bookshelf_deep_frame", hex_to_float_color(PALETTE["deep"])),
        Material("mat_bookshelf_edge_shadow", (0.025, 0.055, 0.090, 1.0)),
        Material("mat_bookshelf_pale_board", hex_to_float_color(PALETTE["pale"])),
        Material("mat_bookshelf_green_books", hex_to_float_color(PALETTE["green"])),
        Material("mat_bookshelf_dim_green", (0.12, 0.32, 0.19, 1.0)),
        Material("mat_bookshelf_pale_label", (0.72, 0.90, 0.73, 1.0)),
        Material("mat_collision_proxy", (0.15, 0.7, 0.95, 0.12), alpha_mode="BLEND"),
    ]


def desk_materials() -> list[Material]:
    return [
        Material("mat_desk_deep_frame", hex_to_float_color(PALETTE["deep"])),
        Material("mat_desk_pale_top", hex_to_float_color(PALETTE["pale"])),
        Material("mat_desk_green_panel", hex_to_float_color(PALETTE["green"])),
        Material("mat_desk_recess", (0.015, 0.035, 0.055, 1.0)),
        Material("mat_desk_pale_edge", (0.74, 0.88, 0.75, 1.0)),
        Material("mat_desk_dim_green", (0.12, 0.32, 0.18, 1.0)),
        Material("mat_collision_proxy", (0.15, 0.7, 0.95, 0.12), alpha_mode="BLEND"),
    ]


def beanbag_materials() -> list[Material]:
    return [
        Material("mat_beanbag_green_fabric", (0.18, 0.44, 0.22, 1.0), roughness=0.98),
        Material("mat_beanbag_dark_fabric_shadow", (0.08, 0.19, 0.12, 1.0), roughness=1.0),
        Material("mat_beanbag_rib_highlight", (0.35, 0.62, 0.36, 1.0), roughness=0.96),
        Material("mat_beanbag_deep_seam", hex_to_float_color(PALETTE["deep"]), roughness=0.95),
        Material("mat_beanbag_pale_stitch", hex_to_float_color(PALETTE["pale"]), roughness=0.9),
        Material("mat_collision_proxy", (0.15, 0.7, 0.95, 0.12), alpha_mode="BLEND"),
    ]


def disc_rug_materials() -> list[Material]:
    return [
        Material("mat_rug_green_swirl", (0.12, 0.47, 0.25, 1.0), roughness=1.0),
        Material("mat_rug_lime_swirl", hex_to_float_color(PALETTE["green"]), roughness=1.0),
        Material("mat_rug_deep_rim", hex_to_float_color(PALETTE["deep"]), roughness=0.95),
        Material("mat_rug_pale_print", hex_to_float_color(PALETTE["pale"]), roughness=0.98),
        Material("mat_rug_center_label", (0.030, 0.035, 0.040, 1.0), roughness=0.9),
        Material("mat_collision_proxy", (0.15, 0.7, 0.95, 0.12), alpha_mode="BLEND"),
    ]


def room_materials() -> list[Material]:
    return [
        Material("mat_room_wall_pale", (0.74, 0.83, 0.74, 1.0)),
        Material("mat_room_floor_deep", (0.045, 0.070, 0.075, 1.0)),
        Material("mat_room_deep_trim", hex_to_float_color(PALETTE["deep"])),
        Material("mat_room_poster_dark", (0.030, 0.040, 0.048, 1.0)),
        Material("mat_room_poster_green", hex_to_float_color(PALETTE["green"])),
        Material("mat_room_poster_pale", hex_to_float_color(PALETTE["pale"])),
        Material("mat_room_paper", (0.86, 0.94, 0.84, 1.0)),
        Material("mat_room_lamp_glow", (0.55, 0.92, 0.58, 1.0), roughness=0.55),
        Material("mat_room_chair_fabric", (0.11, 0.30, 0.18, 1.0), roughness=0.95),
        Material("mat_room_chair_metal", (0.42, 0.50, 0.45, 1.0), metallic=0.18),
        Material("mat_room_plant_pot", (0.10, 0.18, 0.16, 1.0)),
        Material("mat_room_plant_leaf", (0.18, 0.58, 0.25, 1.0)),
        Material("mat_room_book_spine", (0.06, 0.12, 0.18, 1.0)),
        Material("mat_room_cd_case", (0.55, 0.70, 0.66, 1.0), roughness=0.62),
        Material("mat_collision_proxy", (0.15, 0.7, 0.95, 0.12), alpha_mode="BLEND"),
    ]


def prop_materials() -> list[Material]:
    return [
        Material("mat_prop_deep", hex_to_float_color(PALETTE["deep"])),
        Material("mat_prop_green", hex_to_float_color(PALETTE["green"])),
        Material("mat_prop_pale", hex_to_float_color(PALETTE["pale"])),
        Material("mat_prop_dim_green", (0.13, 0.34, 0.20, 1.0)),
        Material("mat_prop_shadow", (0.025, 0.050, 0.070, 1.0)),
        Material("mat_prop_glass", (0.40, 0.62, 0.58, 0.72), roughness=0.30, metallic=0.06, alpha_mode="BLEND"),
        Material("mat_prop_metal", (0.50, 0.58, 0.54, 1.0), roughness=0.55, metallic=0.20),
        Material("mat_collision_proxy", (0.15, 0.7, 0.95, 0.12), alpha_mode="BLEND"),
    ]


def build_console_texture() -> list[tuple[int, int, int, int]]:
    w = h = 256
    pixels = make_canvas(w, h, hex_to_rgba(PALETTE["pale"]))
    ink = hex_to_rgba(PALETTE["deep"])
    red = rgb_to_rgba((50, 128, 62))
    green = hex_to_rgba(PALETTE["green"])
    blue = rgb_to_rgba((19, 44, 49))
    gray = rgb_to_rgba((118, 146, 126))
    light = rgb_to_rgba((246, 255, 240))
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
    pixels = make_canvas(w, h, rgb_to_rgba((190, 214, 196)))
    cx = cy = 64
    for y in range(h):
        for x in range(w):
            dx = x - cx
            dy = y - cy
            radius = math.sqrt(dx * dx + dy * dy)
            if radius < 10:
                pixels[y * w + x] = hex_to_rgba(PALETTE["pale"])
            elif radius < 32:
                pixels[y * w + x] = hex_to_rgba(PALETTE["deep"])
            elif radius < 61:
                shade = 186 + int(28 * math.sin((x + y) * 0.18))
                pixels[y * w + x] = rgb_to_rgba((shade - 20, shade + 12, shade - 10))
            else:
                pixels[y * w + x] = rgb_to_rgba((0, 0, 0), 0)
    draw_text(pixels, w, h, 37, 49, "DISC", hex_to_rgba(PALETTE["green"]), 1)
    draw_text(pixels, w, h, 43, 64, "03", hex_to_rgba(PALETTE["green"]), 1)
    draw_line(pixels, w, h, 18, 80, 110, 50, hex_to_rgba(PALETTE["pale"]))
    draw_line(pixels, w, h, 20, 84, 112, 54, rgb_to_rgba((70, 122, 82)))
    return pixels


def build_crt_texture() -> list[tuple[int, int, int, int]]:
    w = h = 256
    pixels = make_canvas(w, h, hex_to_rgba(PALETTE["deep"]))
    pale = hex_to_rgba(PALETTE["pale"])
    green = hex_to_rgba(PALETTE["green"])
    dark = rgb_to_rgba((5, 14, 24))
    glass = rgb_to_rgba((2, 7, 12))
    glass_edge = rgb_to_rgba((7, 20, 31))
    face = rgb_to_rgba((17, 36, 54))
    draw_rect(pixels, w, h, 8, 8, 248, 168, face)
    draw_rect(pixels, w, h, 28, 24, 178, 118, glass_edge)
    draw_rect(pixels, w, h, 36, 32, 170, 110, glass)
    for y in range(42, 104, 11):
        draw_line(pixels, w, h, 42, y, 164, y + 1, rgb_to_rgba((12, 68, 43)))
    draw_line(pixels, w, h, 52, 44, 154, 36, rgb_to_rgba((118, 184, 126)))
    draw_line(pixels, w, h, 58, 58, 118, 54, rgb_to_rgba((186, 226, 190)))
    draw_line(pixels, w, h, 52, 74, 86, 72, rgb_to_rgba((160, 214, 166)))
    draw_rect(pixels, w, h, 8, 176, 248, 224, dark)
    draw_text(pixels, w, h, 112, 184, "XW", pale, 1)
    for x in range(72, 158, 11):
        draw_rect(pixels, w, h, x, 204, x + 4, 218, rgb_to_rgba((35, 54, 56)))
    for x in (24, 68, 190, 226):
        draw_rect(pixels, w, h, x, 188, x + 20, 192, green)
    draw_rect(pixels, w, h, 16, 232, 240, 246, rgb_to_rgba((8, 22, 34)))
    return pixels


def build_console_asset() -> Asset:
    asset = Asset(
        name="psx_dvr_console",
        output_dir=ASSET_ROOT / "psx_dvr_console",
        texture_size=(256, 256),
        texture_pixels=build_console_texture(),
        materials=console_materials(),
        dimensions=(0.44, 0.40, 0.14),
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
    for row, y in enumerate([-1.22, -0.96, -0.70, -0.44, -0.18, 0.08, 0.34, 0.60, 0.86, 1.12]):
        for col, x in enumerate([-1.30, -1.02, -0.74, -0.46, -0.18, 0.10, 0.38, 0.66, 0.94, 1.22]):
            if (row + col) % 2 == 0:
                b.add_box(
                    f"console_pixel_panel_detail_{row:02d}_{col:02d}",
                    (x, y, 0.982),
                    (0.080, 0.026, 0.010),
                    6 if (row + col) % 2 else 1,
                )
    return finalize_asset(asset, (0.44, 0.40, 0.14))


def build_disc_asset() -> Asset:
    asset = Asset(
        name="psx_dvr_disc",
        output_dir=ASSET_ROOT / "psx_dvr_disc",
        texture_size=(128, 128),
        texture_pixels=build_disc_texture(),
        materials=disc_materials(),
        dimensions=(0.12, 0.12, 0.018),
        notes=["Generated as one GLB mesh/node for clean Blender import; source geometry is reproducible from tools/create_psx_dvr_assets.py."],
    )
    b = MeshBuilder(asset)
    b.add_cylinder_z("disc_outer_silver_ring", (0.0, 0.0, 0.035), 0.48, 0.055, 48, 0, hole_radius=0.075)
    b.add_cylinder_z("disc_printed_label_ring", (0.0, 0.0, 0.069), 0.30, 0.018, 48, 2, hole_radius=0.11)
    b.add_cylinder_z("disc_inner_clear_ring", (0.0, 0.0, 0.083), 0.14, 0.022, 32, 3, hole_radius=0.075)
    for idx in range(12):
        angle = math.tau * idx / 12.0
        x = math.cos(angle) * 0.25
        y = math.sin(angle) * 0.25
        b.add_box(f"disc_pixel_label_tick_{idx}", (x, y, 0.095), (0.11, 0.018, 0.01), 1)
    return finalize_asset(asset, (0.12, 0.12, 0.018))


def build_crt_tv_asset() -> Asset:
    asset = Asset(
        name="crt_tv",
        output_dir=ASSET_ROOT / "crt_tv",
        texture_size=(256, 256),
        texture_pixels=build_crt_texture(),
        materials=crt_materials(),
        dimensions=(0.70, 0.58, 0.56),
        manifest_extra={
            "screen_state": "black_glass",
            "front_style": "large_bezel_box_crt",
            "screen_material": "convex_black_glass",
            "control_layout": "bottom_button_row",
        },
        notes=["Large-bezel box CRT television with dominant convex black glass screen and bottom button row."],
    )
    b = MeshBuilder(asset)
    b.add_box("crt_boxy_side_depth", (0.0, 0.12, 0.90), (2.42, 1.76, 1.62), 0)
    b.add_box("crt_rear_tube_block", (0.0, 0.76, 0.92), (1.86, 0.86, 1.30), 1)
    b.add_box("crt_heavy_bottom_plinth", (0.0, -0.02, 0.13), (2.48, 1.86, 0.26), 1)
    b.add_box("crt_front_deep_bezel_outer", (0.0, -0.835, 1.02), (2.18, 0.18, 1.42), 1)
    b.add_box("crt_front_bezel_face", (0.0, -0.940, 1.02), (1.96, 0.10, 1.20), 0)
    b.add_box("crt_screen_shadow_cavity", (-0.04, -1.010, 1.12), (1.54, 0.075, 0.90), 5)
    b.add_box("crt_large_black_glass_panel", (-0.04, -1.060, 1.12), (1.38, 0.052, 0.78), 2)
    b.add_box("crt_glass_left_curved_edge", (-0.76, -1.045, 1.12), (0.08, 0.038, 0.72), 2)
    b.add_box("crt_glass_right_curved_edge", (0.68, -1.045, 1.12), (0.08, 0.038, 0.72), 2)
    b.add_box("crt_glass_top_curved_edge", (-0.04, -1.040, 1.53), (1.26, 0.035, 0.07), 2)
    b.add_box("crt_glass_bottom_curved_edge", (-0.04, -1.040, 0.71), (1.26, 0.035, 0.07), 2)
    b.add_box("crt_glass_reflection_top", (-0.36, -1.086, 1.43), (0.60, 0.014, 0.028), 6)
    b.add_box("crt_glass_reflection_mid", (-0.50, -1.088, 1.24), (0.34, 0.014, 0.025), 6)
    for idx, z in enumerate([0.80, 0.92, 1.04, 1.16, 1.28, 1.40]):
        b.add_box(f"crt_glass_dark_scanline_{idx:02d}", (-0.04, -1.092, z), (1.24, 0.010, 0.014), 3)
    b.add_box("crt_bottom_control_strip", (0.0, -1.005, 0.42), (2.04, 0.070, 0.20), 5)
    b.add_box("crt_center_brand_plate", (0.0, -1.048, 0.50), (0.34, 0.020, 0.030), 4)
    for idx, x in enumerate([-0.52, -0.40, -0.28, -0.16, -0.04, 0.08, 0.20, 0.32]):
        b.add_box(f"crt_bottom_button_{idx:02d}", (x, -1.050, 0.36), (0.046, 0.032, 0.085), 5)
    b.add_box("crt_power_button_square", (0.82, -1.050, 0.37), (0.14, 0.032, 0.09), 5)
    b.add_box("crt_power_indicator_green", (1.02, -1.052, 0.46), (0.06, 0.020, 0.045), 3)
    for idx, x in enumerate([-0.98, -0.64, 0.64, 0.98]):
        b.add_box(f"crt_front_lower_accent_{idx:02d}", (x, -1.053, 0.27), (0.18, 0.016, 0.024), 4)
    for row, z in enumerate([0.56, 0.66, 0.76]):
        for col, x in enumerate([0.72, 0.86, 1.00]):
            b.add_cylinder_y(f"crt_bottom_speaker_hole_{row:02d}_{col:02d}", (x, -1.052, z), 0.024, 0.040, 8, 5)
    for idx, x in enumerate([-0.92, -0.64, -0.36, -0.08, 0.20, 0.48, 0.76, 1.04]):
        b.add_box(f"crt_top_case_tab_{idx:02d}", (x, -0.06, 1.735), (0.08, 0.22, 0.035), 5)
    for idx, z in enumerate([0.46, 0.58, 0.70, 0.82, 0.94, 1.06, 1.18]):
        b.add_box(f"crt_left_side_vent_{idx:02d}", (-1.235, 0.18, z), (0.035, 0.50, 0.045), 5)
        b.add_box(f"crt_right_side_vent_{idx:02d}", (1.235, 0.18, z), (0.035, 0.50, 0.045), 5)
    b.add_box("crt_back_service_panel", (0.0, 1.170, 0.94), (1.34, 0.055, 0.76), 5)
    b.add_box("crt_back_cable_port", (0.0, 1.205, 0.58), (0.34, 0.026, 0.16), 1)
    for idx, (x, y) in enumerate([(-0.82, -0.50), (0.82, -0.50), (-0.76, 0.62), (0.76, 0.62)]):
        b.add_box(f"crt_rubber_foot_{idx}", (x, y, -0.02), (0.30, 0.24, 0.10), 5)
    for row, z in enumerate([0.42, 0.54, 0.66, 0.78, 0.90, 1.02, 1.14, 1.26, 1.38]):
        for col, x in enumerate([-1.05, -0.84, -0.63, -0.42, 0.42, 0.63, 0.84, 1.05]):
            b.add_box(f"crt_bezel_pixel_dither_{row:02d}_{col:02d}", (x, -1.062, z), (0.080, 0.012, 0.018), 4 if (row + col) % 2 else 5)
    for row, z in enumerate([0.48, 0.62, 0.76, 0.90, 1.04, 1.18, 1.32]):
        for col, y in enumerate([-0.48, -0.26, -0.04, 0.18, 0.40, 0.62]):
            b.add_box(f"crt_side_case_pixel_{row:02d}_{col:02d}_l", (-1.252, y, z), (0.018, 0.070, 0.020), 5)
            b.add_box(f"crt_side_case_pixel_{row:02d}_{col:02d}_r", (1.252, y, z), (0.018, 0.070, 0.020), 5)
    b.add_box("col_crt_tv_box", (0.0, 0.08, 0.91), (2.48, 1.86, 1.82), 7)
    return finalize_asset(asset, (0.70, 0.58, 0.56))


def build_bookshelf_texture() -> list[tuple[int, int, int, int]]:
    w = h = 256
    pixels = make_canvas(w, h, hex_to_rgba(PALETTE["deep"]))
    pale = hex_to_rgba(PALETTE["pale"])
    green = hex_to_rgba(PALETTE["green"])
    shadow = rgb_to_rgba((6, 24, 30))
    draw_rect(pixels, w, h, 12, 10, 244, 54, shadow)
    draw_text(pixels, w, h, 24, 22, "SHELF", pale, 2)
    for row, y in enumerate([74, 106, 138, 170, 202]):
        draw_rect(pixels, w, h, 14, y, 242, y + 8, pale if row % 2 else rgb_to_rgba((175, 216, 178)))
        x = 22
        for col in range(13):
            width = 8 + (col % 4) * 3
            color = green if (col + row) % 3 else rgb_to_rgba((29, 73, 48))
            draw_rect(pixels, w, h, x, y - 23, x + width, y - 2, color)
            if col % 2 == 0:
                draw_rect(pixels, w, h, x + 2, y - 16, x + width - 2, y - 13, pale)
            x += width + 5
    for x in range(18, 240, 19):
        draw_line(pixels, w, h, x, 224, x + 12, 219, rgb_to_rgba((40, 118, 61)))
    return pixels


def build_desk_texture() -> list[tuple[int, int, int, int]]:
    w = h = 256
    pixels = make_canvas(w, h, hex_to_rgba(PALETTE["deep"]))
    pale = hex_to_rgba(PALETTE["pale"])
    green = hex_to_rgba(PALETTE["green"])
    draw_rect(pixels, w, h, 10, 10, 246, 70, pale)
    for y in range(18, 66, 10):
        draw_line(pixels, w, h, 18, y, 236, y + 2, rgb_to_rgba((148, 193, 151)))
    draw_rect(pixels, w, h, 12, 92, 118, 210, rgb_to_rgba((8, 28, 42)))
    draw_rect(pixels, w, h, 138, 92, 244, 210, rgb_to_rgba((8, 28, 42)))
    for x0 in (22, 148):
        for y0 in (104, 140, 176):
            draw_rect(pixels, w, h, x0, y0, x0 + 84, y0 + 24, green)
            draw_rect(pixels, w, h, x0 + 20, y0 + 10, x0 + 64, y0 + 13, pale)
    draw_text(pixels, w, h, 88, 226, "DESK", green, 2)
    return pixels


def build_beanbag_texture() -> list[tuple[int, int, int, int]]:
    w = h = 256
    pixels = make_canvas(w, h, rgb_to_rgba((28, 78, 38)))
    pale = hex_to_rgba(PALETTE["pale"])
    green = hex_to_rgba(PALETTE["green"])
    deep = hex_to_rgba(PALETTE["deep"])
    dark_green = rgb_to_rgba((17, 52, 26))
    for y in range(h):
        for x in range(w):
            wave = math.sin(x * 0.10 + y * 0.035) + math.sin((x - y) * 0.045)
            if wave > 1.35:
                pixels[y * w + x] = rgb_to_rgba((54, 112, 54))
            elif wave < -1.35:
                pixels[y * w + x] = dark_green
    for angle in range(0, 360, 18):
        rad = math.radians(angle)
        x0 = 128 + int(math.cos(rad) * 14)
        y0 = 128 + int(math.sin(rad) * 10)
        x1 = 128 + int(math.cos(rad) * 110)
        y1 = 128 + int(math.sin(rad) * 86)
        draw_line(pixels, w, h, x0, y0, x1, y1, rgb_to_rgba((66, 130, 62)))
    draw_rect(pixels, w, h, 184, 190, 232, 232, deep)
    draw_text(pixels, w, h, 190, 204, "SIT", green, 1)
    draw_text(pixels, w, h, 34, 34, "SOFT", pale, 2)
    return pixels


def build_disc_rug_texture() -> list[tuple[int, int, int, int]]:
    w = h = 256
    pixels = make_canvas(w, h, rgb_to_rgba((0, 0, 0), 0))
    cx = cy = 128
    deep = hex_to_rgba(PALETTE["deep"])
    pale = hex_to_rgba(PALETTE["pale"])
    green = hex_to_rgba(PALETTE["green"])
    for y in range(h):
        for x in range(w):
            dx = x - cx
            dy = y - cy
            radius = math.sqrt(dx * dx + dy * dy)
            angle = math.atan2(dy, dx)
            if radius > 124:
                continue
            if radius > 116:
                pixels[y * w + x] = deep
            elif radius < 23:
                pixels[y * w + x] = rgb_to_rgba((20, 25, 24))
            elif radius < 30:
                pixels[y * w + x] = pale
            else:
                swirl = math.sin(angle * 5.0 + radius * 0.055) + math.sin((x + y) * 0.028)
                if swirl > 0.85:
                    pixels[y * w + x] = rgb_to_rgba((63, 188, 74))
                elif swirl < -0.80:
                    pixels[y * w + x] = rgb_to_rgba((12, 74, 44))
                else:
                    pixels[y * w + x] = rgb_to_rgba((28, 138, 62))
    draw_text(pixels, w, h, 88, 42, "X WHEEL", pale, 1)
    draw_text(pixels, w, h, 78, 205, "DISC RUG", pale, 2)
    draw_rect(pixels, w, h, 72, 142, 116, 164, deep)
    draw_text(pixels, w, h, 80, 149, "XW", green, 1)
    draw_rect(pixels, w, h, 142, 142, 184, 164, pale)
    draw_text(pixels, w, h, 150, 149, "03", deep, 1)
    return pixels


def build_room_texture() -> list[tuple[int, int, int, int]]:
    w = h = 512
    pixels = make_canvas(w, h, rgb_to_rgba((188, 213, 187)))
    deep = hex_to_rgba(PALETTE["deep"])
    pale = hex_to_rgba(PALETTE["pale"])
    green = hex_to_rgba(PALETTE["green"])
    for y in range(18, 250, 22):
        draw_line(pixels, w, h, 8, y, 504, y + (y % 3), rgb_to_rgba((144, 166, 148)))
    poster_colors = [
        rgb_to_rgba((16, 34, 42)),
        rgb_to_rgba((42, 112, 55)),
        rgb_to_rgba((218, 238, 214)),
        rgb_to_rgba((28, 58, 58)),
    ]
    poster_slots = [
        (18, 22, 90, 104), (104, 18, 174, 94), (188, 30, 252, 118), (270, 20, 344, 104),
        (362, 28, 444, 116), (34, 128, 112, 210), (128, 118, 190, 206), (208, 138, 280, 220),
        (296, 126, 370, 208), (392, 138, 482, 230), (74, 236, 158, 318), (190, 246, 270, 332),
    ]
    for idx, (x0, y0, x1, y1) in enumerate(poster_slots):
        draw_rect(pixels, w, h, x0, y0, x1, y1, poster_colors[idx % len(poster_colors)])
        draw_rect(pixels, w, h, x0 + 4, y0 + 4, x1 - 4, y0 + 8, green if idx % 2 else pale)
        draw_text(pixels, w, h, x0 + 8, y0 + 16, f"EMI {idx:02d}", pale if idx % 2 else deep, 1)
    draw_rect(pixels, w, h, 18, 352, 204, 494, rgb_to_rgba((18, 36, 45)))
    draw_text(pixels, w, h, 36, 374, "DESK NOTES", pale, 2)
    draw_rect(pixels, w, h, 240, 346, 490, 494, rgb_to_rgba((16, 46, 30)))
    for x in range(250, 486, 18):
        draw_line(pixels, w, h, x, 356, x - 22, 488, rgb_to_rgba((70, 154, 78)))
    return pixels


def build_prop_texture(label: str) -> list[tuple[int, int, int, int]]:
    w = h = 128
    pixels = make_canvas(w, h, hex_to_rgba(PALETTE["pale"]))
    deep = hex_to_rgba(PALETTE["deep"])
    green = hex_to_rgba(PALETTE["green"])
    dim_green = rgb_to_rgba((35, 86, 48))
    draw_rect(pixels, w, h, 0, 0, 127, 18, deep)
    draw_text(pixels, w, h, 8, 6, label[:10], green, 1)
    draw_rect(pixels, w, h, 8, 28, 118, 102, rgb_to_rgba((198, 226, 196)))
    for y in range(34, 100, 9):
        draw_line(pixels, w, h, 12, y, 114, y + (y % 2), dim_green)
    for x in range(14, 116, 18):
        draw_rect(pixels, w, h, x, 106, x + 8, 116, green if x % 3 else deep)
    return pixels


def build_bookshelf_asset() -> Asset:
    asset = Asset(
        name="bookshelf",
        output_dir=ASSET_ROOT / "bookshelf",
        texture_size=(256, 256),
        texture_pixels=build_bookshelf_texture(),
        materials=bookshelf_materials(),
        dimensions=(1.20, 0.36, 1.55),
        notes=["Large room-scale bookshelf prop, sized above the CRT while staying in the shared PSX palette."],
    )
    b = MeshBuilder(asset)
    b.add_box("bookshelf_back_panel", (0.0, 0.245, 1.20), (2.90, 0.06, 2.28), 1)
    b.add_box("bookshelf_left_upright", (-1.39, 0.0, 1.20), (0.12, 0.55, 2.40), 0)
    b.add_box("bookshelf_right_upright", (1.39, 0.0, 1.20), (0.12, 0.55, 2.40), 0)
    b.add_box("bookshelf_bottom_plinth", (0.0, 0.0, 0.06), (2.90, 0.55, 0.12), 0)
    b.add_box("bookshelf_top_cap", (0.0, 0.0, 2.34), (2.90, 0.55, 0.12), 0)
    b.add_box("bookshelf_center_divider", (0.0, 0.02, 1.18), (0.08, 0.49, 2.06), 1)
    shelf_z = [0.42, 0.82, 1.22, 1.62, 2.02]
    for idx, z in enumerate(shelf_z):
        b.add_box(f"bookshelf_shelf_board_{idx:02d}", (0.0, 0.0, z), (2.70, 0.50, 0.08), 2)
        b.add_box(f"bookshelf_shelf_shadow_{idx:02d}", (0.0, -0.25, z - 0.055), (2.62, 0.035, 0.045), 1)

    for row, z in enumerate(shelf_z):
        cursor = -1.18
        for col in range(10):
            width = 0.12 + ((row + col) % 4) * 0.025
            height = 0.24 + ((row * 2 + col) % 5) * 0.035
            depth = 0.26 + (col % 3) * 0.035
            material = 3 if (row + col) % 3 else 4
            x = cursor + width * 0.5
            zc = z + 0.06 + height * 0.5
            b.add_box(f"bookshelf_book_{row:02d}_{col:02d}", (x, -0.08, zc), (width, depth, height), material)
            if (row + col) % 2 == 0:
                b.add_box(f"bookshelf_book_label_{row:02d}_{col:02d}", (x, -0.235, zc + height * 0.10), (width * 0.58, 0.018, 0.035), 5)
            else:
                b.add_box(f"bookshelf_book_spine_line_{row:02d}_{col:02d}", (x, -0.235, zc - height * 0.18), (width * 0.32, 0.016, 0.028), 2)
            cursor += width + 0.075

    for idx, x in enumerate([-1.16, -0.78, -0.40, 0.36, 0.74, 1.12]):
        b.add_box(f"bookshelf_plinth_scuff_{idx:02d}", (x, -0.286, 0.145), (0.18, 0.018, 0.028), 5)
    for row, z in enumerate([0.56, 0.96, 1.36, 1.76, 2.16]):
        for col, x in enumerate([-1.18, -0.92, -0.66, -0.40, -0.14, 0.14, 0.40, 0.66, 0.92, 1.18]):
            if (row + col) % 2 == 0:
                b.add_box(f"bookshelf_pixel_book_edge_{row:02d}_{col:02d}", (x, -0.242, z), (0.070, 0.016, 0.030), 5 if col % 3 else 2)
    for idx, x in enumerate([-1.05, -0.75, -0.45, -0.15, 0.15, 0.45, 0.75, 1.05]):
        b.add_box(f"bookshelf_top_label_chip_{idx:02d}", (x, -0.286, 2.365), (0.12, 0.018, 0.025), 3 if idx % 2 else 5)
    b.add_box("col_bookshelf_box", (0.0, 0.0, 1.20), (2.90, 0.55, 2.40), 6)
    return finalize_asset(asset, (1.20, 0.36, 1.55))


def build_desk_asset() -> Asset:
    asset = Asset(
        name="desk",
        output_dir=ASSET_ROOT / "desk",
        texture_size=(256, 256),
        texture_pixels=build_desk_texture(),
        materials=desk_materials(),
        dimensions=(1.65, 0.82, 0.72),
        notes=["Large desk prop, wider and deeper than the CRT television for room-scale placement."],
    )
    b = MeshBuilder(asset)
    b.add_box("desk_tabletop", (0.0, 0.0, 0.98), (3.40, 1.92, 0.14), 1)
    b.add_box("desk_tabletop_shadow", (0.0, 0.0, 0.89), (3.28, 1.80, 0.08), 0)
    b.add_box("desk_front_apron", (0.0, -0.88, 0.80), (3.18, 0.10, 0.18), 0)
    b.add_box("desk_back_apron", (0.0, 0.88, 0.78), (3.08, 0.10, 0.20), 0)
    b.add_box("desk_left_side_panel", (-1.52, 0.0, 0.49), (0.16, 1.52, 0.78), 0)
    b.add_box("desk_right_side_panel", (1.52, 0.0, 0.49), (0.16, 1.52, 0.78), 0)
    b.add_box("desk_modesty_panel", (0.0, 0.76, 0.48), (2.36, 0.10, 0.58), 3)
    for idx, (x, y) in enumerate([(-1.43, -0.76), (1.43, -0.76), (-1.43, 0.74), (1.43, 0.74)]):
        b.add_box(f"desk_square_leg_{idx:02d}", (x, y, 0.43), (0.18, 0.18, 0.82), 0)
        b.add_box(f"desk_foot_pad_{idx:02d}", (x, y, 0.035), (0.30, 0.28, 0.07), 3)

    for side, x in (("left", -0.92), ("right", 0.92)):
        b.add_box(f"desk_{side}_drawer_cavity", (x, -0.65, 0.49), (0.82, 0.12, 0.70), 3)
        for row, z in enumerate([0.31, 0.52, 0.73]):
            face_mat = 2 if row != 1 else 5
            b.add_box(f"desk_{side}_drawer_face_{row:02d}", (x, -0.73, z), (0.72, 0.08, 0.17), face_mat)
            b.add_box(f"desk_{side}_drawer_shadow_{row:02d}", (x, -0.782, z - 0.076), (0.66, 0.025, 0.018), 3)
            b.add_box(f"desk_{side}_drawer_handle_l_{row:02d}", (x - 0.16, -0.792, z), (0.12, 0.025, 0.026), 4)
            b.add_box(f"desk_{side}_drawer_handle_r_{row:02d}", (x + 0.16, -0.792, z), (0.12, 0.025, 0.026), 4)
            b.add_box(f"desk_{side}_drawer_label_{row:02d}", (x, -0.795, z + 0.05), (0.22, 0.018, 0.025), 1)

    for idx, x in enumerate([-1.25, -1.02, -0.79, -0.56, 0.56, 0.79, 1.02, 1.25]):
        b.add_box(f"desk_front_vent_{idx:02d}", (x, -0.812, 0.145), (0.055, 0.025, 0.18), 5)
    for idx, y in enumerate([-0.52, -0.30, -0.08, 0.14, 0.36, 0.58]):
        b.add_box(f"desk_left_side_slit_{idx:02d}", (-1.615, y, 0.66), (0.026, 0.12, 0.045), 5)
        b.add_box(f"desk_right_side_slit_{idx:02d}", (1.615, y, 0.66), (0.026, 0.12, 0.045), 5)
    for idx, x in enumerate([-1.30, -0.98, -0.66, -0.34, -0.02, 0.30, 0.62, 0.94, 1.26]):
        b.add_box(f"desk_top_pixel_scuff_{idx:02d}", (x, -0.58 + (idx % 3) * 0.22, 1.061), (0.16, 0.026, 0.012), 4)
    b.add_cylinder_z("desk_back_cable_grommet", (0.0, 0.62, 1.065), 0.13, 0.018, 12, 3)
    b.add_box("desk_under_keyboard_tray", (0.0, -0.36, 0.71), (0.92, 0.48, 0.07), 3)
    b.add_box("desk_keyboard_tray_pull", (0.0, -0.61, 0.72), (0.44, 0.032, 0.035), 4)
    for row, y in enumerate([-0.72, -0.54, -0.36, -0.18, 0.00, 0.18, 0.36, 0.54, 0.72]):
        for col, x in enumerate([-1.38, -1.10, -0.82, -0.54, -0.26, 0.26, 0.54, 0.82, 1.10, 1.38]):
            if (row + col) % 2 == 0:
                b.add_box(f"desk_top_pixel_grain_{row:02d}_{col:02d}", (x, y, 1.066), (0.12, 0.020, 0.010), 4 if col % 3 else 5)
    for row, z in enumerate([0.22, 0.38, 0.54, 0.70]):
        for col, x in enumerate([-1.18, -0.88, -0.58, -0.28, 0.28, 0.58, 0.88, 1.18]):
            b.add_box(f"desk_front_pixel_trim_{row:02d}_{col:02d}", (x, -0.822, z), (0.075, 0.018, 0.020), 5 if (row + col) % 2 else 3)
    b.add_box("col_desk_box", (0.0, 0.0, 0.525), (3.40, 1.92, 1.05), 6)
    return finalize_asset(asset, (1.65, 0.82, 0.72))


def build_beanbag_asset() -> Asset:
    asset = Asset(
        name="beanbag_chair",
        output_dir=ASSET_ROOT / "beanbag_chair",
        texture_size=(256, 256),
        texture_pixels=build_beanbag_texture(),
        materials=beanbag_materials(),
        dimensions=(1.10, 1.00, 0.58),
        manifest_extra={
            "seat_role": "player_sittable",
            "shape_construction": "single_sculpted_body",
            "sculpt_base": "uv_sphere",
            "fabric_style": "sculpted_green_velour",
        },
        notes=["Player-sittable lazy sofa generated from a UV-sphere body with procedural sculpt deformations."],
    )
    b = MeshBuilder(asset)
    segments = 56
    rings = 22
    positions: list[tuple[float, float, float]] = []
    normals: list[tuple[float, float, float]] = []
    uvs: list[tuple[float, float]] = []
    indices: list[int] = []

    def add_sculpted_vertex(theta: float, phi: float, u: float, v: float) -> int:
        sin_phi = math.sin(phi)
        cos_phi = math.cos(phi)
        lopsided_x = 1.0 + 0.035 * math.sin(theta * 3.0 + 0.4)
        lopsided_y = 1.0 + 0.030 * math.cos(theta * 2.0 - 0.2)
        x = math.cos(theta) * sin_phi * 1.14 * lopsided_x
        y = -0.05 + math.sin(theta) * sin_phi * 0.96 * lopsided_y
        z = 0.62 + cos_phi * 0.52

        top_weight = max(0.0, cos_phi)
        center_sink = math.exp(-(sin_phi * sin_phi) / 0.115) * (top_weight ** 0.55)
        rim_puff = math.exp(-((sin_phi - 0.73) ** 2) / 0.050) * (0.35 + top_weight * 0.65)
        radial_fold = math.sin(theta * 14.0 + sin_phi * 5.0) * sin_phi * (top_weight ** 1.15)
        side_lump = math.sin(theta * 7.0 + 0.6) * max(0.0, -cos_phi) * 0.012
        z = z - 0.30 * center_sink + 0.08 * rim_puff + 0.026 * radial_fold + side_lump

        if cos_phi < -0.62:
            floor_mix = min(1.0, (-cos_phi - 0.62) / 0.38)
            z = z * (1.0 - floor_mix) + (0.13 + 0.025 * sin_phi) * floor_mix

        nx = math.cos(theta) * sin_phi / 1.14
        ny = math.sin(theta) * sin_phi / 0.96
        nz = cos_phi / 0.52
        length = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
        positions.append((x, y, z))
        normals.append((nx / length, ny / length, nz / length))
        uvs.append((u, v))
        return len(positions) - 1

    top_index = add_sculpted_vertex(0.0, 0.0, 0.5, 0.0)
    ring_indices: list[list[int]] = []
    for ring_id in range(1, rings):
        phi = math.pi * ring_id / rings
        ring: list[int] = []
        for idx in range(segments):
            theta = math.tau * idx / segments
            ring.append(add_sculpted_vertex(theta, phi, idx / segments, ring_id / rings))
        ring_indices.append(ring)
    bottom_index = add_sculpted_vertex(0.0, math.pi, 0.5, 1.0)

    first_ring = ring_indices[0]
    for idx in range(segments):
        indices.extend((top_index, first_ring[(idx + 1) % segments], first_ring[idx]))
    for ring_idx in range(len(ring_indices) - 1):
        inner = ring_indices[ring_idx]
        outer = ring_indices[ring_idx + 1]
        for idx in range(segments):
            a = inner[idx]
            b2 = inner[(idx + 1) % segments]
            c = outer[(idx + 1) % segments]
            d = outer[idx]
            indices.extend((a, b2, c, a, c, d))
    last_ring = ring_indices[-1]
    for idx in range(segments):
        indices.extend((last_ring[idx], last_ring[(idx + 1) % segments], bottom_index))

    b.add_primitive("beanbag_uv_sphere_sculpted_body", 0, positions, normals, uvs, indices)
    b.add_elliptical_cylinder_z("beanbag_center_sink", (0.0, -0.12, 0.855), 0.20, 0.16, 0.016, 24, 1)
    for idx in range(28):
        theta = math.tau * idx / 28.0
        x = math.cos(theta) * 0.36
        y = -0.08 + math.sin(theta) * 0.29
        b.add_box_z_rotated(
            f"beanbag_soft_radial_fold_{idx:02d}",
            (x, y, 0.935 + 0.035 * math.sin(theta + 0.3)),
            (0.022, 0.68, 0.022),
            theta - math.pi / 2,
            2,
        )
    b.add_box("beanbag_small_side_tag", (1.10, -0.42, 0.54), (0.035, 0.18, 0.14), 4)
    b.add_box("beanbag_side_tag_mark", (1.123, -0.42, 0.55), (0.012, 0.10, 0.026), 3)
    b.add_box("col_beanbag_sit_volume", (0.0, -0.08, 0.60), (2.26, 1.88, 1.12), 5)
    return finalize_asset(asset, (1.10, 1.00, 0.58))


def build_disc_rug_asset() -> Asset:
    asset = Asset(
        name="disc_rug",
        output_dir=ASSET_ROOT / "disc_rug",
        texture_size=(256, 256),
        texture_pixels=build_disc_rug_texture(),
        materials=disc_rug_materials(),
        dimensions=(1.70, 1.70, 0.035),
        manifest_extra={"surface_role": "floor_rug", "rug_style": "green_disc_rug"},
        notes=["Round floor rug inspired by game disc and vinyl silhouettes, with original X WHEEL markings."],
    )
    b = MeshBuilder(asset)
    b.add_cylinder_z("disc_rug_outer_round_mat", (0.0, 0.0, 0.018), 1.70, 0.032, 72, 0)
    b.add_cylinder_z("disc_rug_deep_outer_rim", (0.0, 0.0, 0.040), 1.70, 0.020, 72, 2, hole_radius=1.54)
    b.add_cylinder_z("disc_rug_lime_inner_swirl", (0.0, 0.0, 0.052), 1.18, 0.016, 72, 1, hole_radius=0.34)
    b.add_cylinder_z("disc_rug_center_label", (0.0, 0.0, 0.064), 0.34, 0.018, 48, 4, hole_radius=0.075)
    b.add_cylinder_z("disc_rug_center_hole_pale", (0.0, 0.0, 0.078), 0.085, 0.014, 24, 3)
    for idx in range(20):
        angle = 0.10 + math.tau * idx / 20.0
        radius = 0.92 + 0.18 * math.sin(idx)
        x = math.cos(angle) * 0.54
        y = math.sin(angle) * 0.54
        b.add_box_z_rotated(
            f"disc_rug_swirl_streak_{idx:02d}",
            (x, y, 0.080),
            (0.055, radius, 0.012),
            angle - math.pi / 2,
            1 if idx % 2 else 0,
        )
    b.add_box("disc_rug_lower_title_block", (0.0, -1.18, 0.086), (1.10, 0.16, 0.012), 2)
    b.add_box("disc_rug_lower_title_text_a", (-0.24, -1.18, 0.096), (0.36, 0.030, 0.010), 3)
    b.add_box("disc_rug_lower_title_text_b", (0.28, -1.18, 0.096), (0.42, 0.030, 0.010), 3)
    b.add_box("disc_rug_small_rating_block", (-0.86, -0.48, 0.088), (0.28, 0.22, 0.012), 3)
    b.add_box("disc_rug_small_logo_block", (0.82, -0.48, 0.088), (0.30, 0.20, 0.012), 3)
    b.add_box("col_disc_rug_box", (0.0, 0.0, 0.025), (3.40, 3.40, 0.05), 5)
    return finalize_asset(asset, (1.70, 1.70, 0.035))


def build_poster_asset() -> Asset:
    asset = Asset(
        name="poster",
        output_dir=ASSET_ROOT / "poster",
        texture_size=(128, 128),
        texture_pixels=build_prop_texture("POSTER"),
        materials=prop_materials(),
        dimensions=(0.46, 0.025, 0.58),
        manifest_extra={"asset_role": "wall_decor"},
        notes=["Reusable taped wall poster asset for Emi room poster clusters."],
    )
    b = MeshBuilder(asset)
    b.add_box("poster_00", (0.0, 0.0, 0.30), (0.44, 0.020, 0.56), 2)
    b.add_box("poster_top_band", (0.0, -0.014, 0.54), (0.40, 0.012, 0.040), 1)
    b.add_box("poster_lower_band", (0.0, -0.014, 0.13), (0.34, 0.012, 0.030), 0)
    for idx, z in enumerate([0.22, 0.29, 0.36, 0.43]):
        b.add_box(f"poster_pixel_line_{idx:02d}", (0.0, -0.016, z), (0.28 - idx * 0.025, 0.010, 0.018), 3 if idx % 2 else 0)
    for idx, (x, z) in enumerate([(-0.16, 0.57), (0.16, 0.57), (-0.16, 0.03), (0.16, 0.03)]):
        b.add_box(f"poster_tape_{idx:02d}", (x, -0.020, z), (0.10, 0.014, 0.026), 2)
    b.add_box("col_poster_box", (0.0, 0.0, 0.29), (0.46, 0.025, 0.58), 7)
    return finalize_asset(asset, (0.46, 0.025, 0.58))


def build_draft_paper_asset() -> Asset:
    asset = Asset(
        name="draft_paper",
        output_dir=ASSET_ROOT / "draft_paper",
        texture_size=(128, 128),
        texture_pixels=build_prop_texture("DRAFT"),
        materials=prop_materials(),
        dimensions=(0.30, 0.22, 0.010),
        manifest_extra={"asset_role": "desk_clutter"},
        notes=["Reusable loose draft-paper sheet with pixel line marks."],
    )
    b = MeshBuilder(asset)
    b.add_box("draft_paper_00", (0.0, 0.0, 0.006), (0.30, 0.22, 0.010), 2)
    for idx, y in enumerate([-0.075, -0.045, -0.015, 0.015, 0.045, 0.075]):
        b.add_box(f"draft_paper_line_{idx:02d}", (-0.015 + idx * 0.004, y, 0.014), (0.20 - idx * 0.010, 0.006, 0.004), 3 if idx % 2 else 0)
    b.add_box("draft_paper_fold", (-0.11, 0.08, 0.016), (0.050, 0.045, 0.004), 1)
    b.add_box("col_draft_paper_box", (0.0, 0.0, 0.005), (0.30, 0.22, 0.010), 7)
    return finalize_asset(asset, (0.30, 0.22, 0.010))


def build_table_lamp_asset() -> Asset:
    asset = Asset(
        name="table_lamp",
        output_dir=ASSET_ROOT / "table_lamp",
        texture_size=(128, 128),
        texture_pixels=build_prop_texture("LAMP"),
        materials=prop_materials(),
        dimensions=(0.28, 0.22, 0.48),
        manifest_extra={"asset_role": "desk_lighting"},
        notes=["Desk table lamp with pixel-era shade, pull chain, and green glow accent."],
    )
    b = MeshBuilder(asset)
    b.add_cylinder_z("table_lamp_base", (0.0, 0.0, 0.025), 0.105, 0.050, 24, 4)
    b.add_cylinder_z("table_lamp_base_ring", (0.0, 0.0, 0.058), 0.118, 0.018, 24, 6, hole_radius=0.085)
    b.add_cylinder_z("table_lamp_stem", (0.0, 0.0, 0.235), 0.020, 0.34, 12, 6)
    b.add_box("table_lamp", (0.0, 0.0, 0.425), (0.28, 0.22, 0.13), 1)
    b.add_box("table_lamp_shade_dark_lower", (0.0, -0.006, 0.365), (0.32, 0.25, 0.035), 0)
    b.add_box("table_lamp_glow_strip", (0.0, -0.118, 0.395), (0.20, 0.012, 0.034), 2)
    b.add_box("table_lamp_pull_chain", (0.13, -0.09, 0.270), (0.008, 0.008, 0.18), 2)
    b.add_cylinder_z("table_lamp_chain_knob", (0.13, -0.09, 0.165), 0.018, 0.018, 8, 1)
    b.add_box("col_table_lamp_box", (0.0, 0.0, 0.24), (0.32, 0.25, 0.48), 7)
    return finalize_asset(asset, (0.28, 0.22, 0.48))


def build_pencil_asset() -> Asset:
    asset = Asset(
        name="pencil",
        output_dir=ASSET_ROOT / "pencil",
        texture_size=(128, 128),
        texture_pixels=build_prop_texture("PENCIL"),
        materials=prop_materials(),
        dimensions=(0.026, 0.26, 0.026),
        manifest_extra={"asset_role": "desk_clutter"},
        notes=["Reusable short pencil prop sized for desk clutter."],
    )
    b = MeshBuilder(asset)
    b.add_cylinder_y("pencil", (0.0, 0.0, 0.013), 0.013, 0.22, 16, 1)
    b.add_cylinder_y("pencil_tip_wood", (0.0, -0.125, 0.013), 0.013, 0.035, 12, 2)
    b.add_cylinder_y("pencil_eraser_cap", (0.0, 0.125, 0.013), 0.014, 0.035, 12, 3)
    b.add_box("pencil_pixel_mark", (0.0, -0.02, 0.029), (0.006, 0.10, 0.004), 0)
    b.add_box("col_pencil_box", (0.0, 0.0, 0.013), (0.026, 0.26, 0.026), 7)
    return finalize_asset(asset, (0.026, 0.26, 0.026))


def build_eraser_asset() -> Asset:
    asset = Asset(
        name="eraser",
        output_dir=ASSET_ROOT / "eraser",
        texture_size=(128, 128),
        texture_pixels=build_prop_texture("ERASER"),
        materials=prop_materials(),
        dimensions=(0.13, 0.075, 0.035),
        manifest_extra={"asset_role": "desk_clutter"},
        notes=["Reusable small eraser with wrapper bands."],
    )
    b = MeshBuilder(asset)
    b.add_box("eraser", (0.0, 0.0, 0.018), (0.13, 0.075, 0.035), 2)
    b.add_box("eraser_green_wrapper", (0.0, 0.0, 0.039), (0.075, 0.081, 0.010), 1)
    b.add_box("eraser_deep_wrapper_line_a", (-0.030, 0.0, 0.046), (0.010, 0.083, 0.006), 0)
    b.add_box("eraser_deep_wrapper_line_b", (0.030, 0.0, 0.046), (0.010, 0.083, 0.006), 0)
    for idx, x in enumerate([-0.054, 0.054]):
        b.add_box(f"eraser_chamfer_pixel_{idx:02d}", (x, 0.0, 0.040), (0.018, 0.065, 0.006), 3)
    b.add_box("eraser_corner_scuff", (0.050, 0.026, 0.047), (0.024, 0.018, 0.006), 0)
    b.add_box("col_eraser_box", (0.0, 0.0, 0.018), (0.13, 0.075, 0.035), 7)
    return finalize_asset(asset, (0.13, 0.075, 0.035))


def build_potted_plant_asset() -> Asset:
    asset = Asset(
        name="potted_plant",
        output_dir=ASSET_ROOT / "potted_plant",
        texture_size=(128, 128),
        texture_pixels=build_prop_texture("PLANT"),
        materials=prop_materials(),
        dimensions=(0.32, 0.30, 0.38),
        manifest_extra={"asset_role": "shelf_decor"},
        notes=["Small potted plant for shelf-top decoration."],
    )
    b = MeshBuilder(asset)
    b.add_cylinder_z("bookshelf_planter", (0.0, 0.0, 0.09), 0.115, 0.18, 20, 4)
    b.add_cylinder_z("plant_pot_rim", (0.0, 0.0, 0.185), 0.130, 0.030, 20, 0, hole_radius=0.090)
    b.add_cylinder_z("plant_soil", (0.0, 0.0, 0.205), 0.085, 0.018, 16, 0)
    for idx in range(12):
        angle = math.tau * idx / 12.0
        radius = 0.055 + 0.035 * (idx % 3)
        x = math.cos(angle) * radius
        y = math.sin(angle) * radius
        b.add_box_z_rotated(f"plant_leaf_{idx:02d}", (x, y, 0.285 + 0.012 * (idx % 4)), (0.035, 0.20, 0.018), angle, 1 if idx % 2 else 3)
    b.add_box("col_potted_plant_box", (0.0, 0.0, 0.19), (0.32, 0.30, 0.38), 7)
    return finalize_asset(asset, (0.32, 0.30, 0.38))


def build_wheeled_lounge_chair_asset() -> Asset:
    asset = Asset(
        name="wheeled_lounge_chair",
        output_dir=ASSET_ROOT / "wheeled_lounge_chair",
        texture_size=(128, 128),
        texture_pixels=build_prop_texture("CHAIR"),
        materials=prop_materials(),
        dimensions=(0.62, 0.58, 0.78),
        manifest_extra={"asset_role": "player_seat"},
        notes=["Wheeled lounge chair sized for a five-head chibi player character."],
    )
    b = MeshBuilder(asset)
    b.add_box("wheeled_lounge_chair", (0.0, 0.0, 0.38), (0.55, 0.48, 0.17), 3)
    b.add_box("chair_seat_front_roll", (0.0, -0.25, 0.42), (0.58, 0.08, 0.12), 1)
    b.add_box_z_rotated("chair_back", (0.0, 0.19, 0.67), (0.58, 0.10, 0.45), 0.0, 3)
    b.add_box("chair_back_top_roll", (0.0, 0.22, 0.92), (0.60, 0.10, 0.08), 1)
    b.add_cylinder_z("chair_center_post", (0.0, 0.0, 0.21), 0.030, 0.32, 16, 6)
    b.add_cylinder_z("chair_hub", (0.0, 0.0, 0.08), 0.085, 0.050, 20, 6)
    for idx in range(5):
        angle = math.tau * idx / 5.0
        x = math.cos(angle) * 0.23
        y = math.sin(angle) * 0.20
        b.add_box_z_rotated(f"chair_wheel_arm_{idx:02d}", (x * 0.5, y * 0.5, 0.08), (0.045, 0.30, 0.040), angle - math.pi / 2, 6)
        b.add_cylinder_y(f"chair_wheel_{idx:02d}", (x, y, 0.045), 0.045, 0.030, 12, 0)
    for idx, x in enumerate([-0.18, -0.06, 0.06, 0.18]):
        b.add_box(f"chair_back_stitch_{idx:02d}", (x, 0.135, 0.70), (0.014, 0.010, 0.30), 2)
    b.add_box("col_wheeled_lounge_chair_box", (0.0, 0.0, 0.39), (0.62, 0.58, 0.78), 7)
    return finalize_asset(asset, (0.62, 0.58, 0.78))


def build_floor_book_asset() -> Asset:
    asset = Asset(
        name="floor_book",
        output_dir=ASSET_ROOT / "floor_book",
        texture_size=(128, 128),
        texture_pixels=build_prop_texture("BOOK"),
        materials=prop_materials(),
        dimensions=(0.22, 0.30, 0.045),
        manifest_extra={"asset_role": "floor_clutter"},
        notes=["Reusable fallen book asset for room floor clutter."],
    )
    b = MeshBuilder(asset)
    b.add_box("floor_book_00", (0.0, 0.0, 0.023), (0.22, 0.30, 0.045), 1)
    b.add_box("floor_book_pages_00", (0.016, 0.0, 0.051), (0.18, 0.25, 0.010), 2)
    b.add_box("floor_book_spine", (-0.105, 0.0, 0.055), (0.020, 0.30, 0.014), 0)
    for idx, y in enumerate([-0.10, -0.04, 0.02, 0.08]):
        b.add_box(f"floor_book_page_line_{idx:02d}", (0.026, y, 0.060), (0.13, 0.006, 0.004), 3)
    b.add_box("col_floor_book_box", (0.0, 0.0, 0.023), (0.22, 0.30, 0.045), 7)
    return finalize_asset(asset, (0.22, 0.30, 0.045))


def build_cd_case_asset() -> Asset:
    asset = Asset(
        name="cd_case",
        output_dir=ASSET_ROOT / "cd_case",
        texture_size=(128, 128),
        texture_pixels=build_prop_texture("CD CASE"),
        materials=prop_materials(),
        dimensions=(0.20, 0.20, 0.022),
        manifest_extra={"asset_role": "floor_clutter"},
        notes=["Reusable translucent CD case for room floor clutter."],
    )
    b = MeshBuilder(asset)
    b.add_box("floor_cd_case_00", (0.0, 0.0, 0.011), (0.20, 0.20, 0.022), 5)
    b.add_box("floor_cd_case_deep_spine", (-0.090, 0.0, 0.026), (0.018, 0.19, 0.010), 0)
    b.add_box("floor_cd_label", (0.020, 0.0, 0.030), (0.11, 0.040, 0.006), 2)
    b.add_cylinder_z("floor_cd_case_disc_hint", (0.020, 0.0, 0.034), 0.045, 0.005, 20, 1, hole_radius=0.010)
    b.add_box("col_cd_case_box", (0.0, 0.0, 0.011), (0.20, 0.20, 0.022), 7)
    return finalize_asset(asset, (0.20, 0.20, 0.022))


def copy_materials_with_prefix(materials: list[Material], prefix: str) -> list[Material]:
    return [Material(f"{prefix}_{material.name}", material.color, material.roughness, material.metallic, material.alpha_mode) for material in materials]


def transform_primitive_for_room(
    primitive: Primitive,
    prefix: str,
    material_offset: int,
    translation: tuple[float, float, float],
    scale: float = 1.0,
    rotation_z: float = 0.0,
) -> Primitive:
    tx, ty, tz = translation
    cos_a = math.cos(rotation_z)
    sin_a = math.sin(rotation_z)

    def transform_position(point: tuple[float, float, float]) -> tuple[float, float, float]:
        x, y, z = point
        xr = cos_a * x * scale - sin_a * y * scale
        yr = sin_a * x * scale + cos_a * y * scale
        return (xr + tx, yr + ty, z * scale + tz)

    def transform_normal(normal: tuple[float, float, float]) -> tuple[float, float, float]:
        x, y, z = normal
        return (cos_a * x - sin_a * y, sin_a * x + cos_a * y, z)

    return Primitive(
        name=f"{prefix}_{primitive.name}",
        material_index=primitive.material_index + material_offset,
        positions=[transform_position(point) for point in primitive.positions],
        normals=[transform_normal(normal) for normal in primitive.normals],
        uvs=list(primitive.uvs),
        colors=list(primitive.colors),
        indices=list(primitive.indices),
    )


def add_asset_instance_to_room(
    room: Asset,
    source: Asset,
    prefix: str,
    translation: tuple[float, float, float],
    scale: float = 1.0,
    rotation_z: float = 0.0,
) -> None:
    material_offset = len(room.materials)
    room.materials.extend(copy_materials_with_prefix(source.materials, prefix))
    room.primitives.extend(
        transform_primitive_for_room(primitive, prefix, material_offset, translation, scale, rotation_z)
        for primitive in source.export_primitives
    )


def build_emi_room_asset(
    console: Asset,
    disc: Asset,
    crt: Asset,
    bookshelf: Asset,
    desk: Asset,
    rug: Asset,
    poster: Asset,
    draft_paper: Asset,
    table_lamp: Asset,
    pencil: Asset,
    eraser: Asset,
    potted_plant: Asset,
    wheeled_lounge_chair: Asset,
    floor_book: Asset,
    cd_case: Asset,
) -> Asset:
    asset = Asset(
        name="emi_room",
        output_dir=ASSET_ROOT / "emi_room",
        texture_size=(512, 512),
        texture_pixels=build_room_texture(),
        materials=room_materials(),
        dimensions=(4.20, 3.20, 2.60),
        manifest_extra={
            "scene_role": "character_room",
            "room_owner": "emi",
            "poster_count": 14,
            "disc_count_on_desk": 3,
            "floor_book_count": 6,
            "floor_cd_case_count": 5,
            "included_assets": [
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
            ],
        },
        notes=["Complete low-poly room scene for Emi, composed from prior assets plus original room clutter."],
    )
    b = MeshBuilder(asset)
    b.add_box("emi_room_floor", (0.0, 0.0, -0.025), (4.20, 3.20, 0.05), 1)
    b.add_box("emi_room_back_wall", (0.0, 1.58, 1.30), (4.20, 0.07, 2.60), 0)
    b.add_box("emi_room_left_wall", (-2.10, 0.02, 1.30), (0.07, 3.12, 2.60), 0)
    b.add_box("emi_room_right_wall", (2.10, 0.02, 1.30), (0.07, 3.12, 2.60), 0)
    b.add_box("emi_room_back_baseboard", (0.0, 1.535, 0.11), (4.16, 0.08, 0.12), 2)
    b.add_box("emi_room_left_baseboard", (-2.045, 0.02, 0.11), (0.08, 3.08, 0.12), 2)
    b.add_box("emi_room_right_baseboard", (2.045, 0.02, 0.11), (0.08, 3.08, 0.12), 2)
    for row, z in enumerate([0.42, 0.58, 0.74, 0.90, 1.06, 1.22, 1.38, 1.54, 1.70, 1.86, 2.02, 2.18]):
        for col, x in enumerate([-1.90, -1.62, -1.34, -1.06, -0.78, -0.50, -0.22, 0.06, 0.34, 0.62, 0.90, 1.18, 1.46, 1.74]):
            if (row + col) % 2 == 0:
                b.add_box(
                    f"emi_room_wall_pixel_patch_{row:02d}_{col:02d}",
                    (x, 1.522, z),
                    (0.10, 0.012, 0.020),
                    5 if (row + col) % 4 else 2,
                )
    for row, y in enumerate([-1.28, -1.04, -0.80, -0.56, -0.32, -0.08, 0.16, 0.40, 0.64, 0.88, 1.12]):
        for col, x in enumerate([-1.78, -1.46, -1.14, -0.82, -0.50, -0.18, 0.14, 0.46, 0.78, 1.10, 1.42, 1.74]):
            if True:
                b.add_box(
                    f"emi_room_floor_pixel_wear_{row:02d}_{col:02d}",
                    (x, y, 0.006),
                    (0.12, 0.030, 0.008),
                    2 if col % 2 else 4,
                )

    poster_specs = [
        (-1.72, 1.520, 1.88, 0.94), (-1.18, 1.518, 1.90, 0.84),
        (-0.66, 1.516, 1.86, 0.98), (-0.14, 1.520, 1.92, 0.88),
        (0.42, 1.518, 1.88, 0.96), (0.96, 1.516, 1.93, 0.86),
        (1.50, 1.520, 1.86, 0.92), (-1.66, 1.518, 1.20, 0.80),
        (-1.12, 1.516, 1.16, 0.90), (-0.56, 1.520, 1.24, 0.78),
        (0.04, 1.518, 1.18, 0.92), (0.66, 1.516, 1.22, 0.82),
        (1.20, 1.520, 1.16, 0.90), (1.68, 1.518, 1.26, 0.76),
    ]
    for x, y, z, scale in poster_specs:
        add_asset_instance_to_room(asset, poster, "emi_room", (x, y, z), scale, 0.0)

    add_asset_instance_to_room(asset, desk, "emi_room_desk", (-0.05, 0.84, 0.0), 1.0, 0.0)
    b.add_box("emi_room_desk_cluster", (-0.05, 0.43, 0.035), (1.82, 0.62, 0.030), 14)
    add_asset_instance_to_room(asset, bookshelf, "emi_room_bookshelf", (-1.48, 0.86, 0.0), 1.0, 0.0)
    add_asset_instance_to_room(asset, crt, "emi_room_crt_tv", (-0.42, 0.76, 0.72), 1.0, 0.0)
    add_asset_instance_to_room(asset, console, "emi_room_game_console", (0.42, 0.64, 0.72), 1.0, 0.0)
    for x, y, rot in [(0.30, 0.34, 0.20), (0.52, 0.35, -0.35), (0.72, 0.37, 0.55)]:
        add_asset_instance_to_room(asset, disc, "emi_room_desk_disc", (x, y, 0.735), 1.0, rot)
    add_asset_instance_to_room(asset, rug, "emi_room_disc_rug", (-0.70, -0.70, 0.0), 1.0, 0.0)
    add_asset_instance_to_room(asset, table_lamp, "emi_room", (-0.76, 0.48, 0.72), 1.0, 0.0)
    add_asset_instance_to_room(asset, potted_plant, "emi_room", (-1.55, 0.86, 1.55), 1.0, 0.0)
    add_asset_instance_to_room(asset, wheeled_lounge_chair, "emi_room", (-0.72, -0.68, 0.0), 1.0, 0.0)

    for x, y, rot in [(-0.18, 0.36, 0.10), (0.02, 0.30, -0.25), (0.18, 0.40, 0.35)]:
        add_asset_instance_to_room(asset, pencil, "emi_room", (x, y, 0.725), 1.0, rot)
    add_asset_instance_to_room(asset, eraser, "emi_room", (0.30, 0.46, 0.725), 1.0, 0.0)
    for x, y, rot in [(-0.42, 0.36, 0.10), (-0.22, 0.24, -0.12), (0.02, 0.22, 0.18), (0.24, 0.25, -0.28)]:
        add_asset_instance_to_room(asset, draft_paper, "emi_room", (x, y, 0.724), 1.0, rot)

    for x, y, rot in [(-0.50, 0.08, 0.20), (-0.22, -0.12, -0.35), (0.28, -0.08, 0.55), (0.52, -0.26, -0.15), (0.78, 0.05, 0.35), (0.96, -0.20, -0.45)]:
        add_asset_instance_to_room(asset, floor_book, "emi_room", (x, y, 0.0), 1.0, rot)
    for x, y, rot in [(-0.88, -0.16, 0.05), (-0.66, -0.42, 0.40), (-0.06, -0.48, -0.30), (0.36, -0.60, 0.18), (0.98, -0.54, -0.62)]:
        add_asset_instance_to_room(asset, cd_case, "emi_room", (x, y, 0.0), 1.0, rot)

    b.add_box("col_emi_room_box", (0.0, 0.0, 1.30), (4.20, 3.20, 2.60), 14)
    return finalize_asset(asset, (4.20, 3.20, 2.60))


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
    console = build_console_asset()
    disc = build_disc_asset()
    crt = build_crt_tv_asset()
    bookshelf = build_bookshelf_asset()
    desk = build_desk_asset()
    beanbag = build_beanbag_asset()
    rug = build_disc_rug_asset()
    poster = build_poster_asset()
    draft_paper = build_draft_paper_asset()
    table_lamp = build_table_lamp_asset()
    pencil = build_pencil_asset()
    eraser = build_eraser_asset()
    potted_plant = build_potted_plant_asset()
    wheeled_lounge_chair = build_wheeled_lounge_chair_asset()
    floor_book = build_floor_book_asset()
    cd_case = build_cd_case_asset()
    emi_room = build_emi_room_asset(
        console,
        disc,
        crt,
        bookshelf,
        desk,
        rug,
        poster,
        draft_paper,
        table_lamp,
        pencil,
        eraser,
        potted_plant,
        wheeled_lounge_chair,
        floor_book,
        cd_case,
    )
    assets = [
        console,
        disc,
        crt,
        bookshelf,
        desk,
        beanbag,
        rug,
        poster,
        draft_paper,
        table_lamp,
        pencil,
        eraser,
        potted_plant,
        wheeled_lounge_chair,
        floor_book,
        cd_case,
        emi_room,
    ]
    manifest = {
        "generator": "tools/create_psx_dvr_assets.py",
        "source_note": "GLB geometry is generated reproducibly by script. Blender imports each object as an individual asset.",
        "scale_reference": {
            "character": SCALE_REFERENCE,
            "character_height_m": 1.40,
            "head_count": 5,
            "desk_height_m": 0.72,
        },
        "style": {
            "detail_level": DETAIL_LEVEL,
            "color_policy": COLOR_POLICY,
            "reference": "chunky low-poly forms with denser pixel details and preserved green/pale/deep palette",
        },
        "palette": {
            "primary": PALETTE_PRIMARY,
            "usage": {
                "#3FA943": "status lights, labels, book spines, drawer fronts, green fabric, rug swirls, and accents",
                "#E8F8E4": "pale plastic highlights, shelf boards, desktop, stitches, rug print, and disc center",
                "#0C1725": "deep shell, recesses, ports, and shadows",
            },
        },
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
            "dimensions": list(asset.dimensions) if asset.dimensions else None,
            "objects": [asset.name],
            "source_parts": [primitive.name for primitive in asset.export_primitives],
            "notes": asset.notes,
        }
        manifest["assets"][asset.name].update(asset.manifest_extra)
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
        ASSET_ROOT / "crt_tv" / "crt_tv.glb",
        ASSET_ROOT / "bookshelf" / "bookshelf.glb",
        ASSET_ROOT / "desk" / "desk.glb",
        ASSET_ROOT / "beanbag_chair" / "beanbag_chair.glb",
        ASSET_ROOT / "disc_rug" / "disc_rug.glb",
        ASSET_ROOT / "poster" / "poster.glb",
        ASSET_ROOT / "draft_paper" / "draft_paper.glb",
        ASSET_ROOT / "table_lamp" / "table_lamp.glb",
        ASSET_ROOT / "pencil" / "pencil.glb",
        ASSET_ROOT / "eraser" / "eraser.glb",
        ASSET_ROOT / "potted_plant" / "potted_plant.glb",
        ASSET_ROOT / "wheeled_lounge_chair" / "wheeled_lounge_chair.glb",
        ASSET_ROOT / "floor_book" / "floor_book.glb",
        ASSET_ROOT / "cd_case" / "cd_case.glb",
        ASSET_ROOT / "emi_room" / "emi_room.glb",
    ]
    for path in expected:
        print(verify_glb(path))


def report_outputs() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if manifest.get("palette", {}).get("primary") != PALETTE_PRIMARY:
        raise ValueError(f"palette mismatch: {manifest.get('palette')}")
    if manifest.get("scale_reference", {}).get("character") != SCALE_REFERENCE:
        raise ValueError(f"scale reference mismatch: {manifest.get('scale_reference')}")
    if manifest.get("style", {}).get("detail_level") != DETAIL_LEVEL:
        raise ValueError(f"detail level mismatch: {manifest.get('style')}")
    console = manifest["assets"]["psx_dvr_console"]
    disc = manifest["assets"]["psx_dvr_disc"]
    crt = manifest["assets"]["crt_tv"]
    bookshelf = manifest["assets"]["bookshelf"]
    desk = manifest["assets"]["desk"]
    beanbag = manifest["assets"]["beanbag_chair"]
    rug = manifest["assets"]["disc_rug"]
    room = manifest["assets"]["emi_room"]
    small_props = {
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
    if "psx_dvr_crt_set" in manifest["assets"]:
        raise ValueError("psx_dvr_crt_set should not be generated")
    for asset_name, asset in manifest["assets"].items():
        if asset.get("scale_reference") != SCALE_REFERENCE:
            raise ValueError(f"{asset_name} scale reference mismatch: {asset.get('scale_reference')}")
    if not (1800 <= console["triangles"] <= 4200):
        raise ValueError(f"psx_dvr_console triangle count outside budget: {console['triangles']}")
    if console["texture_size"] != [256, 256]:
        raise ValueError(f"psx_dvr_console texture size mismatch: {console['texture_size']}")
    if not (700 <= disc["triangles"] <= 1800):
        raise ValueError(f"psx_dvr_disc triangle count outside budget: {disc['triangles']}")
    if disc["texture_size"] != [128, 128]:
        raise ValueError(f"psx_dvr_disc texture size mismatch: {disc['texture_size']}")
    if not (2200 <= crt["triangles"] <= 5200):
        raise ValueError(f"crt_tv triangle count outside budget: {crt['triangles']}")
    if crt["texture_size"] != [256, 256]:
        raise ValueError(f"crt_tv texture size mismatch: {crt['texture_size']}")
    if crt.get("screen_state") != "black_glass":
        raise ValueError(f"crt_tv screen state mismatch: {crt.get('screen_state')}")
    if crt.get("front_style") != "large_bezel_box_crt":
        raise ValueError(f"crt_tv front style mismatch: {crt.get('front_style')}")
    if crt.get("screen_material") != "convex_black_glass":
        raise ValueError(f"crt_tv screen material mismatch: {crt.get('screen_material')}")
    if crt.get("control_layout") != "bottom_button_row":
        raise ValueError(f"crt_tv control layout mismatch: {crt.get('control_layout')}")
    for asset_name, room_asset in (("bookshelf", bookshelf), ("desk", desk)):
        if not (1800 <= room_asset["triangles"] <= 5200):
            raise ValueError(f"{asset_name} triangle count outside budget: {room_asset['triangles']}")
        if room_asset["texture_size"] != [256, 256]:
            raise ValueError(f"{asset_name} texture size mismatch: {room_asset['texture_size']}")
    if not (2200 <= beanbag["triangles"] <= 5600):
        raise ValueError(f"beanbag_chair triangle count outside budget: {beanbag['triangles']}")
    if beanbag["texture_size"] != [256, 256]:
        raise ValueError(f"beanbag_chair texture size mismatch: {beanbag['texture_size']}")
    if beanbag.get("seat_role") != "player_sittable":
        raise ValueError(f"beanbag_chair seat role mismatch: {beanbag.get('seat_role')}")
    if beanbag.get("shape_construction") != "single_sculpted_body":
        raise ValueError(f"beanbag_chair shape construction mismatch: {beanbag.get('shape_construction')}")
    if beanbag.get("sculpt_base") != "uv_sphere":
        raise ValueError(f"beanbag_chair sculpt base mismatch: {beanbag.get('sculpt_base')}")
    if beanbag.get("fabric_style") != "sculpted_green_velour":
        raise ValueError(f"beanbag_chair fabric style mismatch: {beanbag.get('fabric_style')}")
    if not (1200 <= rug["triangles"] <= 3200):
        raise ValueError(f"disc_rug triangle count outside budget: {rug['triangles']}")
    if rug["texture_size"] != [256, 256]:
        raise ValueError(f"disc_rug texture size mismatch: {rug['texture_size']}")
    if rug.get("surface_role") != "floor_rug":
        raise ValueError(f"disc_rug surface role mismatch: {rug.get('surface_role')}")
    if rug.get("rug_style") != "green_disc_rug":
        raise ValueError(f"disc_rug style mismatch: {rug.get('rug_style')}")
    for asset_name, asset_role in small_props.items():
        prop = manifest["assets"].get(asset_name)
        if not prop:
            raise ValueError(f"{asset_name} was not generated")
        if prop.get("asset_role") != asset_role:
            raise ValueError(f"{asset_name} role mismatch: {prop.get('asset_role')}")
        if not (80 <= prop["triangles"] <= 1800):
            raise ValueError(f"{asset_name} triangle count outside budget: {prop['triangles']}")
    if not (22000 <= room["triangles"] <= 62000):
        raise ValueError(f"emi_room triangle count outside budget: {room['triangles']}")
    if room["texture_size"] != [512, 512]:
        raise ValueError(f"emi_room texture size mismatch: {room['texture_size']}")
    if room.get("scene_role") != "character_room":
        raise ValueError(f"emi_room scene role mismatch: {room.get('scene_role')}")
    if not (10 <= room.get("poster_count", 0) <= 15):
        raise ValueError(f"emi_room poster count mismatch: {room.get('poster_count')}")
    if room.get("disc_count_on_desk") != 3:
        raise ValueError(f"emi_room disc count mismatch: {room.get('disc_count_on_desk')}")
    if not (bookshelf["dimensions"][2] > crt["dimensions"][2] and bookshelf["dimensions"][0] > crt["dimensions"][0]):
        raise ValueError("bookshelf must be larger than crt_tv in width and height")
    if not (desk["dimensions"][0] > crt["dimensions"][0] and desk["dimensions"][1] > crt["dimensions"][1]):
        raise ValueError("desk must be larger than crt_tv in width and depth")
    print("psx_dvr_console: higher-detail five-head scale asset, texture 256x256")
    print("psx_dvr_disc: higher-detail five-head scale asset, texture 128x128")
    print("crt_tv: large-bezel box CRT with convex black glass, higher-detail texture 256x256")
    print("bookshelf: five-head scale room furniture, texture 256x256")
    print("desk: five-head scale room furniture, texture 256x256")
    print("beanbag_chair: player-sittable sculpted sofa, higher-detail texture 256x256")
    print("disc_rug: green disc-style floor rug, higher-detail texture 256x256")
    print("room clutter: poster, draft_paper, table_lamp, pencil, eraser, potted_plant, wheeled_lounge_chair, floor_book, cd_case")
    print("emi_room: character room scene, higher-detail five-head scale, texture 512x512")


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
