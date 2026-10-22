# Put the hybrid into your assigned repository

This is a complete project folder, not an incremental patch. Extract the ZIP first. Do not upload the ZIP itself or create an extra nested project directory inside the repository.

1. Back up your local work or commit it. Open a clean checkout of the assigned repository in VS Code.
2. Create a review branch:

```powershell
git switch main
git pull origin main
git switch -c feature/jalq-hybrid
```

3. Copy the CONTENTS of `JalQ-R_Hybrid` into the repository root (where README.md lives), replacing same-named application files. Preserve the repository's `.git` directory. Do not run `apply_final_fixes.py` on this hybrid: its corrections are already integrated or superseded.
4. Follow README setup and tests. Review `git diff`; confirm that old caches or temporary patch scripts are not being submitted.
5. Commit and push the review branch:

```powershell
git add .
git commit -m "feat: integrate budgeted JalQ-R hybrid and field-specific evaluation"
git push -u origin feature/jalq-hybrid
```

6. Open a pull request into the required submission branch, review it, then merge through your team workflow. Add the real video URL and submit the PPT/links through the organizer portal.

If tracked `.pyc` files exist in your checkout, remove those tracked cache files separately; `.gitignore` does not untrack existing files. Do not delete unrelated team work to match the archive.

This package does not push, merge, publish, record a video or submit a portal form automatically.

## Replacing an earlier package

After copying this package into an existing checkout, remove the four superseded root documents if they remain: `MEMBER1_README.md`, `MEMBER2_README.md`, `MEMBER3_README.md`, and `EXPERIMENTS_README.md`. Their content now lives in `docs/contributions/` and `docs/experiments.md`. Copying files alone does not remove old files. Review these document moves in your Git diff before committing.
