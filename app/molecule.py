from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .examples import resolve_example

InputKind = Literal["smiles", "xyz"]


@dataclass(frozen=True)
class MolecularGeometry:
    species: list[str]
    coords: list[tuple[float, float, float]]
    source: str
    kind: InputKind

    def to_xyz(self) -> str:
        lines = [str(len(self.species)), self.source]
        lines.extend(
            f"{element} {x:.8f} {y:.8f} {z:.8f}"
            for element, (x, y, z) in zip(self.species, self.coords)
        )
        return "\n".join(lines)


def normalize_input(raw_input: str) -> tuple[str, InputKind, str]:
    text = raw_input.strip()
    if not text:
        raise ValueError("Enter a molecule name, formula, SMILES string, or XYZ coordinates.")

    example = resolve_example(text)
    if example:
        return example["input"], example["kind"], example["label"]

    if _looks_like_xyz(text):
        return text, "xyz", "XYZ input"

    return text, "smiles", text


def build_geometry(raw_input: str) -> MolecularGeometry:
    normalized, kind, source = normalize_input(raw_input)
    if kind == "xyz":
        return parse_xyz(normalized, source)
    return smiles_to_geometry(normalized, source)


def _looks_like_xyz(text: str) -> bool:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) < 3:
        return False
    if lines[0].isdigit():
        return True
    return _line_has_atom_and_xyz(lines[0])


def _line_has_atom_and_xyz(line: str) -> bool:
    parts = line.split()
    if len(parts) < 4:
        return False
    try:
        float(parts[1])
        float(parts[2])
        float(parts[3])
    except ValueError:
        return False
    return parts[0][0].isalpha()


def parse_xyz(text: str, source: str = "XYZ input") -> MolecularGeometry:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        raise ValueError("XYZ input is empty.")

    if lines[0].isdigit():
        atom_count = int(lines[0])
        atom_lines = lines[2:] if len(lines) >= atom_count + 2 else lines[1:]
    else:
        atom_count = len(lines)
        atom_lines = lines

    species: list[str] = []
    coords: list[tuple[float, float, float]] = []
    for line in atom_lines[:atom_count]:
        parts = line.split()
        if len(parts) < 4:
            raise ValueError(f"Could not parse XYZ atom line: {line}")
        try:
            xyz = (float(parts[1]), float(parts[2]), float(parts[3]))
        except ValueError as exc:
            raise ValueError(f"XYZ coordinates must be numbers: {line}") from exc
        species.append(parts[0])
        coords.append(xyz)

    if len(species) != atom_count:
        raise ValueError(f"XYZ atom count mismatch. Expected {atom_count}, found {len(species)}.")
    return MolecularGeometry(species=species, coords=coords, source=source, kind="xyz")


def smiles_to_geometry(smiles: str, source: str) -> MolecularGeometry:
    try:
        from rdkit import Chem
        from rdkit.Chem import AllChem
    except ImportError as exc:
        raise RuntimeError(
            "RDKit is required to convert SMILES input into a 3D structure. "
            "Run `pip install -r requirements.txt` and try again."
        ) from exc

    molecule = Chem.MolFromSmiles(smiles)
    if molecule is None:
        raise ValueError(f"Could not interpret this as a SMILES string or built-in molecule name: {smiles}")

    molecule = Chem.AddHs(molecule)
    params = AllChem.ETKDGv3()
    params.randomSeed = 42
    status = AllChem.EmbedMolecule(molecule, params)
    if status != 0:
        raise ValueError("RDKit could not generate 3D coordinates. Try entering XYZ coordinates directly.")
    AllChem.UFFOptimizeMolecule(molecule, maxIters=500)

    conformer = molecule.GetConformer()
    species: list[str] = []
    coords: list[tuple[float, float, float]] = []
    for atom in molecule.GetAtoms():
        position = conformer.GetAtomPosition(atom.GetIdx())
        species.append(atom.GetSymbol())
        coords.append((position.x, position.y, position.z))

    return MolecularGeometry(species=species, coords=coords, source=source, kind="smiles")
