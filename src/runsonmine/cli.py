"""runsonmine validate | add | build-site"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from .site import build
from .validate import check_file, content_id

ROOT = Path.cwd()


def _validate(paths: list[Path]) -> int:
    files = [f for p in paths for f in (sorted(p.glob("*.json")) if p.is_dir() else [p])]
    bad = 0
    for f in files:
        v = check_file(f)
        status = "ok" if v.ok else "REJECTED"
        extra = f" [{', '.join(v.flags)}]" if v.flags else ""
        print(f"{status:8s} {f}{extra}")
        for e in v.errors:
            print(f"         - {e}")
        bad += not v.ok
    print(f"{len(files) - bad} valid, {bad} rejected")
    return 1 if bad else 0


def _add(src: Path, results_dir: Path) -> int:
    v = check_file(src)
    if not v.ok:
        for e in v.errors:
            print(f"rejected: {e}")
        return 1
    result = json.loads(src.read_text(encoding="utf-8"))
    dest = results_dir / f"{content_id(result)}.json"
    results_dir.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        print(f"already added: {dest}")
        return 0
    shutil.copyfile(src, dest)
    print(f"added {dest}" + (f" (flags: {', '.join(v.flags)})" if v.flags else ""))
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="runsonmine")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("validate", help="check result files or folders")
    p.add_argument("paths", nargs="*", type=Path, default=[ROOT / "data" / "results"])
    p = sub.add_parser("add", help="validate a result and copy it into data/results/")
    p.add_argument("file", type=Path)
    p.add_argument("--results-dir", type=Path, default=ROOT / "data" / "results")
    p = sub.add_parser("build-site", help="build the static site")
    p.add_argument("--results-dir", type=Path, default=ROOT / "data" / "results")
    p.add_argument("--out", type=Path, default=ROOT / "site")
    args = ap.parse_args(argv)
    if args.cmd == "validate":
        return _validate(args.paths)
    if args.cmd == "add":
        return _add(args.file, args.results_dir)
    n = build(args.results_dir, args.out)
    print(f"built {args.out / 'index.html'} with {n} results")
    return 0


if __name__ == "__main__":
    sys.exit(main())
