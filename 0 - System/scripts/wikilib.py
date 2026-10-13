#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
wikilib — shared helpers for the wiki bookkeeping scripts.

The boundary is an allowlist: only the folders in ALLOWED are ever listed or read,
nothing under them may be reached through a symlink, and every read opens each path
component with O_NOFOLLOW. Anything else (the private folder included) is simply
outside the world these scripts can see, so they never need to know its name.
"""
import os, re, shutil, stat, unicodedata
from datetime import datetime
from pathlib import Path

import yaml

# Vault root: from VAULT_ROOT (for tests), or two levels above scripts/.
VAULT  = Path(os.environ.get("VAULT_ROOT") or Path(__file__).resolve().parents[2])
WIKI   = VAULT / "7 - Wikipedia"
RAW    = WIKI / "raw"
NOTES  = VAULT / "2 - Notes"
TOPICS = VAULT / "1 - Topics"
SYS    = VAULT / "0 - System"

# The allowlist of top-level folders.
ALLOWED = (WIKI.name, NOTES.name, TOPICS.name, SYS.name)

# Catalogs in 7 - Wikipedia/ that are not summaries.
NON_CONTENT = {"index.md", "log.md"}


def nfc(s):
    return unicodedata.normalize("NFC", s or "")


def today():
    return datetime.now().strftime("%Y-%m-%d")


def rel(path):
    return nfc(str(Path(path).relative_to(VAULT)))


# ---------- the boundary ----------

def has_symlink(path):
    """A symlink anywhere on the path, or a path that can't be inspected, counts as one."""
    p = Path(os.path.abspath(path))
    for item in reversed((p, *p.parents)):
        try:
            if item.is_symlink():
                return True
        except OSError:
            return True
    return False


def is_forbidden(path):
    """True for anything outside the allowlisted folders, any `..`, or any symlink on the path."""
    path = Path(path)
    try:
        parts = path.relative_to(VAULT).parts
    except ValueError:
        return True
    if not parts or parts[0] not in ALLOWED or ".." in parts:
        return True
    # Nested vault copies and numbered areas inside an allowed folder are refused too.
    if any(re.match(r"^\d+\s+-\s+", part) for part in parts[1:]):
        return True
    return has_symlink(path)


def read_text(path):
    """Text of a regular file inside the boundary, opening every component with O_NOFOLLOW."""
    p = Path(os.path.abspath(path))
    if is_forbidden(p):
        raise PermissionError("Unavailable input")
    flags = os.O_RDONLY | os.O_NOFOLLOW
    dir_fd = os.open(p.anchor, flags | os.O_DIRECTORY)
    try:
        for part in p.parts[1:-1]:
            next_fd = os.open(part, flags | os.O_DIRECTORY, dir_fd=dir_fd)
            os.close(dir_fd)
            dir_fd = next_fd
        fd = os.open(p.name, flags | os.O_NONBLOCK, dir_fd=dir_fd)
        with os.fdopen(fd, "rb") as f:
            if not stat.S_ISREG(os.fstat(f.fileno()).st_mode):
                raise PermissionError("Unavailable input")
            return f.read().decode("utf-8-sig").replace("\r\n", "\n")
    finally:
        os.close(dir_fd)


# ---------- frontmatter ----------
# Same parser as the auditor's split_header; test_audit checks the two copies agree.

class HeaderLoader(yaml.SafeLoader):
    """SafeLoader without timestamps, so dates stay strings."""


HeaderLoader.yaml_implicit_resolvers = {
    ch: [(tag, rx) for tag, rx in items if tag != "tag:yaml.org,2002:timestamp"]
    for ch, items in yaml.SafeLoader.yaml_implicit_resolvers.items()}

HEADER_FENCE = re.compile(r"\A---[ \t]*\n(.*?)^---[ \t]*(?:\n|\Z)", re.S | re.M)


def split_header(text):
    """(meta, body). A malformed header reads as {} and stays in the body."""
    m = HEADER_FENCE.match(text)
    if not m:
        return {}, text
    try:
        meta = yaml.load(m.group(1), Loader=HeaderLoader)
    except (yaml.YAMLError, RecursionError, ValueError):
        return {}, text
    if meta is None:
        meta = {}
    if not isinstance(meta, dict):
        return {}, text
    return {nfc(str(k)): v for k, v in meta.items()}, text[m.end():]


def read_page(path):
    return split_header(read_text(path))


# ---------- discovery ----------

def iter_wiki_pages():
    """(path, meta, body) for the summaries in 7 - Wikipedia/: top level only, no catalogs,
    no `_` files, no reports."""
    if is_forbidden(WIKI) or not WIKI.is_dir():
        return
    for p in sorted(WIKI.glob("*.md")):
        name = nfc(p.name)
        if name in NON_CONTENT or name.startswith("_") or is_forbidden(p):
            continue
        meta, body = read_page(p)
        tags = meta.get("tags") or []
        if isinstance(tags, str):
            tags = [tags]
        if meta.get("type") == "report" or "report" in tags:
            continue
        yield p, meta, body


def all_md_index():
    """stem -> [paths] for every Markdown file under the allowed folders, never the vault root."""
    idx = {}
    for root in (WIKI, NOTES, TOPICS, SYS):
        if is_forbidden(root) or not root.is_dir():
            continue
        for here, dirs, files in os.walk(root, followlinks=False):
            dirs[:] = sorted(d for d in dirs
                             if not d.startswith(".") and not is_forbidden(Path(here) / d))
            for name in sorted(files):
                p = Path(here) / name
                if p.suffix == ".md" and not is_forbidden(p):
                    idx.setdefault(nfc(p.stem), []).append(p)
    return idx


def resolve_link(inner, md_index=None):
    """(status, path or None) for the inside of a [[wikilink]]; status is ok | missing | ambiguous.

    A `raw/...` path is read relative to the wiki folder, the way Obsidian resolves it.
    """
    inner = nfc(inner.split("|")[0].split("#")[0].strip())
    cand = inner[:-3] if inner.endswith(".md") else inner

    def visible(p):
        return not is_forbidden(p) and p.is_file()

    if "/" in cand or "\\" in cand:
        if "\\" in cand or Path(cand).is_absolute() or ".." in Path(cand).parts:
            return ("missing", None)
        base = WIKI if cand.startswith("raw/") else VAULT
        p = base / (cand + ".md")
        return ("ok", p) if visible(p) else ("missing", None)
    md_index = all_md_index() if md_index is None else md_index
    matches = [p for p in md_index.get(nfc(cand), []) if visible(p)]
    if len(matches) == 1:
        return ("ok", matches[0])
    return ("missing", None) if not matches else ("ambiguous", None)


# ---------- backups ----------

def backup(paths, label):
    """Copy files to 7 - Wikipedia/.backup/<timestamp-label>/ before modifying them.
    The whole batch is checked before anything is created or copied."""
    paths = [Path(p) for p in paths]
    if not re.fullmatch(r"[\w-]+", label) or any(is_forbidden(p) for p in paths):
        raise PermissionError("Unavailable backup target")
    dest = WIKI / ".backup" / f"{datetime.now():%Y%m%d-%H%M%S}-{label}"
    if has_symlink(dest):
        raise PermissionError("Unavailable backup target")
    for p in paths:
        if not p.exists():
            continue
        target = dest / p.relative_to(VAULT)
        target.parent.mkdir(parents=True, exist_ok=True)
        if is_forbidden(p) or has_symlink(target):
            raise PermissionError("Unavailable backup target")
        shutil.copy2(p, target)
    return dest
