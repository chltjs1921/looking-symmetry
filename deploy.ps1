$ErrorActionPreference = "Stop"

python -m pytest
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

git status --short

git push origin master
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

# Hugging Face Spaces deploys this app from main, while this local repo uses master.
git push space master:main
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

git ls-remote --heads space
