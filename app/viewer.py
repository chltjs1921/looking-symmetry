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
    operation_progress: float = 100,
) -> str:
    try:
        import py3Dmol
    except ImportError:
        return (
            "<div style='padding:16px;border:1px solid #d0d7de;border-radius:8px'>"
            "py3Dmol is not installed, so the 3D viewer cannot be rendered. "
            "Run <code>pip install -r requirements.txt</code> and try again.</div>"
        )

    center = _center(geometry.coords)
    radius = _radius(geometry.coords, center)
    profile = _overlay_profile(geometry.source, symmetry.point_group)
    demonstration = _operation_demonstration(
        geometry,
        symmetry,
        profile,
        operation_mode,
        language,
        operation_progress,
    )

    right_geometry = _shift_geometry(
        MolecularGeometry(
            species=geometry.species,
            coords=demonstration["coords"],
            source=demonstration["title"],
            kind=geometry.kind,
        ),
        (0, 0, 0),
        demonstration["title"],
    )

    left_view = py3Dmol.view(width="100%", height=520)
    _add_geometry_model(left_view, geometry)
    _add_overlays(left_view, geometry, symmetry, profile)
    left_view.addLabel(
        "fixed view" if not _is_korean(language) else "고정 보기",
        {"position": _point(_translate(center, (0, -radius * 1.08, 0))), "fontSize": 13, "fontColor": "0x111827", "backgroundOpacity": 0.7},
    )
    _fit_view(left_view)

    right_view = py3Dmol.view(width="100%", height=520)
    if demonstration["kind"] == "reflection":
        _add_reflection_preview(right_view, geometry, demonstration, center, radius)
    elif demonstration["kind"] == "inversion":
        _add_inversion_preview(right_view, geometry, demonstration, center, radius)
    else:
        _add_geometry_model(right_view, right_geometry)
    right_view.addLabel(
        demonstration["title"],
        {"position": _point(_translate(center, (0, -radius * 1.08, 0))), "fontSize": 13, "fontColor": PURPLE, "backgroundOpacity": 0.75},
    )
    _fit_view(right_view)

    panes = _split_viewer_panes(
        _as_iframe(_inline_3dmol_loader() + _use_local_3dmol_loader(left_view._make_html()), height=540),
        _as_iframe(_inline_3dmol_loader() + _use_local_3dmol_loader(right_view._make_html()), height=540),
        language,
        demonstration["progress_percent"],
    )
    return _viewer_frame(demonstration, panes, language)


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


def _add_geometry_model(view, geometry: MolecularGeometry, model_index: int = 0, muted: bool = False) -> None:
    view.addModel(geometry.to_xyz(), "xyz")
    if muted:
        style = {
            "stick": {"radius": 0.12, "color": "0x9ca3af", "opacity": 0.35},
            "sphere": {"scale": 0.24, "color": "0x9ca3af", "opacity": 0.35},
        }
    else:
        style = {"stick": {"radius": 0.17}, "sphere": {"scale": 0.3}}
    view.setStyle({"model": model_index}, style)


def _add_reflection_preview(view, geometry: MolecularGeometry, demonstration: dict, center, radius: float) -> None:
    progress = _clamp_progress(demonstration.get("progress_percent"))
    operation = demonstration["operation"]
    final_geometry = MolecularGeometry(
        species=geometry.species,
        coords=demonstration["final_coords"],
        source=demonstration["title"],
        kind=geometry.kind,
    )

    _add_geometry_model(view, geometry, model_index=0, muted=progress >= 0.75)

    if progress >= 0.25:
        _add_plane_grid(view, center, radius, operation["plane"], ORANGE, "mirror plane")
    if progress >= 0.5:
        _add_reflection_correspondence(view, geometry.coords, final_geometry.coords, radius)
    if progress >= 0.75:
        _add_geometry_model(view, final_geometry, model_index=1, muted=progress < 1.0)


def _add_inversion_preview(view, geometry: MolecularGeometry, demonstration: dict, center, radius: float) -> None:
    progress = _clamp_progress(demonstration.get("progress_percent"))
    final_geometry = MolecularGeometry(
        species=geometry.species,
        coords=demonstration["final_coords"],
        source=demonstration["title"],
        kind=geometry.kind,
    )

    _add_geometry_model(view, geometry, model_index=0, muted=progress >= 0.75)

    if progress >= 0.25:
        _add_inversion_center_marker(view, center, radius)
    if progress >= 0.5:
        _add_reflection_correspondence(view, geometry.coords, final_geometry.coords, radius)
    if progress >= 0.75:
        _add_geometry_model(view, final_geometry, model_index=1, muted=progress < 1.0)


def _add_inversion_center_marker(view, center, radius: float) -> None:
    view.addSphere(
        {
            "center": _point(center),
            "radius": max(radius * 0.06, 0.1),
            "color": RED,
            "alpha": 0.9,
        }
    )
    view.addLabel(
        "inversion center",
        {"position": _point(_translate(center, (0.12, 0.12, 0.12))), "fontSize": 12, "fontColor": RED, "backgroundOpacity": 0.65},
    )


def _add_reflection_correspondence(
    view,
    start_coords: list[tuple[float, float, float]],
    end_coords: list[tuple[float, float, float]],
    radius: float,
) -> None:
    for start, end in zip(start_coords, end_coords):
        midpoint = tuple((start[index] + end[index]) / 2 for index in range(3))
        _add_line(view, start, end, PURPLE, radius=max(radius * 0.009, 0.018), alpha=0.55)
        view.addSphere(
            {
                "center": _point(midpoint),
                "radius": max(radius * 0.025, 0.045),
                "color": PURPLE,
                "alpha": 0.65,
            }
        )


def _fit_view(view) -> None:
    view.zoomTo()
    view.zoom(0.9)


def _as_iframe(inner_html: str, height: int = 660) -> str:
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
        f"style=\"width:100%;height:{height}px;border:0;display:block;background:#fff;\" "
        "sandbox=\"allow-scripts allow-same-origin\">"
        "</iframe>"
    )


def _split_viewer_panes(left_iframe: str, right_iframe: str, language: str, progress_percent: int = 100) -> str:
    ko = _is_korean(language)
    left_label = "Original molecule" if not ko else "원래 분자"
    right_label = "Operation preview" if not ko else "조작 미리보기"
    left_hint = "fixed view" if not ko else "고정 보기"
    right_hint = f"progress {progress_percent}%" if not ko else f"진행률 {progress_percent}%"
    return (
        "<div class='viewer-split'>"
        "<div class='viewer-pane viewer-pane-active'>"
        "<div class='viewer-pane-head'>"
        f"<span>{escape(left_label)}</span><span>{escape(left_hint)}</span>"
        "</div>"
        f"{left_iframe}"
        "</div>"
        "<div class='viewer-pane viewer-pane-static'>"
        "<div class='viewer-pane-head'>"
        f"<span>{escape(right_label)}</span><span>{escape(right_hint)}</span>"
        "</div>"
        f"{right_iframe}"
        "</div>"
        "</div>"
    )


def _viewer_frame(demonstration: dict, iframe: str, language: str) -> str:
    ko = _is_korean(language)
    title = "왜 이것이 대칭 조작인가?" if ko else "Why this operation is symmetry"
    switch_hint = (
        "다른 조작은 viewer 위의 '현재 확인 중' 메뉴에서 바꿔 볼 수 있습니다."
        if ko
        else "Use the Now inspecting menu above the viewer to switch symmetry operations."
    )
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
        ".viewer-teaching-steps{margin:8px 0 0 18px;padding:0;color:#4b5563;font-size:13px;line-height:1.45;}"
        ".viewer-teaching-hint{font-size:12px;line-height:1.4;color:#6b7280;margin:7px 0 0;}"
        ".viewer-teaching-badge{flex:0 0 auto;border-radius:999px;background:#f3e8ff;color:#6d28d9;padding:5px 9px;font-size:12px;font-weight:900;}"
        ".viewer-teaching-legend{display:flex;flex-wrap:wrap;gap:8px;padding:10px 14px;border-top:1px solid #e5e7eb;color:#4b5563;font-size:12px;}"
        ".viewer-dot{display:inline-block;width:10px;height:10px;border-radius:999px;margin-right:5px;vertical-align:-1px;}"
        ".viewer-split{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:1px;background:#e5e7eb;}"
        ".viewer-pane{min-width:0;background:#fff;}"
        ".viewer-pane-active iframe{pointer-events:none;}"
        ".viewer-pane-static iframe{pointer-events:none;}"
        ".viewer-pane-head{display:flex;align-items:center;justify-content:space-between;gap:8px;padding:8px 10px;border-bottom:1px solid #e5e7eb;color:#111827;font-size:12px;font-weight:900;}"
        ".viewer-pane-head span:last-child{color:#6b7280;font-weight:700;}"
        "@media (max-width:760px){.viewer-split{grid-template-columns:1fr;}}"
        "</style>"
        "<section class='viewer-teaching'>"
        "<div class='viewer-teaching-head'>"
        "<div>"
        f"<p class='viewer-teaching-title'>{escape(title)}</p>"
        f"<p class='viewer-teaching-note'>{escape(demonstration['explanation'])}</p>"
        f"{_teaching_steps(demonstration)}"
        f"<p class='viewer-teaching-hint'>{escape(switch_hint)}</p>"
        "</div>"
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


def _teaching_steps(demonstration: dict) -> str:
    steps = demonstration.get("steps")
    if not steps:
        return ""
    items = "".join(f"<li>{escape(step)}</li>" for step in steps)
    return f"<ul class='viewer-teaching-steps'>{items}</ul>"


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
    progress_percent: float = 100,
) -> dict:
    operation = _choose_operation(symmetry.point_group, profile, operation_mode)
    center = _center(geometry.coords)
    coords = geometry.coords
    progress = _clamp_progress(progress_percent)

    if operation["kind"] == "unavailable":
        final_coords = list(coords)
        transformed = list(coords)
        operation_name = _operation_title(operation["title"], language)
        if _is_korean(language):
            explanation = (
                f"{geometry.source}의 점군 {symmetry.point_group}에는 {operation_name} 조작이 없습니다. "
                "오른쪽 미리보기는 원래 분자를 그대로 보여줍니다. 다른 조작을 선택하면 실제 대칭 조작을 확인할 수 있습니다."
            )
        else:
            explanation = (
                f"{geometry.source} has point group {symmetry.point_group}, which does not include {operation['title']}. "
                "The preview keeps the molecule unchanged. Select another operation to inspect an actual symmetry operation."
            )
        steps = []
    elif operation["kind"] == "rotation":
        final_coords = [
            _rotate_about_axis(coord, center, operation["direction"], operation["angle"])
            for coord in coords
        ]
        transformed = [
            _rotate_about_axis(coord, center, operation["direction"], operation["angle"] * progress)
            for coord in coords
        ]
        if _is_korean(language):
            explanation = (
                f"왼쪽 분자를 표시된 축 주위로 {operation['degrees']}도 회전한 모습이 오른쪽입니다. "
                "실제 대칭 회전은 진행률 슬라이더로 확인합니다. "
                "오른쪽의 원자 배열이 왼쪽과 같아 보이면, 이 회전은 대칭 조작입니다."
            )
        else:
            explanation = (
                f"Rotate the left molecule by {operation['degrees']} degrees around the highlighted axis. "
                "Use the progress slider to inspect the actual symmetry rotation. "
                "The right molecule has the same atom pattern, so the rotation is a symmetry operation."
            )
        steps = []
    elif operation["kind"] == "reflection":
        final_coords = [_reflect_in_plane(coord, center, operation["plane"]) for coord in coords]
        transformed = _interpolate_coords(coords, final_coords, progress)
        if _is_korean(language):
            explanation = (
                f"오른쪽은 {operation['plane']} 거울면을 기준으로 원래 원자와 반사된 원자의 대응을 단계적으로 보여줍니다. "
                "대응선의 가운데가 거울면 위에 놓이고 같은 종류의 원자로 대응되면, 이 평면은 거울면입니다."
            )
            steps = [
                "0%: 원래 분자",
                "25%: 거울면 강조",
                "50%: 원래 원자와 반사 위치를 잇는 대응선",
                "75%: 반사된 분자를 희미하게 표시",
                "100%: 반사 결과를 진하게 표시",
            ]
        else:
            explanation = (
                f"The right panel stages the reflection across the highlighted {operation['plane']} plane. "
                "Correspondence lines show equal distance to the plane and matching atom types."
            )
            steps = [
                "0%: original molecule",
                "25%: mirror plane highlighted",
                "50%: correspondence lines between original and reflected atoms",
                "75%: reflected molecule shown as a ghost",
                "100%: reflected result emphasized",
            ]
    elif operation["kind"] == "inversion":
        final_coords = [_invert(coord, center) for coord in coords]
        transformed = _interpolate_coords(coords, final_coords, progress)
        if _is_korean(language):
            explanation = (
                "오른쪽은 빨간 반전 중심을 기준으로 원래 원자와 반전된 원자의 대응을 단계적으로 보여줍니다. "
                "각 대응선의 가운데가 같은 반전 중심에 놓이고 같은 종류의 원자로 대응되면, 그 점은 반전 중심입니다."
            )
            steps = [
                "0%: 원래 분자",
                "25%: 반전 중심 강조",
                "50%: 원래 원자와 반전 위치를 잇는 대응선",
                "75%: 반전된 분자를 희미하게 표시",
                "100%: 반전 결과를 진하게 표시",
            ]
        else:
            explanation = (
                "The right panel stages each atom's correspondence through the red inversion center. "
                "If each correspondence line shares the same midpoint and matching atom types, that point is an inversion center."
            )
            steps = [
                "0%: original molecule",
                "25%: inversion center highlighted",
                "50%: correspondence lines between original and inverted atoms",
                "75%: inverted molecule shown as a ghost",
                "100%: inverted result emphasized",
            ]
    else:
        final_coords = list(coords)
        transformed = list(coords)
        explanation = (
            "항등 조작은 모든 원자를 원래 자리에 그대로 둡니다."
            if _is_korean(language)
            else "The identity operation leaves every atom exactly where it started."
        )
        steps = []

    return {
        "title": operation["title"],
        "kind": operation["kind"],
        "coords": transformed,
        "final_coords": final_coords,
        "operation": operation,
        "progress_percent": round(progress * 100),
        "explanation": explanation,
        "steps": steps,
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
    if requested_key in {"principal", "mirror", "inversion", "secondary"}:
        return _unavailable_operation(requested_key)
    return available[0]


def _unavailable_operation(requested_key: str) -> dict:
    titles = {
        "principal": "Principal rotation",
        "mirror": "Mirror plane",
        "inversion": "Inversion center",
        "secondary": "Secondary C2 rotation",
    }
    return {
        "kind": "unavailable",
        "key": requested_key,
        "title": titles[requested_key],
    }


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


def _clamp_progress(progress_percent: float) -> float:
    try:
        progress = float(progress_percent) / 100
    except (TypeError, ValueError):
        return 0.0
    return min(max(progress, 0.0), 1.0)


def _interpolate_coords(
    start_coords: list[tuple[float, float, float]],
    end_coords: list[tuple[float, float, float]],
    progress: float,
) -> list[tuple[float, float, float]]:
    return [
        tuple(
            start[index] + (end[index] - start[index]) * progress
            for index in range(3)
        )
        for start, end in zip(start_coords, end_coords)
    ]


def _operation_title(title: str, language: str) -> str:
    if not _is_korean(language):
        return title
    if title.startswith("Principal rotation"):
        return title.replace("Principal rotation", "주축 회전")
    translations = {
        "Mirror plane": "거울면",
        "Inversion center": "반전 중심",
        "Secondary C2 rotation": "보조 C2 회전",
        "Identity": "항등 조작",
    }
    return translations.get(title, title)


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
