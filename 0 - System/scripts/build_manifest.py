#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_manifest.py — regenerates .manifest.json: which source produced which summary.
Merges the existing manifest with what the pages' actual wiki_sources say, so history
is never lost. A record whose source or page has left the boundary is dropped.
"""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import wikilib as V


def require_public_target(path):
    """Reject unavailable targets before body reads, backups or replacement."""
    if V.is_forbidden(path):
        raise SystemExit("Unavailable bookkeeping target; operation refused.")

DOT = V.WIKI / ".manifest.json"


def get_date(meta):
    return str(meta.get("last_compiled") or meta.get("generated_at") or V.today())


def add(store, path, page, ingested):
    key = V.nfc(path)
    rec = store.setdefault(key, {"ingested": ingested, "pages": set()})
    if page:
        rec["pages"].add(V.nfc(page))
    # keep the earliest date
    if ingested and ingested < rec["ingested"]:
        rec["ingested"] = ingested


def reference_is_forbidden(reference, page=False):
    """Check historical local targets without opening their bodies.

    Missing permitted targets are history, not deletion candidates. URLs and
    non-Markdown records remain legacy history; no semantic reclassification.
    """
    inner = str(reference).strip().removeprefix("[[").removesuffix("]]")
    inner = inner.split("|")[0].split("#")[0].strip()
    if inner.startswith(("https://", "http://")):
        return False
    ref = Path(inner)
    if page and len(ref.parts) == 1:
        target = V.WIKI / ref
    elif inner.startswith("raw/"):
        target = V.WIKI / ref
    else:
        target = V.VAULT / ref
    candidates = [target]
    if not target.suffix:
        candidates.append(target.with_suffix(".md"))
    if not page and len(ref.parts) == 1:
        for directory in (V.RAW, V.NOTES, V.TOPICS):
            candidate = directory / ref
            candidates.append(candidate if candidate.suffix else candidate.with_suffix(".md"))
    return any(V.is_forbidden(p) for p in candidates)


def load_existing(store):
    """Fold the current manifest into store. Returns the files that are safe to back up."""
    require_public_target(DOT)
    if not DOT.exists():
        return []
    clean = True
    for e in json.loads(V.read_text(DOT)):
        if reference_is_forbidden(e["path"]):
            clean = False
            continue
        date = e.get("ingested", V.today())
        add(store, e["path"], None, date)
        for pg in e.get("pages_produced", []):
            if reference_is_forbidden(pg, page=True):
                clean = False
                continue
            add(store, e["path"], pg, date)
    # Copying a manifest that maps excluded files would recreate those mappings in .backup.
    return [DOT] if clean else []


def derive_from_pages(store):
    md_index = V.all_md_index()
    for p, meta, _ in V.iter_wiki_pages():
        srcs = meta.get("wiki_sources", [])
        if isinstance(srcs, str):
            srcs = [srcs]
        ingested = get_date(meta)
        for entry in srcs:
            inner = str(entry).strip()
            if inner.startswith("[[") and inner.endswith("]]"):
                inner = inner[2:-2].strip()
            status, target = V.resolve_link(inner, md_index)
            if status != "ok":
                continue                      # problems are already in the report
            if V.nfc(str(target)) == V.nfc(str(p)):
                continue                      # self-reference
            tparents = Path(target).parents
            if V.WIKI in tparents and V.RAW not in tparents:
                continue                      # a wiki page, not a real source
            add(store, V.rel(target), p.stem, ingested)


def main():
    store = {}
    clean_backups = load_existing(store)
    derive_from_pages(store)

    out = [{"path": k,
            "ingested": v["ingested"],
            "pages_produced": sorted(v["pages"])}
           for k, v in sorted(store.items(), key=lambda kv: kv[1]["ingested"])]

    require_public_target(DOT)
    V.backup(clean_backups, "manifest")
    require_public_target(DOT)
    DOT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"✅ Manifest written: {V.rel(DOT)} ({len(out)} sources)")
    print("Limitations: external URLs and non-Markdown records are not validated; permitted history is preserved.")
    print("   Sources:")
    for e in out:
        print(f"     {e['ingested']}  {e['path']}  →  {', '.join(e['pages_produced'])}")


if __name__ == "__main__":
    main()
