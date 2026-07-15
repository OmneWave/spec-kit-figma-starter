# Publishing this extension

Spec Kit's extension model (see the upstream `extensions/` docs) supports three
distribution paths. This extension is set up for all three.

## 1. Direct install from a GitHub release (primary path for users)

1. Set the real repo owner in `extension.yml` (`repository`, `homepage`) and in
   `README.md` (replace `YOUR-GITHUB-USERNAME`).
2. Tag and push a release:
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```
   Then create the GitHub release for that tag.
3. Users install with:
   ```bash
   specify extension add figma-starter \
     --from https://github.com/<owner>/figma-starter/archive/refs/tags/v1.0.0.zip
   ```

## 2. Community catalog (discovery)

File an **Extension Submission** issue on `github/spec-kit` (do **not** open a PR
to edit the catalog). A maintainer reviews metadata (not code) in ~3–7 business
days and lists it in `catalog.community.json`.

> The community catalog is **discovery-only** (`install_allowed: false`). Being
> listed makes the extension appear in `specify extension search`, but users
> still install via `--from <url>` (path 1) or by copying the catalog entry into
> their own `catalog.json`.

**Heads-up on the ID:** the community catalog already contains an extension with
`id: figma` (`Fyloss/spec-kit-figma`). This extension deliberately uses
`id: figma-starter` to avoid the collision. Keep it distinct.

## 3. Organization / private catalog (internal use — no public release)

If this should stay internal, host a `catalog.json` and point Spec Kit at it —
no need to open-source. Private GitHub repos work with a `GITHUB_TOKEN`.

```bash
specify extension catalog add \
  --name "internal" --install-allowed \
  https://your-org.example.com/spec-kit/catalog.json
```

## Pre-publish checklist

- [ ] `extension.yml` `repository`/`homepage` point at the real public repo
- [ ] `README.md` install URL updated (no `YOUR-GITHUB-USERNAME`)
- [ ] LICENSE holder is correct, and you have the right to open-source this work
- [ ] `speckit_version` floor verified against `specify version`
- [ ] Installed and run end-to-end on a real Spec Kit project (`--dev`)
- [ ] GitHub release tagged (`v1.0.0`)
