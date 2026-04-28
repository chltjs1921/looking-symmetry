# Looking Symmetry

분자 점군과 대칭 조작을 3D로 직관적으로 확인해 보는 학습용 프로토타입입니다. 학생 피드백을 받기 위한 버전이며, 완성된 교재나 정밀 분석 도구가 아닙니다.

Looking Symmetry is a prototype teaching app for molecular point groups. It classifies a molecule, then shows a 3D before/after comparison so students can judge whether a rotation, reflection, or inversion really leaves the molecule unchanged.

## 학생 테스트 안내

앱을 처음 열면 직접 분자를 입력하기보다 내장 예시부터 사용해 주세요.

1. `Water / H2O`, `Ammonia / NH3`, `Carbon dioxide / CO2`, `Benzene / C6H6` 중 하나를 고릅니다.
2. viewer에서 왼쪽 원래 분자와 오른쪽 대칭 조작 후 분자를 비교합니다.
3. `Viewer 조작 / Viewer operation`을 바꿔 회전, 거울면, 반전 중심을 확인합니다.
4. 조작 후에도 원자 배열이 같아 보이는지 판단합니다.

피드백으로 알고 싶은 점:

- 어떤 조작이 가장 직관적이었나요?
- 어떤 조작이 가장 헷갈렸나요?
- 왼쪽/오른쪽 비교가 점군을 납득하는 데 도움이 되었나요?
- 축, 거울면, 반전 중심 표시가 명확했나요?
- 먼저 개선해야 할 예시 분자는 무엇인가요?

## Deployment

Recommended public demo setup:

1. Push this repository to GitHub.
2. Create a Hugging Face Space.
3. Choose `Gradio` as the Space SDK.
4. Upload or sync this repository.
5. Hugging Face Spaces will use the root [app.py](app.py) entry point and [requirements.txt](requirements.txt).

After deployment, share the Hugging Face Space URL with students. They should not need Python, Git, or local installation.

## What It Does

- Accepts built-in molecule names/formulas, SMILES strings, or XYZ coordinates.
- Generates 3D coordinates from SMILES with RDKit.
- Classifies the molecular point group with `pymatgen.symmetry.analyzer.PointGroupAnalyzer`.
- Renders the molecule with `py3Dmol`.
- Shows symmetry operations as a before/after 3D comparison.
- Opens the full point-group decision tree from the point-group badge.
- Supports Korean and English UI text.

## Run Locally

```powershell
python -m venv learning-symmerty
.\learning-symmerty\Scripts\Activate.ps1
pip install -r requirements.txt
python -m app.app
```

Then open the local Gradio URL printed in the terminal.

On this development machine, you can also run:

```powershell
.\run_app.bat
```

## Inputs

Built-in examples work by name or formula:

`water`, `H2O`, `ammonia`, `NH3`, `methane`, `CH4`, `benzene`, `C6H6`, `BF3`, `CO2`, `SF6`, `HCl`, `N2`, `C2H2`, `CH2O`, `PCl5`, `XeF4`

For molecules outside the built-in examples, enter a SMILES string:

```text
c1ccccc1
```

XYZ input is also accepted:

```text
3
water
O 0.000 0.000 0.000
H 0.760 0.580 0.000
H -0.760 0.580 0.000
```

## Tests

```powershell
.\learning-symmerty\Scripts\python.exe -m pytest
```

## Notes

SMILES inputs use RDKit ETKDG coordinates, so approximate geometries can make point groups appear lower than the ideal textbook group. For serious checks, use optimized or experimental XYZ coordinates and adjust the tolerance slider.

The viewer currently emphasizes intuition over mathematical completeness. Some high-symmetry groups have many valid axes and planes; the app shows representative operations for teaching.
