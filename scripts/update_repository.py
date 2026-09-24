#!/usr/bin/env python3
"""Synchronize compiled Altium IntLib files and rebuild the README catalog.

The compiled ``IntLib`` is the catalog's source of truth.  Working ``SchLib``
files are deliberately ignored when component rows are generated.

The script performs four operations:

1. finds ``Project Outputs for ...`` directories below ``source/``;
2. copies their ``*.IntLib`` files into the flat ``compiled/`` directory;
3. records the source category of every IntLib and removes generated outputs;
4. reads compiled component parameters from ``compiled/*.IntLib`` and replaces
   only the marked catalog block at the end of README.md.

No Altium installation is required.  Paths are resolved relative to the
repository root, which defaults to the parent of this script's directory.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import struct
import sys
import zlib
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping, Sequence

try:
    import olefile
except ImportError as exc:  # pragma: no cover - exercised only without setup
    raise SystemExit(
        "Missing dependency 'olefile'. Run: python -m pip install -r requirements.txt"
    ) from exc


CATALOG_START = "<!-- ALTIUM-CATALOG:START -->"
CATALOG_END = "<!-- ALTIUM-CATALOG:END -->"
OUTPUT_DIRECTORY_PREFIX = "project outputs for "
MANIFEST_FILENAME = "catalog-index.json"
MANIFEST_VERSION = 1
UNKNOWN_CATEGORY = "UNCATEGORIZED"


class RepositoryUpdateError(RuntimeError):
    """Raised when the repository cannot be updated without ambiguity."""


@dataclass(frozen=True)
class Component:
    category: str
    symbol: str
    manufacturer_part_number: str
    manufacturer: str
    package: str
    intlib: Path
    parameters: Mapping[str, str] = field(compare=False, repr=False)


@dataclass(frozen=True)
class IntLibCandidate:
    path: Path
    category: str


@dataclass(frozen=True)
class SyncResult:
    output_directories: int
    intlibs_found: int
    intlibs_changed: int
    intlibs_unchanged: int
    manifest_changed: bool
    intlib_categories: Mapping[str, str]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_output_directory(path: Path) -> bool:
    return path.name.casefold().startswith(OUTPUT_DIRECTORY_PREFIX)


def find_output_directories(source_root: Path) -> list[Path]:
    matches = [
        path
        for path in source_root.rglob("*")
        if path.is_dir() and is_output_directory(path)
    ]
    # Ignore nested matches if an unusual generated tree contains another
    # directory with the same prefix.
    top_level: list[Path] = []
    for candidate in sorted(matches, key=lambda item: (len(item.parts), str(item).casefold())):
        if not any(parent in candidate.parents for parent in top_level):
            top_level.append(candidate)
    return top_level


def discover_categories(source_root: Path) -> list[str]:
    return sorted(
        [
            path.name
            for path in source_root.iterdir()
            if path.is_dir() and not path.name.startswith(".") and not is_output_directory(path)
        ],
        key=str.casefold,
    )


def category_for_output_directory(output_dir: Path, source_root: Path) -> str:
    relative = output_dir.relative_to(source_root)
    return relative.parts[0] if len(relative.parts) >= 2 else UNKNOWN_CATEGORY


def load_manifest(manifest_path: Path) -> dict[str, str]:
    if not manifest_path.exists():
        return {}
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RepositoryUpdateError(f"Invalid JSON in {manifest_path}: {exc}") from exc

    if data.get("version") != MANIFEST_VERSION:
        raise RepositoryUpdateError(
            f"Unsupported manifest version in {manifest_path}: {data.get('version')!r}"
        )
    libraries = data.get("libraries")
    if not isinstance(libraries, dict) or not all(
        isinstance(path, str) and isinstance(category, str)
        for path, category in libraries.items()
    ):
        raise RepositoryUpdateError(
            f"Manifest field 'libraries' in {manifest_path} must map paths to category names"
        )
    return dict(libraries)


def normalize_category_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.casefold())


def infer_category(intlib: Path, categories: Sequence[str], compiled_root: Path) -> str:
    if intlib.parent != compiled_root:
        return intlib.relative_to(compiled_root).parts[0]

    stem_key = normalize_category_key(intlib.stem)
    exact = {normalize_category_key(category): category for category in categories}
    if stem_key in exact:
        return exact[stem_key]

    # A practical bootstrap for old names such as CONNECTOR -> CONNECTORS and
    # FERRITE -> FERRITES.  Once synchronized, the explicit manifest wins.
    singular_matches = [
        category
        for category in categories
        if normalize_category_key(category).removesuffix("s") == stem_key.removesuffix("s")
    ]
    if len(singular_matches) == 1:
        return singular_matches[0]
    return UNKNOWN_CATEGORY


def render_manifest(mapping: Mapping[str, str]) -> str:
    ordered = {
        key: mapping[key]
        for key in sorted(mapping, key=str.casefold)
    }
    return json.dumps(
        {
            "version": MANIFEST_VERSION,
            "description": (
                "Generated mapping used to preserve the source category of each flat IntLib file."
            ),
            "libraries": ordered,
        },
        ensure_ascii=False,
        indent=2,
    ) + "\n"


def update_manifest(
    compiled_root: Path,
    mapping: Mapping[str, str],
    *,
    dry_run: bool,
) -> bool:
    manifest_path = compiled_root / MANIFEST_FILENAME
    rendered = render_manifest(mapping)
    original = manifest_path.read_text(encoding="utf-8") if manifest_path.exists() else ""
    changed = rendered != original
    if changed:
        print(f"{'Would update' if dry_run else 'Updated'} category manifest: {manifest_path}")
        if not dry_run:
            manifest_path.write_text(rendered, encoding="utf-8", newline="\n")
    else:
        print(f"Category manifest unchanged: {manifest_path}")
    return changed


def sync_intlibs(
    source_root: Path,
    compiled_root: Path,
    *,
    categories: Sequence[str] | None = None,
    dry_run: bool = False,
) -> SyncResult:
    """Collect IntLib files, preserve their categories, and remove outputs.

    All potential filename and category collisions are checked before any
    output directory is deleted.  A new IntLib may replace its previous
    compiled version, but two newly generated files with the same filename
    must be byte-identical and belong to the same category.
    """

    categories = list(categories if categories is not None else discover_categories(source_root))
    output_directories = find_output_directories(source_root)
    candidates: dict[str, list[IntLibCandidate]] = defaultdict(list)

    for output_dir in output_directories:
        category = category_for_output_directory(output_dir, source_root)
        for path in output_dir.rglob("*"):
            if path.is_file() and path.suffix.casefold() == ".intlib":
                candidates[path.name.casefold()].append(IntLibCandidate(path, category))

    # Validate all same-name candidates before making any destructive change.
    for candidate_group in candidates.values():
        if len(candidate_group) <= 1:
            continue
        hashes = {sha256(candidate.path) for candidate in candidate_group}
        source_categories = {candidate.category.casefold() for candidate in candidate_group}
        if len(hashes) != 1 or len(source_categories) != 1:
            rendered = "\n  - ".join(
                f"{candidate.path} [{candidate.category}]" for candidate in candidate_group
            )
            raise RepositoryUpdateError(
                "Generated IntLib files would overwrite the same flat destination "
                "with different data or categories:\n"
                f"  - {rendered}\n"
                "Use globally unique IntLib filenames."
            )

    if not dry_run:
        compiled_root.mkdir(parents=True, exist_ok=True)

    manifest_path = compiled_root / MANIFEST_FILENAME
    previous_mapping = load_manifest(manifest_path)
    existing_intlibs = discover_intlibs(compiled_root) if compiled_root.exists() else []
    existing_by_name = {path.name.casefold(): path for path in existing_intlibs if path.parent == compiled_root}

    changed = 0
    unchanged = 0
    synchronized_categories: dict[str, str] = {}
    for normalized_name, candidate_group in sorted(candidates.items()):
        candidate = sorted(candidate_group, key=lambda item: str(item.path).casefold())[0]
        destination = existing_by_name.get(normalized_name, compiled_root / candidate.path.name)
        same = destination.exists() and sha256(destination) == sha256(candidate.path)
        if same:
            unchanged += 1
            print(f"IntLib unchanged: {destination.name}")
        else:
            changed += 1
            print(
                f"{'Would update' if dry_run else 'Updated'} IntLib: "
                f"{candidate.path} -> {destination}"
            )
            if not dry_run:
                shutil.copy2(candidate.path, destination)
        synchronized_categories[destination.relative_to(compiled_root).as_posix()] = candidate.category

    # Work out the complete mapping after the planned copy.  Stale entries are
    # automatically pruned when their IntLib no longer exists.
    planned_intlibs = list(existing_intlibs)
    known_paths = {path.relative_to(compiled_root).as_posix().casefold() for path in planned_intlibs}
    for candidate_group in candidates.values():
        candidate = sorted(candidate_group, key=lambda item: str(item.path).casefold())[0]
        destination = existing_by_name.get(candidate.path.name.casefold(), compiled_root / candidate.path.name)
        relative_key = destination.relative_to(compiled_root).as_posix()
        if relative_key.casefold() not in known_paths:
            planned_intlibs.append(destination)
            known_paths.add(relative_key.casefold())

    previous_casefold = {key.casefold(): (key, value) for key, value in previous_mapping.items()}
    final_mapping: dict[str, str] = {}
    synchronized_casefold = {
        key.casefold(): category for key, category in synchronized_categories.items()
    }
    for intlib in sorted(planned_intlibs, key=lambda item: str(item).casefold()):
        key = intlib.relative_to(compiled_root).as_posix()
        if key.casefold() in synchronized_casefold:
            category = synchronized_casefold[key.casefold()]
        elif key.casefold() in previous_casefold:
            category = previous_casefold[key.casefold()][1]
        else:
            category = infer_category(intlib, categories, compiled_root)
        final_mapping[key] = category

    manifest_changed = update_manifest(compiled_root, final_mapping, dry_run=dry_run)

    for output_dir in sorted(output_directories, key=lambda item: len(item.parts), reverse=True):
        if not any(
            path.is_file() and path.suffix.casefold() == ".intlib"
            for path in output_dir.rglob("*")
        ):
            emit_warning(
                f"Generated directory contains no IntLib and will still be removed: {output_dir}",
                output_dir,
            )
        print(f"{'Would remove' if dry_run else 'Removed'} generated directory: {output_dir}")
        if not dry_run:
            shutil.rmtree(output_dir)

    return SyncResult(
        output_directories=len(output_directories),
        intlibs_found=sum(len(group) for group in candidates.values()),
        intlibs_changed=changed,
        intlibs_unchanged=unchanged,
        manifest_changed=manifest_changed,
        intlib_categories=final_mapping,
    )


def discover_intlibs(compiled_root: Path) -> list[Path]:
    if not compiled_root.exists():
        return []
    return sorted(
        [
            path
            for path in compiled_root.rglob("*")
            if path.is_file() and path.suffix.casefold() == ".intlib"
        ],
        key=lambda item: str(item.relative_to(compiled_root)).casefold(),
    )


def decode_intlib_payload(data: bytes, *, source: Path, stream_name: str) -> bytes:
    if not data:
        raise RepositoryUpdateError(f"Empty stream '{stream_name}' in {source}")
    marker = data[0]
    if marker == 0:
        return data[1:]
    if marker == 2:
        try:
            return zlib.decompress(data[1:])
        except zlib.error as exc:
            raise RepositoryUpdateError(
                f"Cannot decompress stream '{stream_name}' in {source}: {exc}"
            ) from exc
    raise RepositoryUpdateError(
        f"Unsupported IntLib stream encoding marker {marker} in '{stream_name}' of {source}"
    )


def read_compiled_parameters(intlib: Path) -> bytes:
    try:
        ole = olefile.OleFileIO(str(intlib))
    except Exception as exc:
        raise RepositoryUpdateError(f"Cannot open IntLib {intlib}: {exc}") from exc

    try:
        candidates = [
            stream
            for stream in ole.listdir(streams=True, storages=False)
            if stream[-1].replace(" ", "").casefold() == "parameters.bin"
        ]
        if len(candidates) != 1:
            raise RepositoryUpdateError(
                f"Expected exactly one Parameters.bin stream in {intlib}, found {len(candidates)}"
            )
        stream = candidates[0]
        raw = ole.openstream(stream).read()
        return decode_intlib_payload(raw, source=intlib, stream_name="/".join(stream))
    except RepositoryUpdateError:
        raise
    except Exception as exc:
        raise RepositoryUpdateError(f"Cannot read compiled parameters from {intlib}: {exc}") from exc
    finally:
        ole.close()


def iter_length_prefixed_records(data: bytes, source: Path) -> Iterator[bytes]:
    offset = 0
    while offset < len(data):
        if offset + 4 > len(data):
            raise RepositoryUpdateError(
                f"Truncated parameter record header at byte {offset} in {source}"
            )
        size = struct.unpack_from("<I", data, offset)[0]
        offset += 4
        end = offset + size
        if end > len(data):
            raise RepositoryUpdateError(
                f"Parameter record at byte {offset - 4} exceeds stream in {source}"
            )
        yield data[offset:end]
        offset = end


def decode_mixed_utf8_cp1252(raw: bytes) -> str:
    """Decode Altium text that can mix UTF-8 fields with legacy CP1252 bytes."""

    characters: list[str] = []
    offset = 0
    while offset < len(raw):
        first = raw[offset]
        if first < 0x80:
            characters.append(chr(first))
            offset += 1
            continue

        if 0xC2 <= first <= 0xDF:
            width = 2
        elif 0xE0 <= first <= 0xEF:
            width = 3
        elif 0xF0 <= first <= 0xF4:
            width = 4
        else:
            width = 1

        if width > 1 and offset + width <= len(raw):
            chunk = raw[offset : offset + width]
            try:
                characters.append(chunk.decode("utf-8"))
                offset += width
                continue
            except UnicodeDecodeError:
                pass

        characters.append(bytes([first]).decode("cp1252", errors="replace"))
        offset += 1
    return "".join(characters)


def parse_pipe_record(raw: bytes) -> dict[str, str]:
    """Parse an Altium pipe-delimited record.

    Altium can store a UTF-8 field and a legacy fallback in one record.  The
    UTF-8 form (``%UTF8%Field``) deliberately wins regardless of ordering.
    Legacy CP1252 bytes are decoded individually when they are not part of a
    valid UTF-8 sequence.  This matters for manufacturer names containing
    characters such as ``ü`` as well as older descriptions containing ``®``.
    """

    text = decode_mixed_utf8_cp1252(raw.rstrip(b"\x00"))
    values: dict[str, str] = {}
    utf8_values: dict[str, str] = {}
    for token in text.split("|"):
        if "=" not in token:
            continue
        key, value = token.split("=", 1)
        if key.startswith("%UTF8%"):
            utf8_values[key[len("%UTF8%") :]] = value
        else:
            values[key] = value
    values.update(utf8_values)
    return values


def normalize_parameter_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", name.casefold())


def get_parameter(parameters: Mapping[str, str], aliases: Sequence[str]) -> str:
    normalized = {
        normalize_parameter_name(name): value.strip()
        for name, value in parameters.items()
    }
    for alias in aliases:
        value = normalized.get(normalize_parameter_name(alias), "")
        if value:
            return value
    return ""


def parse_parameter_blob(
    data: bytes,
    *,
    category: str,
    intlib: Path,
    aliases: Mapping[str, Sequence[str]],
) -> list[Component]:
    components: list[Component] = []
    for raw_record in iter_length_prefixed_records(data, intlib):
        parameters = parse_pipe_record(raw_record)
        symbol = parameters.get("Library Reference", "").strip()
        if not symbol:
            # Footprint records share Parameters.bin but have no Library
            # Reference, so they must not become component catalog rows.
            continue
        manufacturer = get_parameter(parameters, aliases["manufacturer"])
        mpn = get_parameter(parameters, aliases["manufacturer_part_number"])
        package = get_parameter(parameters, aliases["package"])
        if not package:
            package = parameters.get("Footprint", "").strip()
        components.append(
            Component(
                category=category,
                symbol=symbol,
                manufacturer_part_number=mpn,
                manufacturer=manufacturer,
                package=package,
                intlib=intlib,
                parameters=parameters,
            )
        )
    return components


def parse_intlib(
    intlib: Path,
    *,
    category: str,
    aliases: Mapping[str, Sequence[str]],
) -> list[Component]:
    data = read_compiled_parameters(intlib)
    return parse_parameter_blob(data, category=category, intlib=intlib, aliases=aliases)


def markdown_cell(value: str) -> str:
    if not value:
        return "—"
    return (
        value.replace("\\", "\\\\")
        .replace("|", "\\|")
        .replace("\r\n", "<br>")
        .replace("\r", "<br>")
        .replace("\n", "<br>")
    )


def render_catalog(components: Sequence[Component], categories: Sequence[str]) -> str:
    grouped: dict[str, list[Component]] = defaultdict(list)
    for component in components:
        grouped[component.category].append(component)

    all_categories = sorted(set(categories) | set(grouped), key=str.casefold)
    lines = [
        "## Compiled Library Contents",
        "",
        "> This section is generated by `scripts/update_repository.py`. Do not edit it manually.",
        "> Data is read exclusively from the compiled libraries in `compiled/*.IntLib`.",
        "",
        f"Total: **{len(components)} components** in **{len(all_categories)} categories**.",
        "",
        "### Category Summary",
        "",
        "| Category | Components | IntLib files |",
        "|---|---:|---:|",
    ]

    for category in all_categories:
        items = grouped.get(category, [])
        intlib_count = len({item.intlib for item in items})
        lines.append(f"| {markdown_cell(category)} | {len(items)} | {intlib_count} |")

    populated = [category for category in all_categories if grouped.get(category)]
    if not populated:
        lines.extend(
            [
                "",
                "No compiled components were found. Compile the `LibPkg` in Altium Designer "
                "and push the `Project Outputs for ...` directory.",
            ]
        )
        return "\n".join(lines)

    for category in populated:
        lines.extend(
            [
                "",
                f"### {category}",
                "",
                "| Manufacturer part number | Manufacturer | Package |",
                "|---|---|---|",
            ]
        )
        items = sorted(
            grouped[category],
            key=lambda item: (
                item.manufacturer_part_number.casefold(),
                item.manufacturer.casefold(),
                item.package.casefold(),
                item.symbol.casefold(),
            ),
        )
        for component in items:
            lines.append(
                "| "
                + " | ".join(
                    [
                        markdown_cell(component.manufacturer_part_number),
                        markdown_cell(component.manufacturer),
                        markdown_cell(component.package),
                    ]
                )
                + " |"
            )
    return "\n".join(lines)


def update_readme(readme: Path, catalog: str, *, dry_run: bool = False) -> bool:
    if not readme.exists():
        raise RepositoryUpdateError(f"README file does not exist: {readme}")
    original = readme.read_text(encoding="utf-8")
    start_count = original.count(CATALOG_START)
    end_count = original.count(CATALOG_END)

    if start_count == 0 and end_count == 0:
        updated = (
            original.rstrip()
            + "\n\n"
            + CATALOG_START
            + "\n\n"
            + catalog.rstrip()
            + "\n\n"
            + CATALOG_END
            + "\n"
        )
    elif start_count == 1 and end_count == 1:
        prefix, remainder = original.split(CATALOG_START, 1)
        _old_catalog, suffix = remainder.split(CATALOG_END, 1)
        updated = (
            prefix.rstrip()
            + "\n\n"
            + CATALOG_START
            + "\n\n"
            + catalog.rstrip()
            + "\n\n"
            + CATALOG_END
            + suffix
        )
        if not updated.endswith("\n"):
            updated += "\n"
    else:
        raise RepositoryUpdateError(
            f"README must contain either zero or one matching catalog marker pair: {readme}"
        )

    changed = updated != original
    if changed:
        print(f"{'Would update' if dry_run else 'Updated'} catalog in {readme}")
        if not dry_run:
            readme.write_text(updated, encoding="utf-8", newline="\n")
    else:
        print(f"README catalog unchanged: {readme}")
    return changed


def emit_warning(message: str, path: Path | None = None) -> None:
    if os.environ.get("GITHUB_ACTIONS") == "true":
        escaped = message.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
        file_part = f" file={path.as_posix()}" if path else ""
        print(f"::warning{file_part}::{escaped}")
    else:
        location = f" [{path}]" if path else ""
        print(f"WARNING{location}: {message}", file=sys.stderr)


def validate_components(
    components: Sequence[Component],
    *,
    known_categories: Iterable[str],
    configured_categories: Iterable[str],
) -> list[str]:
    warnings: list[str] = []
    configured = {category.casefold() for category in configured_categories}
    for category in known_categories:
        if category == UNKNOWN_CATEGORY:
            warnings.append(
                "At least one compiled IntLib has no category mapping; inspect compiled/catalog-index.json"
            )
        elif category.casefold() not in configured:
            warnings.append(
                f"Category '{category}' is auto-detected but has no parameter guidance in "
                "config/catalog_schema.json"
            )

    ignored_mpn = {"", "generic", "n/a", "na", "none", "tbd"}
    for component in components:
        missing = []
        if not component.manufacturer_part_number:
            missing.append("Part Number / MPN")
        if not component.manufacturer:
            missing.append("Manufacturer / MFN")
        if not component.package:
            missing.append("Package")
        if missing:
            warnings.append(
                f"{component.intlib}: compiled symbol '{component.symbol}' is missing "
                "catalog field(s): " + ", ".join(missing)
            )

        # Advisory consistency check performed on the compiled record itself.
        mpn_key = normalize_parameter_name(component.manufacturer_part_number)
        value_key = normalize_parameter_name(component.parameters.get("Value", ""))
        footprint_key = normalize_parameter_name(component.parameters.get("Footprint", ""))
        symbol_key = normalize_parameter_name(component.symbol)
        if component.manufacturer_part_number.strip().casefold() not in ignored_mpn:
            if footprint_key == mpn_key and symbol_key not in {"", mpn_key}:
                warnings.append(
                    f"{component.intlib}: MPN and Footprint identify "
                    f"'{component.manufacturer_part_number}', but Library Reference is "
                    f"'{component.symbol}'"
                )
            if value_key and value_key == footprint_key and value_key != mpn_key:
                warnings.append(
                    f"{component.intlib}: compiled Value/Footprint identify "
                    f"'{component.parameters.get('Value', '')}', but Part Number is "
                    f"'{component.manufacturer_part_number}'"
                )

    # Exact duplicate real ordering codes are usually accidental.  Generic and
    # N/A entries are excluded because reusable passives/test points can share them.
    seen: dict[tuple[str, str], Component] = {}
    for component in components:
        mpn_key = component.manufacturer_part_number.strip().casefold()
        if mpn_key in ignored_mpn:
            continue
        key = (component.manufacturer.strip().casefold(), mpn_key)
        previous = seen.get(key)
        if previous is not None:
            warnings.append(
                "Duplicate Manufacturer + MPN: "
                f"'{component.manufacturer}' / '{component.manufacturer_part_number}' in "
                f"{previous.intlib} and {component.intlib}"
            )
        else:
            seen[key] = component
    return warnings


def load_config(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RepositoryUpdateError(f"Missing configuration file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise RepositoryUpdateError(f"Invalid JSON in {path}: {exc}") from exc

    aliases = data.get("catalog_aliases", {})
    required_alias_groups = {"manufacturer_part_number", "manufacturer", "package"}
    missing = required_alias_groups - set(aliases)
    if missing:
        raise RepositoryUpdateError(
            f"Configuration {path} lacks alias group(s): {', '.join(sorted(missing))}"
        )
    for key in required_alias_groups:
        if not isinstance(aliases[key], list) or not all(
            isinstance(item, str) and item for item in aliases[key]
        ):
            raise RepositoryUpdateError(f"Alias group '{key}' in {path} must be a string list")
    return data


def resolve_from_repo(repo_root: Path, value: Path) -> Path:
    return value if value.is_absolute() else repo_root / value


def category_for_intlib(
    intlib: Path,
    *,
    compiled_root: Path,
    mapping: Mapping[str, str],
) -> str:
    relative_key = intlib.relative_to(compiled_root).as_posix()
    direct = mapping.get(relative_key)
    if direct:
        return direct
    casefold_mapping = {key.casefold(): value for key, value in mapping.items()}
    return casefold_mapping.get(relative_key.casefold(), UNKNOWN_CATEGORY)


def build_argument_parser() -> argparse.ArgumentParser:
    default_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=default_root)
    parser.add_argument("--source", type=Path, default=Path("source"))
    parser.add_argument("--compiled", type=Path, default=Path("compiled"))
    parser.add_argument("--readme", type=Path, default=Path("README.md"))
    parser.add_argument("--config", type=Path, default=Path("config/catalog_schema.json"))
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="show intended synchronization and README changes without writing",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="return a non-zero exit code when compiled metadata warnings are found",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    repo_root = args.repo_root.resolve()
    source_root = resolve_from_repo(repo_root, args.source).resolve()
    compiled_root = resolve_from_repo(repo_root, args.compiled).resolve()
    readme = resolve_from_repo(repo_root, args.readme).resolve()
    config_path = resolve_from_repo(repo_root, args.config).resolve()

    if not source_root.is_dir():
        raise RepositoryUpdateError(f"Source directory does not exist: {source_root}")

    config = load_config(config_path)
    aliases = config["catalog_aliases"]
    categories = discover_categories(source_root)

    sync_result = sync_intlibs(
        source_root,
        compiled_root,
        categories=categories,
        dry_run=args.dry_run,
    )

    intlibs = discover_intlibs(compiled_root)
    # During a dry run, generated candidates have not physically reached
    # compiled/, so the existing catalog is intentionally parsed as-is.
    components: list[Component] = []
    for intlib in intlibs:
        category = category_for_intlib(
            intlib,
            compiled_root=compiled_root,
            mapping=sync_result.intlib_categories,
        )
        parsed = parse_intlib(intlib, category=category, aliases=aliases)
        if not parsed:
            emit_warning(f"No compiled schematic components found in {intlib}", intlib)
        components.extend(parsed)

    catalog_categories = sorted(
        set(categories) | set(sync_result.intlib_categories.values()),
        key=str.casefold,
    )
    warnings = validate_components(
        components,
        known_categories=catalog_categories,
        configured_categories=config.get("category_parameters", {}).keys(),
    )
    for warning in warnings:
        emit_warning(warning)

    catalog = render_catalog(components, catalog_categories)
    readme_changed = update_readme(readme, catalog, dry_run=args.dry_run)

    print(
        "Summary: "
        f"{len(intlibs)} compiled IntLib, {len(components)} compiled components, "
        f"{sync_result.intlibs_found} generated IntLib, "
        f"{sync_result.intlibs_changed} compiled file(s) changed, "
        f"{sync_result.output_directories} output folder(s) removed, "
        f"README {'changed' if readme_changed else 'unchanged'}, "
        f"{len(warnings)} warning(s)."
    )
    if args.strict and warnings:
        return 2
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RepositoryUpdateError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
