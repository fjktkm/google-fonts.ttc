#!/usr/bin/env python3
import os
import tempfile
from pathlib import Path

import uharfbuzz as hb
from fontTools.ttLib import TTCollection, TTFont

FONT_PATTERNS = ("apache/*/*.ttf", "ofl/*/*.ttf", "ufl/*/*.ttf")
FONT_ROOT = Path("data/google/fonts")
OUTPUT = Path("output/google-fonts.ttc")
SVG = int.from_bytes(b"SVG ", "big")
KERN = int.from_bytes(b"kern", "big")
GPOS = int.from_bytes(b"GPOS", "big")


def discover_fonts() -> list[Path]:
    return sorted(path for pattern in FONT_PATTERNS for path in FONT_ROOT.glob(pattern))


def windows_unique_id(font: TTFont) -> str:
    names = font["name"]
    version = names.getName(5, 3, 1, 0x0409).toUnicode()
    version = version.removeprefix("Version ").split(";", 1)[0]
    postscript_name = names.getName(6, 3, 1, 0x0409).toUnicode()
    vendor = font["OS/2"].achVendID.strip()
    return f"{version};{vendor};{postscript_name}"


def repair_windows_names(font: TTFont) -> str | None:
    names = font["name"]
    if names.getName(3, 3, 1, 0x0409) or names.getName(3, 3, 10, 0x0409):
        return None
    unique_id = windows_unique_id(font)
    names.setName(unique_id, 3, 3, 1, 0x0409)
    return unique_id


def optimize_with_harfbuzz(path: Path) -> bytes:
    face = hb.Face(hb.Blob.from_file_path(path))
    subset_input = hb.SubsetInput()
    subset_input.unicode_set.add_range(0, 0x10FFFF)
    subset_input.glyph_set.add_range(0, face.glyph_count - 1)
    subset_input.flags |= hb.SubsetFlags.NO_HINTING | hb.SubsetFlags.OPTIMIZE_IUP_DELTAS

    subset_input.drop_table_tag_set.discard(SVG)
    subset_input.no_subset_table_tag_set.add(SVG)

    if GPOS not in face.table_tags:
        subset_input.drop_table_tag_set.discard(KERN)
        subset_input.no_subset_table_tag_set.add(KERN)

    return subset_input.subset(face).blob.data


def build_collection(font_paths: list[Path]) -> int:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    temporary = OUTPUT.with_suffix(OUTPUT.suffix + ".tmp")
    repair_count = 0
    with tempfile.TemporaryDirectory(prefix=".harfbuzz-", dir=OUTPUT.parent) as directory:
        prepared_paths = []
        for index, path in enumerate(font_paths, start=1):
            prepared = Path(directory) / f"{index:05d}{path.suffix.lower()}"
            prepared.write_bytes(optimize_with_harfbuzz(path))
            prepared_paths.append(prepared)
            if index % 250 == 0:
                print(f"Optimized {index:,}/{len(font_paths):,} fonts", flush=True)

        collection = TTCollection()
        collection.fonts = [
            TTFont(path, lazy=True, recalcTimestamp=False) for path in prepared_paths
        ]
        for path, font in zip(font_paths, collection.fonts, strict=True):
            unique_id = repair_windows_names(font)
            if unique_id is not None:
                repair_count += 1
                print(f"Added Windows Name ID 3 to {path}: {unique_id}")
        collection.save(temporary, shareTables=True)
        os.replace(temporary, OUTPUT)
        for font in collection.fonts:
            font.close()
    return repair_count


def main() -> None:
    fonts = discover_fonts()
    print(f"Found {len(fonts):,} fonts", flush=True)
    repairs = build_collection(fonts)
    print(f"Wrote {OUTPUT} ({OUTPUT.stat().st_size:,} bytes)")
    print(f"Normalized {len(fonts):,} fonts; repaired {repairs:,} names")


if __name__ == "__main__":
    main()
