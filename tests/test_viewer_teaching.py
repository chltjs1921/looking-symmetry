from app.molecule import build_geometry
from app.symmetry import analyze_point_group
from app.viewer import (
    _operation_demonstration,
    _overlay_profile,
    _split_viewer_panes,
    _viewer_frame,
    teaching_operation_choices,
)


def test_viewer_operation_choices_include_student_facing_operations():
    choices = teaching_operation_choices()
    joined = " ".join(choices)
    assert "Best teaching operation" in joined
    assert "Principal rotation" in joined
    assert "Mirror plane" in joined
    assert "Inversion center" in joined
    assert "추천 조작" in joined


def test_operation_demonstration_explains_mirror_plane_for_water():
    geometry = build_geometry("water")
    symmetry = analyze_point_group(geometry)
    profile = _overlay_profile(geometry.source, symmetry.point_group)

    demonstration = _operation_demonstration(geometry, symmetry, profile, "Mirror plane", "English")

    assert demonstration["title"] == "Mirror plane"
    assert "same atom pattern" not in demonstration["explanation"].casefold()
    assert "Correspondence lines" in demonstration["explanation"]
    assert "25%: mirror plane highlighted" in demonstration["steps"]
    assert "100%: reflected result emphasized" in demonstration["steps"]
    assert len(demonstration["coords"]) == len(geometry.coords)
    assert len(demonstration["final_coords"]) == len(geometry.coords)


def test_rotation_explanation_points_to_operation_progress_slider():
    geometry = build_geometry("water")
    symmetry = analyze_point_group(geometry)
    profile = _overlay_profile(geometry.source, symmetry.point_group)

    demonstration = _operation_demonstration(geometry, symmetry, profile, "Principal rotation", "English")

    assert "Use the progress slider" in demonstration["explanation"]
    assert "Dragging the left panel" not in demonstration["explanation"]


def test_operation_demonstration_defaults_to_korean():
    geometry = build_geometry("water")
    symmetry = analyze_point_group(geometry)
    profile = _overlay_profile(geometry.source, symmetry.point_group)

    demonstration = _operation_demonstration(geometry, symmetry, profile, "거울면 / Mirror plane")

    assert "거울면" in demonstration["explanation"]


def test_viewer_frame_points_to_operation_menu_above_viewer():
    html = _viewer_frame(
        {"title": "Mirror plane", "explanation": "설명"},
        "<iframe></iframe>",
        "한국어",
    )

    assert "viewer 위의 &#x27;현재 확인 중&#x27; 메뉴" in html
    assert "거울면" in html


def test_viewer_frame_supports_split_viewer_panes():
    html = _viewer_frame(
        {"title": "Mirror plane", "explanation": "Reflect across a plane.", "steps": []},
        "<div class='viewer-split'><iframe></iframe><iframe></iframe></div>",
        "English",
    )

    assert "viewer-split" in html
    assert "viewer-pane-active iframe{pointer-events:none;}" in html
    assert "viewer-pane-static iframe{pointer-events:none;}" in html


def test_viewer_frame_renders_teaching_steps_as_bullets():
    html = _viewer_frame(
        {
            "title": "Mirror plane",
            "explanation": "Reflect across a plane.",
            "steps": ["0%: original molecule", "25%: mirror plane highlighted"],
        },
        "<iframe></iframe>",
        "English",
    )

    assert "viewer-teaching-steps" in html
    assert "<li>0%: original molecule</li>" in html
    assert "<li>25%: mirror plane highlighted</li>" in html


def test_split_viewer_panes_use_readable_korean_labels():
    html = _split_viewer_panes("<iframe></iframe>", "<iframe></iframe>", "한국어", 0)

    assert "원래 분자" in html
    assert "조작 미리보기" in html
    assert "고정 보기" in html
    assert "진행률 0%" in html


def test_reflection_preview_progress_interpolates_between_start_and_end():
    geometry = build_geometry("water")
    symmetry = analyze_point_group(geometry)
    profile = _overlay_profile(geometry.source, symmetry.point_group)

    start = _operation_demonstration(geometry, symmetry, profile, "Mirror plane", "English", 0)
    halfway = _operation_demonstration(geometry, symmetry, profile, "Mirror plane", "English", 50)
    end = _operation_demonstration(geometry, symmetry, profile, "Mirror plane", "English", 100)

    assert start["coords"] == geometry.coords
    assert halfway["progress_percent"] == 50
    assert end["progress_percent"] == 100
    assert end["coords"] == end["final_coords"]
    for original, mid, final in zip(geometry.coords, halfway["coords"], end["final_coords"]):
        assert mid == tuple((original[index] + final[index]) / 2 for index in range(3))


def test_inversion_preview_uses_center_correspondence_steps():
    geometry = build_geometry("benzene")
    symmetry = analyze_point_group(geometry)
    profile = _overlay_profile(geometry.source, symmetry.point_group)

    halfway = _operation_demonstration(geometry, symmetry, profile, "Inversion center", "English", 50)
    end = _operation_demonstration(geometry, symmetry, profile, "Inversion center", "English", 100)

    assert halfway["kind"] == "inversion"
    assert "same midpoint" in halfway["explanation"]
    assert "25%: inversion center highlighted" in halfway["steps"]
    assert "100%: inverted result emphasized" in halfway["steps"]
    assert end["coords"] == end["final_coords"]


def test_unavailable_operation_does_not_fallback_to_rotation():
    geometry = build_geometry("water")
    symmetry = analyze_point_group(geometry)
    profile = _overlay_profile(geometry.source, symmetry.point_group)

    demonstration = _operation_demonstration(geometry, symmetry, profile, "Inversion center", "English", 100)

    assert demonstration["kind"] == "unavailable"
    assert demonstration["title"] == "Inversion center"
    assert "does not include Inversion center" in demonstration["explanation"]
    assert "Rotate the left molecule" not in demonstration["explanation"]
    assert demonstration["coords"] == geometry.coords


def test_missing_progress_defaults_to_start_preview():
    geometry = build_geometry("water")
    symmetry = analyze_point_group(geometry)
    profile = _overlay_profile(geometry.source, symmetry.point_group)

    demonstration = _operation_demonstration(geometry, symmetry, profile, "Mirror plane", "English", None)

    assert demonstration["progress_percent"] == 0
