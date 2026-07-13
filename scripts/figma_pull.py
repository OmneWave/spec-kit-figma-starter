#!/usr/bin/env python3
"""Self-contained Figma REST helper for the figma-images Spec Kit extension.

Standard library only (urllib, json, re, argparse) — no pip install, no uv, no
external CLI. Ships inside the extension and is invoked by the pipeline skills:

    python3 figma_pull.py screens   "<figma section url>" [-o <module>] [--root <dir>]
    python3 figma_pull.py resources "<figma section url>" [-o <module>] [--root <dir>] [--assets-only]

Output lands under <root>/figma-specs/<module>/ (root defaults to the current
directory, i.e. the Spec Kit project root).

Token resolution order: FIGMA_TOKEN or FIGMA_ACCESS_TOKEN environment variable,
otherwise a KEY=VALUE line in <root>/.env.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# --------------------------------------------------------------------------- #
# Token / .env
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


def figma_token(root: Path) -> str:
    token = os.environ.get("FIGMA_TOKEN") or os.environ.get("FIGMA_ACCESS_TOKEN")
    if not token:
        load_dotenv(root)
        token = os.environ.get("FIGMA_TOKEN") or os.environ.get("FIGMA_ACCESS_TOKEN")
    if not token:
        sys.exit(
            "No Figma token. Set FIGMA_TOKEN (or FIGMA_ACCESS_TOKEN) in the "
            "environment or in a .env file at the project root. Without a token, "
            "let the agent fall back to the Figma MCP server."
        )
    return token


# --------------------------------------------------------------------------- #
# Paths — <root>/figma-specs/<module>/...
# --------------------------------------------------------------------------- #

FIGMA_SPECS_DIR = "figma-specs"


def module_slug_dir(module: str, root: Path) -> Path:
    return root / FIGMA_SPECS_DIR / module


def page_resources_dir(module: str, page_slug: str, root: Path) -> Path:
    return module_slug_dir(module, root) / page_slug / "figma-resources"


def page_screens_dir(module: str, page_slug: str, root: Path) -> Path:
    return page_resources_dir(module, page_slug, root) / "screens"


def page_icons_dir(module: str, page_slug: str, root: Path) -> Path:
    return page_resources_dir(module, page_slug, root) / "icons"


def page_embedded_dir(module: str, page_slug: str, root: Path) -> Path:
    return page_resources_dir(module, page_slug, root) / "embedded"


def module_design_tokens_dir(module: str, root: Path) -> Path:
    return module_slug_dir(module, root) / "design-tokens"


def module_typography_dir(module: str, root: Path) -> Path:
    return module_slug_dir(module, root) / "typography"


# --------------------------------------------------------------------------- #
# Shared Figma URL parsing and API helpers
# --------------------------------------------------------------------------- #


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "module"


def page_slug_map(frames: list[dict]) -> dict[str, str]:
    """Map each frame id to its `<NN>-<slug>` page folder name.

    Both screens and resources rely on identical numbering so a screen's PNG and
    its scoped icons land in the same page folder.
    """
    result: dict[str, str] = {}
    for i, frame in enumerate(frames, start=1):
        fid = frame["id"]
        label = frame.get("name", "Screen")
        base = f"{i:02d}-{slug(label)}"
        if sum(1 for f in frames if f.get("name") == label) > 1:
            base = f"{base}-{fid.replace(':', '-')}"
        result[fid] = base
    return result


def parse_url(url: str) -> tuple[str, str]:
    path = urllib.parse.urlparse(url)
    parts = [p for p in path.path.split("/") if p]
    node = urllib.parse.parse_qs(path.query).get("node-id", [None])[0]
    key = None
    if "design" in parts:
        i = parts.index("design")
        key = parts[i + 1] if i + 1 < len(parts) else None
        if i + 2 < len(parts) and parts[i + 2] == "branch" and i + 3 < len(parts):
            key = parts[i + 3]
    if not key or not node:
        raise ValueError("Need a Figma design URL with node-id=...")
    return key, node.replace("-", ":")


def api_get(path: str, token: str, *, max_retries: int = 5) -> dict:
    """GET a Figma REST endpoint, retrying with backoff on rate limits (429)."""
    req = urllib.request.Request(
        f"https://api.figma.com/v1/{path}",
        headers={"X-Figma-Token": token},
    )
    for attempt in range(max_retries + 1):
        try:
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read())
        except urllib.error.HTTPError as err:
            if err.code != 429 or attempt == max_retries:
                raise
            retry_after = err.headers.get("Retry-After")
            delay = float(retry_after) if retry_after and retry_after.isdigit() else 2**attempt
            print(f"[WARN] Figma rate limit (429); retrying in {delay:.0f}s")
            time.sleep(delay)
    raise RuntimeError("unreachable")


def api_get_optional(path: str, token: str) -> dict | None:
    try:
        return api_get(path, token)
    except urllib.error.HTTPError as err:
        if err.code in (403, 404):
            print(f"[WARN] Skipping {path} ({err.code})")
            return None
        raise


def save_bytes(url: str, dest: Path) -> bool:
    if not url:
        return False
    try:
        with urllib.request.urlopen(url) as response:
            dest.write_bytes(response.read())
        return True
    except (urllib.error.URLError, OSError) as err:
        print(f"[WARN] {dest.name}: {err}")
        return False


# --------------------------------------------------------------------------- #
# screens — frames as PNGs + prototype taps -> screens.json
# --------------------------------------------------------------------------- #

POPUP = "popup"
SCREEN = "screen"
BACK = "back"
CLOSE = "close"


def _iter_actions(ix: dict):
    """Yield every action in an interaction, descending into CONDITIONAL blocks."""
    raw = ix.get("actions")
    if not raw:
        raw = [ix["action"]] if ix.get("action") else []
    for action in raw:
        if not action:
            continue
        if action.get("type") == "CONDITIONAL":
            for block in action.get("conditionalActions", []) or []:
                for nested in (block or {}).get("actions", []) or []:
                    if nested:
                        yield nested
            continue
        yield action


def walk_taps(node: dict, out: list[dict]) -> None:
    layer = node.get("name", "")
    for ix in node.get("interactions", []):
        for action in _iter_actions(ix):
            atype = action.get("type")
            if atype == "NODE":
                dest = action.get("destinationId")
                if not dest:
                    continue
                nav = action.get("navigation", "NAVIGATE")
                # CHANGE_TO / SCROLL_TO are intra-component behaviour (variant
                # swaps for hover/pressed states, in-page scroll) — not page or
                # dialog navigation, so they must not pollute the flow map.
                if nav in ("CHANGE_TO", "SCROLL_TO"):
                    continue
                out.append(
                    {
                        "control": layer,
                        "opens": dest,
                        "type": POPUP if nav in ("OVERLAY", "SWAP") else SCREEN,
                    }
                )
            elif atype in ("BACK", "CLOSE"):
                out.append(
                    {
                        "control": layer,
                        "opens": None,
                        "type": BACK if atype == "BACK" else CLOSE,
                    }
                )
    for child in node.get("children", []):
        walk_taps(child, out)


def resolve_node_names(file_key: str, token: str, ids: set[str]) -> dict[str, str]:
    """Look up human titles for node IDs outside the pulled section."""
    resolved: dict[str, str] = {}
    ordered = [i for i in ids if i]
    for start in range(0, len(ordered), 50):
        chunk = ordered[start : start + 50]
        q = urllib.parse.quote(",".join(chunk), safe=",:")
        try:
            data = api_get(f"files/{file_key}/nodes?ids={q}", token)
        except urllib.error.URLError as err:
            print(f"[WARN] could not resolve {len(chunk)} tap targets: {err}")
            continue
        for node_id, entry in (data.get("nodes") or {}).items():
            name = ((entry or {}).get("document") or {}).get("name")
            if name:
                resolved[node_id] = name
    return resolved


def pull_screens(url: str, *, output: str | None, root: Path, token: str) -> Path:
    file_key, section_id = parse_url(url)
    doc = api_get(f"files/{file_key}/nodes?ids={section_id}", token)
    section = next(iter(doc["nodes"].values()))["document"]
    title = section.get("name", "Module")
    module = slug(output or title)

    frames = [c for c in section.get("children", []) if c.get("type") == "FRAME"]
    if not frames:
        raise ValueError("No frames in this section.")

    spec_dir = module_slug_dir(module, root)
    spec_dir.mkdir(parents=True, exist_ok=True)

    ids = [frame["id"] for frame in frames]
    q = urllib.parse.quote(",".join(ids), safe=",:")
    exports = api_get(f"images/{file_key}?ids={q}&format=png&scale=1", token).get("images", {})
    names = {frame["id"]: frame.get("name", "Screen") for frame in frames}
    page_slugs = page_slug_map(frames)

    screens: list[dict] = []
    all_taps: list[list[dict]] = []
    for frame in frames:
        fid = frame["id"]
        page_slug = page_slugs[fid]
        file_name = f"{page_slug}.png"

        screens_dir = page_screens_dir(module, page_slug, root)
        screens_dir.mkdir(parents=True, exist_ok=True)
        save_bytes(exports.get(fid, ""), screens_dir / file_name)

        taps: list[dict] = []
        walk_taps(frame, taps)
        all_taps.append(taps)

    resolved = dict(names)
    unknown = {
        tap["opens"]
        for taps in all_taps
        for tap in taps
        if tap["opens"] and tap["opens"] not in resolved
    }
    resolved.update(resolve_node_names(file_key, token, unknown))

    for i, frame in enumerate(frames, start=1):
        fid = frame["id"]
        label = names[fid]
        page_slug = page_slugs[fid]
        file_name = f"{page_slug}.png"
        taps = all_taps[i - 1]
        for tap in taps:
            if tap["opens"]:
                tap["opens"] = resolved.get(tap["opens"], tap["opens"])

        screens.append(
            {
                "order": i,
                "title": label,
                "slug": page_slug,
                "image": f"{module}/{page_slug}/figma-resources/screens/{file_name}",
                "figma": f"https://www.figma.com/design/{file_key}?node-id={fid.replace(':', '-')}",
                "taps": taps,
            }
        )

    catalog = {
        "title": title,
        "module": module,
        "figma": url,
        "screenCount": len(screens),
        "screens": screens,
        "layout": {
            "module": f"figma-specs/{module}/",
            "designTokens": f"figma-specs/{module}/design-tokens/",
            "typography": f"figma-specs/{module}/typography/",
            "pageResources": f"figma-specs/{module}/<NN>-<slug>/figma-resources/",
        },
    }
    (spec_dir / "screens.json").write_text(json.dumps(catalog, indent=2) + "\n")
    return spec_dir


# --------------------------------------------------------------------------- #
# resources — icons, embedded rasters, (optionally) tokens + typography
# --------------------------------------------------------------------------- #

ICON_TYPES = {"VECTOR", "BOOLEAN_OPERATION", "STAR", "LINE", "ELLIPSE", "REGULAR_POLYGON"}
ICON_CONTAINER_TYPES = {"COMPONENT", "INSTANCE", "FRAME", "GROUP"}
MAX_ICON_PX = 64
ICON_NAME = re.compile(r"icon", re.I)


def rgba_to_hex(color: dict) -> str:
    r = round(color.get("r", 0) * 255)
    g = round(color.get("g", 0) * 255)
    b = round(color.get("b", 0) * 255)
    a = color.get("a", 1)
    if a >= 0.999:
        return f"#{r:02x}{g:02x}{b:02x}"
    return f"rgba({r}, {g}, {b}, {a:.3f})"


def bbox(node: dict) -> tuple[float, float] | None:
    box = node.get("absoluteBoundingBox")
    if not box:
        return None
    return box.get("width", 0), box.get("height", 0)


def walk(node: dict) -> list[dict]:
    nodes = [node]
    for child in node.get("children", []):
        nodes.extend(walk(child))
    return nodes


def paint_key(paint: dict) -> str | None:
    if paint.get("type") != "SOLID" or not paint.get("visible", True):
        return None
    color = paint.get("color")
    if not color:
        return None
    return rgba_to_hex(color)


def typography_key(style: dict) -> str:
    parts = [
        style.get("fontFamily", ""),
        str(style.get("fontWeight", "")),
        str(style.get("fontSize", "")),
        str(style.get("lineHeightPx", style.get("lineHeightPercentFontSize", ""))),
        str(style.get("letterSpacing", "")),
    ]
    return "|".join(parts)


def is_icon_candidate(node: dict) -> bool:
    name = node.get("name", "")
    if ICON_NAME.search(name):
        return True
    size = bbox(node)
    if not size:
        return False
    w, h = size
    if w <= 0 or h <= 0 or w > MAX_ICON_PX or h > MAX_ICON_PX:
        return False
    ntype = node.get("type", "")
    if ntype in ICON_TYPES:
        return True
    if ntype in ICON_CONTAINER_TYPES and w <= MAX_ICON_PX and h <= MAX_ICON_PX:
        return True
    return False


def export_nodes(
    file_key: str,
    token: str,
    nodes: dict[str, str],
    fmt: str,
    dest_dir: Path,
    *,
    rel_prefix: str,
) -> dict[str, str]:
    if not nodes:
        return {}
    saved: dict[str, str] = {}
    ids = list(nodes.keys())
    chunk = 40
    ext = "svg" if fmt == "svg" else "png"
    for i in range(0, len(ids), chunk):
        batch = ids[i : i + chunk]
        q = urllib.parse.quote(",".join(batch), safe=",:")
        resp = api_get(f"images/{file_key}?ids={q}&format={fmt}", token).get("images", {})
        for nid, url in resp.items():
            if not url:
                continue
            name = f"{slug(nodes[nid])}-{nid.replace(':', '-')}.{ext}"
            path = dest_dir / name
            rel = f"{rel_prefix}/{path.name}"
            if path.exists() and path.stat().st_size > 0:
                saved[nid] = rel
            elif save_bytes(url, path):
                saved[nid] = rel
    return saved


def pull_variables(file_key: str, token: str) -> list[dict]:
    data = api_get_optional(f"files/{file_key}/variables/local", token)
    if not data:
        return []
    meta = data.get("meta", {})
    variables = meta.get("variables", {})
    collections = meta.get("variableCollections", {})
    tokens: list[dict] = []
    for var_id, var in variables.items():
        if var.get("resolvedType") != "COLOR":
            continue
        collection = collections.get(var.get("variableCollectionId", ""), {})
        values = var.get("valuesByMode", {})
        resolved = next(iter(values.values()), None)
        if isinstance(resolved, dict) and "r" in resolved:
            hex_val = rgba_to_hex(resolved)
        else:
            continue
        tokens.append(
            {
                "name": var.get("name", var_id),
                "value": hex_val,
                "source": "figma-variable",
                "collection": collection.get("name"),
                "id": var_id,
            }
        )
    return tokens


def collect_node_data(
    node: dict,
    colors: dict[str, dict],
    typography: dict[str, dict],
    image_refs: dict[str, str],
    icon_nodes: dict[str, dict],
) -> None:
    name = node.get("name", "Layer")
    for key in ("fills", "strokes", "background"):
        paints = node.get(key)
        if not isinstance(paints, list):
            continue
        for paint in paints:
            if paint.get("type") == "IMAGE" and paint.get("imageRef"):
                image_refs[paint["imageRef"]] = name
            hex_val = paint_key(paint)
            if hex_val and hex_val not in colors:
                colors[hex_val] = {"value": hex_val, "source": "fill", "usedIn": [name]}
            elif hex_val:
                used = colors[hex_val].setdefault("usedIn", [])
                if name not in used and len(used) < 20:
                    used.append(name)

    if node.get("type") == "TEXT":
        style = node.get("style") or {}
        tkey = typography_key(style)
        if tkey not in typography:
            typography[tkey] = {
                "fontFamily": style.get("fontFamily"),
                "fontPostScriptName": style.get("fontPostScriptName"),
                "fontWeight": style.get("fontWeight"),
                "fontSize": style.get("fontSize"),
                "lineHeightPx": style.get("lineHeightPx"),
                "letterSpacing": style.get("letterSpacing"),
                "textCase": style.get("textCase"),
                "usedIn": [name],
            }
        else:
            used = typography[tkey].setdefault("usedIn", [])
            if name not in used and len(used) < 20:
                used.append(name)

    if is_icon_candidate(node):
        nid = node["id"]
        if nid not in icon_nodes:
            icon_nodes[nid] = {"name": name, "id": nid}


def pull_resources(
    url: str,
    *,
    output: str | None,
    root: Path,
    token: str,
    assets_only: bool = False,
) -> Path:
    file_key, section_id = parse_url(url)
    doc = api_get(f"files/{file_key}/nodes?ids={section_id}", token)
    section = next(iter(doc["nodes"].values()))["document"]
    module = slug(output or section.get("name", "Module"))

    frames = [c for c in section.get("children", []) if c.get("type") == "FRAME"]
    if not frames:
        raise ValueError("No frames in this section.")

    spec_dir = module_slug_dir(module, root)
    spec_dir.mkdir(parents=True, exist_ok=True)

    page_slugs = page_slug_map(frames)
    module_colors: dict[str, dict] = {}
    module_typography: dict[str, dict] = {}

    image_urls: dict[str, str] | None = None

    def image_ref_urls() -> dict[str, str]:
        nonlocal image_urls
        if image_urls is None:
            image_urls = api_get(f"files/{file_key}/images", token).get("images", {})
        return image_urls

    pages: list[dict] = []
    for frame in frames:
        fid = frame["id"]
        page_slug = page_slugs[fid]

        colors: dict[str, dict] = {}
        typography: dict[str, dict] = {}
        image_refs: dict[str, str] = {}
        icon_nodes: dict[str, dict] = {}
        for node in walk(frame):
            collect_node_data(node, colors, typography, image_refs, icon_nodes)

        for hex_val, info in colors.items():
            module_colors.setdefault(hex_val, info)
        for tkey, info in typography.items():
            module_typography.setdefault(tkey, info)

        icons_dir = page_icons_dir(module, page_slug, root)
        embedded_dir = page_embedded_dir(module, page_slug, root)
        icons_dir.mkdir(parents=True, exist_ok=True)
        embedded_dir.mkdir(parents=True, exist_ok=True)

        icon_rel = f"{module}/{page_slug}/figma-resources/icons"
        icon_names = {nid: info["name"] for nid, info in icon_nodes.items()}
        icon_paths = export_nodes(
            file_key, token, icon_names, "svg", icons_dir, rel_prefix=icon_rel
        )

        embedded_images: list[dict] = []
        if image_refs:
            refs = image_ref_urls()
            for ref, layer_name in image_refs.items():
                url_value = refs.get(ref)
                if not url_value:
                    continue
                file_name = f"{slug(layer_name)}-{ref[:8]}.png"
                if save_bytes(url_value, embedded_dir / file_name):
                    embedded_images.append(
                        {
                            "name": layer_name,
                            "file": f"{module}/{page_slug}/figma-resources/embedded/{file_name}",
                            "imageRef": ref,
                        }
                    )

        pages.append(
            {
                "slug": page_slug,
                "title": frame.get("name", "Screen"),
                "figmaNodeId": fid,
                "resources": f"{module}/{page_slug}/figma-resources/",
                "icons": [
                    {"name": icon_nodes[nid]["name"], "file": icon_paths[nid], "figmaNodeId": nid}
                    for nid in icon_nodes
                    if nid in icon_paths
                ],
                "images": embedded_images,
            }
        )

    manifest: dict = {"module": module, "pages": pages}
    if not assets_only:
        tokens_dir = module_design_tokens_dir(module, root)
        typography_dir = module_typography_dir(module, root)
        tokens_dir.mkdir(parents=True, exist_ok=True)
        typography_dir.mkdir(parents=True, exist_ok=True)
        color_tokens = pull_variables(file_key, token) + list(module_colors.values())
        (tokens_dir / "tokens.json").write_text(json.dumps(color_tokens, indent=2) + "\n")
        (typography_dir / "typography.json").write_text(
            json.dumps(list(module_typography.values()), indent=2) + "\n"
        )
        manifest["designTokens"] = f"{module}/design-tokens/tokens.json"
        manifest["typography"] = f"{module}/typography/typography.json"

    manifest["notes"] = {
        "fonts": "Figma API exports typography tokens only, not font files (TTF/WOFF).",
        "tokens": "Design tokens and typography are module-level (shared across all screens).",
        "pageResources": f"Per-screen icons/images live in figma-specs/{module}/<NN>-<slug>/figma-resources/.",
    }
    (spec_dir / "resources-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return spec_dir


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="figma_pull.py",
        description="Pull Figma screens/resources via the REST API (stdlib only).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    for name, helptext in (
        ("screens", "Download section frames as PNGs and write screens.json (with taps)."),
        ("resources", "Extract per-screen icons/embedded images (+ tokens/typography)."),
    ):
        p = sub.add_parser(name, help=helptext)
        p.add_argument("url", help="Figma section URL (must include node-id=...)")
        p.add_argument("-o", "--output", default=None, help="Module folder name override")
        p.add_argument(
            "--root",
            default=".",
            help="Project root; output goes to <root>/figma-specs/ (default: current dir)",
        )
        if name == "resources":
            p.add_argument(
                "--assets-only",
                action="store_true",
                help="Only icons + embedded images; skip tokens/typography",
            )

    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    token = figma_token(root)

    try:
        if args.command == "screens":
            spec_dir = pull_screens(args.url, output=args.output, root=root, token=token)
        else:
            spec_dir = pull_resources(
                args.url,
                output=args.output,
                root=root,
                token=token,
                assets_only=args.assets_only,
            )
    except ValueError as err:
        sys.exit(str(err))

    print(f"[OK] {args.command} -> {spec_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
