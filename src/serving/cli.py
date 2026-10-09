"""Serving CLI — the read-only consumer boundary for the first vertical slice.

Single-user, personal-use (D23 §13; D16 §13 non-goals): a command-line consumer that
reads *only* through the serving/query layer over a verified qualified baseline. It
opens no network listener, selects no authentication, and introduces no
multi-user/enterprise architecture. Every subcommand is read-only with respect to the
baseline package; the only writes are to the caller-supplied ``--state`` directory
(durable state class (4)), which must live outside the package.

Commands:
  verify    verify a package against its manifests (and, with --m2, the pinned M2 pin)
  build     build the class-(4) index from the verified baseline into --state
  query     run the Q3 instrument query (D16-10) and print canonical JSON to stdout
  rebuild   delete and rebuild the class-(4) state (delegated operation (b))
  info      print a diagnostic summary of the serving state

Exit codes: 0 = ok; 2 = usage/verification failure (fail closed); 3 = index/stale
failure. No partial results are printed on failure.
"""

from __future__ import annotations

import argparse
import json
import sys

from . import baseline as baseline_mod
from .index import index_state, load_index, write_index, build_index, ServingIndexError
from .query import QUERY_ID, query_instrument
from .rebuild import rebuild_state


def _print_json(obj) -> None:
    sys.stdout.write(
        json.dumps(obj, sort_keys=True, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    )


def _open(args, verify_files=True):
    spec = baseline_mod.DEFAULT_M2_SPEC if getattr(args, "m2", False) else None
    return baseline_mod.open_baseline(args.package, spec=spec, verify_files=verify_files)


def cmd_verify(args) -> int:
    try:
        handle = _open(args, verify_files=not args.fast)
    except baseline_mod.BaselineError as exc:
        _print_json({"result": "fail", "check": exc.check, "detail": exc.detail})
        return 2
    _print_json(
        {
            "result": "pass",
            "checks_passed": list(handle.checks_passed),
            "manifest_sha256": handle.manifest_digest,
            "manifest_entries": len(handle.manifest_entries),
            "total_bytes": handle.total_bytes,
            "run_id": handle.marker.get("run_id"),
            "pinned": "m2" if args.m2 else "unpinned",
        }
    )
    return 0


def cmd_build(args) -> int:
    try:
        handle = _open(args)
        document = build_index(handle)
        digest = write_index(args.state, document)
    except (baseline_mod.BaselineError, ServingIndexError) as exc:
        _print_json({"result": "fail", "detail": str(exc)})
        return 3
    _print_json(
        {
            "result": "pass",
            "index_sha256": digest,
            "counts": document["counts"],
            "partitions": sorted(document["partitions"].keys()),
            "package_manifest_sha256": document["package"]["manifest_sha256"],
        }
    )
    return 0


def cmd_query(args) -> int:
    try:
        handle = _open(args)
        document, _digest = load_index(args.state, handle)
        rows = query_instrument(handle, document, args.symbol, args.series, year=args.year)
    except (baseline_mod.BaselineError, ServingIndexError) as exc:
        _print_json({"result": "fail", "detail": str(exc)})
        return 3
    _print_json({"query": QUERY_ID, "result_count": len(rows), "rows": list(rows)})
    return 0


def cmd_rebuild(args) -> int:
    try:
        handle = _open(args)
        report = rebuild_state(handle, args.state)
    except (baseline_mod.BaselineError, ServingIndexError) as exc:
        _print_json({"result": "fail", "detail": str(exc)})
        return 3
    _print_json({"result": "pass", **report})
    return 0


def cmd_info(args) -> int:
    state = index_state(args.state)
    if state is None:
        _print_json({"result": "fail", "detail": "no serving state at %s" % args.state})
        return 3
    _print_json({"result": "pass", **state})
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="serving", description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    def add_common(p, state=False):
        p.add_argument("--package", required=True, help="path to the qualified run package")
        p.add_argument("--m2", action="store_true", help="pin to the qualified M2 baseline identity")
        if state:
            p.add_argument("--state", required=True, help="serving state dir (OUTSIDE the package)")

    p_verify = sub.add_parser("verify", help="verify a package against its manifests")
    add_common(p_verify)
    p_verify.add_argument("--fast", action="store_true", help="skip per-file digest recompute")
    p_verify.set_defaults(func=cmd_verify)

    p_build = sub.add_parser("build", help="build the class-(4) index")
    add_common(p_build, state=True)
    p_build.set_defaults(func=cmd_build)

    p_query = sub.add_parser("query", help="run the Q3 instrument query")
    add_common(p_query, state=True)
    p_query.add_argument("symbol")
    p_query.add_argument("series")
    p_query.add_argument("--year", type=int, default=None)
    p_query.set_defaults(func=cmd_query)

    p_rebuild = sub.add_parser("rebuild", help="delete and rebuild class-(4) state (op b)")
    add_common(p_rebuild, state=True)
    p_rebuild.set_defaults(func=cmd_rebuild)

    p_info = sub.add_parser("info", help="summarise the serving state")
    p_info.add_argument("--state", required=True)
    p_info.set_defaults(func=cmd_info)
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
