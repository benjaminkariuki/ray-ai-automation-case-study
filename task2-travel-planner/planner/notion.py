"""Minimal Notion API client (Notion-Version 2026-03-11) with rate limiting and retries."""
import os
import time

import requests

API = "https://api.notion.com/v1"
VERSION = "2026-03-11"


class Notion:
    def __init__(self, token=None):
        self.token = token or os.environ.get("NOTION_TOKEN", "")
        if not self.token:
            raise SystemExit("NOTION_TOKEN is not set (see .env.example).")
        self._last = 0.0

    def call(self, method, path, body=None, params=None):
        for attempt in range(5):
            wait = 0.35 - (time.time() - self._last)  # Notion allows ~3 requests/second
            if wait > 0:
                time.sleep(wait)
            self._last = time.time()
            r = requests.request(method, API + path, json=body, params=params, timeout=60, headers={
                "Authorization": f"Bearer {self.token}", "Notion-Version": VERSION,
                "Content-Type": "application/json"})
            if r.status_code in (429, 500, 502, 503, 504) and attempt < 4:
                time.sleep(float(r.headers.get("Retry-After", 2 * (attempt + 1))))
                continue
            if r.status_code >= 400:
                raise RuntimeError(f"Notion {method} {path} -> {r.status_code}: {r.text[:500]}")
            return r.json() if r.content else {}

    def children(self, block_id):
        out, cursor = [], None
        while True:
            data = self.call("GET", f"/blocks/{block_id}/children",
                             params={"page_size": 100, **({"start_cursor": cursor} if cursor else {})})
            out += data.get("results", [])
            if not data.get("has_more"):
                return out
            cursor = data["next_cursor"]

    def append(self, block_id, blocks, after=None):
        """Append blocks (max 100 per request); keeps order when inserting after a given block."""
        created = []
        for i in range(0, len(blocks), 100):
            body = {"children": blocks[i:i + 100]}
            if after:
                body["position"] = {"type": "after_block", "after_block": {"id": after}}
            res = self.call("PATCH", f"/blocks/{block_id}/children", body).get("results", [])
            created += res
            if after and res:
                after = res[-1]["id"]
        return created

    def query(self, data_source_id, body=None):
        out, cursor = [], None
        while True:
            data = self.call("POST", f"/data_sources/{data_source_id}/query",
                             {**(body or {}), "page_size": 100, **({"start_cursor": cursor} if cursor else {})})
            out += data.get("results", [])
            if not data.get("has_more"):
                return out
            cursor = data["next_cursor"]


def plain(rich):
    """Concatenate the plain text of a rich_text/title array."""
    return "".join(part.get("plain_text", "") for part in rich or [])


def text(content, bold=False, color=None, link=None):
    """Rich text segments (split to respect Notion's 2,000-character limit per segment)."""
    content = str(content)
    parts = [content[i:i + 1900] for i in range(0, len(content), 1900)] or [""]
    out = []
    for p in parts:
        t = {"type": "text", "text": {"content": p, **({"link": {"url": link}} if link else {})}}
        ann = {k: v for k, v in (("bold", bold), ("color", color)) if v}
        if ann:
            t["annotations"] = ann
        out.append(t)
    return out
