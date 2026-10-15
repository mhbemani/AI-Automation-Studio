# Releasing

How a version of this project is cut. Only the creator publishes: nothing here is pushed, uploaded or tagged on the remote by an agent (see `docs/GIT_RULES.md`). There is no remote yet.

## Versioning
[Semantic Versioning](https://semver.org/): `MAJOR.MINOR.PATCH`, tags `vMAJOR.MINOR.PATCH` on `main` only.
- MAJOR: a change that breaks a documented path, command or file format.
- MINOR: new labs, assets, stages or features that keep everything existing working.
- PATCH: fixes and documentation only.

**The folder layout is part of the contract.** `docs/QUICKSTART.md` depends on `lab/tts`, `lab/ffmpeg` and `lab/integration` (models, scripts, the storyboard). Do not move or rename these folders (or the other `lab/` folders) in a MINOR or PATCH release; moving one is a MAJOR change and requires updating the quickstart in the same commit.

## Cutting a release
1. **Branch.** One task = one worktree branch; finish with `git merge --ff-only` into `main`, then delete the branch and the worktree.
2. **Check the tree.** `git status` is clean; the pre-commit hook is active (`git config core.hooksPath` prints `.githooks`); run the quickstart's commands on a fresh clone if the pipeline changed.
3. **Update `CHANGELOG.md`.** Move the entries of `## [Unreleased]` under a new heading `## [X.Y.Z] - YYYY-MM-DD`, leave an empty `## [Unreleased]` above it, group entries as Added / Changed / Deprecated / Removed / Fixed / Security.
4. **Update the state docs.** `docs/V1_MANIFEST.md` (or its successor) describes what the release contains and the known gaps; keep it in sync.
5. **Commit.** `release: vX.Y.Z` (plain message, no trailers).
6. **Tag.** `git tag -a vX.Y.Z -m "vX.Y.Z"`. Never move or delete a published tag; a mistake gets a new patch version.
7. **Build the asset zip** (only if there is something that may be zipped, see below).
8. **Publish.** Only when the creator says "push": show `git log --oneline origin/main..` and `git status`, then `git push` and `git push --tags`. The zip and its checksums are attached to the release page by the creator.

## The asset zip
Large or binary files never go into git (the hook blocks `.blend`, archives, audio and files over 5 MB). Redistributable binaries travel as a zip attached to the release.

**May be zipped:** `.blend` files that are entirely own-made, or whose third-party content is CC0 and listed in the lab's `ASSETS.md`; stills and sheets that are not in git; small clips (5 MB or less) for the README.

**Must not be zipped, ever:**
- anything containing BlenderKit (Royalty Free) models, even partly, even after editing;
- voice samples and trained voice models of the creator or friends;
- model weights (Kokoro, Whisper): they are downloaded by script;
- downloaded asset packs (CC0 or not): they are fetched by `fetch_assets.py`-style scripts;
- secrets, tokens, `.env*`, credentials; videos longer than a short preview (finished videos go to YouTube); audio.

**Provenance check before zipping a `.blend`:** read the lab's `ASSETS.md`, then check every object and material of the file for third-party origin. BlenderKit imports usually carry an `asset_data` custom property on their data blocks; a headless script that lists any datablock with `asset_data` (or `blenderkit` in a property name) is a quick first filter, but the `ASSETS.md` comparison decides. If in doubt, the file is blocked.

**Build and verify** (`dist/` is local and never committed):
```bash
mkdir -p dist/vX.Y.Z && cp <allowed files> dist/vX.Y.Z/
(cd dist && zip -r assets-vX.Y.Z.zip vX.Y.Z)
(cd dist && shasum -a 256 assets-vX.Y.Z.zip > SHA256SUMS && shasum -a 256 -c SHA256SUMS)
```
Unzip the result into a temporary folder and open the files once. The release notes list the file names, their licences and the SHA-256 value.

## Per-version asset table
Status: **OK** may be zipped, **BLOCKED** contains BlenderKit models and is never zipped, **HOLD** needs a review or a split first.

| Version | Zip | File | Contains BlenderKit models | Status |
|---|---|---|---|---|
| 1.0.0 | none: no file qualifies | `lab/animation-library/library_v1.blend` | yes: the human scan and the hero car | **BLOCKED** |
| 1.0.0 | | `lab/asset-lineup/lineup.blend` | yes: hero car, parked car, human scan | **BLOCKED** |
| 1.0.0 | | `lab/scene-realistic-car/scene.blend` | yes: hero car, parked car, human scan | **BLOCKED** |
| 1.0.0 | | `lab/animation-build/anim_work.blend` and snapshots | yes (copies of the above) | **BLOCKED** |
| 1.0.0 | | archived low-poly scene (`archive/scene-lowpoly-car-heavy.tar.gz`) | no (CC0 packs and own-made), but it is an archive that bundles downloaded packs | **HOLD** (packs are fetched by script) |
| future | possible `assets-v1.x.0.zip` | an own-made file with only Claude (armature, cushion, magic ring) and the phone, split out of the library | no, once split and checked | **HOLD** until it exists and passes the provenance check |

The BlenderKit assets (the human scan, the hero car, the parked car) are credited in `lab/scene-realistic-car/ASSETS.md`; their licence allows use in own videos but not redistribution of the models. A release therefore ships code, docs and reports only, plus the build instructions that let anyone with their own BlenderKit access recreate the scenes.

Add a row for every new `.blend` or zipped file in each release.

## History
This repository starts at `v1.0.0`. Earlier internal snapshots existed before the first release; they are not part of this repository.
