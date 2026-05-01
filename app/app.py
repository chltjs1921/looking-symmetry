from __future__ import annotations

from html import escape

import gradio as gr

from .config import APP_SUBTITLE, APP_TITLE, DEFAULT_TOLERANCE
from .examples import by_label, dropdown_choices, teaching_note
from .molecule import build_geometry
from .symmetry import analyze_point_group, point_group_guide
from .viewer import render_viewer, teaching_operation_choices

LANGUAGE_CHOICES = ["한국어", "English"]
FEEDBACK_FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSdNcry-R4oqNx6AdtbTq-KTC91EA97k1J35d5uiRNqt9RoWFw/viewform?usp=publish-editor"


def is_korean(language: str) -> bool:
    return not language.casefold().startswith("english")


def render_student_intro(language: str = "한국어") -> str:
    if is_korean(language):
        subtitle = "분자 점군을 3D로 탐색하는 학습용 프로토타입입니다. 대칭 조작이 실제로 직관적으로 보이는지 테스트하기 위한 앱입니다."
        steps = [
            ("1. 예시를 고르기", "직접 입력하기보다 Water, Ammonia, CO2, Benzene부터 시작하세요."),
            ("2. 양쪽을 비교하기", "왼쪽은 원래 분자, 오른쪽은 회전/반사/반전 후의 분자입니다."),
            ("3. 같은지 판단하기", "원자 배열이 변하지 않은 것처럼 보이면 그 조작은 대칭 조작입니다."),
        ]
        feedback = "피드백 초점: 어떤 조작이 직관적이었는지, 무엇이 헷갈렸는지, viewer가 점군을 납득하는 데 도움이 되었는지 알려주세요."
    else:
        subtitle = f"{APP_SUBTITLE}. This prototype is for testing whether molecular symmetry operations feel intuitive in 3D."
        steps = [
            ("1. Pick an example", "Start with Water, Ammonia, CO2, or Benzene instead of typing your own molecule."),
            ("2. Compare both sides", "Left is the original molecule. Right is the molecule after rotation, reflection, or inversion."),
            ("3. Judge the match", "If the atom pattern is unchanged, that operation is a symmetry operation."),
        ]
        feedback = "Feedback focus: tell us which operation was intuitive, which one was confusing, and whether the viewer made the point group easier to believe."

    step_html = "".join(
        f"<div class='student-step'><b>{escape(title)}</b><span>{escape(body)}</span></div>"
        for title, body in steps
    )
    return (
        "<style>"
        ".student-intro{font-family:Inter,ui-sans-serif,system-ui,sans-serif;margin:0 0 18px;padding:16px 18px;border:1px solid #dde3f8;border-radius:8px;background:#ffffff;color:#111827;}"
        ".student-intro h1{margin:0 0 6px;font-size:30px;line-height:1.15;letter-spacing:0;}"
        ".student-intro .subtitle{margin:0 0 12px;color:#374151;font-size:15px;line-height:1.45;}"
        ".student-steps{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin:12px 0 0;}"
        ".student-step{border:1px solid #e5e7eb;border-radius:8px;padding:10px 11px;background:#f9fafb;}"
        ".student-step b{display:block;color:#3730a3;font-size:13px;margin-bottom:4px;}"
        ".student-step span{display:block;color:#4b5563;font-size:13px;line-height:1.35;}"
        ".student-feedback{margin:12px 0 0;color:#4b5563;font-size:13px;line-height:1.45;}"
        "@media (max-width:760px){.student-steps{grid-template-columns:1fr}.student-intro h1{font-size:26px}}"
        "</style>"
        "<section class='student-intro'>"
        f"<h1>{escape(APP_TITLE)}</h1>"
        f"<p class='subtitle'>{escape(subtitle)}</p>"
        "<div class='student-steps'>"
        f"{step_html}"
        "</div>"
        f"<p class='student-feedback'>{escape(feedback)}</p>"
        "</section>"
    )


def render_feedback_button() -> str:
    return (
        "<div style='margin-top:12px;padding:12px;border:1px solid #dde3f8;border-radius:8px;background:#fff'>"
        f"<a href='{escape(FEEDBACK_FORM_URL, quote=True)}' target='_blank' rel='noopener noreferrer' "
        "style='display:inline-block;width:100%;box-sizing:border-box;text-align:center;padding:10px 14px;"
        "border-radius:8px;background:#4f46e5;color:white;font-weight:800;text-decoration:none'>"
        "피드백 남기기 / Leave feedback"
        "</a>"
        "<p style='margin:8px 0 0;color:#4b5563;font-size:13px;line-height:1.4'>"
        "앱을 사용한 뒤 헷갈린 점이나 개선 의견을 남겨 주세요."
        "<br>"
        "After trying the app, please share what was confusing or useful."
        "</p>"
        "</div>"
    )


def load_example(label: str) -> str:
    molecule = by_label(label)
    return molecule["aliases"][0] if molecule else ""


def render_result_panel(symmetry, geometry, language: str = "한국어") -> str:
    ko = is_korean(language)
    teaching = teaching_note(geometry.source)
    clue_label = "예시 힌트" if ko else "Example clue"
    teaching_html = (
        f"<p class='result-clue'><b>{escape(clue_label)}:</b> {escape(teaching)}</p>"
        if teaching
        else ""
    )
    modal_id = f"decision-modal-{escape(symmetry.point_group)}"
    point_group_label = "점군" if ko else "Point group"
    open_tree = "결정 트리 열기" if ko else "open tree"
    input_label = "입력 해석" if ko else "Input interpreted as"
    guide_label = "읽는 법" if ko else "How to read this"
    modal_title = "전체 결정 트리" if ko else "Full decision tree"
    close = "닫기" if ko else "Close"
    return (
        "<style>"
        ".result-panel{font-family:Inter,ui-sans-serif,system-ui,sans-serif;margin:0 0 14px;color:#111827;}"
        ".result-card{border:1px solid #dde3f8;border-radius:8px;background:#fff;padding:16px 18px;box-shadow:0 1px 2px rgba(15,23,42,.06);}"
        ".result-eyebrow{margin:0 0 8px;color:#4b5563;font-size:13px;font-weight:800;text-transform:uppercase;letter-spacing:.04em;}"
        ".point-group-trigger{display:inline-flex;align-items:center;gap:8px;border:1px solid #4f46e5;border-radius:8px;background:#eef2ff;color:#3730a3;padding:7px 11px;font-size:24px;line-height:1;font-weight:900;cursor:pointer;}"
        ".point-group-trigger:hover{background:#e0e7ff;}"
        ".point-group-hint{font-size:12px;font-weight:800;color:#4f46e5;}"
        ".result-meta{margin:12px 0 0;font-size:14px;line-height:1.45;color:#374151;}"
        ".result-guide,.result-clue{margin:10px 0 0;font-size:14px;line-height:1.5;color:#374151;}"
        ".pg-modal-toggle{position:absolute;opacity:0;pointer-events:none;}"
        ".pg-modal{display:none;position:fixed;inset:0;z-index:9999;}"
        ".pg-modal-toggle:checked~.pg-modal{display:block;}"
        ".pg-modal-backdrop{position:absolute;inset:0;background:rgba(15,23,42,.46);cursor:pointer;}"
        ".pg-modal-panel{position:absolute;top:5vh;left:50%;transform:translateX(-50%);width:min(1100px,92vw);max-height:88vh;overflow:auto;border-radius:8px;background:#fff;box-shadow:0 24px 72px rgba(15,23,42,.32);padding:18px;}"
        ".pg-modal-head{display:flex;align-items:center;justify-content:space-between;gap:12px;margin:0 0 8px;}"
        ".pg-modal-title{font-size:18px;font-weight:900;color:#111827;}"
        ".pg-modal-close{border:1px solid #d1d5db;border-radius:8px;background:#fff;color:#374151;padding:6px 10px;font-size:13px;font-weight:900;cursor:pointer;}"
        ".pg-modal-close:hover{background:#f3f4f6;}"
        "</style>"
        "<section class='result-panel'>"
        f"<input id='{modal_id}' class='pg-modal-toggle' type='checkbox'>"
        "<div class='result-card'>"
        f"<p class='result-eyebrow'>{escape(point_group_label)}</p>"
        f"<label class='point-group-trigger' for='{modal_id}' title='Open full decision tree'>{escape(symmetry.point_group)}"
        f"<span class='point-group-hint'>{escape(open_tree)}</span></label>"
        f"<p class='result-meta'><b>{escape(input_label)}:</b> {escape(geometry.source)}</p>"
        f"<p class='result-guide'><b>{escape(guide_label)}:</b> {escape(localized_point_group_guide(symmetry.point_group, language))}</p>"
        f"{teaching_html}"
        "</div>"
        "<div class='pg-modal'>"
        f"<label class='pg-modal-backdrop' for='{modal_id}' aria-label='Close decision tree'></label>"
        "<div class='pg-modal-panel'>"
        "<div class='pg-modal-head'>"
        f"<div class='pg-modal-title'>{escape(modal_title)}</div>"
        f"<label class='pg-modal-close' for='{modal_id}'>{escape(close)}</label>"
        "</div>"
        f"{render_decision_tree(symmetry, language)}"
        "</div>"
        "</div>"
        "</section>"
    )


def localized_point_group_guide(point_group: str, language: str = "한국어") -> str:
    if not is_korean(language):
        return point_group_guide(point_group)
    guides = {
        "C1": "항등 조작(E) 말고는 뚜렷한 대칭이 없는 가장 낮은 대칭입니다.",
        "Cs": "거울면은 하나 있지만, 유용한 회전축은 없는 경우입니다.",
        "Ci": "반전 중심은 있지만, 거울면이나 고유 회전축은 없는 경우입니다.",
        "C2v": "C2 회전축과 그 축을 포함하는 수직 거울면들이 있습니다. 물이 대표 예시입니다.",
        "C3v": "C3 회전축과 수직 거울면들이 있습니다. 암모니아가 대표 예시입니다.",
        "D2h": "서로 수직인 C2 축들, 거울면, 반전 중심을 함께 가집니다.",
        "D3h": "C3 축, 여러 C2 축, 수평 거울면을 가집니다.",
        "D4h": "C4 축, 수직 C2 축들, 거울면, 반전 중심을 가집니다.",
        "D6h": "C6 축, 수직 C2 축들, 거울면, 반전 중심을 가집니다.",
        "Dinfh": "CO2처럼 반전 중심을 가진 선형 분자입니다.",
        "Cinfv": "HCl처럼 반전 중심이 없는 선형 분자입니다.",
        "Td": "정사면체 대칭입니다. 동등한 C3 축들이 여러 개 있습니다.",
        "Oh": "정팔면체 또는 입방형 대칭입니다. 동등한 C4, C3, C2 축들이 여러 개 있습니다.",
    }
    return guides.get(point_group, point_group_guide(point_group))


def render_decision_tree(symmetry, language: str = "한국어") -> str:
    active_ids = _active_tree_ids(symmetry.point_group)
    tree_html = _render_tree_node(_full_decision_tree(), active_ids, language=language)
    title = "전체 결정 트리" if is_korean(language) else "Full decision tree"
    caption = (
        f"주요 분기 전체를 보여줍니다. 강조된 경로가 <b>{escape(symmetry.point_group)}</b>로 가는 길입니다."
        if is_korean(language)
        else f"All major branches are shown. The highlighted route is the path for <b>{escape(symmetry.point_group)}</b>."
    )
    return (
        "<style>"
        ".decision-tree{font-family:Inter,ui-sans-serif,system-ui,sans-serif;margin:12px 0 22px;overflow-x:auto;padding-bottom:8px;}"
        ".decision-tree h3{margin:0 0 6px;font-size:20px;line-height:1.25;color:#111827;}"
        ".tree-caption{color:#4b5563;font-size:13px;line-height:1.35;margin:0 0 14px;}"
        ".tree-root,.tree-children{list-style:none;margin:0;padding:0;}"
        ".tree-root{min-width:760px;}"
        ".tree-item{position:relative;margin:0 0 0 24px;padding:0 0 0 22px;border-left:2px solid #d7dced;}"
        ".tree-item.active{border-left-color:#4f46e5;}"
        ".tree-branch{display:flex;align-items:flex-start;gap:8px;margin:10px 0;}"
        ".tree-edge{min-width:48px;text-align:center;border-radius:999px;padding:3px 8px;font-weight:800;font-size:12px;background:#f3f4f6;color:#374151;}"
        ".tree-edge.yes{background:#dcfce7;color:#166534;}"
        ".tree-edge.no{background:#fee2e2;color:#991b1b;}"
        ".tree-edge.choice{background:#fef3c7;color:#92400e;}"
        ".tree-edge.active{outline:2px solid #4f46e5;outline-offset:1px;}"
        ".tree-card{max-width:340px;border:1px solid #d8def8;border-radius:8px;background:#fff;padding:11px 12px;box-shadow:0 1px 2px rgba(15,23,42,.06);}"
        ".tree-card.active{border-color:#4f46e5;background:#eef2ff;box-shadow:0 0 0 2px rgba(79,70,229,.14);}"
        ".tree-question{font-weight:800;color:#111827;font-size:14px;line-height:1.35;}"
        ".tree-note{color:#4b5563;font-size:12px;line-height:1.35;margin-top:5px;}"
        ".tree-result{font-weight:900;color:#1d4ed8;font-size:16px;}"
        ".tree-result.muted{color:#374151;}"
        ".tree-children{margin-left:42px;}"
        "</style>"
        "<section class='decision-tree'>"
        f"<h3>{escape(title)}</h3>"
        f"<p class='tree-caption'>{caption}</p>"
        f"<ul class='tree-root'>{tree_html}</ul>"
        "</section>"
    )


def _render_tree_node(node: dict, active_ids: set[str], edge: str | None = None, language: str = "한국어") -> str:
    node_id = node["id"]
    active = node_id in active_ids
    edge_html = ""
    if edge is not None:
        edge_class = _edge_class(edge)
        active_edge = " active" if active else ""
        edge_html = f"<span class='tree-edge {edge_class}{active_edge}'>{escape(_tree_text(edge, language))}</span>"

    card_class = "tree-card active" if active else "tree-card"
    if "result" in node:
        result_class = "tree-result" if active else "tree-result muted"
        content = f"<div class='{result_class}'>{escape(node['result'])}</div>"
    else:
        content = (
            f"<div class='tree-question'>{escape(_tree_text(node['question'], language))}</div>"
            f"<div class='tree-note'>{escape(_tree_text(node.get('note', ''), language))}</div>"
        )

    children = "".join(
        _render_tree_node(child, active_ids, branch, language)
        for branch, child in node.get("branches", [])
    )
    children_html = f"<ul class='tree-children'>{children}</ul>" if children else ""
    active_item = " active" if active else ""
    return (
        f"<li class='tree-item{active_item}'>"
        "<div class='tree-branch'>"
        f"{edge_html}<div class='{card_class}'>{content}</div>"
        "</div>"
        f"{children_html}"
        "</li>"
    )


def _tree_text(text: str, language: str = "한국어") -> str:
    if not is_korean(language):
        return text
    translations = {
        "Is the molecule linear?": "분자가 선형인가?",
        "Linear molecules use infinite-axis point groups.": "선형 분자는 무한 회전축을 가진 점군을 사용합니다.",
        "Is there an inversion center, or are both ends equivalent?": "반전 중심이 있거나 양쪽 끝이 서로 동등한가?",
        "CO2 follows Yes; HCl follows No.": "CO2는 Yes, HCl은 No에 해당합니다.",
        "Is it a special high-symmetry shape?": "특별한 고대칭 구조인가?",
        "Tetrahedral, octahedral, and related shapes branch here.": "정사면체, 정팔면체 같은 구조는 여기에서 갈라집니다.",
        "Which high-symmetry shape is it?": "어떤 고대칭 구조인가?",
        "Use the molecular geometry, not only one axis.": "축 하나만 보지 말고 전체 분자 기하를 봅니다.",
        "Is there a proper rotation axis Cn?": "고유 회전축 Cn이 있는가?",
        "Find the highest-order axis first.": "가장 차수가 높은 회전축을 먼저 찾습니다.",
        "Any mirror plane or inversion center?": "거울면이나 반전 중심이 있는가?",
        "These are the low-symmetry non-rotational cases.": "회전축이 없는 낮은 대칭의 경우입니다.",
        "What is the highest-order Cn axis?": "가장 차수가 높은 Cn 축은 무엇인가?",
        "This determines the number in Cn or Dn.": "이 값이 Cn 또는 Dn의 n을 결정합니다.",
        "Are there C2 axes perpendicular to the C2 axis?": "C2 축에 수직인 C2 축들이 있는가?",
        "Are there C2 axes perpendicular to the C3 axis?": "C3 축에 수직인 C2 축들이 있는가?",
        "Are there C2 axes perpendicular to the C4 axis?": "C4 축에 수직인 C2 축들이 있는가?",
        "Are there C2 axes perpendicular to the C6 axis?": "C6 축에 수직인 C2 축들이 있는가?",
        "Are there C2 axes perpendicular to the Cn axis?": "Cn 축에 수직인 C2 축들이 있는가?",
        "Yes means D family; No means C family.": "Yes이면 D 계열, No이면 C 계열입니다.",
        "What extra element is present?": "추가로 어떤 대칭 요소가 있는가?",
        "Vertical planes give Cnv; horizontal planes give Cnh.": "수직 거울면은 Cnv, 수평 거울면은 Cnh를 만듭니다.",
        "Horizontal planes give Dnh; dihedral planes give Dnd.": "수평 거울면은 Dnh, 이면각 거울면은 Dnd를 만듭니다.",
        "Yes": "예",
        "No": "아니오",
        "Tetrahedral": "정사면체",
        "Octahedral": "정팔면체",
        "Mirror plane": "거울면",
        "Inversion center": "반전 중심",
        "Neither": "둘 다 없음",
        "Other Cn": "기타 Cn",
        "vertical mirror": "수직 거울면",
        "horizontal mirror": "수평 거울면",
        "dihedral mirror": "이면각 거울면",
        "none": "없음",
    }
    return translations.get(text, text)


def _edge_class(edge: str) -> str:
    normalized = edge.casefold()
    if normalized == "yes":
        return "yes"
    if normalized == "no":
        return "no"
    return "choice"


def _active_tree_ids(point_group: str) -> set[str]:
    paths = {
        "Dinfh": {"linear", "linear-centrosymmetric", "result-dinfh"},
        "Cinfv": {"linear", "linear-centrosymmetric", "result-cinfv"},
        "Td": {"linear", "special", "special-kind", "result-td"},
        "Oh": {"linear", "special", "special-kind", "result-oh"},
        "C1": {"linear", "special", "has-cn", "low-symmetry", "low-has-sigma", "low-has-i", "result-c1"},
        "Cs": {"linear", "special", "has-cn", "low-symmetry", "low-has-sigma", "result-cs"},
        "Ci": {"linear", "special", "has-cn", "low-symmetry", "low-has-sigma", "low-has-i", "result-ci"},
        "C2v": {"linear", "special", "has-cn", "highest-cn", "perpendicular-c2-c2", "c-family-mirror-c2", "result-c2v"},
        "C3v": {"linear", "special", "has-cn", "highest-cn", "perpendicular-c2-c3", "c-family-mirror-c3", "result-c3v"},
        "D2h": {"linear", "special", "has-cn", "highest-cn", "perpendicular-c2-c2", "d-family-plane-c2", "result-d2h"},
        "D3h": {"linear", "special", "has-cn", "highest-cn", "perpendicular-c2-c3", "d-family-plane-c3", "result-d3h"},
        "D4h": {"linear", "special", "has-cn", "highest-cn", "perpendicular-c2-c4", "d-family-plane-c4", "result-d4h"},
        "D6h": {"linear", "special", "has-cn", "highest-cn", "perpendicular-c2-c6", "d-family-plane-c6", "result-d6h"},
    }
    return paths.get(point_group, {"linear", "special", "has-cn", "highest-cn"})


def _full_decision_tree() -> dict:
    return {
        "id": "linear",
        "question": "Is the molecule linear?",
        "note": "Linear molecules use infinite-axis point groups.",
        "branches": [
            ("Yes", {
                "id": "linear-centrosymmetric",
                "question": "Is there an inversion center, or are both ends equivalent?",
                "note": "CO2 follows Yes; HCl follows No.",
                "branches": [
                    ("Yes", {"id": "result-dinfh", "result": "Dinfh"}),
                    ("No", {"id": "result-cinfv", "result": "Cinfv"}),
                ],
            }),
            ("No", {
                "id": "special",
                "question": "Is it a special high-symmetry shape?",
                "note": "Tetrahedral, octahedral, and related shapes branch here.",
                "branches": [
                    ("Yes", {
                        "id": "special-kind",
                        "question": "Which high-symmetry shape is it?",
                        "note": "Use the molecular geometry, not only one axis.",
                        "branches": [
                            ("Tetrahedral", {"id": "result-td", "result": "Td"}),
                            ("Octahedral", {"id": "result-oh", "result": "Oh"}),
                        ],
                    }),
                    ("No", {
                        "id": "has-cn",
                        "question": "Is there a proper rotation axis Cn?",
                        "note": "Find the highest-order axis first.",
                        "branches": [
                            ("No", {
                                "id": "low-symmetry",
                                "question": "Any mirror plane or inversion center?",
                                "note": "These are the low-symmetry non-rotational cases.",
                                "branches": [
                                    ("Mirror plane", {
                                        "id": "low-has-sigma",
                                        "result": "Cs",
                                    }),
                                    ("Inversion center", {
                                        "id": "low-has-i",
                                        "result": "Ci",
                                    }),
                                    ("Neither", {"id": "result-c1", "result": "C1"}),
                                ],
                            }),
                            ("Yes", {
                                "id": "highest-cn",
                                "question": "What is the highest-order Cn axis?",
                                "note": "This determines the number in Cn or Dn.",
                                "branches": [
                                    ("C2", _cn_family("C2", "C2v", "D2h")),
                                    ("C3", _cn_family("C3", "C3v", "D3h")),
                                    ("C4", _cn_family("C4", "C4v", "D4h")),
                                    ("C6", _cn_family("C6", "C6v", "D6h")),
                                    ("Other Cn", _cn_family("Cn", "Cnv / Cnh / Cn", "Dnh / Dnd / Dn")),
                                ],
                            }),
                        ],
                    }),
                ],
            }),
        ],
    }


def _cn_family(label: str, c_result: str, d_result: str) -> dict:
    key = label.lower()
    return {
        "id": f"perpendicular-c2-{key}",
        "question": f"Are there C2 axes perpendicular to the {label} axis?",
        "note": "Yes means D family; No means C family.",
        "branches": [
            ("No", {
                "id": f"c-family-mirror-{key}",
                "question": "What extra element is present?",
                "note": "Vertical planes give Cnv; horizontal planes give Cnh.",
                "branches": [
                    ("vertical mirror", {"id": f"result-{c_result.lower().replace(' / ', '-')}", "result": c_result}),
                    ("horizontal mirror", {"id": f"result-{key}h", "result": f"{label}h"}),
                    ("none", {"id": f"result-{key}", "result": label}),
                ],
            }),
            ("Yes", {
                "id": f"d-family-plane-{key}",
                "question": "What extra element is present?",
                "note": "Horizontal planes give Dnh; dihedral planes give Dnd.",
                "branches": [
                    ("horizontal mirror", {"id": f"result-{d_result.lower().replace(' / ', '-')}", "result": d_result}),
                    ("dihedral mirror", {"id": f"result-d{key[1:]}d", "result": f"D{label[1:]}d"}),
                    ("none", {"id": f"result-d{key[1:]}", "result": f"D{label[1:]}"}),
                ],
            }),
        ],
    }


def analyze(raw_input: str, tolerance: float, operation_mode: str, operation_progress: float, language: str):
    try:
        geometry = build_geometry(raw_input)
        symmetry = analyze_point_group(geometry, tolerance=tolerance)
        viewer = render_viewer(geometry, symmetry, operation_mode, language, operation_progress)
        elements = "\n".join(
            f"- **{element.label}**: {element.explanation}" for element in symmetry.elements
        )
        operations = "unknown" if symmetry.operation_count is None else str(symmetry.operation_count)
        if is_korean(language):
            details = (
                f"**pymatgen이 찾은 대칭 조작 수:** {operations}\n\n"
                f"### 보이는 대칭 요소\n\n{elements}\n\n"
                "### Viewer 범례\n\n"
                "- **파란 선**: 주 회전축\n"
                "- **초록 선**: 보조 C2 회전축\n"
                "- **주황 격자**: 거울면\n"
                "- **빨간 점**: 반전 중심\n\n"
                "viewer는 원래 분자와 선택한 대칭 조작 후의 분자를 비교합니다. "
                "원자 배열이 변하지 않은 것처럼 보이면 그 조작은 대칭 조작입니다.\n\n"
                f"> 참고: {symmetry.note}"
            )
        else:
            details = (
                f"**Symmetry operations found by pymatgen:** {operations}\n\n"
                f"### Visible symmetry elements\n\n{elements}\n\n"
                "### Viewer legend\n\n"
                "- **Blue line**: principal rotation axis\n"
                "- **Green line**: secondary C2 rotation axis\n"
                "- **Orange grid**: mirror plane\n"
                "- **Red dot**: inversion center\n\n"
                "The viewer compares the original molecule with the molecule after the selected operation. "
                "If the atom pattern is unchanged, that operation is a symmetry operation.\n\n"
                f"> Note: {symmetry.note}"
            )
        return render_result_panel(symmetry, geometry, language), details, viewer, geometry.to_xyz()
    except Exception as exc:
        return f"<h3>Analysis failed</h3><p>{escape(str(exc))}</p>", "", "", ""


def reset_operation_progress():
    return gr.update(value=0)


with gr.Blocks(title=APP_TITLE) as demo:
    intro_output = gr.HTML(render_student_intro("한국어"))
    with gr.Row():
        with gr.Column(scale=5):
            language_picker = gr.Dropdown(
                choices=LANGUAGE_CHOICES,
                label="언어 / Language",
                value="한국어",
            )
            molecule_input = gr.Textbox(
                label="분자 이름, 분자식, SMILES, 또는 XYZ / Molecule input",
                lines=8,
                value="water",
                placeholder="Examples: water, H2O, C, c1ccccc1, or XYZ coordinates",
            )
            with gr.Row():
                example_picker = gr.Dropdown(
                    choices=dropdown_choices(),
                    label="예시 / Examples",
                    value="Water / H2O",
                )
                tolerance = gr.Slider(
                    minimum=0.05,
                    maximum=1.0,
                    value=DEFAULT_TOLERANCE,
                    step=0.05,
                    label="허용 오차 / Tolerance",
            )
            analyze_button = gr.Button("점군 분석 / Analyze point group", variant="primary")
            xyz_output = gr.Textbox(label="생성된 XYZ / Generated XYZ", lines=8)
            gr.HTML(render_feedback_button())
        with gr.Column(scale=7):
            result_output = gr.HTML(label="점군 / Point group")
            detail_output = gr.Markdown()
            operation_picker = gr.Dropdown(
                choices=teaching_operation_choices(),
                label="현재 확인 중 / Now inspecting",
                value="추천 조작 / Best teaching operation",
            )
            operation_progress = gr.Slider(
                minimum=0,
                maximum=100,
                value=0,
                step=5,
                label="대칭 조작 진행률 / Symmetry operation progress (%)",
            )
            viewer_output = gr.HTML(label="3D 대칭 viewer / 3D symmetry viewer")

    example_picker.change(load_example, inputs=example_picker, outputs=molecule_input)
    analyze_button.click(
        reset_operation_progress,
        outputs=operation_progress,
    ).then(
        analyze,
        inputs=[molecule_input, tolerance, operation_picker, operation_progress, language_picker],
        outputs=[result_output, detail_output, viewer_output, xyz_output],
    )
    operation_picker.change(
        reset_operation_progress,
        outputs=operation_progress,
    ).then(
        analyze,
        inputs=[molecule_input, tolerance, operation_picker, operation_progress, language_picker],
        outputs=[result_output, detail_output, viewer_output, xyz_output],
    )
    operation_progress.change(
        analyze,
        inputs=[molecule_input, tolerance, operation_picker, operation_progress, language_picker],
        outputs=[result_output, detail_output, viewer_output, xyz_output],
    )
    operation_progress.input(
        analyze,
        inputs=[molecule_input, tolerance, operation_picker, operation_progress, language_picker],
        outputs=[result_output, detail_output, viewer_output, xyz_output],
    )
    language_picker.change(
        render_student_intro,
        inputs=language_picker,
        outputs=intro_output,
    )
    language_picker.change(
        analyze,
        inputs=[molecule_input, tolerance, operation_picker, operation_progress, language_picker],
        outputs=[result_output, detail_output, viewer_output, xyz_output],
    )
    demo.load(
        analyze,
        inputs=[molecule_input, tolerance, operation_picker, operation_progress, language_picker],
        outputs=[result_output, detail_output, viewer_output, xyz_output],
    )


if __name__ == "__main__":
    demo.launch()
