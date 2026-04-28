from __future__ import annotations

from dataclasses import dataclass
import re

from .molecule import MolecularGeometry


@dataclass(frozen=True)
class SymmetryElement:
    code: str
    label: str
    explanation: str


@dataclass(frozen=True)
class DecisionQuestion:
    question: str
    answer: str
    meaning: str


@dataclass(frozen=True)
class SymmetryResult:
    point_group: str
    operation_count: int | None
    elements: list[SymmetryElement]
    decisions: list[DecisionQuestion]
    note: str


POINT_GROUP_GUIDES = {
    "C1": "No symmetry beyond doing nothing. This is the lowest-symmetry case.",
    "Cs": "One mirror plane, but no useful rotation axis.",
    "Ci": "One inversion center, but no mirror plane or proper rotation axis.",
    "C2v": "A C2 axis plus vertical mirror planes. Water is the standard example.",
    "C3v": "A C3 axis plus vertical mirror planes. Ammonia is the standard example.",
    "D2h": "Three perpendicular C2 axes, mirror planes, and an inversion center.",
    "D3h": "A C3 axis, three C2 axes, and a horizontal mirror plane.",
    "D4h": "A C4 axis, perpendicular C2 axes, mirror planes, and an inversion center.",
    "D6h": "A C6 axis, perpendicular C2 axes, mirror planes, and an inversion center.",
    "Dinfh": "Linear molecule with an inversion center, like CO2.",
    "Cinfv": "Linear molecule without an inversion center, like HCl.",
    "Td": "Tetrahedral symmetry. Several equivalent C3 axes are present.",
    "Oh": "Octahedral or cubic symmetry. Several equivalent C4, C3, and C2 axes are present.",
}


def analyze_point_group(geometry: MolecularGeometry, tolerance: float = 0.3) -> SymmetryResult:
    try:
        from pymatgen.core.structure import Molecule
        from pymatgen.symmetry.analyzer import PointGroupAnalyzer
    except ImportError as exc:
        raise RuntimeError(
            "pymatgen is required for point group analysis. "
            "Run `pip install -r requirements.txt` and try again."
        ) from exc

    molecule = Molecule(geometry.species, geometry.coords)
    analyzer = PointGroupAnalyzer(molecule, tolerance=tolerance)
    point_group = normalize_point_group_symbol(str(analyzer.sch_symbol))

    operation_count = None
    try:
        operation_count = len(analyzer.get_symmetry_operations())
    except Exception:
        operation_count = None

    return SymmetryResult(
        point_group=point_group,
        operation_count=operation_count,
        elements=infer_symmetry_elements(point_group),
        decisions=decision_path(point_group),
        note=(
            "For SMILES input, RDKit generates an approximate 3D structure. "
            "If the result looks lower than the textbook group, use an ideal or optimized XYZ structure "
            "and adjust the tolerance."
        ),
    )


def point_group_guide(point_group: str) -> str:
    return POINT_GROUP_GUIDES.get(
        point_group,
        "Read the visible elements from the list below: identity, rotation axes, mirror planes, inversion centers, and improper axes.",
    )


def normalize_point_group_symbol(symbol: str) -> str:
    cleaned = symbol.strip()
    if cleaned == "D*h":
        return "Dinfh"
    if cleaned == "C*v":
        return "Cinfv"
    return cleaned


def decision_path(point_group: str) -> list[DecisionQuestion]:
    paths = {
        "C1": [
            ("Is there any symmetry operation besides E?", "No", "No rotation axis, mirror plane, or inversion center was detected."),
            ("Point group", "C1", "Only the identity operation remains."),
        ],
        "Cs": [
            ("Is there a proper rotation axis Cn?", "No", "No useful rotational symmetry was detected."),
            ("Is there a mirror plane sigma?", "Yes", "A reflection plane leaves the molecule unchanged."),
            ("Point group", "Cs", "One mirror plane and no proper rotation axis gives Cs."),
        ],
        "Ci": [
            ("Is there a proper rotation axis Cn?", "No", "No useful rotational symmetry was detected."),
            ("Is there a mirror plane sigma?", "No", "No reflection plane was detected."),
            ("Is there an inversion center i?", "Yes", "Each atom maps through the center to an identical atom."),
            ("Point group", "Ci", "Only E and i gives Ci."),
        ],
        "C2v": [
            ("Is the molecule linear?", "No", "Use the nonlinear branch of the decision tree."),
            ("What is the highest-order rotation axis?", "C2", "A 180 degree rotation leaves the molecule unchanged."),
            ("Are there C2 axes perpendicular to the principal axis?", "No", "So this is a C group, not a D group."),
            ("Are there mirror planes containing the principal axis?", "Yes", "Vertical mirror planes are present."),
            ("Point group", "C2v", "Cn plus vertical mirror planes gives Cnv."),
        ],
        "C3v": [
            ("Is the molecule linear?", "No", "Use the nonlinear branch of the decision tree."),
            ("What is the highest-order rotation axis?", "C3", "A 120 degree rotation leaves the molecule unchanged."),
            ("Are there C2 axes perpendicular to the principal axis?", "No", "So this is a C group, not a D group."),
            ("Are there mirror planes containing the principal axis?", "Yes", "Vertical mirror planes are present."),
            ("Point group", "C3v", "Cn plus vertical mirror planes gives Cnv."),
        ],
        "D2h": [
            ("Is the molecule linear?", "No", "Use the nonlinear branch of the decision tree."),
            ("What is the highest-order rotation axis?", "C2", "A 180 degree principal rotation is present."),
            ("Are there C2 axes perpendicular to the principal axis?", "Yes", "That moves the molecule into the D family."),
            ("Is there a mirror plane perpendicular to the principal axis?", "Yes", "A horizontal mirror plane is present."),
            ("Point group", "D2h", "Dn plus sigma_h gives Dnh."),
        ],
        "D3h": [
            ("Is the molecule linear?", "No", "Use the nonlinear branch of the decision tree."),
            ("What is the highest-order rotation axis?", "C3", "A 120 degree principal rotation is present."),
            ("Are there C2 axes perpendicular to the principal axis?", "Yes", "That moves the molecule into the D family."),
            ("Is there a mirror plane perpendicular to the principal axis?", "Yes", "A horizontal mirror plane is present."),
            ("Point group", "D3h", "Dn plus sigma_h gives Dnh."),
        ],
        "D4h": [
            ("Is the molecule linear?", "No", "Use the nonlinear branch of the decision tree."),
            ("What is the highest-order rotation axis?", "C4", "A 90 degree principal rotation is present."),
            ("Are there C2 axes perpendicular to the principal axis?", "Yes", "That moves the molecule into the D family."),
            ("Is there a mirror plane perpendicular to the principal axis?", "Yes", "For square planar molecules this is the molecular plane."),
            ("Point group", "D4h", "Dn plus sigma_h gives Dnh."),
        ],
        "D6h": [
            ("Is the molecule linear?", "No", "Use the nonlinear branch of the decision tree."),
            ("What is the highest-order rotation axis?", "C6", "A 60 degree rotation around the main axis leaves the molecule unchanged."),
            ("Are there C2 axes perpendicular to the principal axis?", "Yes", "That moves the molecule into the D family."),
            ("Is there a mirror plane perpendicular to the principal axis?", "Yes", "For benzene this is the molecular plane."),
            ("Point group", "D6h", "Dn plus sigma_h gives Dnh."),
        ],
        "Dinfh": [
            ("Is the molecule linear?", "Yes", "Linear molecules use the infinite-axis branch."),
            ("Are the two ends symmetry-equivalent or is there an inversion center?", "Yes", "CO2 has an inversion center at carbon."),
            ("Point group", "Dinfh", "Linear molecule with inversion symmetry gives Dinfh."),
        ],
        "Cinfv": [
            ("Is the molecule linear?", "Yes", "Linear molecules use the infinite-axis branch."),
            ("Are the two ends symmetry-equivalent or is there an inversion center?", "No", "Heteronuclear linear molecules usually lack inversion symmetry."),
            ("Point group", "Cinfv", "Linear molecule without inversion symmetry gives Cinfv."),
        ],
        "Td": [
            ("Is this a special high-symmetry shape?", "Yes", "Tetrahedral molecules skip the ordinary C/D branch."),
            ("Are there four equivalent C3 axes?", "Yes", "Each axis passes through one vertex and the opposite face center."),
            ("Is there an inversion center?", "No", "Tetrahedral molecules do not have a center of inversion."),
            ("Point group", "Td", "Tetrahedral symmetry gives Td."),
        ],
        "Oh": [
            ("Is this a special high-symmetry shape?", "Yes", "Octahedral molecules skip the ordinary C/D branch."),
            ("Are there three equivalent C4 axes?", "Yes", "The x, y, and z directions are equivalent."),
            ("Is there an inversion center?", "Yes", "Opposite atoms map through the central atom."),
            ("Point group", "Oh", "Octahedral symmetry gives Oh."),
        ],
    }
    fallback = [
        ("Is the molecule linear?", "Check", "Linear molecules go to Cinfv or Dinfh."),
        ("Find the highest-order rotation axis Cn.", "Check", "This is the principal axis."),
        ("Look for perpendicular C2 axes.", "Check", "If present, the group is usually in the D family."),
        ("Look for mirror planes and inversion centers.", "Check", "These suffixes distinguish h, v, d, i, and related groups."),
        ("Point group", point_group, "The computed point group is shown above."),
    ]
    return [DecisionQuestion(*item) for item in paths.get(point_group, fallback)]


def infer_symmetry_elements(point_group: str) -> list[SymmetryElement]:
    symbol = point_group.replace("_", "").replace(" ", "")
    elements = [
        SymmetryElement(
            "E",
            "E: identity",
            "The molecule is left unchanged. Every molecule has this operation.",
        )
    ]

    if symbol in {"Ci", "S2"}:
        elements.append(
            SymmetryElement(
                "i",
                "i: inversion center",
                "Every atom maps to an identical atom through the center of the molecule.",
            )
        )
        return elements
    if symbol == "Cs":
        elements.append(
            SymmetryElement(
                "sigma",
                "sigma: mirror plane",
                "Reflection across this plane leaves the molecule unchanged.",
            )
        )
        return elements

    rotation = re.match(r"^([CDS])(\d+|inf)", symbol)
    if rotation:
        family, order = rotation.groups()
        if family == "S":
            elements.append(
                SymmetryElement(
                    f"S{order}",
                    f"S{order}: improper rotation axis",
                    "Rotate, then reflect through a plane perpendicular to the axis.",
                )
            )
        else:
            axis_name = f"C{order}" if order != "inf" else "Cinf"
            elements.append(
                SymmetryElement(
                    axis_name,
                    f"{axis_name}: principal rotation axis",
                    "Rotation around this axis leaves the molecule unchanged.",
                )
            )

    if symbol.startswith("D"):
        elements.append(
            SymmetryElement(
                "C2",
                "C2: secondary rotation axes",
                "D groups also have C2 axes perpendicular to the principal axis.",
            )
        )
    if symbol.endswith(("h", "v", "d")):
        elements.append(
            SymmetryElement(
                "sigma",
                "sigma: mirror plane",
                "Reflection across a plane leaves the molecule unchanged.",
            )
        )
    if symbol.endswith("h") or symbol in {"Oh", "Ih"}:
        elements.append(
            SymmetryElement(
                "i",
                "i: inversion center",
                "Each atom has a matching atom in the opposite direction through the center.",
            )
        )
    if symbol in {"Td", "Th", "Oh", "Ih", "T", "O", "I"}:
        elements.append(
            SymmetryElement(
                "high-order",
                "multiple equivalent rotation axes",
                "High-symmetry molecules have several axes of the same importance.",
            )
        )
    if symbol in {"Td", "Oh", "Ih"}:
        elements.append(
            SymmetryElement(
                "S_n",
                "S_n: improper rotation axes",
                "These combine rotation and reflection; they are easier to study after Cn and sigma are clear.",
            )
        )

    unique: dict[str, SymmetryElement] = {}
    for element in elements:
        unique.setdefault(element.code, element)
    return list(unique.values())
