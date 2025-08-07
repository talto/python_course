#!/usr/bin/env python3
"""Periodic Hacker News crawler with SQLite storage

• Каждые N секунд берёт топ‑страницу Hacker News
• Сохраняет новые новости (id, title, url, content, timestamp)
• Из обсуждения каждой новости вытягивает **только внешние ссылки** и кладёт в таблицу `links`
• Ждёт освобождения SQLite‑блокировки (`timeout=30s`)

Запуск:
    python crawler.py  # Ctrl+C для остановки

Зависимости:
    pip install aiohttp selectolax aiosqlite
"""
from __future__ import annotations

import asyncio, signal, urllib.parse
from datetime import datetime, timezone

import aiohttp, aiosqlite
from selectolax.parser import HTMLParser

HN_TOP = "https://news.ycombinator.com/"
HN_ITEM = "https://news.ycombinator.com/item?id={}"
DB = "hn_top.db"
INTERVAL = 60  # seconds

should_stop = asyncio.Event()

# ---------------------------------------------------------------------------
# signal handling
# ---------------------------------------------------------------------------

def setup_signal_handlers() -> None:
    def handler(sig, frame):
        print("\nReceived exit signal. Shutting down…")
        should_stop.set()

    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def is_external_link(href: str) -> bool:
    """Return True for http(s) links NOT pointing to *.news.ycombinator.com"""
    if not href.startswith(("http://", "https://")):
        return False
    host = urllib.parse.urlparse(href).netloc.lower()
    return not host.endswith("news.ycombinator.com")


def extract_links_from_discussion(html: str) -> list[str]:
    """Return unique external links that live inside comment bodies."""
    tree = HTMLParser(html)
    out: list[str] = []
    seen: set[str] = set()

    for a in tree.css("a"):
        href = a.attributes.get("href")
        if not href or href in seen or not is_external_link(href):
            continue
        # ensure <a> is inside comment text
        node = a.parent
        while node is not None and node.tag != "html":
            cls = node.attributes.get("class", "")
            if (
                (node.tag == "span" and "commtext" in cls)
                or (node.tag == "div" and "comment" in cls)
            ):
                seen.add(href)
                out.append(href)
                break
            node = node.parent
    return out


def extract_comment_text(html: str) -> str:
    tree = HTMLParser(html)
    return "\n\n".join(el.text(strip=True) for el in tree.css("span.commtext"))

# ---------------------------------------------------------------------------
# db helpers
# ---------------------------------------------------------------------------
async def init_db(db: aiosqlite.Connection) -> None:
    await db.executescript(
        """
        CREATE TABLE IF NOT EXISTS news (
            id        INTEGER PRIMARY KEY,
            title     TEXT NOT NULL,
            url       TEXT NOT NULL,
            content   TEXT,
            timestamp TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS links (
            news_id INTEGER,
            url     TEXT NOT NULL,
            UNIQUE(news_id, url)
        );
        """
    )
    await db.commit()


async def news_exists(db: aiosqlite.Connection, story_id: int) -> bool:
    async with db.execute("SELECT 1 FROM news WHERE id=?", (story_id,)) as cur:
        return await cur.fetchone() is not None


async def save_news(db: aiosqlite.Connection, story_id: int, title: str, url: str, content: str) -> None:
    ts = datetime.now(timezone.utc).isoformat()
    await db.execute(
        "INSERT OR IGNORE INTO news VALUES (?,?,?,?,?)",
        (story_id, title, url, content, ts),
    )


async def save_links(db: aiosqlite.Connection, story_id: int, links: list[str]) -> None:
    for link in links:
        await db.execute(
            "INSERT OR IGNORE INTO links VALUES (?,?)",
            (story_id, link),
        )

# ---------------------------------------------------------------------------
# network helpers
# ---------------------------------------------------------------------------
async def fetch(session: aiohttp.ClientSession, url: str) -> str:
    async with session.get(url, headers={"User-Agent": "HNCrawler/1.0"}) as r:
        r.raise_for_status()
        return await r.text()

# ---------------------------------------------------------------------------
# main crawl logic
# ---------------------------------------------------------------------------
async def crawl_once(session: aiohttp.ClientSession, db: aiosqlite.Connection) -> int:
    top_html = await fetch(session, HN_TOP)
    tree = HTMLParser(top_html)
    new_count = 0

    for row in tree.css("tr.athing"):
        item_id = row.attributes.get("id")
        title_el = row.css_first("a.storylink") or row.css_first("span.titleline a")
        if not (item_id and title_el):
            continue

        sid = int(item_id)
        title = title_el.text(strip=True)
        url = title_el.attributes.get("href", "")
        is_new = not await news_exists(db, sid)

        discussion_html = await fetch(session, HN_ITEM.format(sid))
        links = extract_links_from_discussion(discussion_html)
        content = extract_comment_text(discussion_html)

        if is_new:
            print(f"{sid}: {title} → {url}")
            await save_news(db, sid, title, url, content)
            new_count += 1

        await save_links(db, sid, links)

    await db.commit()
    return new_count

# ---------------------------------------------------------------------------
# periodic runner
# ---------------------------------------------------------------------------
async def run(interval: int = INTERVAL):
    print(f"Starting crawler, interval={interval}s. Press Ctrl+C to stop.")
    async with aiohttp.ClientSession() as session, aiosqlite.connect(DB, timeout=30) as db:
        await init_db(db)
        while not should_stop.is_set():
            try:
                added = await crawl_once(session, db)
                print(f"[{datetime.now(timezone.utc).isoformat()}] New stories: {added}\n")
            except Exception as e:
                print("Error:", e)
            try:
                await asyncio.wait_for(should_stop.wait(), timeout=interval)
            except asyncio.TimeoutError:
                continue

# ---------------------------------------------------------------------------
if __name__ == "__main__":
    setup_signal_handlers()
    asyncio.run(run())
