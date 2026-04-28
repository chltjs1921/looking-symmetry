WATER_XYZ = """3
water
O 0.000000 0.000000 0.000000
H 0.758602 0.504284 0.000000
H -0.758602 0.504284 0.000000
"""

AMMONIA_XYZ = """4
ammonia
N 0.000000 0.000000 0.116489
H 0.000000 0.939731 -0.271808
H 0.813831 -0.469866 -0.271808
H -0.813831 -0.469866 -0.271808
"""

CARBON_DIOXIDE_XYZ = """3
carbon dioxide
O -1.160000 0.000000 0.000000
C 0.000000 0.000000 0.000000
O 1.160000 0.000000 0.000000
"""

BENZENE_XYZ = """12
benzene
C 1.396000 0.000000 0.000000
C 0.698000 1.209000 0.000000
C -0.698000 1.209000 0.000000
C -1.396000 0.000000 0.000000
C -0.698000 -1.209000 0.000000
C 0.698000 -1.209000 0.000000
H 2.479000 0.000000 0.000000
H 1.240000 2.147000 0.000000
H -1.240000 2.147000 0.000000
H -2.479000 0.000000 0.000000
H -1.240000 -2.147000 0.000000
H 1.240000 -2.147000 0.000000
"""

BF3_XYZ = """4
boron trifluoride
B 0.000000 0.000000 0.000000
F 1.300000 0.000000 0.000000
F -0.650000 1.125833 0.000000
F -0.650000 -1.125833 0.000000
"""

ETHENE_XYZ = """6
ethene
C -0.670000 0.000000 0.000000
C 0.670000 0.000000 0.000000
H -1.230000 0.930000 0.000000
H -1.230000 -0.930000 0.000000
H 1.230000 0.930000 0.000000
H 1.230000 -0.930000 0.000000
"""

SF6_XYZ = """7
sulfur hexafluoride
S 0.000000 0.000000 0.000000
F 1.560000 0.000000 0.000000
F -1.560000 0.000000 0.000000
F 0.000000 1.560000 0.000000
F 0.000000 -1.560000 0.000000
F 0.000000 0.000000 1.560000
F 0.000000 0.000000 -1.560000
"""

HCL_XYZ = """2
hydrogen chloride
H 0.000000 0.000000 -0.640000
Cl 0.000000 0.000000 0.640000
"""

NITROGEN_XYZ = """2
nitrogen
N 0.000000 0.000000 -0.550000
N 0.000000 0.000000 0.550000
"""

ETHYNE_XYZ = """4
ethyne
H 0.000000 0.000000 -1.660000
C 0.000000 0.000000 -0.600000
C 0.000000 0.000000 0.600000
H 0.000000 0.000000 1.660000
"""

FORMALDEHYDE_XYZ = """4
formaldehyde
C 0.000000 0.000000 0.000000
O 1.210000 0.000000 0.000000
H -0.600000 0.940000 0.000000
H -0.600000 -0.940000 0.000000
"""

PCL5_XYZ = """6
phosphorus pentachloride
P 0.000000 0.000000 0.000000
Cl 0.000000 0.000000 2.000000
Cl 0.000000 0.000000 -2.000000
Cl 2.000000 0.000000 0.000000
Cl -1.000000 1.732000 0.000000
Cl -1.000000 -1.732000 0.000000
"""

XEF4_XYZ = """5
xenon tetrafluoride
Xe 0.000000 0.000000 0.000000
F 1.950000 0.000000 0.000000
F -1.950000 0.000000 0.000000
F 0.000000 1.950000 0.000000
F 0.000000 -1.950000 0.000000
"""

EXAMPLE_MOLECULES = [
    {
        "label": "Water / H2O",
        "aliases": ["water", "h2o"],
        "input": WATER_XYZ,
        "kind": "xyz",
        "expected": "C2v",
        "teaching": "Bent molecule. One C2 axis bisects the H-O-H angle, and two mirror planes contain that axis.",
    },
    {
        "label": "Ammonia / NH3",
        "aliases": ["ammonia", "nh3"],
        "input": AMMONIA_XYZ,
        "kind": "xyz",
        "expected": "C3v",
        "teaching": "Trigonal pyramidal molecule. The C3 axis passes through N and the center of the H3 triangle.",
    },
    {
        "label": "Methane / CH4",
        "aliases": ["methane", "ch4"],
        "input": "C",
        "kind": "smiles",
        "expected": "Td",
        "teaching": "Tetrahedral molecule. Several equivalent C3 and C2 axes make this a high-symmetry point group.",
    },
    {
        "label": "Carbon dioxide / CO2",
        "aliases": ["carbon dioxide", "co2"],
        "input": CARBON_DIOXIDE_XYZ,
        "kind": "xyz",
        "expected": "Dinfh",
        "teaching": "Linear molecule. The molecular line is the principal axis and the center atom is an inversion center.",
    },
    {
        "label": "Benzene / C6H6",
        "aliases": ["benzene", "c6h6"],
        "input": BENZENE_XYZ,
        "kind": "xyz",
        "expected": "D6h",
        "teaching": "Planar hexagon. The C6 axis is perpendicular to the ring, and the molecular plane is sigma_h.",
    },
    {
        "label": "Boron trifluoride / BF3",
        "aliases": ["boron trifluoride", "bf3"],
        "input": BF3_XYZ,
        "kind": "xyz",
        "expected": "D3h",
        "teaching": "Trigonal planar molecule. The C3 axis is perpendicular to the molecular plane.",
    },
    {
        "label": "Sulfur hexafluoride / SF6",
        "aliases": ["sulfur hexafluoride", "sf6"],
        "input": SF6_XYZ,
        "kind": "xyz",
        "expected": "Oh",
        "teaching": "Octahedral molecule. The x, y, and z directions are equivalent C4 axes.",
    },
    {
        "label": "Ethene / C2H4",
        "aliases": ["ethene", "ethylene", "c2h4"],
        "input": ETHENE_XYZ,
        "kind": "xyz",
        "expected": "D2h",
        "teaching": "Planar molecule. It has three mutually perpendicular C2 axes and a center of inversion.",
    },
    {
        "label": "Hydrogen chloride / HCl",
        "aliases": ["hydrogen chloride", "hcl"],
        "input": HCL_XYZ,
        "kind": "xyz",
        "expected": "Cinfv",
        "teaching": "Heteronuclear linear molecule. The ends are different, so there is no inversion center.",
    },
    {
        "label": "Nitrogen / N2",
        "aliases": ["nitrogen", "n2"],
        "input": NITROGEN_XYZ,
        "kind": "xyz",
        "expected": "Dinfh",
        "teaching": "Homonuclear linear molecule. The two ends are equivalent and the midpoint is an inversion center.",
    },
    {
        "label": "Ethyne / C2H2",
        "aliases": ["ethyne", "acetylene", "c2h2"],
        "input": ETHYNE_XYZ,
        "kind": "xyz",
        "expected": "Dinfh",
        "teaching": "Linear molecule with equivalent ends. The midpoint is an inversion center.",
    },
    {
        "label": "Formaldehyde / CH2O",
        "aliases": ["formaldehyde", "ch2o"],
        "input": FORMALDEHYDE_XYZ,
        "kind": "xyz",
        "expected": "C2v",
        "teaching": "Planar molecule. A C2 axis and two vertical mirror planes give C2v.",
    },
    {
        "label": "Phosphorus pentachloride / PCl5",
        "aliases": ["phosphorus pentachloride", "pcl5"],
        "input": PCL5_XYZ,
        "kind": "xyz",
        "expected": "D3h",
        "teaching": "Trigonal bipyramidal molecule. The equatorial plane is sigma_h.",
    },
    {
        "label": "Xenon tetrafluoride / XeF4",
        "aliases": ["xenon tetrafluoride", "xef4"],
        "input": XEF4_XYZ,
        "kind": "xyz",
        "expected": "D4h",
        "teaching": "Square planar molecule. A C4 axis, perpendicular C2 axes, and sigma_h give D4h.",
    },
]

_ALIASES = {
    alias.casefold(): molecule for molecule in EXAMPLE_MOLECULES for alias in molecule["aliases"]
}


def resolve_example(text: str) -> dict | None:
    return _ALIASES.get(text.strip().casefold())


def dropdown_choices() -> list[str]:
    return [molecule["label"] for molecule in EXAMPLE_MOLECULES]


def by_label(label: str) -> dict | None:
    return next((molecule for molecule in EXAMPLE_MOLECULES if molecule["label"] == label), None)


def teaching_note(source: str) -> str | None:
    molecule = by_label(source)
    return molecule["teaching"] if molecule else None
