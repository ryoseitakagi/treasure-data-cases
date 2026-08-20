"""Synchronize Treasure AI customer pages into data/cases.json.

The public Japanese sitemap is the source of truth for discoverable case URLs.
Curated presentation metadata lives in data/overrides.json and is never replaced
by the crawler.
"""
from __future__ import annotations

import concurrent.futures
import hashlib
import json
import re
import sys
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import certifi
import requests
from lxml import etree, html

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
CASES_FILE = DATA_DIR / "cases.json"
OVERRIDES_FILE = DATA_DIR / "overrides.json"
SITEMAP_URL = "https://www.treasure.ai/sitemap.xml"
SITE_ROOT = "https://www.treasure.ai"
UA = "TreasureCasesSync/1.0 (+https://ryoseitakagi.github.io/treasure-data-cases/)"
MAX_CONTEXT = 16000
MAX_WORKERS = 4

# A page that disappeared from both the current Japanese sitemap and the old
# public domain is not useful as a detail link. It is omitted instead of
# publishing a broken card.
RETIRED_SLUGS = {"asako-tsi-joint-webinar"}

session = requests.Session()
session.headers.update({"User-Agent": UA, "Accept-Language": "ja,en;q=0.8"})


def clean(value: str) -> str:
    value = unicodedata.normalize("NFKC", value or "")
    return re.sub(r"\s+", " ", value).strip()


def unique(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        value = clean(value)
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def load_json(path: Path, fallback: Any) -> Any:
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON: {path}: {exc}") from exc


def fetch(url: str, timeout: int = 40) -> requests.Response:
    response = session.get(url, timeout=timeout, verify=certifi.where())
    response.raise_for_status()
    return response


def discover_urls() -> list[dict[str, str]]:
    response = fetch(SITEMAP_URL)
    root = etree.fromstring(response.content)
    result: list[dict[str, str]] = []
    for node in root.xpath("//*[local-name()='url']"):
        locs = node.xpath("./*[local-name()='loc']/text()")
        if not locs:
            continue
        url = clean(locs[0]).rstrip("/") + "/"
        if not re.match(r"^https://www\.treasure\.ai/ja/customers/[^/?#]+/$", url):
            continue
        slug = url.rstrip("/").rsplit("/", 1)[-1]
        if slug in RETIRED_SLUGS:
            continue
        lastmods = node.xpath("./*[local-name()='lastmod']/text()")
        result.append({"slug": slug, "url": url, "lastmod": clean(lastmods[0]) if lastmods else ""})
    return sorted({item["slug"]: item for item in result}.values(), key=lambda x: x["slug"])


def meta(doc: html.HtmlElement, selector: str) -> str:
    values = doc.xpath(selector)
    return clean(values[0]) if values else ""


def text_nodes(node: html.HtmlElement, xpath: str) -> list[str]:
    return unique([clean(" ".join(element.xpath(".//text()"))) for element in node.xpath(xpath)])


def extract_page(item: dict[str, str], old: dict[str, Any] | None, override: dict[str, Any] | None) -> dict[str, Any]:
    url = item["url"]
    response = fetch(url)
    document = html.fromstring(response.content)

    # Keep the article body but remove navigation, scripts and recommendations.
    for node in document.xpath("//script|//style|//noscript|//svg|//header|//footer|//nav"):
        node.drop_tree()
    mains = document.xpath("//main")
    main = mains[0] if mains else document

    title = meta(document, '//meta[@property="og:title"]/@content')
    h1 = clean(" ".join(document.xpath("//h1[1]//text()")))
    title = title or h1 or item["slug"]
    headings = text_nodes(main, ".//h1|.//h2|.//h3|.//h4")
    paragraphs = text_nodes(main, ".//p")
    body = clean(" ".join(main.itertext()))
    body = body[:MAX_CONTEXT]

    # Existing curated fields win. They contain reviewed Japanese summaries and
    # outcome figures that cannot be safely inferred from arbitrary HTML.
    old = old or {}
    override = override or {}
    company = override.get("company") or old.get("company")
    if not company:
        candidate_headings = [x for x in headings if x not in {title, "CASE STUDY"}]
        company = candidate_headings[0] if candidate_headings else item["slug"]
    sub = override.get("sub") or old.get("sub") or (headings[1] if len(headings) > 1 else "")

    generic_description = "トレジャーAIの導入事例・実績企業一覧です。"
    description = override.get("description") or old.get("description")
    if not description:
        description = next((p for p in paragraphs if len(p) >= 30 and generic_description not in p), "")
    background = override.get("background") or old.get("background") or ""
    if not background:
        # A conservative fallback: use the first meaningful heading/paragraph,
        # rather than inventing a result that is not present on the source page.
        background = next((p for p in paragraphs if len(p) >= 30), "")

    metrics = list(override.get("metrics") or old.get("metrics") or [])
    if not metrics:
        metric_pattern = re.compile(r"(?:\d[\d,.]*\s*(?:%|％|倍|人月|時間|件|万人|万円|日|分)|\+\s*[\d,.]+\s*[%％])")
        metrics = [h for h in headings if metric_pattern.search(h)]
    results = list(override.get("results") or old.get("results") or [])
    if not results:
        results = metrics[:]

    industries = list(override.get("industries") or old.get("industries") or [])
    products = list(override.get("products") or old.get("products") or [])
    search = " ".join(unique([
        company, sub, title, " ".join(headings), old.get("search", ""), body[:6000]
    ]))
    summary = override.get("summary") or old.get("summary")
    if not summary:
        first = next((p for p in paragraphs if len(p) >= 30), "")
        summary = f"{first[:260]}" if first else title
    badges = list(override.get("badges") or old.get("badges") or [])
    catchcopy = override.get("catchcopy") or old.get("catchcopy") or ""
    context = "\n".join(unique([
        f"会社: {company}", f"タイトル: {title}", f"業種: {' '.join(industries)}",
        f"製品: {' '.join(products)}", f"導入背景: {background}",
        f"概要: {summary}", f"成果: {' / '.join(results + metrics)}",
        body, "見出し: " + " / ".join(headings)
    ]))[:MAX_CONTEXT]

    return {
        "slug": item["slug"],
        "url": url,
        "company": company,
        "sub": sub,
        "title": title,
        "industries": industries,
        "products": products,
        "search": search,
        "description": description,
        "background": background,
        "summary": summary,
        "catchcopy": catchcopy,
        "badges": badges,
        "metrics": unique(metrics),
        "results": unique(results),
        "context": context,
        "source": "treasure.ai sitemap",
        "sourceLastmod": item.get("lastmod", ""),
        "sourceHash": hashlib.sha256(context.encode("utf-8")).hexdigest(),
        "lastCheckedAt": datetime.now(timezone.utc).isoformat(),
        "featured": bool(override.get("featured", old.get("featured", False))),
        "status": "active",
    }


def keep_legacy(record: dict[str, Any]) -> dict[str, Any]:
    """Keep curated global/unlinked records until the source exposes a URL."""
    record = dict(record)
    record.setdefault("context", " ".join(unique([
        record.get("company", ""), record.get("search", ""), record.get("background", ""),
        record.get("summary", ""), " ".join(record.get("results", [])),
    ])))
    record.setdefault("status", "unlinked" if not record.get("url") else "legacy")
    record.setdefault("source", "curated legacy")
    record.setdefault("lastCheckedAt", datetime.now(timezone.utc).isoformat())
    return record


def main() -> None:
    overrides_list = load_json(OVERRIDES_FILE, [])
    existing_list = load_json(CASES_FILE, [])
    overrides = {str(x.get("slug")): x for x in overrides_list if x.get("slug")}
    existing = {str(x.get("slug")): x for x in existing_list if x.get("slug")}
    discovered = discover_urls()
    print(f"discovered official Japanese case URLs: {len(discovered)}")

    records: dict[str, dict[str, Any]] = {}
    failures: list[str] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {
            pool.submit(extract_page, item, existing.get(item["slug"]), overrides.get(item["slug"])): item
            for item in discovered
        }
        for future in concurrent.futures.as_completed(futures):
            item = futures[future]
            try:
                records[item["slug"]] = future.result()
            except Exception as exc:  # preserve a previous record on transient failure
                failures.append(f"{item['slug']}: {exc}")
                if item["slug"] in existing:
                    records[item["slug"]] = existing[item["slug"]]

    # Preserve reviewed global cases and reviewed cards that have no current
    # detail URL. These remain searchable but are clearly unlinked in the UI.
    discovered_slugs = set(records)
    for slug, record in {**existing, **overrides}.items():
        if slug in discovered_slugs or slug in RETIRED_SLUGS:
            continue
        if slug in RETIRED_SLUGS:
            continue
        records[slug] = keep_legacy({**existing.get(slug, {}), **record})

    if not records:
        raise RuntimeError("No case records were produced; refusing to overwrite data/cases.json")
    # Do not publish a partial catalog after a source outage or a parser break.
    minimum = max(20, int(len(discovered) * 0.70))
    if failures and len(records) < minimum:
        raise RuntimeError(f"Only {len(records)}/{len(discovered)} official pages were read; refusing partial sync")
    if failures:
        print(f"transient fetch failures: {len(failures)}", file=sys.stderr)
        for line in failures[:10]: print(" ", line, file=sys.stderr)

    ordered = sorted(records.values(), key=lambda x: (not x.get("featured", False), x.get("company", ""), x.get("slug", "")))
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CASES_FILE.write_text(json.dumps(ordered, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote case records: {len(ordered)}")
    print(f"active: {sum(x.get('status') == 'active' for x in ordered)}; unlinked/legacy: {sum(x.get('status') != 'active' for x in ordered)}")


if __name__ == "__main__":
    main()
