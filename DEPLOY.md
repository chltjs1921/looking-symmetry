# Deployment Notes

Use this checklist when publishing updates to GitHub and the Hugging Face Space.

## Remotes

- GitHub: `origin` -> `https://github.com/chltjs1921/looking-symmetry.git`
- Hugging Face Space: `space` -> `https://huggingface.co/spaces/Eunwoo-Choi/looking-symmetry`

## Important Branch Detail

This local repository works on `master`.

The Hugging Face Space deploys from `main`.

Therefore, push with:

```powershell
git push origin master
git push space master:main
```

Pushing only `git push space master` creates or updates the Space's `master` branch, but it may not update the deployed app.

## Manual Checklist

```powershell
python -m pytest
git status --short
git add README.md DEPLOY.md deploy.ps1 app tests
git commit -m "Describe the update"
git push origin master
git push space master:main
git ls-remote --heads space
```

After pushing to Hugging Face, wait for the Space to rebuild. It can take from several seconds to a few minutes.
