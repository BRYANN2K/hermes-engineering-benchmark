#!/usr/bin/env python3
"""Deterministic verification for the severity-weighted score slides."""

from __future__ import annotations

import re
import runpy
import struct
import sys
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parent
CONFIG = runpy.run_path(str(ROOT / "apply-quality-scores.py"))
SLIDES: dict[str, dict] = CONFIG["SLIDES"]
ROUTES = set(CONFIG["ROUTES"])
LOCKUP = "BRYANN2K · LLM ENGINEERING BENCHMARK"
METRIC = "METRIC: SEVERITY-WEIGHTED QUALITY · HIGHER IS BETTER"
REMOTE_PATTERN = re.compile(r"(?:https?:)?//", re.IGNORECASE)
PLACEHOLDER_PATTERN = re.compile(r"\{\{|\}\}|lorem ipsum|placeholder text|sample content", re.IGNORECASE)
FRENCH_UI_PATTERN = re.compile(r"\b(résolu|tâches?|échec|meilleur|classement|pondéré|moyenne)\b", re.IGNORECASE)


class Verification:
    def __init__(self) -> None:
        self.failures: list[str] = []
        self.checks = 0

    def require(self, condition: bool, message: str) -> None:
        self.checks += 1
        if not condition:
            self.failures.append(message)


def png_dimensions(path: Path) -> tuple[int, int]:
    with path.open("rb") as handle:
        header = handle.read(24)
    if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
        return 0, 0
    return struct.unpack(">II", header[16:24])


def by_od_id(root: ET.Element, value: str) -> ET.Element | None:
    return next((element for element in root.iter() if element.attrib.get("data-od-id") == value), None)


def by_class(root: ET.Element, value: str) -> ET.Element | None:
    return next((element for element in root.iter() if element.attrib.get("class") == value), None)


def main() -> int:
    check = Verification()
    svg_files = sorted(ROOT.glob("*.svg"))
    png_files = sorted(ROOT.glob("*.png"))
    check.require(len(svg_files) == 11, f"expected 11 SVG files, found {len(svg_files)}")
    check.require(len(png_files) in {0, 11}, f"expected either 0 or 11 PNG files, found {len(png_files)}")
    check.require({path.name for path in svg_files} == set(SLIDES), "SVG filename set differs from score config")
    if png_files:
        check.require({path.stem + ".svg" for path in png_files} == set(SLIDES), "PNG filename set differs from score config")

    all_task_ids: list[str] = []
    category_cells = 0

    for filename, spec in SLIDES.items():
        path = ROOT / filename
        check.require(path.exists(), f"missing {filename}")
        if not path.exists():
            continue
        raw = path.read_text(encoding="utf-8")
        try:
            root = ET.fromstring(raw)
        except ET.ParseError as error:
            check.require(False, f"invalid XML in {filename}: {error}")
            continue

        check.require(root.attrib.get("width") == "1600" and root.attrib.get("height") == "900", f"{filename}: canvas is not 1600 × 900")
        check.require(LOCKUP in raw, f"{filename}: missing benchmark lockup")
        check.require(METRIC in raw, f"{filename}: missing quality metric")
        check.require(spec["title"] in raw and spec["headline"] in raw, f"{filename}: title or headline mismatch")
        is_overview = filename == "00-overall-hook.svg"
        check.require(spec["coverage"] in raw, f"{filename}: missing category coverage")
        check.require(spec["note"] in raw, f"{filename}: missing score note")
        check.require("QUALITY SCORES · 2026-08-15" in raw, f"{filename}: missing analysis date")
        check.require(not REMOTE_PATTERN.search(raw.replace('xmlns="http://www.w3.org/2000/svg"', "")), f"{filename}: remote reference detected")
        check.require(not PLACEHOLDER_PATTERN.search(raw), f"{filename}: placeholder copy detected")
        check.require(not FRENCH_UI_PATTERN.search(raw), f"{filename}: French user-visible copy detected")
        check.require("stroke:var(--accent)" not in raw, f"{filename}: accent is overused on winner outlines")
        check.require(raw.count("var(--accent)") <= 2, f"{filename}: accent token exceeds the per-screen cap")
        check.require(len(spec["coverage"]) <= 120, f"{filename}: coverage line is too dense")
        check.require(len(spec["note"]) <= 118, f"{filename}: score note is too dense")

        coverage_elements = [element for element in root.iter() if element.attrib.get("data-od-id") == "category-coverage"]
        note_elements = [element for element in root.iter() if element.attrib.get("data-od-id") == "score-note"]
        check.require(len(coverage_elements) == 1, f"{filename}: coverage line count mismatch")
        check.require(len(note_elements) == 1, f"{filename}: expected exactly one score note")
        coverage = coverage_elements[0] if coverage_elements else None
        note = note_elements[0] if note_elements else None
        check.require(coverage is not None and coverage.attrib.get("y") == "772", f"{filename}: coverage baseline drifted")
        check.require(note is not None and note.attrib.get("y") == "805", f"{filename}: score note baseline drifted")

        if is_overview:
            leaderboard = by_od_id(root, "leaderboard")
            series = [element for element in root.iter() if "data-series" in element.attrib]
            check.require(leaderboard is not None, f"{filename}: missing horizontal leaderboard")
            check.require(len(series) == 0, f"{filename}: radar series remain in the overview")
            check.require(len([element for element in root.iter() if element.attrib.get("class") == "bar"]) == 6, f"{filename}: expected six overview bars")

        groups = [element for element in root.iter() if "data-route" in element.attrib]
        check.require(len(groups) == 6, f"{filename}: expected six route rows, found {len(groups)}")
        actual_routes = {group.attrib.get("data-route") for group in groups}
        check.require(actual_routes == ROUTES, f"{filename}: route set mismatch")
        check.require(sum(1 for group in groups if group.attrib.get("data-rank") == "1") == sum(1 for _, rank, _ in spec["rows"] if rank == 1), f"{filename}: winner count mismatch")

        for position, ((expected_route, expected_rank, expected_score), group) in enumerate(zip(spec["rows"], groups)):
            check.require(group.attrib.get("data-route") == expected_route, f"{filename}: row {position + 1} route mismatch")
            check.require(group.attrib.get("data-rank") == str(expected_rank), f"{filename}: {expected_route} rank mismatch")
            check.require(group.attrib.get("data-percent") == f"{expected_score:.1f}%", f"{filename}: {expected_route} score mismatch")
            check.require(group.attrib.get("data-scope") == spec["task_count"], f"{filename}: {expected_route} scope label mismatch")
            score_text = by_class(group, "score-percent")
            check.require(score_text is not None and score_text.text == f"{expected_score:.1f}%", f"{filename}: {expected_route} visible score mismatch")
            bar = by_class(group, "bar")
            expected_width = expected_score / 100 * 520
            check.require(bar is not None and abs(float(bar.attrib.get("width", "-1")) - expected_width) <= 0.06, f"{filename}: {expected_route} bar is not score-derived")
            outlines = [child for child in group if child.attrib.get("class") == "winner-outline"]
            check.require(len(outlines) == (1 if expected_rank == 1 else 0), f"{filename}: {expected_route} winner outline mismatch")

        if filename != "00-overall-hook.svg":
            category_cells += len(groups)
            check.require("SOURCE: PUBLIC FAILURE ANALYSIS · PRIMARY ATTEMPT 1" in raw, f"{filename}: source footer mismatch")
            for task_id in spec["tasks"]:
                check.require(raw.count(task_id) == 1, f"{filename}: task ID {task_id} must appear exactly once")
                all_task_ids.append(task_id)
        else:
            check.require("SOURCE: PUBLIC FAILURE ANALYSIS · 40 PRIMARY TASKS" in raw, f"{filename}: overview source footer mismatch")

        png_path = path.with_suffix(".png")
        if png_path.exists():
            check.require(png_dimensions(png_path) == (1600, 900), f"{png_path.name}: PNG dimensions are not 1600 × 900")

    check.require(category_cells == 60, f"expected 60 category score cells, found {category_cells}")
    check.require(len(all_task_ids) == 40 and len(set(all_task_ids)) == 40, "task IDs are not 40 unique values")

    html_path = ROOT / "index.html"
    html = html_path.read_text(encoding="utf-8") if html_path.exists() else ""
    check.require(bool(html), "missing index.html")
    check.require("localStorage" in html, "index.html does not persist slide position")
    check.require("ArrowLeft" in html and "ArrowRight" in html, "index.html is missing keyboard navigation")
    check.require(all(filename in html for filename in SLIDES), "index.html is missing one or more slides")
    check.require(not REMOTE_PATTERN.search(html), "index.html contains a remote reference")
    check.require(not PLACEHOLDER_PATTERN.search(html), "index.html contains placeholder copy")

    readme_path = ROOT / "README.md"
    readme = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""
    check.require("arena-code-leaderboard.png" in readme and "arena-agent-comparison.png" in readme, "README does not record both inspected references")
    check.require("not embedded" in readme.lower() and "remote" in readme.lower(), "README does not document asset boundaries")

    if check.failures:
        print(f"FAIL — {len(check.failures)} of {check.checks} checks failed")
        for failure in check.failures:
            print(f"- {failure}")
        return 1

    print(f"PASS — {check.checks} deterministic checks passed")
    png_summary = "11 PNG" if png_files else "SVG/HTML source deck"
    print(f"11 SVG + {png_summary} · 60 category scores · 40 unique tasks · rankings and notes verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
