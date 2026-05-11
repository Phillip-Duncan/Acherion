# Releasing and Publishing

This repository is configured for automated semantic versioning with
conventional commits, GitHub Releases, and trusted publishing to PyPI.

## Release model

Version bumps are determined from commit messages on `main` using
`python-semantic-release`.

- `feat:` triggers a minor release
- `fix:` and `perf:` trigger a patch release
- `!` or `BREAKING CHANGE:` triggers the next breaking release
- `docs:`, `refactor:`, `test:`, `chore:`, `ci:`, `style:`, and `build:` do not
	publish a new version on their own, but they can still appear in the
	changelog when they are included in a release triggered by another commit

While Acherion is still in `0.x`, the repository is configured with
`major_on_zero = false`, so breaking changes continue to advance the minor
version instead of jumping directly to `1.0.0`.

## Conventional commit workflow

GitHub Actions validates pull request titles with
`.github/workflows/conventional-pr.yml`.

That workflow validates the PR title only. It does not lint every commit in the
branch.

The intended workflow is:

1. open a pull request with a conventional title such as `feat: add scoped theme overrides`
2. merge with **Squash and merge** so the PR title becomes the commit message on `main`
3. let the release workflow evaluate that commit and decide whether a new version is needed

Direct pushes to `main` should also use conventional commit messages, otherwise
semantic-release may correctly decide that no release is required.
If you use merge commits or rebase merges, the final commit subjects on `main`
still need to be conventional or releases and changelog entries may be skipped.

## GitHub Actions workflows

`.github/workflows/ci.yml` runs on pushes, pull requests, and manual dispatch.
It keeps the packaging path healthy by:

- installing the project with development dependencies
- byte-compiling the source tree
- running `pytest` when a `tests/` directory is present
- building sdist and wheel artifacts
- running `twine check` against built distributions

`.github/workflows/publish-pypi.yml` is now the release workflow. On pushes to
`main` it:

1. runs `python-semantic-release` to determine the next version
2. updates `pyproject.toml`
3. updates `CHANGELOG.md`
4. creates the release commit, tag, and GitHub Release
5. checks out the released tag
6. builds and verifies the distributions
7. publishes them to PyPI through GitHub OIDC trusted publishing

The workflow checks out the full branch history and tags before running
semantic-release so changelog generation can see the complete commit range.

This keeps version calculation, GitHub release creation, and PyPI publication in
one pipeline instead of relying on a second workflow triggered by a release event.

## PyPI trusted publisher setup

Before the workflow can publish, configure a trusted publisher in PyPI:

1. create the `acherion` project on PyPI if it does not already exist
2. open the project's publishing settings in PyPI
3. add a trusted publisher for this GitHub repository
4. set the workflow filename to `publish-pypi.yml`
5. set the environment name to `pypi`

The workflow already declares the `pypi` environment and requests the `id-token`
permission required for trusted publishing.

## GitHub repository setup

The release workflow pushes a release commit and tag back to the default branch.
If branch protection blocks GitHub Actions from pushing, either:

1. allow GitHub Actions to bypass that protection, or
2. replace `secrets.GITHUB_TOKEN` in the release workflow with a dedicated PAT that has `contents: write`

## Bootstrap the first automated release

Semantic-release works best when the repository already has a Git tag that
matches the current package version.

With the current configuration, you have two sane bootstrap choices:

1. if `0.1.0` is already the baseline you want to keep, create and push `v0.1.0` once before enabling automatic releases
2. if you want automation to determine the very first public version, reset `project.version` to `0.0.0` before the first release run

After that bootstrap step, version updates should be fully automatic.

## Local dry-run checks

Install development dependencies:

```bash
pip install -e ".[dev]"
```

Preview the next release without mutating anything:

```bash
semantic-release --noop version
```

Validate the packaging path locally:

```bash
python -m build --sdist --wheel
python -m twine check dist/*
```

## Recommended release flow

1. merge conventional-commit pull requests into `main`
2. let GitHub Actions create the release commit, tag, changelog entry, and GitHub Release automatically
3. let the same workflow publish the built distributions to PyPI
4. verify the new version on GitHub Releases and PyPI