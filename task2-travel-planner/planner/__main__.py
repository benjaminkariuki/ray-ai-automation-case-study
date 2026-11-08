"""Command line.

  python -m planner build --page <PAGE_URL_OR_ID> [--with-samples]   one-time: create the workspace in Notion
  python -m planner briefs [--all]                                  refresh Trip Briefs that changed (or all)

Settings come from environment variables or a .env file: NOTION_TOKEN, NOTION_DATA_SOURCE_ID (see .env.example).
"""
import argparse
import json
import os
import re
from pathlib import Path

from .brief import needs_refresh, prop, write_brief
from .notion import Notion
from .sample_data import TRIPS, page_properties
from .workspace import create_workspace

ROOT = Path(__file__).resolve().parent.parent


def load_dotenv():
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def page_id_from(value):
    m = re.search(r"([0-9a-f]{32})", value.replace("-", ""))
    if not m:
        raise SystemExit(f"Could not find a Notion page id in: {value}")
    return m.group(1)


def refresh_briefs(notion, data_source_id, force_all=False):
    pages = notion.query(data_source_id)
    done = 0
    for page in pages:
        if force_all or needs_refresh(page):
            write_brief(notion, page)
            done += 1
            print(f"Brief updated: {prop(page, 'Trip')}")
    print(f"{done} of {len(pages)} trip briefs refreshed.")
    return done


def main():
    load_dotenv()
    ap = argparse.ArgumentParser(description="Executive Travel Planner (Notion)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="Create the workspace under an existing (connected) Notion page")
    b.add_argument("--page", default=os.environ.get("NOTION_PAGE_URL"), help="Page URL or id")
    b.add_argument("--with-samples", action="store_true", help="Add 5 sample trips")
    r = sub.add_parser("briefs", help="Refresh Trip Briefs")
    r.add_argument("--all", action="store_true", help="Rebuild every brief, not only changed trips")
    args = ap.parse_args()
    notion = Notion()

    if args.cmd == "build":
        if not args.page:
            raise SystemExit("Pass --page <Notion page URL> (or set NOTION_PAGE_URL).")
        ids = create_workspace(notion, page_id_from(args.page))
        print(json.dumps(ids, indent=2))
        if args.with_samples:
            for trip in TRIPS:
                notion.call("POST", "/pages", {"parent": {"type": "data_source_id",
                                                          "data_source_id": ids["data_source_id"]},
                                               "icon": {"type": "emoji", "emoji": "🧳"},
                                               "properties": page_properties(trip)})
                print(f"Added trip: {trip['Trip']}")
        refresh_briefs(notion, ids["data_source_id"], force_all=True)
        (ROOT / "workspace.json").write_text(json.dumps(ids, indent=2), encoding="utf-8")
        print("Saved ids to workspace.json. Set NOTION_DATA_SOURCE_ID =", ids["data_source_id"])
    else:
        ds = os.environ.get("NOTION_DATA_SOURCE_ID") or json.loads((ROOT / "workspace.json").read_text())["data_source_id"]
        refresh_briefs(notion, ds, force_all=args.all)


if __name__ == "__main__":
    main()
