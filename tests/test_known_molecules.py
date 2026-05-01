from app.examples import EXAMPLE_MOLECULES
from app.molecule import build_geometry
from app.symmetry import analyze_point_group


def test_builtin_examples_have_expected_point_groups():
    for molecule in EXAMPLE_MOLECULES:
        geometry = build_geometry(molecule["aliases"][0])
        result = analyze_point_group(geometry)
        assert result.point_group == molecule["expected"], molecule["label"]


def test_new_linear_and_square_planar_aliases_resolve():
    examples = {
        "HCl": "Hydrogen chloride / HCl",
        "N2": "Nitrogen / N2",
        "C2H2": "Ethyne / C2H2",
        "XeF4": "Xenon tetrafluoride / XeF4",
    }
    for user_input, source in examples.items():
        geometry = build_geometry(user_input)
        assert geometry.source == source


def test_hcn_formula_uses_rdkit_smiles_pipeline():
    geometry = build_geometry("HCN")
    assert geometry.kind == "smiles"
    assert geometry.source == "HCN"
    assert sorted(geometry.species) == ["C", "H", "N"]
