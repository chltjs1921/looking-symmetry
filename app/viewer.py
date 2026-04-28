from __future__ import annotations

from functools import lru_cache
from html import escape
from math import cos, pi, sin
from pathlib import Path

from .molecule import MolecularGeometry
from .symmetry import SymmetryResult

STATIC_DIR = Path(__file__).parent / "static"
THREEDMOL_JS = STATIC_DIR / "3Dmol-min.js"

BLUE = "0x2563eb"
GREEN = "0x059669"
ORANGE = "0xf59e0b"
RED = "0xdc2626"
PURPLE = "0x7c3aed"

OPERATION_CHOICES = [
    "추천 조작 / Best teaching operation",
    "주축 회전 / Principal rotation",
    "거울면 / Mirror plane",
    "반전 중심 / Inversion center",
    "보조 C2 회전 / Secondary C2 rotation",
]


def teaching_operation_choices() -> list[str]:
    return OPERATION_CHOICES


def render_viewer(
    geometry: MolecularGeometry,
    symmetry: SymmetryResult,
    operation_mode: str = "Best teaching operation",
    language: str = "한국어",
) -> str:
    try:
        import py3Dmol
    except ImportError:
        return (
            "<div style='padding:16px;border:1px solid #d0d7de;border-radius:8px'>"
            "py3Dmol is not installed, so the 3D viewer cannot be rendered. "
            "Run <code>pip install -r requirements.txt</code> and try again.</div>"
        )

    view = py3Dmol.view(width="100%", height=640)
    center = _center(geometry.coords)
    radius = _radius(geometry.coords, center)
    separation = radius * 2.45
    profile = _overlay_profile(geometry.source, symmetry.point_group)
    demonstration = _operation_demonstration(geometry, symmetry, profile, operation_mode, language)

    left_geometry = _shift_geometry(geometry, (-separation / 2, 0, 0), "original")
    right_geometry = _shift_geometry(
        MolecularGeometry(
            species=geometry.species,
            coords=demonstration["coords"],
            source=demonstration["title"],
            kind=geometry.kind,
        ),
        (separation / 2, 0, 0),
        demonstration["title"],
    )

    view.addModel(left_geometry.to_xyz(), "xyz")
    view.setStyle({"model": 0}, {"stick": {"radius": 0.17}, "sphere": {"scale": 0.3}})
    view.addModel(right_geometry.to_xyz(), "xyz")
    view.setStyle({"model": 1}, {"stick": {"radius": 0.17}, "sphere": {"scale": 0.3}})
    _add_overlays(view, left_geometry, symmetry, profile)
    _add_demonstration_guides(view, center, radius, separation, demonstration)
    view.zoomTo()
    view.zoom(0.9)
    viewer_html = _use_local_3dmol_loader(view._make_html())
    return _viewer_frame(demonstration, _as_iframe(_inline_3dmol_loader() + viewer_html), language)


@lru_cache(maxsize=1)
def _inline_3dmol_loader() -> str:
    if not THREEDMOL_JS.exists():
        return ""

    script = THREEDMOL_JS.read_text(encoding="utf-8")
    return (
        "<script>"
        "if (typeof window.$3Dmol === 'undefined') {"
        f"{script}"
        "}"
        "window.$3Dmolpromise = Promise.resolve(window.$3Dmol);"
        "</script>"
    )


def _as_iframe(inner_html: str) -> str:
    document = (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<style>html,body{margin:0;width:100%;height:100%;overflow:hidden;background:#ffffff;}"
        "#viewer-root{width:100%;height:100%;}</style>"
        "</head><body><div id='viewer-root'>"
        f"{inner_html}"
        "</div></body></html>"
    )
    return (
        "<iframe "
        f"srcdoc=\"{escape(document, quote=True)}\" "
        "style=\"width:100%;height:660px;border:0;display:block;background:#fff;\" "
        "sandbox=\"allow-scripts allow-same-origin\">"
        "</iframe>"
    )


def _viewer_frame(demonstration: dict, iframe: str, language: str) -> str:
    ko = _is_korean(language)
    title = "왜 이것이 대칭 조작인가?" if ko else "Why this operation is symmetry"
    legend_axis = "주축" if ko else "principal axis"
    legend_secondary = "보조축" if ko else "secondary axis"
    legend_plane = "거울면" if ko else "mirror plane"
    legend_arrow = "조작 방향" if ko else "operation arrow"
    compare = (
        "왼쪽: 원래 분자. 오른쪽: 선택한 조작을 한 뒤의 분자."
        if ko
        else "Left: original. Right: after the selected operation."
    )
    return (
        "<style>"
        ".viewer-teaching{font-family:Inter,ui-sans-serif,system-ui,sans-serif;border:1px solid #dde3f8;border-radius:8px;background:#fff;overflow:hidden;}"
        ".viewer-teaching-head{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;padding:12px 14px;border-bottom:1px solid #e5e7eb;}"
        ".viewer-teaching-title{font-size:15px;font-weight:900;color:#111827;margin:0;}"
        ".viewer-teaching-note{font-size:13px;line-height:1.45;color:#4b5563;margin:4px 0 0;}"
        ".viewer-teaching-badge{flex:0 0 auto;border-radius:999px;background:#f3e8ff;color:#6d28d9;padding:5px 9px;font-size:12px;font-weight:900;}"
        ".viewer-teaching-legend{display:flex;flex-wrap:wrap;gap:8px;padding:10px 14px;border-top:1px solid #e5e7eb;color:#4b5563;font-size:12px;}"
        ".viewer-dot{display:inline-block;width:10px;height:10px;border-radius:999px;margin-right:5px;vertical-align:-1px;}"
        "</style>"
        "<section class='viewer-teaching'>"
        "<div class='viewer-teaching-head'>"
        "<div>"
        f"<p class='viewer-teaching-title'>{escape(title)}</p>"
        f"<p class='viewer-teaching-note'>{escape(demonstration['explanation'])}</p>"
        "</div>"
        f"<div class='viewer-teaching-badge'>{escape(demonstration['title'])}</div>"
        "</div>"
        f"{iframe}"
        "<div class='viewer-teaching-legend'>"
        f"<span><span class='viewer-dot' style='background:#2563eb'></span>{escape(legend_axis)}</span>"
        f"<span><span class='viewer-dot' style='background:#059669'></span>{escape(legend_secondary)}</span>"
        f"<span><span class='viewer-dot' style='background:#f59e0b'></span>{escape(legend_plane)}</span>"
        f"<span><span class='viewer-dot' style='background:#7c3aed'></span>{escape(legend_arrow)}</span>"
        f"<span>{escape(compare)}</span>"
        "</div>"
        "</section>"
    )


def _use_local_3dmol_loader(html: str) -> str:
    cdn_loader = (
        "if(typeof $3Dmolpromise === 'undefined') {\n"
        "$3Dmolpromise = null;\n"
        "  $3Dmolpromise = loadScriptAsync('https://cdn.jsdelivr.net/npm/3dmol@2.5.4/build/3Dmol-min.js');\n"
        "}\n"
    )
    local_loader = (
        "if (typeof $3Dmolpromise === 'undefined') {\n"
        "  var $3Dmolpromise = Promise.resolve($3Dmol);\n"
        "}\n"
    )
    return html.replace(cdn_loader, local_loader)


def _add_overlays(view, geometry: MolecularGeometry, symmetry: SymmetryResult, profile: dict | None = None) -> None:
    center = _center(geometry.coords)
    radius = _radius(geometry.coords, center)
    profile = profile or _overlay_profile(geometry.source, symmetry.point_group)

    for direction, label in profile["principal_axes"]:
        _add_axis(view, center, radius, direction, BLUE, label)
    for direction, label in profile["secondary_axes"]:
        _add_axis(view, center, radius * 0.82, direction, GREEN, label)
    for plane, label in profile["planes"]:
        _add_plane_grid(view, center, radius, plane, ORANGE, label)

    if profile["inversion_center"]:
        view.addSphere(
            {
                "center": _point(center),
                "radius": max(radius * 0.045, 0.08),
                "color": RED,
                "alpha": 0.9,
            }
        )
        view.addLabel("inversion center", {"position": _point(_translate(center, (0.12, 0.12, 0.12))), "fontSize": 12, "fontColor": RED})


def _operation_demonstration(
    geometry: MolecularGeometry,
    symmetry: SymmetryResult,
    profile: dict,
    operation_mode: str,
    language: str = "한국어",
) -> dict:
    operation = _choose_operation(symmetry.point_group, profile, operation_mode)
    center = _center(geometry.coords)
    coords = geometry.coords

    if operation["kind"] == "rotation":
        transformed = [
            _rotate_about_axis(coord, center, operation["direction"], operation["angle"])
            for coord in coords
        ]
        if _is_korean(language):
            explanation = (
                f"왼쪽 분자를 표시된 축 주위로 {operation['degrees']}도 회전한 모습이 오른쪽입니다. "
                "오른쪽의 원자 배열이 왼쪽과 같아 보이면, 이 회전은 대칭 조작입니다."
            )
        else:
            explanation = (
                f"Rotate the left molecule by {operation['degrees']} degrees around the highlighted axis. "
                "The right molecule has the same atom pattern, so the rotation is a symmetry operation."
            )
    elif operation["kind"] == "reflection":
        transformed = [_reflect_in_plane(coord, center, operation["plane"]) for coord in coords]
        if _is_korean(language):
            explanation = (
                f"왼쪽 분자를 표시된 {operation['plane']} 평면에 비친 모습이 오른쪽입니다. "
                "각 원자가 같은 종류의 원자 자리로 옮겨가면, 이 평면은 거울면입니다."
            )
        else:
            explanation = (
                f"Reflect the left molecule across the highlighted {operation['plane']} plane. "
                "Atoms land on identical atoms, so the mirror plane is a symmetry element."
            )
    elif operation["kind"] == "inversion":
        transformed = [_invert(coord, center) for coord in coords]
        if _is_korean(language):
            explanation = (
                "모든 원자를 빨간 중심을 지나 반대편으로 보낸 모습이 오른쪽입니다. "
                "각 원자가 같은 종류의 원자 자리로 옮겨가면, 그 점은 반전 중심입니다."
            )
        else:
            explanation = (
                "Send every atom through the red center to the opposite side. "
                "If each atom lands on an identical atom, the center is an inversion center."
            )
    else:
        transformed = list(coords)
        explanation = (
            "항등 조작은 모든 원자를 원래 자리에 그대로 둡니다."
            if _is_korean(language)
            else "The identity operation leaves every atom exactly where it started."
        )

    return {
        "title": operation["title"],
        "kind": operation["kind"],
        "coords": transformed,
        "operation": operation,
        "explanation": explanation,
    }


def _choose_operation(point_group: str, profile: dict, requested: str) -> dict:
    available = _available_operations(point_group, profile)
    requested_key = _operation_key(requested)
    for operation in available:
        if operation["key"] == requested_key:
            return operation

    if requested_key == "best":
        for preferred in ("Mirror plane", "Principal rotation", "Inversion center", "Secondary C2 rotation"):
            for operation in available:
                if operation["title"].startswith(preferred):
                    return operation
    return available[0]


def _available_operations(point_group: str, profile: dict) -> list[dict]:
    operations = []
    if profile["principal_axes"]:
        direction, _ = profile["principal_axes"][0]
        order = _principal_order(point_group)
        operations.append(
            {
                "kind": "rotation",
                "key": "principal",
                "title": f"Principal rotation C{order}",
                "direction": direction,
                "angle": 2 * pi / order,
                "degrees": round(360 / order),
            }
        )
    if profile["planes"]:
        plane, _ = profile["planes"][0]
        operations.append({"kind": "reflection", "key": "mirror", "title": "Mirror plane", "plane": plane})
    if profile["inversion_center"]:
        operations.append({"kind": "inversion", "key": "inversion", "title": "Inversion center"})
    if profile["secondary_axes"]:
        direction, _ = profile["secondary_axes"][0]
        operations.append(
            {
                "kind": "rotation",
                "key": "secondary",
                "title": "Secondary C2 rotation",
                "direction": direction,
                "angle": pi,
                "degrees": 180,
            }
        )
    operations.append({"kind": "identity", "key": "identity", "title": "Identity"})
    return operations


def _operation_key(requested: str) -> str:
    text = requested.casefold()
    if "best" in text or "추천" in text:
        return "best"
    if "principal" in text or "주축" in text:
        return "principal"
    if "mirror" in text or "거울" in text:
        return "mirror"
    if "inversion" in text or "반전" in text:
        return "inversion"
    if "secondary" in text or "보조" in text:
        return "secondary"
    return text


def _is_korean(language: str) -> bool:
    return not language.casefold().startswith("english")


def _principal_order(point_group: str) -> int:
    for char in point_group:
        if char.isdigit():
            return int(char)
    if "inf" in point_group:
        return 2
    return 2


def _add_demonstration_guides(view, center, radius: float, separation: float, demonstration: dict) -> None:
    left_center = _translate(center, (-separation / 2, 0, 0))
    right_center = _translate(center, (separation / 2, 0, 0))
    view.addLabel("original", {"position": _point(_translate(left_center, (0, -radius * 1.08, 0))), "fontSize": 13, "fontColor": "0x111827", "backgroundOpacity": 0.7})
    view.addLabel("after operation", {"position": _point(_translate(right_center, (0, -radius * 1.08, 0))), "fontSize": 13, "fontColor": "0x111827", "backgroundOpacity": 0.7})
    _add_arrow(view, _translate(center, (-separation * 0.22, radius * 0.95, 0)), _translate(center, (separation * 0.22, radius * 0.95, 0)), PURPLE)
    view.addLabel(demonstration["title"], {"position": _point(_translate(center, (0, radius * 1.08, 0))), "fontSize": 13, "fontColor": PURPLE, "backgroundOpacity": 0.75})


def _add_arrow(view, start, end, color: str) -> None:
    _add_line(view, start, end, color, radius=0.025, alpha=0.8)
    direction = _normalize((end[0] - start[0], end[1] - start[1], end[2] - start[2]))
    head_base = _translate(end, tuple(-0.22 * value for value in direction))
    _add_line(view, head_base, end, color, radius=0.065, alpha=0.8)


def _shift_geometry(geometry: MolecularGeometry, delta, source: str) -> MolecularGeometry:
    return MolecularGeometry(
        species=geometry.species,
        coords=[_translate(coord, delta) for coord in geometry.coords],
        source=source,
        kind=geometry.kind,
    )


def _overlay_profile(source: str, point_group: str) -> dict:
    profile = {
        "principal_axes": [((0, 0, 1), f"{point_group} principal axis")],
        "secondary_axes": [],
        "planes": [],
        "inversion_center": False,
    }

    if source == "Water / H2O":
        profile.update(
            principal_axes=[((0, 1, 0), "C2 axis")],
            planes=[("xy", "molecular mirror plane"), ("yz", "second mirror plane")],
        )
    elif source == "Ammonia / NH3":
        profile.update(
            principal_axes=[((0, 0, 1), "C3 axis")],
            planes=[("xz", "vertical mirror plane"), ("yz", "vertical mirror plane")],
        )
    elif source == "Carbon dioxide / CO2":
        profile.update(
            principal_axes=[((1, 0, 0), "linear axis")],
            planes=[("xy", "mirror plane"), ("xz", "mirror plane")],
            inversion_center=True,
        )
    elif source == "Benzene / C6H6":
        profile.update(
            principal_axes=[((0, 0, 1), "C6 axis")],
            secondary_axes=[((1, 0, 0), "C2 axis"), ((0, 1, 0), "C2 axis")],
            planes=[("xy", "sigma_h: molecular plane")],
            inversion_center=True,
        )
    elif source == "Boron trifluoride / BF3":
        profile.update(
            principal_axes=[((0, 0, 1), "C3 axis")],
            secondary_axes=[((1, 0, 0), "C2 axis")],
            planes=[("xy", "sigma_h: molecular plane")],
        )
    elif source == "Sulfur hexafluoride / SF6":
        profile.update(
            principal_axes=[((1, 0, 0), "C4 axis"), ((0, 1, 0), "C4 axis"), ((0, 0, 1), "C4 axis")],
            secondary_axes=[],
            planes=[("xy", "mirror plane")],
            inversion_center=True,
        )
    elif source == "Ethene / C2H4":
        profile.update(
            principal_axes=[((0, 0, 1), "C2 axis")],
            secondary_axes=[((1, 0, 0), "C2 axis"), ((0, 1, 0), "C2 axis")],
            planes=[("xy", "molecular mirror plane")],
            inversion_center=True,
        )
    elif source == "Hydrogen chloride / HCl":
        profile.update(
            principal_axes=[((0, 0, 1), "linear axis")],
            planes=[("xz", "vertical mirror plane")],
        )
    elif source == "Nitrogen / N2":
        profile.update(
            principal_axes=[((0, 0, 1), "linear axis")],
            planes=[("xz", "mirror plane"), ("yz", "mirror plane")],
            inversion_center=True,
        )
    elif source == "Ethyne / C2H2":
        profile.update(
            principal_axes=[((0, 0, 1), "linear axis")],
            planes=[("xz", "mirror plane"), ("yz", "mirror plane")],
            inversion_center=True,
        )
    elif source == "Formaldehyde / CH2O":
        profile.update(
            principal_axes=[((1, 0, 0), "C2 axis")],
            planes=[("xy", "molecular mirror plane"), ("xz", "second mirror plane")],
        )
    elif source == "Phosphorus pentachloride / PCl5":
        profile.update(
            principal_axes=[((0, 0, 1), "C3 axis")],
            secondary_axes=[((1, 0, 0), "C2 axis"), ((-0.5, 0.866, 0), "C2 axis")],
            planes=[("xy", "sigma_h: equatorial plane")],
        )
    elif source == "Xenon tetrafluoride / XeF4":
        profile.update(
            principal_axes=[((0, 0, 1), "C4 axis")],
            secondary_axes=[((1, 0, 0), "C2 axis"), ((0, 1, 0), "C2 axis")],
            planes=[("xy", "sigma_h: molecular plane")],
            inversion_center=True,
        )
    else:
        if point_group.startswith("D") or point_group in {"Td", "Oh", "Ih"}:
            profile["secondary_axes"] = [((1, 0, 0), "secondary C2 axis"), ((0, 1, 0), "secondary C2 axis")]

    if not profile["planes"] and point_group.endswith(("h", "v", "d")):
        profile["planes"] = [("xy", "mirror plane")]
    if point_group.endswith("h") or point_group in {"Oh", "Ih"}:
        profile["inversion_center"] = True
    return profile


def _center(coords: list[tuple[float, float, float]]) -> tuple[float, float, float]:
    n = len(coords)
    return (
        sum(coord[0] for coord in coords) / n,
        sum(coord[1] for coord in coords) / n,
        sum(coord[2] for coord in coords) / n,
    )


def _radius(coords: list[tuple[float, float, float]], center: tuple[float, float, float]) -> float:
    distances = [
        ((x - center[0]) ** 2 + (y - center[1]) ** 2 + (z - center[2]) ** 2) ** 0.5
        for x, y, z in coords
    ]
    return max(max(distances, default=1.0) * 1.8, 1.8)


def _add_axis(view, center, radius: float, direction, color: str, label: str) -> None:
    unit = _normalize(direction)
    start = _translate(center, tuple(-radius * value for value in unit))
    end = _translate(center, tuple(radius * value for value in unit))
    view.addCylinder(
        {
            "start": _point(start),
            "end": _point(end),
            "radius": max(radius * 0.012, 0.025),
            "color": color,
            "alpha": 0.82,
        }
    )
    view.addLabel(label, {"position": _point(end), "fontSize": 12, "fontColor": color, "backgroundOpacity": 0.65})


def _add_plane_grid(view, center, radius: float, plane: str, color: str, label: str) -> None:
    steps = [-0.5, 0, 0.5]
    label_pos = center
    for step in steps:
        offset = step * radius
        if plane == "xy":
            _add_line(view, (center[0] - radius, center[1] + offset, center[2]), (center[0] + radius, center[1] + offset, center[2]), color)
            _add_line(view, (center[0] + offset, center[1] - radius, center[2]), (center[0] + offset, center[1] + radius, center[2]), color)
            label_pos = (center[0] + radius, center[1] + radius, center[2])
        elif plane == "yz":
            _add_line(view, (center[0], center[1] - radius, center[2] + offset), (center[0], center[1] + radius, center[2] + offset), color)
            _add_line(view, (center[0], center[1] + offset, center[2] - radius), (center[0], center[1] + offset, center[2] + radius), color)
            label_pos = (center[0], center[1] + radius, center[2] + radius)
        else:
            _add_line(view, (center[0] - radius, center[1], center[2] + offset), (center[0] + radius, center[1], center[2] + offset), color)
            _add_line(view, (center[0] + offset, center[1], center[2] - radius), (center[0] + offset, center[1], center[2] + radius), color)
            label_pos = (center[0] + radius, center[1], center[2] + radius)
    view.addLabel(label, {"position": _point(label_pos), "fontSize": 12, "fontColor": color, "backgroundOpacity": 0.65})


def _add_line(view, start, end, color: str, radius: float = 0.012, alpha: float = 0.32) -> None:
    view.addCylinder(
        {
            "start": _point(start),
            "end": _point(end),
            "radius": radius,
            "color": color,
            "alpha": alpha,
        }
    )


def _rotate_about_axis(coord, center, direction, angle: float) -> tuple[float, float, float]:
    unit = _normalize(direction)
    vector = (coord[0] - center[0], coord[1] - center[1], coord[2] - center[2])
    dot = sum(unit[index] * vector[index] for index in range(3))
    cross = (
        unit[1] * vector[2] - unit[2] * vector[1],
        unit[2] * vector[0] - unit[0] * vector[2],
        unit[0] * vector[1] - unit[1] * vector[0],
    )
    rotated = tuple(
        vector[index] * cos(angle)
        + cross[index] * sin(angle)
        + unit[index] * dot * (1 - cos(angle))
        for index in range(3)
    )
    return _translate(center, rotated)


def _reflect_in_plane(coord, center, plane: str) -> tuple[float, float, float]:
    x, y, z = coord
    cx, cy, cz = center
    if plane == "xy":
        return (x, y, 2 * cz - z)
    if plane == "yz":
        return (2 * cx - x, y, z)
    return (x, 2 * cy - y, z)


def _invert(coord, center) -> tuple[float, float, float]:
    return (
        2 * center[0] - coord[0],
        2 * center[1] - coord[1],
        2 * center[2] - coord[2],
    )


def _normalize(direction) -> tuple[float, float, float]:
    length = sum(value * value for value in direction) ** 0.5
    if length == 0:
        return (0, 0, 1)
    return tuple(value / length for value in direction)


def _point(coord) -> dict[str, float]:
    return {"x": coord[0], "y": coord[1], "z": coord[2]}


def _translate(center, delta):
    return (center[0] + delta[0], center[1] + delta[1], center[2] + delta[2])
