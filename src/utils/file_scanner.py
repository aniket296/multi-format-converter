"""Recursive document file scanner and directory tree mirror output path resolver."""
import os
from pathlib import Path
from typing import Optional
from src.models.doc_format import CollisionPolicy, DocFormat


def scan_path_for_documents(
    path: str,
    allowed_formats: Optional[set[DocFormat]] = None,
) -> list[tuple[str, Optional[str], DocFormat]]:
    """
    Scans a single file or recursively walks a root directory for supported documents.

    Returns a list of tuples:
        (absolute_file_path, root_dir_or_None, detected_doc_format)
    """
    target = Path(path).resolve()
    if not target.exists():
        return []

    results: list[tuple[str, Optional[str], DocFormat]] = []

    if target.is_file():
        doc_fmt = DocFormat.from_extension(target.suffix)
        if doc_fmt is not None and (allowed_formats is None or doc_fmt in allowed_formats):
            results.append((str(target), None, doc_fmt))
        return results

    if target.is_dir():
        root_dir_str = str(target)
        for dirpath, dirnames, filenames in os.walk(target):
            # Ignore hidden/system directories
            dirnames[:] = sorted(
                d for d in dirnames if not d.startswith(".") and d not in ("__pycache__", "venv", ".venv")
            )
            for fname in sorted(filenames):
                if fname.startswith(".") or fname.startswith("~$"):
                    continue
                full_path = Path(dirpath) / fname
                doc_fmt = DocFormat.from_extension(full_path.suffix)
                if doc_fmt is not None and (allowed_formats is None or doc_fmt in allowed_formats):
                    results.append((str(full_path.resolve()), root_dir_str, doc_fmt))

    return results


def resolve_output_path(
    source_path: str,
    root_ingest_dir: Optional[str],
    output_dir: str,
    target_format: DocFormat,
    preserve_tree: bool,
    collision_policy: CollisionPolicy,
) -> tuple[str, bool]:
    """
    Computes the destination file path for a conversion job and applies the collision policy.

    Returns:
        (resolved_target_path, should_skip)
    """
    src = Path(source_path).resolve()
    out_base = Path(output_dir).resolve() if output_dir else src.parent

    # Determine target directory preserving sub-folder hierarchy when requested
    target_subdir = out_base
    if preserve_tree and root_ingest_dir:
        root_path = Path(root_ingest_dir).resolve()
        try:
            rel_parent = src.parent.relative_to(root_path)
            target_subdir = out_base / rel_parent
        except ValueError:
            target_subdir = out_base

    os.makedirs(target_subdir, exist_ok=True)

    stem = src.stem
    ext = f".{target_format.value}"
    candidate = target_subdir / f"{stem}{ext}"

    if not candidate.exists():
        return str(candidate), False

    if collision_policy == CollisionPolicy.SKIP:
        return str(candidate), True

    if collision_policy == CollisionPolicy.OVERWRITE:
        return str(candidate), False

    # CollisionPolicy.RENAME: append _1, _2, ... before extension
    counter = 1
    while True:
        renamed = target_subdir / f"{stem}_{counter}{ext}"
        if not renamed.exists():
            return str(renamed), False
        counter += 1
