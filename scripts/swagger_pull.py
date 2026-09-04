#!/usr/bin/env python3
"""Self-contained OpenAPI/Swagger helper for the figma-starter Spec Kit extension.

Standard library only (urllib, json, re, argparse) — no pip install, no uv, no
external CLI. Ships inside the extension and is invoked by the pipeline skills:

    python3 swagger_pull.py pull "<swagger url or file>" [-m <module>] [--out <folder>]
                                 [--root <dir>] [--header "Name: value"]...

Reads an OpenAPI 3.x or Swagger 2.0 document, flattens it into one normalized
artifact, and writes it to:

    <root>/figma-starter/<out>/.api-index.json        # <out> defaults to api-specs

Every API-derived output lives under that one folder, a sibling of the module
folders rather than a folder inside one. The UI outputs written by
figma-images-to-spec (figma-starter/<module>/) are read-only inputs here: the
artifact records the pages found there, with project-root-relative paths to each
page's spec, screenshots, and the api-bindings.md that mirrors it under
api-specs/ — so the binding step knows what to read and where to write. Pages are
listed in build-order.md order, so the binding step walks them in the sequence the
user journeys run rather than in folder-name order.

--out renames that output folder. A project whose figma-starter/ holds several
modules needs one output folder per module, since the module-wide files at the
top of it — entities.md and api-catalog.md — describe the module that was run.
The folder stays one level under figma-starter/ whatever it is called, so every
recorded path is project-root-relative and one level deep, and a folder holding
an .api-index.json is never mistaken for a design module on a later run.

YAML documents require PyYAML; JSON documents need nothing. Most servers expose
JSON at /v3/api-docs, /v2/api-docs, /swagger.json or /openapi.json.
"""

from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

FIGMA_STARTER_DIR = "figma-starter"
# All API-derived output, kept apart from the design-derived module folders it mirrors.
API_SPECS_DIR = "api-specs"
BINDINGS_FILE = "api-bindings.md"
BUILD_ORDER_FILE = "build-order.md"
# Hidden: a generated intermediate the pipeline reads, not a deliverable anyone hand-edits.
INDEX_FILE = ".api-index.json"
LEGACY_INDEX_FILE = "api-index.json"

# Path segments that are transport scaffolding, not the resource being served.
PREFIX_SEGMENTS = {"api", "rest", "services", "service", "public", "internal"}
VERSION_SEGMENT = re.compile(r"^v\d+(\.\d+)*$", re.IGNORECASE)

# Tags are usually named after the class serving them, not the resource.
TAG_SUFFIX = re.compile(r"[-_ ]?(controller|resource|endpoint|api|service)s?$", re.IGNORECASE)

# Fields that carry the real payload inside a pagination / envelope wrapper.
WRAPPER_FIELDS = ("content", "items", "data", "results", "records", "elements")

# Payload types that carry no information — generators emit these for untyped envelopes.
GENERIC_ENTITIES = {"object", "any", "map", "hashmap", "json", "jsonnode", "serializable"}

JSON_CONTENT = ("application/json", "application/*+json", "text/json", "*/*")

HTTP_METHODS = ("get", "post", "put", "patch", "delete", "head", "options")


# --------------------------------------------------------------------------- #
# Loading the document
# --------------------------------------------------------------------------- #


def load_dotenv(root: Path) -> None:
    """Parse a simple KEY=VALUE .env at <root>/.env into os.environ."""
    env_path = root / ".env"
    if not env_path.is_file():
        return
    for line in env_path.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        key = key.strip()
        value = value.strip().strip("'\"")
        if key and key not in os.environ:
            os.environ[key] = value


def auth_headers(root: Path, extra: list[str]) -> dict[str, str]:
    """Build request headers from --header flags plus SWAGGER_TOKEN/API_TOKEN."""
    headers = {"Accept": "application/json, text/yaml, */*"}
    load_dotenv(root)
    token = os.environ.get("SWAGGER_TOKEN") or os.environ.get("API_TOKEN")
    if token:
        headers["Authorization"] = token if " " in token else f"Bearer {token}"
    for item in extra or []:
        name, sep, value = item.partition(":")
        if not sep:
            raise ValueError(f'Bad --header {item!r}; expected "Name: value"')
        headers[name.strip()] = value.strip()
    return headers


def fetch(source: str, headers: dict[str, str]) -> str:
    if not re.match(r"^https?://", source):
        path = Path(source).expanduser()
        if not path.is_file():
            raise ValueError(f"No such API document: {source}")
        return path.read_text()
    req = urllib.request.Request(source, headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            return response.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as err:
        raise ValueError(
            f"{source} returned HTTP {err.code}. "
            "If the endpoint needs auth, pass --header \"Authorization: Bearer <token>\" "
            "or set SWAGGER_TOKEN."
        ) from err
    except urllib.error.URLError as err:
        raise ValueError(f"Could not reach {source}: {err.reason}") from err


def parse_document(text: str, source: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    try:
        import yaml  # type: ignore
    except ImportError:
        raise ValueError(
            f"{source} is not JSON and PyYAML is not installed. Either point at the "
            "JSON form of the document (usually /v3/api-docs, /v2/api-docs, "
            "swagger.json or openapi.json) or run: pip install pyyaml"
        ) from None
    loaded = yaml.safe_load(text)
    if not isinstance(loaded, dict):
        raise ValueError(f"{source} did not parse into an object")
    return loaded


# --------------------------------------------------------------------------- #
# Schema helpers
# --------------------------------------------------------------------------- #


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-") or "api"


def ref_name(ref: str) -> str:
    """'#/components/schemas/Specification' -> 'Specification'."""
    return urllib.parse.unquote(ref.rsplit("/", 1)[-1])


def schema_ref(schema: dict | None) -> tuple[str | None, bool]:
    """Resolve a schema to (entity name, is_array), following arrays and compositions."""
    if not isinstance(schema, dict):
        return None, False
    if "$ref" in schema:
        return ref_name(schema["$ref"]), False
    if schema.get("type") == "array" or "items" in schema:
        name, _ = schema_ref(schema.get("items"))
        return name, True
    for key in ("allOf", "oneOf", "anyOf"):
        for member in schema.get(key) or []:
            name, is_array = schema_ref(member)
            if name:
                return name, is_array
    return None, False


def scalar_type(schema: dict) -> str:
    """Human-readable type for a non-$ref schema."""
    raw = schema.get("type")
    if isinstance(raw, list):
        raw = next((t for t in raw if t != "null"), None)
    if not raw and "properties" in schema:
        raw = "object"
    fmt = schema.get("format")
    if raw == "array":
        inner = schema.get("items") or {}
        name, _ = schema_ref(inner)
        return f"{name or scalar_type(inner)}[]" if (name or inner) else "array"
    if raw and fmt:
        return f"{raw}({fmt})"
    return raw or "any"


def merged_properties(schema: dict, schemas: dict, seen: set[str]) -> tuple[dict, list[str]]:
    """Flatten `properties` and `required` across allOf chains."""
    props: dict = {}
    required: list[str] = []
    for member in schema.get("allOf") or []:
        if "$ref" in member:
            name = ref_name(member["$ref"])
            if name in seen or name not in schemas:
                continue
            seen.add(name)
            sub_props, sub_required = merged_properties(schemas[name], schemas, seen)
        else:
            sub_props, sub_required = merged_properties(member, schemas, seen)
        props.update(sub_props)
        required.extend(sub_required)
    props.update(schema.get("properties") or {})
    required.extend(schema.get("required") or [])
    return props, required


def build_entity(name: str, schema: dict, schemas: dict) -> dict:
    props, required = merged_properties(schema, schemas, {name})
    fields = []
    for field_name, field_schema in props.items():
        if not isinstance(field_schema, dict):
            continue
        entity, is_array = schema_ref(field_schema)
        fields.append(
            {
                "name": field_name,
                "type": f"{entity}[]" if entity and is_array else (entity or scalar_type(field_schema)),
                "entity": entity,
                "array": is_array or field_schema.get("type") == "array",
                "required": field_name in required,
                "enum": field_schema.get("enum"),
                "description": (field_schema.get("description") or "").strip() or None,
            }
        )
    return {
        "name": name,
        "description": (schema.get("description") or "").strip() or None,
        "fields": fields,
        "usedBy": [],
    }


def unwrap_entity(name: str | None, entities: dict[str, dict], is_array: bool = False) -> tuple[str | None, bool]:
    """Follow envelope/pagination wrappers (Page<T>, ListResponse) to the payload entity.

    Returns the payload entity and whether it arrives as a collection — a wrapper
    such as `Page<T>` is a single object but still yields many `T`.
    """
    seen: set[str] = set()
    while name and name in entities and name not in seen:
        seen.add(name)
        payload = next(
            (f for f in entities[name]["fields"] if f["name"] in WRAPPER_FIELDS and f["entity"]),
            None,
        )
        if not payload:
            break
        is_array = is_array or payload["array"]
        name = payload["entity"]
    return name, is_array


# --------------------------------------------------------------------------- #
# Document normalization
# --------------------------------------------------------------------------- #


def spec_flavor(doc: dict) -> str:
    version = doc.get("openapi") or doc.get("swagger") or ""
    return f"openapi-{version}" if doc.get("openapi") else f"swagger-{version or '2.0'}"


def all_schemas(doc: dict) -> dict:
    if doc.get("openapi"):
        return (doc.get("components") or {}).get("schemas") or {}
    return doc.get("definitions") or {}


def server_urls(doc: dict) -> list[str]:
    if doc.get("openapi"):
        return [s.get("url", "") for s in doc.get("servers") or [] if s.get("url")]
    host = doc.get("host")
    base = doc.get("basePath", "")
    schemes = doc.get("schemes") or ["https"]
    return [f"{scheme}://{host}{base}" for scheme in schemes] if host else ([base] if base else [])


def path_tokens(path: str) -> list[str]:
    """Non-templated path segments, minus transport scaffolding like /api/v1."""
    return [
        segment
        for segment in path.split("/")
        if segment
        and not segment.startswith("{")
        and segment.lower() not in PREFIX_SEGMENTS
        and not VERSION_SEGMENT.match(segment)
    ]


def prefix_depth(token_lists: list[list[str]], limit: int = 3) -> int:
    """How many leading segments every path shares — a service prefix, not a resource.

    `/loancorp/Loan` and `/loancorp/Person` group by `Loan`/`Person`, not `loancorp`.
    Only strips a segment when *every* path has the same value there and something
    deeper to fall back to, so a genuine single-resource API keeps its name.
    """
    depth = 0
    while depth < limit:
        deeper = [t for t in token_lists if len(t) > depth + 1]
        if not deeper or len(deeper) != len(token_lists):
            break
        if len({t[depth] for t in deeper}) != 1:
            break
        depth += 1
    return depth


def refine_entity(
    name: str | None, resource: str, tags: list[str], entities: dict[str, dict]
) -> tuple[str | None, bool]:
    """Recover the payload type when the document declares an untyped one.

    Generators commonly emit a single generic envelope (`Page` with
    `content: Object[]`), which loses the element type for every list endpoint.
    Where the payload is that kind of dead end, the resource the endpoint belongs
    to names the entity instead. Returns the name and whether it was inferred, so
    the inference stays visible rather than passing as a documented fact.
    """
    if name is None:
        return None, False
    if name.lower() not in GENERIC_ENTITIES and entities.get(name, {}).get("fields"):
        return name, False
    candidates = [slug(TAG_SUFFIX.sub("", tags[0]))] if tags else []
    candidates.append(resource)
    for candidate in candidates:
        for entity_name, entity in entities.items():
            if slug(entity_name) == candidate and entity["fields"]:
                return entity_name, True
    return name, False


def resource_of(path: str, tags: list[str], depth: int = 0, use_tags: bool = False) -> str:
    """Group an endpoint by its authored tag, or by its path.

    The two signals are never mixed: a document where only some operations are
    tagged would split one resource across both spellings (`Specification` from a
    tag, `specifications` from a path), so tags are used only when every
    operation has one.
    """
    if use_tags and tags:
        name = slug(TAG_SUFFIX.sub("", tags[0]))
        if name and name != "api":
            return name
    tokens = path_tokens(path)
    return slug(tokens[depth]) if len(tokens) > depth else (slug(tokens[-1]) if tokens else "root")


def body_from_v3(operation: dict) -> dict | None:
    body = operation.get("requestBody")
    if not isinstance(body, dict):
        return None
    content = body.get("content") or {}
    media = next((c for c in JSON_CONTENT if c in content), next(iter(content), None))
    if media is None:
        return None
    entity, is_array = schema_ref((content[media] or {}).get("schema"))
    return {
        "entity": entity,
        "array": is_array,
        "contentType": media,
        "required": bool(body.get("required")),
    }


def body_from_v2(parameters: list[dict]) -> dict | None:
    body = next((p for p in parameters if p.get("in") == "body"), None)
    if not body:
        return None
    entity, is_array = schema_ref(body.get("schema"))
    return {
        "entity": entity,
        "array": is_array,
        "contentType": "application/json",
        "required": bool(body.get("required")),
    }


def responses_of(operation: dict, is_v3: bool) -> list[dict]:
    out = []
    for status, payload in (operation.get("responses") or {}).items():
        if not isinstance(payload, dict):
            continue
        if is_v3:
            content = payload.get("content") or {}
            media = next((c for c in JSON_CONTENT if c in content), next(iter(content), None))
            schema = (content.get(media) or {}).get("schema") if media else None
        else:
            schema = payload.get("schema")
        entity, is_array = schema_ref(schema)
        out.append(
            {
                "status": str(status),
                "entity": entity,
                "array": is_array,
                "description": (payload.get("description") or "").strip() or None,
            }
        )
    return sorted(out, key=lambda r: r["status"])


def parameters_of(raw: list, is_v3: bool) -> list[dict]:
    out = []
    for param in raw:
        if not isinstance(param, dict) or param.get("in") == "body":
            continue
        schema = param.get("schema") if is_v3 else param
        entity, is_array = schema_ref(schema if isinstance(schema, dict) else {})
        out.append(
            {
                "name": param.get("name", ""),
                "in": param.get("in", "query"),
                "required": bool(param.get("required")),
                "type": entity or scalar_type(schema if isinstance(schema, dict) else {}),
                "array": is_array,
                "enum": (schema or {}).get("enum") if isinstance(schema, dict) else None,
                "description": (param.get("description") or "").strip() or None,
            }
        )
    return out


def endpoint_id(method: str, path: str) -> str:
    return f"{method.lower()}-{slug(path)}"


def normalize(doc: dict) -> tuple[list[dict], list[dict]]:
    """Flatten a spec document into (endpoints, entities)."""
    is_v3 = bool(doc.get("openapi"))
    schemas = all_schemas(doc)
    entities = {name: build_entity(name, s, schemas) for name, s in schemas.items() if isinstance(s, dict)}

    paths = {p: i for p, i in (doc.get("paths") or {}).items() if isinstance(i, dict)}
    depth = prefix_depth([path_tokens(p) for p in paths])
    operations = [
        op
        for item in paths.values()
        for method, op in item.items()
        if method.lower() in HTTP_METHODS and isinstance(op, dict)
    ]
    use_tags = bool(operations) and all(op.get("tags") for op in operations)

    endpoints: list[dict] = []
    for path, item in paths.items():
        shared = [p for p in item.get("parameters") or [] if isinstance(p, dict)]
        for method, operation in item.items():
            if method.lower() not in HTTP_METHODS or not isinstance(operation, dict):
                continue
            raw_params = shared + [p for p in operation.get("parameters") or [] if isinstance(p, dict)]
            tags = [t for t in operation.get("tags") or [] if isinstance(t, str)]
            request_body = body_from_v3(operation) if is_v3 else body_from_v2(raw_params)
            responses = responses_of(operation, is_v3)

            success = next((r for r in responses if r["status"].startswith("2") and r["entity"]), None)
            if success:
                primary, collection = unwrap_entity(success["entity"], entities, success["array"])
            elif request_body:
                primary, collection = unwrap_entity(request_body["entity"], entities, request_body["array"])
            else:
                primary, collection = None, False

            resource = resource_of(path, tags, depth, use_tags)
            primary, inferred = refine_entity(primary, resource, tags, entities)

            endpoints.append(
                {
                    "id": endpoint_id(method, path),
                    "method": method.upper(),
                    "path": path,
                    "resource": resource,
                    "operationId": operation.get("operationId"),
                    "summary": (operation.get("summary") or "").strip() or None,
                    "description": (operation.get("description") or "").strip() or None,
                    "tags": tags,
                    "deprecated": bool(operation.get("deprecated")),
                    "parameters": parameters_of(raw_params, is_v3),
                    "requestBody": request_body,
                    "responses": responses,
                    "primaryEntity": primary,
                    "entityInferred": inferred,
                    "collection": collection,
                }
            )

    for endpoint in endpoints:
        referenced = {endpoint["primaryEntity"]}
        if endpoint["requestBody"]:
            referenced.add(endpoint["requestBody"]["entity"])
        referenced.update(r["entity"] for r in endpoint["responses"])
        for name in referenced:
            if name in entities and endpoint["id"] not in entities[name]["usedBy"]:
                entities[name]["usedBy"].append(endpoint["id"])

    endpoints.sort(key=lambda e: (e["resource"], e["path"], e["method"]))
    return endpoints, list(entities.values())


def group_resources(endpoints: list[dict]) -> list[dict]:
    order: list[str] = []
    for endpoint in endpoints:
        if endpoint["resource"] not in order:
            order.append(endpoint["resource"])
    return [
        {
            "name": name,
            "slug": f"{i:02d}-{name}",
            "endpointIds": [e["id"] for e in endpoints if e["resource"] == name],
            "entities": sorted(
                {e["primaryEntity"] for e in endpoints if e["resource"] == name and e["primaryEntity"]}
            ),
        }
        for i, name in enumerate(order, start=1)
    ]


# --------------------------------------------------------------------------- #
# Figma module discovery
# --------------------------------------------------------------------------- #


def is_output_dir(path: Path, specs_dirname: str) -> bool:
    """True when a folder under figma-starter/ is this pipeline's output, not a design module.

    Three markers, because the name alone is not enough once `--out` lets the
    output be called anything: the folder this run is about to write, the default
    name (which covers a folder not yet written to), and any folder holding an
    `.api-index.json` — the file only this pipeline produces, which identifies
    every output folder an earlier `--out` run left behind.
    """
    return (
        path.name in (specs_dirname, API_SPECS_DIR)
        or (path / INDEX_FILE).is_file()
        or (path / LEGACY_INDEX_FILE).is_file()
    )


def existing_modules(root: Path, specs_dirname: str = API_SPECS_DIR) -> list[str]:
    """Module folders already present under figma-starter/, in name order.

    An output folder is not a design module — counting one would make a
    single-module project look ambiguous the moment it has been run once, and
    with `--out` there can be one output folder per module sitting right there
    alongside them.
    """
    starter = root / FIGMA_STARTER_DIR
    if not starter.is_dir():
        return []
    return [
        d.name
        for d in sorted(starter.iterdir())
        if d.is_dir() and not d.name.startswith(".") and not is_output_dir(d, specs_dirname)
    ]


def resolve_out(out: str | None, root: Path) -> str:
    """Validate the output folder, which is always one level under figma-starter/.

    A single path segment, so every path this script records stays
    project-root-relative and one level deep — the shape every later step
    assumes. Writing into a design module is refused outright: the module folder
    is a read-only input, and a run that overwrote it could not be re-run.
    """
    if out is None:
        return API_SPECS_DIR
    name = out.strip().strip("/")
    if not name or name in (".", "..") or "/" in name or "\\" in name or name.startswith("."):
        raise ValueError(
            f"--out {out!r} is not a folder name. Pass a single folder to create under "
            f"{FIGMA_STARTER_DIR}/, such as --out api-specs-dashboard."
        )
    candidate = root / FIGMA_STARTER_DIR / name
    if candidate.is_dir():
        holds_screens = (candidate / "screens.json").is_file() or any(
            (d / "spec.md").is_file() for d in candidate.iterdir() if d.is_dir()
        )
        if holds_screens:
            raise ValueError(
                f"--out {name} is a design module, not an output folder — the module folder is a "
                f"read-only input to this run. Pick another name, such as --out api-specs-{name}."
            )
    return name


def resolve_module(module: str | None, root: Path, specs_dirname: str = API_SPECS_DIR) -> str:
    """Pick the module folder to read the UI outputs from.

    Every run binds endpoints to imported screens, so a module that isn't there
    is a dead end, not a degraded run. Both the ambiguous case and the wrong-name
    case stop here rather than producing a clean-looking run with no bindings.
    """
    modules = existing_modules(root, specs_dirname)
    if not modules:
        raise ValueError(
            f"{FIGMA_STARTER_DIR}/ holds no module folder, so there are no screens to bind against. "
            "Run /speckit.figma-starter.import first to produce the UI outputs this command reads."
        )
    if module:
        name = slug(module)
        if name not in modules:
            near = difflib.get_close_matches(name, modules, n=1, cutoff=0.6)
            hint = (
                f"Did you mean -m {near[0]}?"
                if near
                else f"Modules that do exist: {', '.join(modules)}."
            )
            raise ValueError(f"-m {name} names no module under {FIGMA_STARTER_DIR}/. {hint}")
        return name
    if len(modules) > 1:
        raise ValueError(
            f"{FIGMA_STARTER_DIR}/ holds {len(modules)} modules ({', '.join(modules)}) and no -m was "
            "given. Re-run with -m <module> to say which one this API belongs to."
        )
    return modules[0]


def build_order_steps(module_dir: Path) -> dict[str, int]:
    """WaveMaker page name -> its step number in `build-order.md`.

    Step 1 is usually shared partials with no page folder of their own, and one
    cell can hold several comma-separated names sharing a step, so this is a
    name lookup rather than a list of pages.
    """
    path = module_dir / BUILD_ORDER_FILE
    if not path.is_file():
        return {}
    steps: dict[str, int] = {}
    for line in path.read_text(errors="replace").splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        # Skip the header and the `|---|` separator: only numbered step rows count.
        if len(cells) < 2 or not cells[0].strip("`").isdigit():
            continue
        step = int(cells[0].strip("`"))
        for name in cells[1].split(","):
            name = name.strip().strip("`").strip()
            if name and name != "—":
                steps.setdefault(name, step)
    return steps


def wavemaker_page(spec: Path) -> str:
    """The `WaveMaker page:` name a page spec declares — the join key to build order."""
    for line in spec.read_text(errors="replace").splitlines()[:40]:
        head, sep, tail = line.partition(":")
        if sep and head.strip().lstrip("#*- ").lower() == "wavemaker page":
            return tail.strip().strip("`*").strip()
    return ""


def figma_pages(module_dir: Path, module: str, specs_dirname: str = API_SPECS_DIR) -> list[dict]:
    """Page folders written by figma-images-to-spec, so bind-ui knows what exists.

    Inputs and outputs no longer share a folder, so every path is recorded
    project-root-relative and in full: `spec` and `screens` point back into the
    UI outputs to read, `bindings` points into api-specs/ to write. A later step
    never has to work out which root a path is relative to.

    Ordered by `build-order.md`, not by folder name, so the binding step walks
    the pages in the sequence the user journeys run — login before dashboard,
    whatever the folder numbering says. Pages the build order does not name keep
    folder order behind the ones it does.
    """
    if not module_dir.is_dir():
        return []
    titles: dict[str, str] = {}
    screens_json = module_dir / "screens.json"
    if screens_json.is_file():
        try:
            data = json.loads(screens_json.read_text())
            for screen in data.get("screens") or []:
                if screen.get("slug"):
                    titles[screen["slug"]] = screen.get("title") or screen["slug"]
        except (json.JSONDecodeError, OSError):
            pass

    ui_root = f"{FIGMA_STARTER_DIR}/{module}"
    specs_root = f"{FIGMA_STARTER_DIR}/{specs_dirname}"

    steps = build_order_steps(module_dir)

    pages = []
    for folder in sorted(module_dir.iterdir()):
        spec = folder / "spec.md"
        if not folder.is_dir() or not spec.is_file():
            continue
        screens_dir = folder / "figma-resources" / "screens"
        name = wavemaker_page(spec)
        pages.append(
            {
                "slug": folder.name,
                "title": titles.get(folder.name, folder.name),
                "wavemakerPage": name or None,
                "buildStep": steps.get(name),
                "spec": f"{ui_root}/{folder.name}/spec.md",
                "screens": sorted(
                    f"{ui_root}/{folder.name}/figma-resources/screens/{p.name}"
                    for p in (screens_dir.iterdir() if screens_dir.is_dir() else [])
                    if p.is_file()
                ),
                "bindings": f"{specs_root}/{folder.name}/{BINDINGS_FILE}",
            }
        )
    pages.sort(key=lambda p: (p["buildStep"] is None, p["buildStep"] or 0, p["slug"]))
    return pages


def select_pages(pages: list[dict], requested: list[str]) -> tuple[list[dict], list[str]]:
    """Narrow discovered pages to the ones asked for, so a run can target one screen.

    Accepts a folder name (`01-specification-list`), the slug without its number
    prefix (`specification-list`), or just the number (`1`).
    """
    if not requested:
        return pages, []

    by_slug = {p["slug"]: p for p in pages}
    chosen: list[dict] = []
    missing: list[str] = []
    for want in requested:
        key = slug(want)
        hit = by_slug.get(key)
        if hit is None:
            hit = next((p for p in pages if p["slug"].split("-", 1)[-1] == key), None)
        if hit is None and key.isdigit():
            hit = next((p for p in pages if p["slug"].split("-", 1)[0] == key.zfill(2)), None)
        if hit is None:
            missing.append(want)
        elif hit not in chosen:
            chosen.append(hit)
    return chosen, missing


def warn_legacy_layout(module_dir: Path, module: str, specs_dirname: str = API_SPECS_DIR) -> None:
    """Point out output from the superseded in-module layout.

    Earlier runs wrote `<module>/api/` and dropped each `api-bindings.md` into
    the page folder beside its `spec.md`. Those files are not read any more, so
    left in place they are a stale second answer sitting next to the live one.
    Reporting beats deleting: they may hold review comments, and this script does
    not own anything under a module folder.
    """
    if not module_dir.is_dir():
        return
    stale: list[str] = []
    if (module_dir / "api").is_dir():
        stale.append(f"{FIGMA_STARTER_DIR}/{module}/api/")
    stale += [
        f"{FIGMA_STARTER_DIR}/{module}/{folder.name}/{BINDINGS_FILE}"
        for folder in sorted(module_dir.iterdir())
        if folder.is_dir() and (folder / BINDINGS_FILE).is_file()
    ]
    if stale:
        print(
            f"[WARN] output from the previous layout is still present: {', '.join(stale)}. "
            f"This run writes to {FIGMA_STARTER_DIR}/{specs_dirname}/ instead, so those files "
            "are now stale copies — review and delete them.",
            file=sys.stderr,
        )


# --------------------------------------------------------------------------- #
# pull — write .api-index.json
# --------------------------------------------------------------------------- #


def pull(
    source: str,
    *,
    module_name: str | None,
    root: Path,
    headers: dict[str, str],
    only_pages: list[str] | None = None,
    out: str | None = None,
) -> Path:
    doc = parse_document(fetch(source, headers), source)
    if "paths" not in doc:
        raise ValueError(
            f"{source} has no `paths` object — it does not look like an OpenAPI or Swagger document."
        )

    info = doc.get("info") or {}
    specs_dirname = resolve_out(out, root)
    module = resolve_module(module_name, root, specs_dirname)
    module_dir = root / FIGMA_STARTER_DIR / module
    specs_dir = root / FIGMA_STARTER_DIR / specs_dirname

    endpoints, entities = normalize(doc)
    resources = group_resources(endpoints)
    available = figma_pages(module_dir, module, specs_dirname)
    if not available:
        raise ValueError(
            f"{FIGMA_STARTER_DIR}/{module}/ holds no page folder with a spec.md, so there is nothing "
            "to bind endpoints to. Run /speckit.figma-starter.import first, or check -m names the "
            "right module."
        )
    pages, missing = select_pages(available, only_pages or [])
    if missing:
        known = ", ".join(p["slug"] for p in available) or "none — no page folder here has a spec.md"
        raise ValueError(
            f"--page {', '.join(missing)} matched no page in figma-starter/{module}/. Pages found: {known}"
        )

    # Created only once the run is certain to produce something, so a rejected
    # --page or an unreadable document leaves no empty folder behind. The page
    # folders are mirrored from the UI outputs up front, so the layout the later
    # steps write into exists before they run.
    specs_dir.mkdir(parents=True, exist_ok=True)
    for page in pages:
        (specs_dir / page["slug"]).mkdir(exist_ok=True)

    index = {
        "module": module,
        "paths": {
            "uiRoot": f"{FIGMA_STARTER_DIR}/{module}",
            "apiSpecs": f"{FIGMA_STARTER_DIR}/{specs_dirname}",
            "userStories": f"{FIGMA_STARTER_DIR}/{module}/user-stories.md",
            "buildOrder": f"{FIGMA_STARTER_DIR}/{module}/{BUILD_ORDER_FILE}",
        },
        "source": {
            "location": source,
            "specVersion": spec_flavor(doc),
            "fetchedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        },
        "info": {
            "title": info.get("title"),
            "version": info.get("version"),
            "description": (info.get("description") or "").strip() or None,
        },
        "servers": server_urls(doc),
        "resources": resources,
        "endpoints": endpoints,
        "entities": entities,
        "figmaPages": pages,
        "scope": "page" if only_pages else "module",
        "pagesAvailable": [p["slug"] for p in available],
        "stats": {
            "endpoints": len(endpoints),
            "entities": len(entities),
            "resources": len(resources),
            "figmaPages": len(pages),
        },
    }
    (specs_dir / INDEX_FILE).write_text(json.dumps(index, indent=2) + "\n")

    # An index from before this file was hidden would sit alongside as a stale twin.
    legacy = specs_dir / LEGACY_INDEX_FILE
    if legacy.is_file():
        legacy.unlink()
        print(f"[OK] removed superseded {LEGACY_INDEX_FILE} (now {INDEX_FILE})")

    warn_legacy_layout(module_dir, module, specs_dirname)

    print(
        f"[OK] {len(endpoints)} endpoints, {len(entities)} entities, "
        f"{len(resources)} resources -> {len(pages)} Figma pages"
    )
    print(f"[OK] module={module} -> output under {FIGMA_STARTER_DIR}/{specs_dirname}/")
    if build_order_steps(module_dir):
        print(f"[OK] pages ordered by {BUILD_ORDER_FILE}: {', '.join(p['slug'] for p in pages)}")
    else:
        print(
            f"[WARN] no {BUILD_ORDER_FILE} under {FIGMA_STARTER_DIR}/{module}/ — pages fall back to "
            "folder order, which may not be the order the user journeys run.",
            file=sys.stderr,
        )
    if only_pages:
        print(
            f"[OK] scope=page -> {', '.join(p['slug'] for p in pages)} "
            f"(of {len(available)} pages in the module)"
        )
    return specs_dir / INDEX_FILE


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="swagger_pull.py",
        description="Flatten an OpenAPI/Swagger document into .api-index.json (stdlib only).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("pull", help="Fetch and normalize an OpenAPI/Swagger document.")
    p.add_argument("source", help="Swagger/OpenAPI URL or local JSON/YAML file path")
    p.add_argument(
        "-m",
        "--module",
        default=None,
        help="Module folder under figma-starter/ to read the UI outputs from",
    )
    p.add_argument(
        "--out",
        default=None,
        metavar="FOLDER",
        help="Folder under figma-starter/ to write this run's output to "
        f"(default: {API_SPECS_DIR}). Use one per module to keep their outputs apart",
    )
    p.add_argument(
        "--root",
        default=".",
        help="Project root; the output folder is created under <root>/figma-starter/ (default: current dir)",
    )
    p.add_argument(
        "--header",
        action="append",
        default=[],
        metavar='"Name: value"',
        help="Extra request header; repeatable (e.g. Authorization)",
    )
    p.add_argument(
        "--page",
        action="append",
        default=[],
        metavar="SLUG",
        help="Bind only this page folder; repeatable. Accepts 01-specification-list, "
        "specification-list, or 1. Default: every page in the module",
    )

    args = parser.parse_args(argv)
    root = Path(args.root).resolve()

    try:
        out = pull(
            args.source,
            module_name=args.module,
            root=root,
            headers=auth_headers(root, args.header),
            only_pages=args.page,
            out=args.out,
        )
    except ValueError as err:
        sys.exit(str(err))

    print(f"[OK] {args.command} -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
