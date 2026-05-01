from app.examples import resolve_example
from app.app import render_decision_tree, render_result_panel
from app.molecule import normalize_input, parse_xyz
from app.symmetry import decision_path, infer_symmetry_elements


def test_resolves_common_formula_to_example_xyz():
    normalized, kind, source = normalize_input("H2O")
    assert normalized.startswith("3\nwater")
    assert kind == "xyz"
    assert source == "Water / H2O"


def test_resolves_formula_to_example_xyz():
    normalized, kind, source = normalize_input("C6H6")
    assert normalized.startswith("12\nbenzene")
    assert kind == "xyz"
    assert source == "Benzene / C6H6"


def test_small_formula_maps_to_smiles_pipeline():
    normalized, kind, source = normalize_input("HCN")
    assert normalized == "C#N"
    assert kind == "smiles"
    assert source == "HCN"


def test_parse_xyz_with_count_and_comment():
    geometry = parse_xyz(
        """3
water
O 0 0 0
H 0.76 0.58 0
H -0.76 0.58 0
"""
    )
    assert geometry.species == ["O", "H", "H"]
    assert len(geometry.coords) == 3


def test_infers_elements_for_c2v():
    elements = infer_symmetry_elements("C2v")
    codes = [element.code for element in elements]
    assert "E" in codes
    assert "C2" in codes
    assert "sigma" in codes


def test_example_alias_lookup_is_case_insensitive():
    assert resolve_example("cH4")["input"] == "C"


def test_decision_path_for_water_group_is_student_readable():
    decisions = decision_path("C2v")
    assert decisions[0].question == "Is the molecule linear?"
    assert [decision.answer for decision in decisions][-1] == "C2v"


def test_decision_tree_renders_as_html():
    class Result:
        point_group = "C2v"
        decisions = decision_path("C2v")

    html = render_decision_tree(Result(), "English")
    assert "Full decision tree" in html
    assert "tree-item" in html
    assert "Is the molecule linear?" in html
    assert "Dinfh" in html


def test_result_panel_contains_clickable_decision_tree_modal():
    class Result:
        point_group = "C2v"
        decisions = decision_path("C2v")

    class Geometry:
        source = "Water / H2O"

    html = render_result_panel(Result(), Geometry(), "English")
    assert "point-group-trigger" in html
    assert "pg-modal-panel" in html
    assert "Full decision tree" in html


def test_result_panel_defaults_to_korean_copy():
    class Result:
        point_group = "C2v"
        decisions = decision_path("C2v")

    class Geometry:
        source = "Water / H2O"

    html = render_result_panel(Result(), Geometry())
    assert "점군" in html
    assert "전체 결정 트리" in html
    assert "분자가 선형인가?" in html
    assert "예" in html
