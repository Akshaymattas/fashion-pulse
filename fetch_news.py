#!/usr/bin/env python3
"""
Fashion Pulse — daily RSS aggregator.

Reads feeds.json, pulls every feed, normalises the items,
tags them by region (Global / India / Europe), and writes
data/news.json for the static site to render.

Run locally:  python fetch_news.py
Run in CI:    scheduled by .github/workflows/update.yml at 11:00 IST
"""

import json
import re
import time
import html
from datetime import datetime, timedelta, timezone
from pathlib import Path

import feedparser

ROOT = Path(__file__).parent
CONFIG = json.loads((ROOT / "feeds.json").read_text(encoding="utf-8"))

IST = timezone(timedelta(hours=5, minutes=30))

# Keyword overrides: an item from a Global feed that clearly talks about
# India or Europe also gets tagged with that region so it shows in the tab.
INDIA_KEYWORDS = re.compile(
    r"\b(india|indian|mumbai|delhi|bengaluru|bangalore|myntra|ajio|reliance retail|"
    r"tata cliq|nykaa|aditya birla|fabindia|rupee)\b", re.I)
EUROPE_KEYWORDS = re.compile(
    r"\b(europe|european|eu\b|uk\b|britain|london|paris|milan|france|italy|germany|"
    r"spain|zara|inditex|h&m|lvmh|kering|primark|asos|zalando|boohoo|m&s|next plc)\b", re.I)

USER_AGENT = "Mozilla/5.0 (compatible; FashionPulseBot/1.0; +https://github.com)"


def clean(text: str, limit: int = 280) -> str:
    """Strip HTML tags and trim a summary."""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[: limit - 1] + "…" if len(text) > limit else text


def parse_date(entry) -> datetime | None:
    for key in ("published_parsed", "updated_parsed"):
        t = entry.get(key)
        if t:
            return datetime.fromtimestamp(time.mktime(t), tz=timezone.utc)
    return None


def regions_for(feed_region: str, title: str, summary: str) -> list[str]:
    regions = {feed_region}
    blob = f"{title} {summary}"
    if INDIA_KEYWORDS.search(blob):
        regions.add("India")
    if EUROPE_KEYWORDS.search(blob):
        regions.add("Europe")
    return sorted(regions)


def fetch_feed(feed_cfg: dict, max_items: int, cutoff: datetime) -> list[dict]:
    items = []
    try:
        parsed = feedparser.parse(feed_cfg["url"], agent=USER_AGENT)
        if parsed.bozo and not parsed.entries:
            raise RuntimeError(parsed.get("bozo_exception", "unparseable feed"))
        for entry in parsed.entries[: max_items * 2]:
            link = entry.get("link", "")
            title = clean(entry.get("title", ""), 200)
            if not link or not title:
                continue
            published = parse_date(entry)
            if published and published < cutoff:
                continue
            summary = clean(entry.get("summary", "") or entry.get("description", ""))
            items.append({
                "title": title,
                "link": link,
                "summary": summary,
                "source": feed_cfg["name"],
                "regions": regions_for(feed_cfg["region"], title, summary),
                "published": published.isoformat() if published else None,
            })
            if len(items) >= max_items:
                break
        print(f"  ✓ {feed_cfg['name']}: {len(items)} items")
    except Exception as exc:  # keep the run alive if one source is down
        print(f"  ✗ {feed_cfg['name']}: {exc}")
    return items


def main() -> None:
    max_items = CONFIG.get("max_items_per_feed", 15)
    max_age = CONFIG.get("max_age_days", 7)
    cutoff = datetime.now(timezone.utc) - timedelta(days=max_age)

    print(f"Fetching {len(CONFIG['feeds'])} feeds…")
    all_items: list[dict] = []
    for feed_cfg in CONFIG["feeds"]:
        all_items.extend(fetch_feed(feed_cfg, max_items, cutoff))

    # De-duplicate by link, then by near-identical title
    seen_links, seen_titles, unique = set(), set(), []
    for item in all_items:
        key_link = item["link"].split("?")[0].rstrip("/")
        key_title = re.sub(r"\W+", "", item["title"].lower())[:80]
        if key_link in seen_links or key_title in seen_titles:
            continue
        seen_links.add(key_link)
        seen_titles.add(key_title)
        unique.append(item)

    # Newest first; undated items go last
    unique.sort(key=lambda i: i["published"] or "", reverse=True)

    out = {
        "updated_at": datetime.now(IST).strftime("%d %b %Y, %I:%M %p IST"),
        "updated_at_iso": datetime.now(timezone.utc).isoformat(),
        "count": len(unique),
        "reference_links": CONFIG.get("reference_links", []),
        "items": unique,
    }
    out_path = ROOT / "data" / "news.json"
    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nWrote {len(unique)} unique items → {out_path}")


if __name__ == "__main__":
    main()
