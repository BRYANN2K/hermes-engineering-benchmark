#!/usr/bin/env python3
"""Apply the severity-weighted quality scores to the copied SVG deck."""

from __future__ import annotations

import math
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parent
NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", NS)


ROUTES = {
    "Daybreak Blue": {"slug": "daybreak", "mark": "DB", "model": "GPT-5.6 Sol"},
    "Luna": {"slug": "luna", "mark": "LU", "model": "GPT-5.6 Luna"},
    "Terra": {"slug": "terra", "mark": "TE", "model": "GPT-5.6 Terra"},
    "Sol standard": {"slug": "sol", "mark": "SO", "model": "GPT-5.6 Sol"},
    "DeepSeek V4 Flash": {"slug": "flash", "mark": "DF", "model": "DeepSeek V4 Flash"},
    "DeepSeek V4 Pro": {"slug": "pro", "mark": "DP", "model": "DeepSeek V4 Pro"},
}


def row(route: str, rank: int, score: float) -> tuple[str, int, float]:
    return route, rank, score


SLIDES = {
    "00-overall-hook.svg": {
        "title": "Engineering Arena",
        "headline": "Luna: Ranked #1",
        "highlight_width": 476,
        "subtitle": "Category-equal quality across 40 primary tasks",
        "counter": "OVERVIEW",
        "tasks": [],
        "task_count": "10 CAT.",
        "coverage": "COVERS: 40 executable tasks across 10 engineering categories",
        "note": "NOTE: Full stack dominates the spread; SRE and Security tie for the next-widest gap.",
        "source": "SOURCE: PUBLIC FAILURE ANALYSIS · 40 PRIMARY TASKS",
        "disclosure": "Category-equal quality score; UI-05 excluded. Stability remains a separate metric.",
        "rows": [
            row("Luna", 1, 98.3), row("Terra", 2, 97.6), row("Daybreak Blue", 3, 96.4),
            row("Sol standard", 4, 92.6), row("DeepSeek V4 Flash", 5, 89.6), row("DeepSeek V4 Pro", 6, 82.8),
        ],
        "radar_categories": ["DevOps", "Cloud", "Front end", "Back end", "Full stack", "Bug fixing", "Feature", "Data / SQL", "SRE", "Security"],
        "radar_values": {
            "Daybreak Blue": [90, 100, 100, 100, 100, 100, 100, 94, 100, 80],
            "Luna": [90, 100, 100, 93, 100, 100, 100, 100, 100, 100],
            "Terra": [90, 100, 100, 97, 100, 96.4, 98.5, 94, 100, 100],
            "Sol standard": [90, 100, 100, 93.4, 100, 96.4, 100, 83, 100, 63.3],
            "DeepSeek V4 Flash": [90, 80, 100, 90, 85, 81, 87, 83, 100, 100],
            "DeepSeek V4 Pro": [78.8, 100, 100, 93.4, 15, 98.4, 95.5, 84, 63.3, 100],
        },
    },
    "01-devops.svg": {
        "title": "DevOps Arena", "headline": "5 routes tied at #1", "highlight_width": 588,
        "subtitle": "Severity-weighted quality score", "counter": "01 / 10",
        "tasks": ["DEVOPS-01", "DEVOPS-02", "DEVOPS-03", "DEVOPS-04"], "task_count": "4 TASKS",
        "coverage": "COVERS: dependency-safe deploy plans · atomic releases · CI job selection · restart-safe migrations",
        "note": "NOTE: Planning and CI were strong; every route missed first-failure cleanup in atomic releases.",
        "rows": [row("Daybreak Blue",1,90),row("Luna",1,90),row("Terra",1,90),row("Sol standard",1,90),row("DeepSeek V4 Flash",1,90),row("DeepSeek V4 Pro",6,78.8)],
    },
    "02-cloud.svg": {
        "title": "Cloud Arena", "headline": "5 routes tied at #1", "highlight_width": 588,
        "subtitle": "Severity-weighted quality score", "counter": "02 / 10",
        "tasks": ["CLOUD-01", "CLOUD-02", "CLOUD-03"], "task_count": "3 TASKS",
        "coverage": "COVERS: infrastructure change plans · least-privilege network policy · multi-region replica reconciliation",
        "note": "NOTE: Five routes were complete; Flash broke dependency ordering and replacement handling.",
        "rows": [row("Daybreak Blue",1,100),row("Luna",1,100),row("Terra",1,100),row("Sol standard",1,100),row("DeepSeek V4 Pro",1,100),row("DeepSeek V4 Flash",6,80)],
    },
    "03-front-end.svg": {
        "title": "Front end Arena", "headline": "6 routes tied at #1", "highlight_width": 588,
        "subtitle": "Severity-weighted quality score", "counter": "03 / 10",
        "tasks": ["UI-01", "UI-02", "UI-03", "UI-04", "UI-05"], "task_count": "4 SCORED",
        "coverage": "COVERS: accessible tabs · race-safe autocomplete · stable tables · modal focus · persistent cart",
        "note": "NOTE: All four scored tasks were clean; the fifth is excluded because its failing return contract was not public.",
        "rows": [row("Daybreak Blue",1,100),row("Luna",1,100),row("Terra",1,100),row("Sol standard",1,100),row("DeepSeek V4 Flash",1,100),row("DeepSeek V4 Pro",1,100)],
    },
    "04-back-end.svg": {
        "title": "Back end Arena", "headline": "Daybreak Blue: Ranked #1", "highlight_width": 728,
        "subtitle": "Severity-weighted quality score", "counter": "04 / 10",
        "tasks": ["API-01", "API-02", "API-03", "API-04", "API-05"], "task_count": "5 TASKS",
        "coverage": "COVERS: ETags · signed cursors · atomic inventory reservations · HMAC webhooks · versioned PATCH",
        "note": "NOTE: Daybreak cleared every API; validation edges clustered around inventory reservations.",
        "rows": [row("Daybreak Blue",1,100),row("Terra",2,97),row("Sol standard",3,93.4),row("DeepSeek V4 Pro",3,93.4),row("Luna",5,93),row("DeepSeek V4 Flash",6,90)],
    },
    "05-full-stack.svg": {
        "title": "Full stack Arena", "headline": "4 routes tied at #1", "highlight_width": 588,
        "subtitle": "Severity-weighted quality score", "counter": "05 / 10",
        "tasks": ["FULL-01", "FULL-02", "FULL-03"], "task_count": "3 TASKS",
        "coverage": "COVERS: optimistic task board · durable poll voting · idempotent support tickets",
        "note": "NOTE: Four routes were complete; Pro’s core HTTP handlers were largely missing.",
        "rows": [row("Daybreak Blue",1,100),row("Luna",1,100),row("Terra",1,100),row("Sol standard",1,100),row("DeepSeek V4 Flash",5,85),row("DeepSeek V4 Pro",6,15)],
    },
    "06-bug-fixing.svg": {
        "title": "Bug fixing Arena", "headline": "Daybreak + Luna: Ranked #1", "highlight_width": 784,
        "subtitle": "Severity-weighted quality score", "counter": "06 / 10",
        "tasks": ["BUG-01", "BUG-02", "BUG-03", "BUG-04", "BUG-05"], "task_count": "5 TASKS",
        "coverage": "COVERS: TTL/LRU cache · immutable deep merge · job scheduling · NDJSON streaming · backup retention",
        "note": "NOTE: Daybreak and Luna were complete; Flash struggled with deep merge and retention semantics.",
        "rows": [row("Daybreak Blue",1,100),row("Luna",1,100),row("DeepSeek V4 Pro",3,98.4),row("Terra",4,96.4),row("Sol standard",4,96.4),row("DeepSeek V4 Flash",6,81)],
    },
    "07-feature-implementation.svg": {
        "title": "Feature implementation Arena", "headline": "3 routes tied at #1", "highlight_width": 588,
        "subtitle": "Severity-weighted quality score", "counter": "07 / 10",
        "tasks": ["FEAT-01", "FEAT-02", "FEAT-03", "FEAT-04"], "task_count": "4 TASKS",
        "coverage": "COVERS: environment expansion · sliding-window rate limits · dependency batches · retry executor",
        "note": "NOTE: Retry and environment edges were minor; Flash’s grouping constraints were the largest gap.",
        "rows": [row("Daybreak Blue",1,100),row("Luna",1,100),row("Sol standard",1,100),row("Terra",4,98.5),row("DeepSeek V4 Pro",5,95.5),row("DeepSeek V4 Flash",6,87)],
    },
    "08-data-sql.svg": {
        "title": "Data / SQL Arena", "headline": "Luna: Ranked #1", "highlight_width": 476,
        "subtitle": "Severity-weighted quality score", "counter": "08 / 10",
        "tasks": ["DATA-01", "DATA-02", "DATA-03", "DATA-04", "DATA-05"], "task_count": "5 TASKS",
        "coverage": "COVERS: CSV ledger · invoice migration · net-revenue SQL · JSONL sessionization · inventory batches",
        "note": "NOTE: Luna cleared the category; atomicity and strict ingestion drove the largest penalties.",
        "rows": [row("Luna",1,100),row("Daybreak Blue",2,94),row("Terra",2,94),row("DeepSeek V4 Pro",4,84),row("Sol standard",5,83),row("DeepSeek V4 Flash",5,83)],
    },
    "09-sre.svg": {
        "title": "SRE Arena", "headline": "5 routes tied at #1", "highlight_width": 588,
        "subtitle": "Severity-weighted quality score", "counter": "09 / 10",
        "tasks": ["SRE-01", "SRE-02", "SRE-03"], "task_count": "3 TASKS",
        "coverage": "COVERS: incident hysteresis · multi-window burn alerts · quorum outage reconstruction",
        "note": "NOTE: Five routes were complete; Pro missed incident and outage state-machine behavior.",
        "rows": [row("Daybreak Blue",1,100),row("Luna",1,100),row("Terra",1,100),row("Sol standard",1,100),row("DeepSeek V4 Flash",1,100),row("DeepSeek V4 Pro",6,63.3)],
    },
    "10-security.svg": {
        "title": "Security Arena", "headline": "4 routes tied at #1", "highlight_width": 588,
        "subtitle": "Severity-weighted quality score", "counter": "10 / 10",
        "tasks": ["SEC-01", "SEC-02", "SEC-03"], "task_count": "3 TASKS",
        "coverage": "COVERS: safe bundle install · replay-safe signed webhooks · sandboxed health checks",
        "note": "NOTE: Four routes were complete; Sol failed replay concurrency and bundle-install safety.",
        "rows": [row("Luna",1,100),row("Terra",1,100),row("DeepSeek V4 Flash",1,100),row("DeepSeek V4 Pro",1,100),row("Daybreak Blue",5,80),row("Sol standard",6,63.3)],
    },
}


def svg_tag(name: str) -> str:
    return f"{{{NS}}}{name}"


def by_od_id(root: ET.Element, value: str) -> ET.Element:
    for element in root.iter():
        if element.attrib.get("data-od-id") == value:
            return element
    raise ValueError(f"Missing data-od-id={value}")


def by_class(root: ET.Element, value: str) -> ET.Element:
    for element in root.iter():
        if element.attrib.get("class") == value:
            return element
    raise ValueError(f"Missing class={value}")


def set_row_geometry(group: ET.Element, position: int) -> None:
    y = 332 + position * 68
    values = {
        "rank-circle": ("cy", f"{y + 30.5:g}"),
        "rank-text": ("y", f"{y + 37.5:g}"),
        "monogram-circle": ("y", f"{y + 10.5:g}"),
        "monogram-text": ("y", f"{y + 36.5:g}"),
        "route-name": ("y", f"{y + 27:g}"),
        "route-model": ("y", f"{y + 49:g}"),
        "bar": ("y", f"{y + 16.5:g}"),
        "score-count": ("y", f"{y + 38.5:g}"),
        "score-percent": ("y", f"{y + 38.5:g}"),
    }
    for class_name, (attribute, value) in values.items():
        by_class(group, class_name).set(attribute, value)


def add_element(parent: ET.Element, name: str, attributes: dict[str, str], text: str | None = None) -> ET.Element:
    element = ET.SubElement(parent, svg_tag(name), attributes)
    element.text = text
    return element


def radar_points(values: list[float], cx: float, cy: float, radius: float) -> str:
    total = len(values)
    points = []
    for index, value in enumerate(values):
        angle = -math.pi / 2 + index * (2 * math.pi / total)
        distance = radius * value / 100
        points.append(f"{cx + math.cos(angle) * distance:.1f},{cy + math.sin(angle) * distance:.1f}")
    return " ".join(points)


def _render_overall_radar_overlay_reference(root: ET.Element, spec: dict) -> None:
    style = root.find(svg_tag("style"))
    description = root.find(svg_tag("desc"))
    assert style is not None
    if description is not None:
        description.text = "Radar comparison of all six routes across ten scored engineering categories, with the complete overall ranking."
    if ".radar-grid" not in (style.text or ""):
        style.text = (style.text or "") + """
    .overall-radar{--series:var(--accent)}
    .radar-grid{fill:none;stroke:var(--border);stroke-width:1.2}.radar-grid.outer{stroke:var(--fg);stroke-opacity:.22;stroke-width:1.5}
    .radar-axis{stroke:var(--border);stroke-width:1}.radar-label{fill:var(--fg);font-family:\"Helvetica Neue\",Helvetica,sans-serif;font-size:17px;font-weight:600}
    .radar-scale{fill:var(--muted);font-family:Menlo,Monaco,\"Courier New\",monospace;font-size:13px;letter-spacing:.04em}
    .series-daybreak{fill:var(--fg);fill-opacity:.018;stroke:var(--fg);stroke-width:2.2}
    .series-luna{fill:var(--series);fill-opacity:.13;stroke:var(--series);stroke-width:4}
    .series-terra{fill:var(--bar);fill-opacity:.055;stroke:var(--bar);stroke-width:3}
    .series-sol{fill:none;stroke:var(--muted);stroke-width:2.4;stroke-dasharray:10 7}
    .series-flash{fill:none;stroke:var(--fg);stroke-opacity:.48;stroke-width:2.2;stroke-dasharray:3 6}
    .series-pro{fill:var(--bar);fill-opacity:.025;stroke:var(--bar);stroke-opacity:.55;stroke-width:2.2;stroke-dasharray:12 6 2 6}
    .legend-title{fill:var(--muted);font-family:Menlo,Monaco,\"Courier New\",monospace;font-size:14px;font-weight:700;letter-spacing:.09em}
    .legend-rank{fill:var(--muted);font-family:Menlo,Monaco,\"Courier New\",monospace;font-size:15px;font-weight:700}
    .legend-name{fill:var(--fg);font-family:\"Helvetica Neue\",Helvetica,sans-serif;font-size:21px;font-weight:600}
    .legend-score{fill:var(--fg);font-family:Menlo,Monaco,\"Courier New\",monospace;font-size:21px;font-weight:700}
    .legend-rule{stroke:var(--border);stroke-width:1}
    """

    header = by_od_id(root, "slide-header")
    for disclosure in [element for element in header if element.attrib.get("class") == "disclosure"]:
        header.remove(disclosure)

    try:
        radar = by_od_id(root, "overall-radar")
    except ValueError:
        radar = by_od_id(root, "leaderboard")
    for child in list(radar):
        radar.remove(child)
    radar.set("data-od-id", "overall-radar")
    radar.set("class", "overall-radar")

    cx, cy, radius = 600.0, 500.0, 205.0
    categories = spec["radar_categories"]
    chart = add_element(radar, "g", {"data-od-id":"radar-chart", "aria-label":"Six-route quality radar across ten categories"})

    for level in (25, 50, 75, 100):
        ring = [level] * len(categories)
        class_name = "radar-grid outer" if level == 100 else "radar-grid"
        add_element(chart, "polygon", {"data-od-id":f"radar-ring-{level}", "points":radar_points(ring, cx, cy, radius), "class":class_name})
        add_element(chart, "text", {"x":f"{cx + 10:g}", "y":f"{cy - radius * level / 100 + 5:g}", "class":"radar-scale"}, str(level))

    label_radius = radius + 31
    for index, category in enumerate(categories):
        angle = -math.pi / 2 + index * (2 * math.pi / len(categories))
        outer_x = cx + math.cos(angle) * radius
        outer_y = cy + math.sin(angle) * radius
        label_x = cx + math.cos(angle) * label_radius
        label_y = cy + math.sin(angle) * label_radius + 6
        cosine = math.cos(angle)
        anchor = "start" if cosine > .25 else "end" if cosine < -.25 else "middle"
        add_element(chart, "line", {"x1":f"{cx:g}", "y1":f"{cy:g}", "x2":f"{outer_x:.1f}", "y2":f"{outer_y:.1f}", "class":"radar-axis"})
        add_element(chart, "text", {"data-od-id":f"radar-axis-{index + 1}", "x":f"{label_x:.1f}", "y":f"{label_y:.1f}", "text-anchor":anchor, "class":"radar-label"}, category)

    draw_order = ["DeepSeek V4 Pro", "DeepSeek V4 Flash", "Sol standard", "Daybreak Blue", "Terra", "Luna"]
    class_names = {
        "Daybreak Blue":"series-daybreak", "Luna":"series-luna", "Terra":"series-terra",
        "Sol standard":"series-sol", "DeepSeek V4 Flash":"series-flash", "DeepSeek V4 Pro":"series-pro",
    }
    for route_name in draw_order:
        values = spec["radar_values"][route_name]
        route_info = ROUTES[route_name]
        add_element(chart, "polygon", {
            "data-od-id":f"radar-series-{route_info['slug']}",
            "data-series":route_name,
            "data-values":" ".join(f"{value:g}" for value in values),
            "points":radar_points(values, cx, cy, radius),
            "class":class_names[route_name],
        })

    legend = add_element(radar, "g", {"data-od-id":"radar-legend", "aria-label":"Overall route ranking"})
    add_element(legend, "text", {"x":"1072", "y":"322", "class":"legend-title"}, "OVERALL QUALITY · ALL SIX ROUTES")
    add_element(legend, "line", {"x1":"1072", "y1":"342", "x2":"1528", "y2":"342", "class":"legend-rule"})

    for position, (route_name, rank, score) in enumerate(spec["rows"]):
        y = 384 + position * 61
        route_info = ROUTES[route_name]
        group = add_element(legend, "g", {
            "data-od-id":f"route-row-{route_info['slug']}", "data-route":route_name,
            "data-rank":str(rank), "data-percent":f"{score:.1f}%", "data-scope":spec["task_count"],
        })
        add_element(group, "text", {"x":"1072", "y":f"{y:g}", "class":"legend-rank"}, f"{rank:02d}")
        add_element(group, "line", {"x1":"1110", "y1":f"{y - 6:g}", "x2":"1160", "y2":f"{y - 6:g}", "class":class_names[route_name]})
        add_element(group, "text", {"x":"1182", "y":f"{y:g}", "class":"legend-name"}, route_name)
        add_element(group, "text", {"x":"1528", "y":f"{y:g}", "text-anchor":"end", "class":"score-percent"}, f"{score:.1f}%")
        if position < len(spec["rows"]) - 1:
            add_element(group, "line", {"x1":"1072", "y1":f"{y + 22:g}", "x2":"1528", "y2":f"{y + 22:g}", "class":"legend-rule"})

    for coverage in [element for element in root if element.attrib.get("data-od-id") == "category-coverage"]:
        root.remove(coverage)


def _render_overall_radar_small_multiples_reference(root: ET.Element, spec: dict) -> None:
    """Render six non-overlapping radar profiles on one shared scale."""
    style = root.find(svg_tag("style"))
    description = root.find(svg_tag("desc"))
    assert style is not None
    if description is not None:
        description.text = "Six small-multiple radar charts compare every route across the same ten scored engineering categories."

    style_text = style.text or ""
    radar_style_markers = (
        "\n    .overall-radar{--series:var(--accent)}",
        "\n    /* OVERVIEW SMALL MULTIPLES START */",
    )
    marker_positions = [style_text.index(marker) for marker in radar_style_markers if marker in style_text]
    if marker_positions:
        style_text = style_text[:min(marker_positions)].rstrip()
    style.text = style_text + """
    /* OVERVIEW SMALL MULTIPLES START */
    .overall-radar{--series:var(--accent)}
    .overview-rule{stroke:var(--border);stroke-width:1}
    .mini-radar-grid{fill:none;stroke:var(--border);stroke-width:1}.mini-radar-grid.outer{stroke:var(--fg);stroke-opacity:.24;stroke-width:1.35}
    .mini-radar-axis{stroke:var(--border);stroke-width:.85}.mini-radar-number{fill:var(--muted);font-family:Menlo,Monaco,"Courier New",monospace;font-size:12px;font-weight:700}
    .mini-radar-shape{fill:var(--bar);fill-opacity:.12;stroke:var(--bar);stroke-width:2.5;stroke-linejoin:round}
    .mini-radar-panel.is-winner .mini-radar-shape{fill:var(--series);fill-opacity:.18;stroke:var(--series);stroke-width:3.2}
    .panel-rank{fill:var(--muted);font-family:Menlo,Monaco,"Courier New",monospace;font-size:15px;font-weight:700;letter-spacing:.08em}
    .panel-name{fill:var(--fg);font-family:"Helvetica Neue",Helvetica,sans-serif;font-size:21px;font-weight:600}
    .key-label{fill:var(--muted);font-family:Menlo,Monaco,"Courier New",monospace;font-size:13px;font-weight:700;letter-spacing:.09em}
    .key-item{fill:var(--fg);font-family:Menlo,Monaco,"Courier New",monospace;font-size:13px;font-weight:700;letter-spacing:.06em}
    /* OVERVIEW SMALL MULTIPLES END */
    """

    header = by_od_id(root, "slide-header")
    for disclosure in [element for element in header if element.attrib.get("class") == "disclosure"]:
        header.remove(disclosure)

    try:
        radar = by_od_id(root, "overall-radar")
    except ValueError:
        radar = by_od_id(root, "leaderboard")
    for child in list(radar):
        radar.remove(child)
    radar.set("data-od-id", "overall-radar")
    radar.set("class", "overall-radar")

    categories = spec["radar_categories"]
    add_element(radar, "line", {"x1":"72", "y1":"276", "x2":"1528", "y2":"276", "class":"overview-rule"})
    add_element(radar, "line", {"x1":"552", "y1":"286", "x2":"552", "y2":"744", "class":"overview-rule"})
    add_element(radar, "line", {"x1":"1048", "y1":"286", "x2":"1048", "y2":"744", "class":"overview-rule"})
    add_element(radar, "line", {"x1":"72", "y1":"517", "x2":"1528", "y2":"517", "class":"overview-rule"})

    panel_positions = [(72, 286), (568, 286), (1064, 286), (72, 521), (568, 521), (1064, 521)]
    panel_width = 464
    radius = 69.0
    label_radius = 80.0

    for (route_name, rank, score), (panel_x, panel_y) in zip(spec["rows"], panel_positions):
        route_info = ROUTES[route_name]
        group_class = "mini-radar-panel is-winner" if rank == 1 else "mini-radar-panel"
        group = add_element(radar, "g", {
            "data-od-id":f"radar-panel-{route_info['slug']}", "class":group_class, "data-route":route_name,
            "data-rank":str(rank), "data-percent":f"{score:.1f}%", "data-scope":spec["task_count"],
        })
        header_y = panel_y + 32
        add_element(group, "text", {"x":f"{panel_x + 8:g}", "y":f"{header_y:g}", "class":"panel-rank"}, f"{rank:02d}")
        add_element(group, "text", {"x":f"{panel_x + 48:g}", "y":f"{header_y:g}", "class":"panel-name"}, route_name)
        add_element(group, "text", {"x":f"{panel_x + panel_width - 8:g}", "y":f"{header_y:g}", "text-anchor":"end", "class":"score-percent"}, f"{score:.1f}%")
        add_element(group, "line", {"x1":f"{panel_x + 8:g}", "y1":f"{panel_y + 52:g}", "x2":f"{panel_x + panel_width - 8:g}", "y2":f"{panel_y + 52:g}", "class":"overview-rule"})

        cx = panel_x + panel_width / 2
        cy = panel_y + 133
        for level in (50, 100):
            class_name = "mini-radar-grid outer" if level == 100 else "mini-radar-grid"
            add_element(group, "polygon", {
                "data-od-id":f"radar-ring-{route_info['slug']}-{level}",
                "points":radar_points([level] * len(categories), cx, cy, radius),
                "class":class_name,
            })

        for index in range(len(categories)):
            angle = -math.pi / 2 + index * (2 * math.pi / len(categories))
            outer_x = cx + math.cos(angle) * radius
            outer_y = cy + math.sin(angle) * radius
            label_x = cx + math.cos(angle) * label_radius
            label_y = cy + math.sin(angle) * label_radius + 4
            add_element(group, "line", {
                "data-od-id":f"radar-axis-{route_info['slug']}-{index + 1}",
                "x1":f"{cx:.1f}", "y1":f"{cy:.1f}", "x2":f"{outer_x:.1f}", "y2":f"{outer_y:.1f}", "class":"mini-radar-axis",
            })
            add_element(group, "text", {
                "x":f"{label_x:.1f}", "y":f"{label_y:.1f}", "text-anchor":"middle", "class":"mini-radar-number",
            }, f"{index + 1:02d}")

        values = spec["radar_values"][route_name]
        add_element(group, "polygon", {
            "data-od-id":f"radar-series-{route_info['slug']}",
            "data-series":route_name,
            "data-values":" ".join(f"{value:g}" for value in values),
            "points":radar_points(values, cx, cy, radius),
            "class":"mini-radar-shape",
        })

    key = add_element(radar, "g", {"data-od-id":"radar-category-key", "aria-label":"Radar axes clockwise from top"})
    add_element(key, "text", {"x":"72", "y":"756", "class":"key-label"}, "CLOCKWISE FROM TOP")
    key_rows = [
        ["01 DEVOPS", "02 CLOUD", "03 FRONT END", "04 BACK END", "05 FULL STACK"],
        ["06 BUG FIXING", "07 FEATURE", "08 DATA / SQL", "09 SRE", "10 SECURITY"],
    ]
    for row_index, labels in enumerate(key_rows):
        for column_index, label in enumerate(labels):
            add_element(key, "text", {"x":f"{260 + column_index * 255:g}", "y":f"{756 + row_index * 22:g}", "class":"key-item"}, label)

    for coverage in [element for element in root if element.attrib.get("data-od-id") == "category-coverage"]:
        root.remove(coverage)


def render_overall_bars(root: ET.Element, spec: dict) -> None:
    """Render the overview with the same horizontal bars as every category slide."""
    style = root.find(svg_tag("style"))
    description = root.find(svg_tag("desc"))
    assert style is not None
    if description is not None:
        description.text = "Horizontal bar chart ranking all six routes by category-equal quality across forty primary engineering tasks."

    style_text = style.text or ""
    markers = (
        "\n    .overall-radar{--series:var(--accent)}",
        "\n    /* OVERVIEW SMALL MULTIPLES START */",
    )
    marker_positions = [style_text.index(marker) for marker in markers if marker in style_text]
    if marker_positions:
        style.text = style_text[:min(marker_positions)].rstrip()

    try:
        leaderboard = by_od_id(root, "leaderboard")
    except ValueError:
        leaderboard = by_od_id(root, "overall-radar")
    for child in list(leaderboard):
        leaderboard.remove(child)
    leaderboard.set("data-od-id", "leaderboard")
    leaderboard.attrib.pop("class", None)

    for x, label in ((720, "0"), (850, "25"), (980, "50"), (1110, "75"), (1240, "100")):
        add_element(leaderboard, "line", {"x1":str(x), "y1":"318", "x2":str(x), "y2":"733", "class":"grid-line"})
        add_element(leaderboard, "text", {"x":str(x), "y":"307", "text-anchor":"middle", "class":"axis-label"}, label)

    for position, (route_name, rank, score) in enumerate(spec["rows"]):
        route_info = ROUTES[route_name]
        offset = position * 68
        group = add_element(leaderboard, "g", {
            "data-od-id":f"route-row-{route_info['slug']}", "data-route":route_name,
            "data-rank":str(rank), "data-percent":f"{score:.1f}%", "data-scope":spec["task_count"],
        })
        if rank == 1:
            add_element(group, "rect", {
                "x":"50", "y":f"{332 + offset:g}", "width":"1500", "height":"61", "rx":"8", "class":"winner-outline",
            })
        add_element(group, "circle", {"cx":"88", "cy":f"{362.5 + offset:g}", "r":"20", "class":"rank-circle"})
        add_element(group, "text", {"x":"88", "y":f"{369.5 + offset:g}", "text-anchor":"middle", "class":"rank-text"}, str(rank))
        add_element(group, "rect", {"x":"132", "y":f"{342.5 + offset:g}", "width":"40", "height":"40", "rx":"20", "class":"monogram-circle"})
        add_element(group, "text", {"x":"152", "y":f"{368.5 + offset:g}", "text-anchor":"middle", "class":"monogram-text"}, route_info["mark"])
        add_element(group, "text", {"x":"205", "y":f"{359 + offset:g}", "class":"route-name"}, route_name)
        add_element(group, "text", {"x":"205", "y":f"{381 + offset:g}", "class":"route-model"}, f"DECLARED MODEL · {route_info['model']}")
        add_element(group, "rect", {
            "x":"720", "y":f"{348.5 + offset:g}", "width":f"{score / 100 * 520:.1f}", "height":"28", "rx":"2", "class":"bar",
        })
        add_element(group, "text", {"x":"1350", "y":f"{370.5 + offset:g}", "text-anchor":"end", "class":"score-count"}, spec["task_count"])
        add_element(group, "text", {"x":"1518", "y":f"{370.5 + offset:g}", "text-anchor":"end", "class":"score-percent"}, f"{score:.1f}%")


def update_slide(path: Path, spec: dict) -> None:
    tree = ET.parse(path)
    root = tree.getroot()

    title = root.find(svg_tag("title"))
    desc = root.find(svg_tag("desc"))
    metadata = root.find(svg_tag("metadata"))
    style = root.find(svg_tag("style"))
    assert title is not None and desc is not None and metadata is not None and style is not None
    title.text = f"{spec['title']} — {spec['headline']}"
    desc.text = f"Severity-weighted leaderboard for {spec['title'].replace(' Arena', '')}: category coverage, quality scores, strengths and gaps."
    task_ids = " · ".join(spec["tasks"])
    metadata.text = "Severity-weighted quality scores · primary attempt 1"
    if task_ids:
        metadata.text += f" · task IDs: {task_ids}"
    if ".score-note" not in (style.text or ""):
        style.text = (style.text or "").replace(
            ".scope{fill:var(--muted);font-family:Menlo,Monaco,\"Courier New\",monospace;font-size:15px;letter-spacing:.5px}",
            ".scope{fill:var(--muted);font-family:Menlo,Monaco,\"Courier New\",monospace;font-size:15px;letter-spacing:.5px}.score-note{fill:var(--fg);font-family:\"Helvetica Neue\",Helvetica,sans-serif;font-size:16px;font-weight:550}",
        )
    style.text = (style.text or "").replace(
        ".winner-outline{fill:none;stroke:var(--accent);stroke-width:3}",
        ".winner-outline{fill:none;stroke:var(--fg);stroke-width:1.5;opacity:.45}",
    ).replace("font-size:16px;font-weight:550", "font-size:18px;font-weight:550")

    header = by_od_id(root, "slide-header")
    by_od_id(header, "slide-heading").text = spec["title"]
    highlight = by_class(header, "highlight")
    highlight.set("width", str(spec["highlight_width"]))
    by_od_id(header, "highlighted-result").text = spec["headline"]
    by_od_id(header, "slide-subtitle").text = spec["subtitle"]
    by_class(header, "lockup-sub").text = "QUALITY SCORES · 2026-08-15"
    by_class(header, "counter").text = spec["counter"]
    disclosures = [element for element in header if element.attrib.get("class") == "disclosure"]
    if spec.get("disclosure"):
        if disclosures:
            disclosures[0].text = spec["disclosure"]
        else:
            disclosure = ET.SubElement(header, svg_tag("text"), {"x":"74", "y":"279", "class":"disclosure"})
            disclosure.text = spec["disclosure"]
    else:
        for disclosure in disclosures:
            header.remove(disclosure)

    is_existing_radar = path.name == "00-overall-hook.svg" and any(
        element.attrib.get("data-od-id") == "overall-radar" for element in root.iter()
    )
    if not is_existing_radar:
        leaderboard = by_od_id(root, "leaderboard")
        route_groups = {group.attrib["data-route"]: group for group in list(leaderboard) if "data-route" in group.attrib}
        for group in route_groups.values():
            leaderboard.remove(group)

        for position, (route_name, rank, score) in enumerate(spec["rows"]):
            group = route_groups[route_name]
            route_info = ROUTES[route_name]
            group.set("data-od-id", f"route-row-{route_info['slug']}")
            group.set("data-route", route_name)
            group.set("data-rank", str(rank))
            group.set("data-scope", spec["task_count"])
            group.attrib.pop("data-resolved", None)
            group.set("data-percent", f"{score:.1f}%")

            for child in list(group):
                if child.attrib.get("class") in {"winner-outline", "zero-mark"}:
                    group.remove(child)
            if rank == 1:
                winner = ET.Element(svg_tag("rect"), {
                    "x":"50", "y":str(332 + position * 68), "width":"1500", "height":"61", "rx":"8", "class":"winner-outline"
                })
                group.insert(0, winner)

            if not any(child.attrib.get("class") == "bar" for child in group):
                score_count_index = next(i for i, child in enumerate(group) if child.attrib.get("class") == "score-count")
                group.insert(score_count_index, ET.Element(svg_tag("rect"), {
                    "x":"720", "height":"28", "rx":"2", "class":"bar"
                }))

            by_class(group, "rank-text").text = str(rank)
            by_class(group, "monogram-text").text = route_info["mark"]
            by_class(group, "route-name").text = route_name
            by_class(group, "route-model").text = f"DECLARED MODEL · {route_info['model']}"
            by_class(group, "bar").set("width", f"{score / 100 * 520:.1f}")
            by_class(group, "score-count").text = spec["task_count"]
            by_class(group, "score-percent").text = f"{score:.1f}%"
            set_row_geometry(group, position)
            leaderboard.append(group)

    scope_elements = [element for element in root if element.attrib.get("data-od-id") in {"task-scope", "category-coverage"}]
    if scope_elements:
        coverage = scope_elements[0]
        for duplicate in scope_elements[1:]:
            root.remove(duplicate)
    else:
        coverage = ET.Element(svg_tag("text"))
        line_index = next(i for i, child in enumerate(root) if child.tag == svg_tag("line") and child.attrib.get("y1") == "824")
        root.insert(line_index, coverage)
    coverage.attrib.clear()
    coverage.attrib.update({"data-od-id":"category-coverage", "x":"72", "y":"772", "class":"scope"})
    coverage.text = spec["coverage"]

    existing_notes = [element for element in root if element.attrib.get("data-od-id") == "score-note"]
    if existing_notes:
        score_note = existing_notes[0]
        for duplicate in existing_notes[1:]:
            root.remove(duplicate)
    else:
        score_note = ET.Element(svg_tag("text"))
        line_index = next(i for i, child in enumerate(root) if child.tag == svg_tag("line") and child.attrib.get("y1") == "824")
        root.insert(line_index, score_note)
    score_note.attrib.clear()
    score_note.attrib.update({"data-od-id":"score-note", "x":"72", "y":"805", "class":"score-note"})
    score_note.text = spec["note"]

    footer = by_od_id(root, "slide-footer")
    footer_texts = list(footer)
    footer_texts[0].text = spec.get("source", "SOURCE: PUBLIC FAILURE ANALYSIS · PRIMARY ATTEMPT 1")
    footer_texts[1].text = "METRIC: SEVERITY-WEIGHTED QUALITY · HIGHER IS BETTER"

    if path.name == "00-overall-hook.svg":
        render_overall_bars(root, spec)

    ET.indent(tree, space="  ")
    tree.write(path, encoding="UTF-8", xml_declaration=True)


def main() -> None:
    for filename, spec in SLIDES.items():
        update_slide(ROOT / filename, spec)
    print(f"Updated {len(SLIDES)} slides with severity-weighted scores and notes.")


if __name__ == "__main__":
    main()
