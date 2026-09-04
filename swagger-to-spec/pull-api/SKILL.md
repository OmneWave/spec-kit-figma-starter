---
name: swagger-pull-api
description: >-
  Step 1 of swagger-to-spec. Fetch an OpenAPI 3.x or Swagger 2.0 document and
  flatten it into .api-index.json — endpoints, entities, resources, and the
  Figma pages to bind against, ordered by build-order.md. Use when pulling a
  Swagger document or starting a Swagger-to-spec workflow.
disable-model-invocation: true
---

# Pull API

Fetch the API document and normalize it into one artifact every later step reads.

## Run

```bash
# Optional: load SWAGGER_TOKEN from .env if the document is behind auth.
[ -f .env ] && set -a && . ./.env && set +a

python3 .specify/extensions/figma-starter/scripts/swagger_pull.py pull "<swagger url or file>"
```

| Flag | Purpose |
|------|---------|
| `-m`, `--module <module>` | The module folder under `figma-starter/` to **read** the UI outputs from |
| `--out <folder>` | The folder under `figma-starter/` to **write** this run's output to (default: `api-specs`) |
| `--root <dir>` | Project root (defaults to the current directory) |
| `--header "Name: value"` | Extra request header; repeatable — use for `Authorization` |
| `--page <slug>` | Bind only this page; repeatable. Omit to bind every page |

## Output

```
figma-starter/
  <module>/              ← read only — the UI outputs this run binds against
  api-specs/             ← everything this pipeline writes (default name; --out renames it)
    .api-index.json
    01-specification-list/   ← page folders mirrored for the pages in scope
    02-create-specification/
```

Output does **not** go inside the module folder. `api-specs/` is its sibling, and the page folders for the pages in scope are created empty here so the later steps have somewhere to write.

The command prints endpoint/entity/resource counts, the resolved module, how many Figma pages it found, and the order it put them in.

## One output folder per module

`api-specs` is the default output folder, not the only one. `--out <folder>` renames it, still directly under `figma-starter/`.

**A project with more than one module needs one output folder per module.** The files at the top of the output root — `entities.md` and `api-catalog.md` — describe *the module that was run*, so a second module writing to the same folder overwrites them. The page folders would not collide (their slugs differ), which is worse rather than better: you would be left with one folder holding every module's pages under a catalog describing only the last run.

```bash
python3 .../swagger_pull.py pull "<doc>" -m storefront --out api-specs-storefront
python3 .../swagger_pull.py pull "<doc>" -m checkout  --out api-specs-checkout
```

Two rules the script enforces:

| Rule | Why |
|------|-----|
| `--out` is a single folder name — no `/`, no `..`, no leading dot | Every path recorded in `.api-index.json` stays project-root-relative and one level under `figma-starter/`, which is the shape every later step assumes |
| `--out` may not name a design module | The module folder is a read-only input; a run that overwrote it could not be run again |

**Later steps need no flag.** The output root is on the index as `paths.apiSpecs`, and every page's file path is on `figmaPages[].bindings` in full — read those rather than assembling `api-specs/…` by hand, and a renamed output folder works with no other change. Where the rest of these skills write `api-specs/`, they mean the default name.

An output folder is also never mistaken for a design module on a later run: the script discounts any folder holding an `.api-index.json`, so `-m` stays optional on a one-module project however many output folders sit beside it.

## Imported screens are a prerequisite

This pipeline binds endpoints to screens, so it needs screens. The script **stops** when there are none — a missing module or a module with no page folder is a dead end, not a run that can produce something lesser:

| Situation | Message |
|-----------|---------|
| `figma-starter/` holds no module folder | Run `/speckit.figma-starter.import` first |
| The module exists but no page folder has a `spec.md` | Same — or `-m` names the wrong module |

Relay either to the user as-is. Do **not** hand-write page folders to get past it.

## Module resolution

The output folder is where the output goes; the module is where the **input** comes from. It must match the folder the Figma pipeline wrote. The script resolves it in this order:

1. `-m <module>` if given — **always pass this when you know the module.**
2. The single existing module folder under `figma-starter/`, if there is exactly one. This is why `-m` is optional on a one-module project. Output folders never count as modules — the default `api-specs/` by name, and any `--out` folder by the `.api-index.json` inside it — so a project stays unambiguous however many times you re-run, under however many names.

Both ambiguity and a wrong name stop the run, because neither can be guessed past:

| Situation | Script behaviour |
|-----------|------------------|
| No `-m`, and `figma-starter/` holds **more than one** module | **Stops** and lists them. Re-run with `-m <module>` |
| `-m` names a module that **does not exist** | **Stops**, suggesting the near miss (`Did you mean -m storefront?`) |

Check the printed module name against the intended one even when nothing warns.

## Page order comes from `build-order.md`

`figmaPages[]` is **not** in folder-name order. It is in the order `<module>/build-order.md` lays the pages out, which is the order the user journeys run — login before dashboard, list before create — and that is the order `bind-ui` walks them in. Binding in flow order is what lets a page state where its ids come from: the page before it in the list is usually the page that supplies them.

The join is the `WaveMaker page:` line each `spec.md` carries, matched against the `WaveMaker page` column of `build-order.md`. Each entry records what that resolved to:

| Key on `figmaPages[]` | Content |
|-----------------------|---------|
| `wavemakerPage` | The name from the page's `spec.md`, or `null` if it declares none |
| `buildStep` | Its step number in `build-order.md`, or `null` if the build order does not name it |

Pages with a `buildStep` come first, in step order; pages without one follow in folder order. Step 1 is usually shared partials with no page folder of their own, so the first page is normally step 2.

If the script prints `[WARN] no build-order.md`, the module was written by an older import or the file was deleted. The run continues in folder order — say so in the completion report, because folder order is a numbering, not a journey.

## Scope — one page or the whole module

`--page` narrows the run to a single screen, for redoing one page's bindings without touching the other nine. The script records the choice in `.api-index.json`:

| Key | Value |
|-----|-------|
| `scope` | `module` (every page) or `page` (`--page` was given) |
| `figmaPages[]` | **Only the pages in scope** — later steps walk this list, so they need no scope logic of their own. Each entry carries `spec` and `screens[]` to read from the module folder and `bindings` to write under `api-specs/`, all relative to the project root |
| `pagesAvailable[]` | Every page slug in the module, in scope or not, **in build order** |
| `paths` | `uiRoot` (the module folder to read), `apiSpecs` (the output root), `userStories`, `buildOrder` |

`--page` matches a folder name (`01-specification-list`), the slug without its number prefix (`specification-list`), or just the number (`1`). A value matching no page is an error listing the pages that do exist — the run stops rather than silently binding everything.

**`scope: page` limits what may be written.** `figmaPages[]` no longer describes the whole module, so any conclusion that depends on seeing every page is off limits:

- Write `api-specs/<NN>-<slug>/api-bindings.md` **only** for pages in `figmaPages[]` — the path is on each entry as `bindings`. Never touch another page's file.
- Do not mark an endpoint unused, at page or module level — the pages you did not walk may well call it. `pagesAvailable[]` tells you they exist.
- Nothing else in the module is rewritten — `entities.md` and the other pages' files stay as they are. See [write-api-spec](../write-api-spec/SKILL.md).

Narrowing the scope does **not** narrow the reading. `pagesAvailable[]` is still in build order and `user-stories.md` still describes the whole module, so a page-scoped run can and must place its page in the flow: which page precedes it, what that page hands over, and where its own actions lead. Bind it as the page at that point in the journey, not as an island.

## What gets normalized

Both OpenAPI 3.x and Swagger 2.0 flatten into the same shape, so no later step needs to know which flavor the document used.

| Source construct | Normalized to |
|------------------|---------------|
| `components.schemas` / `definitions` | `entities[]` |
| `allOf` chains | Merged into one flat field list |
| `$ref` | `entity` name on the field or payload |
| `requestBody.content` / `in: body` parameter | `requestBody` |
| Path-level + operation-level `parameters` | One merged `parameters[]` |
| `servers` / `host` + `basePath` + `schemes` | `servers[]` |
| `Page<T>`, `content`/`items`/`data`/`results` envelopes | Unwrapped — `primaryEntity` is `T`, `collection` is `true` |
| Untyped envelope payload (`Object`, `Map`, `Any`) | Replaced by the resource's entity, with `entityInferred: true` |
| `tags[0]` when every operation is tagged, else the path | `resource` |

Tags and paths are never mixed as grouping signals — a half-tagged document would split one resource across both spellings. When paths are used, leading segments shared by every path (a service prefix such as `/loancorp/`) are skipped, so `/loancorp/Loan` groups under `Loan`.

**`entityInferred` matters downstream.** Where a document types every list endpoint as `Object`, the entity on those endpoints is this tool's inference from the resource name, not something the document says. Carry that distinction into the specs.

## Failure modes

| Symptom | Cause and fix |
|---------|---------------|
| `not JSON and PyYAML is not installed` | Point at the JSON form of the document, or `pip install pyyaml` |
| `HTTP 401/403` | Pass `--header "Authorization: Bearer <token>"` or set `SWAGGER_TOKEN` |
| `has no 'paths' object` | The URL returned a UI page, not the document — use the raw `/v3/api-docs` style path |
| `--page <x> matched no page` | Wrong slug, or the wrong module — the message lists the pages that exist; pick one of those |
| `figma-starter/ holds N modules and no -m` | Ambiguous target — pass `-m <module>`; do not let it guess |
| `-m <x> names no module` | A typo in `-m`; re-run with the name the message suggests |
| `--out <x> is not a folder name` | `--out` takes one folder name to create under `figma-starter/`, not a path — no `/`, no `..`, no leading dot |
| `--out <x> is a design module` | That name is a module folder, which is a read-only input. Pick an output name of its own, such as `--out api-specs-<x>` |
| `figma-starter/ holds no module folder` | The Figma import has not run. `/speckit.figma-starter.import` first — there are no screens to bind to |
| `<module>/ holds no page folder with a spec.md` | Either the same, or `-m` names a folder that is not the design module |
| `[WARN] no build-order.md` | Written by an older import, or the file was deleted. Pages fall back to folder order — report it, since folder order is a numbering, not a journey |
| `[WARN] output from the previous layout is still present` | The project has output from before API specs moved to `api-specs/` — a `<module>/api/` folder, or `api-bindings.md` files beside the page specs. Nothing reads them now. Name them to the user as stale copies to delete; do not delete them yourself, and do not read them as input |

Stop and report these to the user. There is no fallback source for the API document — do **not** substitute a guessed schema.

The failures above leave **no folder behind**: the output folder is created only once the run is certain to produce an index, so a rejected `--page` or an unreadable document cannot litter `figma-starter/` with empty folders.

## Done when

- `.api-index.json` exists under the output folder (`figma-starter/api-specs/` unless `--out` said otherwise), and a mirror folder exists for each page in scope
- On a project with several modules, `--out` gave this run an output folder of its own, so it did not overwrite another module's `entities.md` and `api-catalog.md`
- Nothing was written inside `figma-starter/<module>/`
- The printed module name matches the intended module, and no `[WARN]` about a previous layout or a missing `build-order.md` went unaddressed
- `figmaPages[]` is in build order, and each entry's `buildStep` resolved — a page with `buildStep: null` is one `build-order.md` does not name, and it is worth knowing which
- `scope` and `figmaPages[]` list exactly the pages this run should write

**Then:** continue to [derive-entities](../derive-entities/SKILL.md).
