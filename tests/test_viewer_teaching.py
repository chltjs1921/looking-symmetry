from app.molecule import build_geometry
from app.symmetry import analyze_point_group
from app.viewer import _operation_demonstration, _overlay_profile, _viewer_frame, teaching_operation_choices


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
    assert "identical atoms" in demonstration["explanation"]
    assert len(demonstration["coords"]) == len(geometry.coords)


def test_operation_demonstration_defaults_to_korean():
    geometry = build_geometry("water")
    symmetry = analyze_point_group(geometry)
    profile = _overlay_profile(geometry.source, symmetry.point_group)

    demonstration = _operation_demonstration(geometry, symmetry, profile, "거울면 / Mirror plane")

    assert "거울면" in demonstration["explanation"]


def test_viewer_frame_prompts_one_operation_at_a_time():
    html = _viewer_frame(
        {"title": "Mirror plane", "explanation": "설명"},
        "<iframe></iframe>",
        "한국어",
    )

    assert "현재 확인 중" in html
    assert "하나씩 바꿔 볼 수 있습니다" in html
    assert "거울면" in html
