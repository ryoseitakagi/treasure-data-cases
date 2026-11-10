"""Fail the sync before publishing mojibake in generated case files."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Iterator

ROOT = Path(__file__).resolve().parents[1]
FILES = (ROOT / "data/cases.json", ROOT / "data/tosup_patterns.json", ROOT / "index.html")
MARKERS = ("ã", "ä", "å", "Â", "�", "1⁄4")


def contains_mojibake(value: str) -> bool:
    return any(marker in value for marker in MARKERS)


def string_values(value: Any, path: str = "") -> Iterator[tuple[str, str]]:
    if isinstance(value, str):
        yield path, value
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from string_values(item, f"{path}[{index}]")
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from string_values(item, f"{path}.{key}" if path else str(key))


def main() -> int:
    findings: list[str] = []
    for path in FILES:
        if not path.is_file():
            findings.append(f"Missing generated file: {path.relative_to(ROOT)}")
            continue
        if path.suffix == ".json":
            try:
                values = string_values(json.loads(path.read_text(encoding="utf-8")))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                findings.append(f"Invalid UTF-8 JSON in {path.relative_to(ROOT)}: {exc}")
                continue
        else:
            try:
                values = ((str(path.relative_to(ROOT)), path.read_text(encoding="utf-8")),)
            except UnicodeDecodeError as exc:
                findings.append(f"Invalid UTF-8 text in {path.relative_to(ROOT)}: {exc}")
                continue
        for location, text in values:
            if contains_mojibake(text):
                sample = text[:120].replace("\n", " ")
                findings.append(f"Mojibake-like text in {path.relative_to(ROOT)} at {location}: {sample!r}")
                if len(findings) >= 20:
                    break
        if len(findings) >= 20:
            break

    if findings:
        print("Text encoding check failed:", file=sys.stderr)
        for finding in findings:
            print(f"- {finding}", file=sys.stderr)
        return 1
    print(f"UTF-8/mojibake check passed for {len(FILES)} generated files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
