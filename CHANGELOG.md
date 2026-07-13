# Changelog

All notable changes to this extension are documented here. Versions follow
[Semantic Versioning](https://semver.org/).

## [1.0.0] - 2026-07-13

### Added
- Initial release as a standalone Spec Kit extension (`id: figma-images`).
- `/speckit.figma-images.specify <figma-url> [-o <module>]` command that runs the
  figma-images-to-spec pipeline (pull-screens → trace-flows → read-screens →
  write-spec) and hands off to core `/speckit.specify`.
- `before_specify` hook offering to generate Figma-derived specs.
- Bundled, standard-library-only `scripts/figma_pull.py` for REST screen and
  asset (icon/embedded-image) export — no `pip install`, `uv`, or external CLI.
