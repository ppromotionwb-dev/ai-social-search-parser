from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from .collectors import get_collectors
from .exporters import export_csv, export_html, send_telegram
from .judge import Judge
from .models import STATUSES
from .pipeline import run_pipeline
from .queries import load_queries
from .storage import Storage


def _storage(args) -> Storage:
    return Storage(args.db or os.environ.get("LEADAGENT_DB", "data/leadagent.db"))


def _export(storage: Storage, out_dir: Path, formats: list[str]) -> None:
    leads = storage.leads()
    if "csv" in formats:
        print("CSV:", export_csv(leads, out_dir / "leads.csv"))
    if "html" in formats:
        print("HTML:", export_html(leads, out_dir / "dashboard.html"))
    if "telegram" in formats:
        new = storage.leads(only_unnotified=True)
        storage.mark_notified(send_telegram(new))
        print(f"Telegram: sent {len(new)} new lead(s)")


def cmd_run(args) -> int:
    queries, cfg = load_queries(args.queries)
    storage = _storage(args)
    judge = Judge()
    if judge.is_stub:
        print("note: ANTHROPIC_API_KEY not set — using stub judge", file=sys.stderr)
    stats = run_pipeline(queries, cfg, get_collectors(args.fixtures), storage, judge)
    print(f"collected={stats.collected} duplicates={stats.duplicates} prefiltered={stats.prefiltered} "
          f"judged={stats.judged} leads={stats.leads}")
    for err in stats.errors:
        print("error:", err, file=sys.stderr)
    _export(storage, Path(args.out_dir), args.formats)
    return 0


def cmd_export(args) -> int:
    _export(_storage(args), Path(args.out_dir), args.formats)
    return 0


def cmd_list(args) -> int:
    for r in _storage(args).leads(status=args.status):
        print(f"{r['score']:>3}  {r['status']:<9} {r['network']:<8} {r['url']}\n     {r['reason']}")
    return 0


def cmd_browser(args) -> int:
    from .collectors.browser import open_for_manual_login
    open_for_manual_login(get_collectors()[args.network])
    return 0


def cmd_status(args) -> int:
    ok = _storage(args).set_status(args.url, args.status)
    print("updated" if ok else "not found")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="leadagent")
    p.add_argument("--db", help="SQLite path (default: $LEADAGENT_DB or data/leadagent.db)")
    sub = p.add_subparsers(dest="cmd", required=True)

    def formats(sp, default):
        sp.add_argument("--formats", nargs="+", choices=["csv", "html", "telegram"], default=default)
        sp.add_argument("--out-dir", default="data/out")

    r = sub.add_parser("run", help="collect -> dedupe -> prefilter -> judge -> export")
    r.add_argument("--queries", default="queries.yaml")
    r.add_argument("--fixtures", nargs="?", const="tests/fixtures", default=None, metavar="DIR",
                   help="use sample posts instead of real collectors (default dir: tests/fixtures)")
    formats(r, ["csv", "html"])
    r.set_defaults(fn=cmd_run)

    e = sub.add_parser("export", help="export stored leads")
    formats(e, ["csv", "html"])
    e.set_defaults(fn=cmd_export)

    l = sub.add_parser("list", help="print stored leads")
    l.add_argument("--status", choices=STATUSES)
    l.set_defaults(fn=cmd_list)

    s = sub.add_parser("status", help="set lead status (new/contacted/skip)")
    s.add_argument("url")
    s.add_argument("status", choices=STATUSES)
    s.set_defaults(fn=cmd_status)

    b = sub.add_parser("browser", help="open the persistent browser profile so YOU can sign in manually")
    b.add_argument("network", choices=["linkedin", "facebook"])
    b.set_defaults(fn=cmd_browser)

    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
