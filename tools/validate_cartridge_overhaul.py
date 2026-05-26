import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIALOGUE_DIR = ROOT / "data" / "dialogue"

CHAPTERS = {
    "cartridge1_fries_rain.csv": {"min_lines": 80, "max_lines": 140},
    "cartridge2_dinner.csv": {"min_lines": 80, "max_lines": 140},
    "cartridge3_hajimi.csv": {"min_lines": 80, "max_lines": 140},
    "final_chapter_panegyris.csv": {"min_lines": 95, "max_lines": 160},
}

SCRIPT_MARKERS = {
    "scripts/ui/menu_controller.gd": [
        "_create_low_poly_bedroom",
        "_create_desk_preview",
        "DeskConsole",
        "CartridgePreview",
    ],
    "scripts/gameplay/cartridge_select_controller.gd": [
        "_create_console_model",
        "_create_cartridge_label",
        "_sync_cartridge_area",
        "_apply_completed_visuals",
    ],
    "scripts/ui/dialogue_box.gd": [
        "_keyboard_target_presses",
        "_keyboard_target_chars",
    ],
    "scripts/gameplay/cartridge2_controller.gd": [
        "_create_fridge_minigame_ui",
        "_on_fridge_item_clicked",
        "FridgeOverlay",
        "MacGuffinFigure",
    ],
    "scripts/gameplay/final_chapter_coordinator.gd": [
        "_on_credit_roll_requested",
        "_show_blood_memory",
        "PostCreditsDouble",
    ],
}

FORBIDDEN_TERMS = [
    "第一自然",
    "第二自然",
    "精神自然",
    "麦乐芬",
    "麦多芬",
    "TODO",
    "TBD",
]


def read_rows(path: Path) -> list[list[str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return [row for row in csv.reader(f) if row and not row[0].startswith("#")]


def validate_csv_shape(filename: str, rows: list[list[str]], errors: list[str]) -> None:
    if not rows:
        errors.append(f"{filename}: empty file")
        return

    header = rows[0]
    expected = [
        "id",
        "character_id",
        "emotion",
        "text_zh",
        "text_ja",
        "safe_version",
        "condition",
        "interaction_type",
    ]
    if header != expected:
        errors.append(f"{filename}: header mismatch: {header}")

    for line_no, row in enumerate(rows[1:], start=2):
        if len(row) != 8:
            errors.append(f"{filename}:{line_no}: expected 8 columns, got {len(row)}")


def validate_script_contract(filename: str, rows: list[list[str]], errors: list[str]) -> None:
    body = rows[1:]
    visible_lines = [
        row for row in body
        if len(row) == 8 and (row[3].strip() or row[7].strip() or row[1].strip() == "CHOICE")
    ]
    limits = CHAPTERS[filename]
    if not (limits["min_lines"] <= len(visible_lines) <= limits["max_lines"]):
        errors.append(
            f"{filename}: expected {limits['min_lines']}-{limits['max_lines']} script rows, got {len(visible_lines)}"
        )

    joined = "\n".join(",".join(row) for row in rows)
    for term in FORBIDDEN_TERMS:
        if term in joined:
            errors.append(f"{filename}: forbidden term found: {term}")

    if filename == "final_chapter_panegyris.csv":
        for line_no, row in enumerate(rows[1:], start=2):
            if len(row) == 8 and row[1] == "CHOICE":
                errors.append(f"{filename}:{line_no}: final chapter must be linear, found CHOICE")


def main() -> int:
    errors: list[str] = []
    for filename in CHAPTERS:
        path = DIALOGUE_DIR / filename
        if not path.exists():
            errors.append(f"{filename}: missing")
            continue
        rows = read_rows(path)
        validate_csv_shape(filename, rows, errors)
        validate_script_contract(filename, rows, errors)

    for rel_path, markers in SCRIPT_MARKERS.items():
        path = ROOT / rel_path
        if not path.exists():
            errors.append(f"{rel_path}: missing")
            continue
        text = path.read_text(encoding="utf-8")
        for marker in markers:
            if marker not in text:
                errors.append(f"{rel_path}: required marker missing: {marker}")

    final_controller = ROOT / "scripts" / "gameplay" / "final_chapter_coordinator.gd"
    if final_controller.exists():
        text = final_controller.read_text(encoding="utf-8")
        for forbidden in ["Phase.CHOICE", "ENDING_A", "ENDING_B", "_on_final_choice"]:
            if forbidden in text:
                errors.append(f"scripts/gameplay/final_chapter_coordinator.gd: linear finale must not contain {forbidden}")

    if errors:
        print("Cartridge overhaul validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Cartridge overhaul validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
