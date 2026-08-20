from __future__ import annotations

import datetime as dt
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "template.html"
CASES = ROOT / "data" / "cases.json"
TOSUP = ROOT / "data" / "tosup_patterns.json"
OUTPUT = ROOT / "index.html"

IND_LABEL = {
    "it": "IT・テクノロジー", "media": "メディア・通信", "finance": "金融・保険",
    "retail": "流通・小売", "ec": "EC", "food": "飲食", "consumer": "消費財",
    "fashion": "ファッション", "auto": "自動車・モビリティ", "transport": "運輸・交通",
    "health": "医療・ヘルスケア", "entertain": "エンタメ・スポーツ", "energy": "エネルギー",
    "realestate": "不動産",
}
PROD_LABEL = {
    "cdp": "CDP", "engage": "Engage Studio", "journey": "Journey",
    "ai_agent": "AI Agent Foundry", "cleanroom": "Data Clean Room", "audience": "Audience Studio",
}
IND_CLASS = set(IND_LABEL)


def esc(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def unique(values: list[str]) -> list[str]:
    out: list[str] = []
    for value in values:
        value = " ".join(str(value or "").split())
        if value and value not in out:
            out.append(value)
    return out


def compact(value: str, limit: int = 38) -> str:
    value = " ".join((value or "").split())
    if len(value) <= limit:
        return value
    return value[: limit - 1] + "…"


def first_sentence(value: str) -> str:
    value = " ".join((value or "").split())
    parts = re.split(r"(?<=[。！？])", value)
    return next((part.strip() for part in parts if len(part.strip()) >= 5), value)


def badge_items(case: dict) -> list[str]:
    metrics = unique(case.get("metrics", []))
    badges = unique(case.get("badges", []))
    values = unique(metrics + badges)
    if values:
        return values[:4]
    background = first_sentence(case.get("background", ""))
    result = unique(case.get("results", []))
    values = [compact(background)] if background else []
    if result:
        values.append(compact(result[0]))
    return values or ["公式ページの導入背景を確認"]


def render_card(case: dict) -> str:
    slug = case.get("slug", "")
    url = case.get("url", "")
    company = case.get("company") or case.get("title") or slug
    sub = case.get("sub") or case.get("title", "")
    industries = [x for x in case.get("industries", []) if x]
    products = [x for x in case.get("products", []) if x]
    ind_label = " / ".join(IND_LABEL.get(x, x) for x in industries) or "未分類"
    ind_class = next((x for x in industries if x in IND_CLASS), "other")
    description = case.get("description") or case.get("summary") or case.get("background") or "公式ページから事例内容を取得中です。"
    results = unique(case.get("results", []))[:4]
    badges = badge_items(case)
    context = case.get("context") or " ".join([
        company, sub, case.get("search", ""), case.get("background", ""), case.get("summary", ""),
        " ".join(results), " ".join(products),
    ])
    attrs = {
        "data-inds": " ".join(industries),
        "data-prods": " ".join(products),
        "data-search": case.get("search", "")[:12000],
        "data-slug": slug,
        "data-summary": case.get("summary", ""),
        "data-background": case.get("background", ""),
        "data-context": context[:16000],
        "data-badges": "|".join(badges),
        "data-catchcopy": case.get("catchcopy", ""),
        "data-status": case.get("status", "active"),
        "data-featured": "true" if case.get("featured") else "false",
    }
    if url:
        attrs["data-url"] = url
    tag = "a" if url else "div"
    attr_text = " ".join(f'{key}="{esc(value)}"' for key, value in attrs.items())
    target = ' target="_blank" rel="noopener noreferrer"' if url else ""
    metrics_html = "\n".join(f'      <span class="metric">{esc(item)}</span>' for item in badges)
    results_html = "\n".join(f'      <span class="result-tag">{esc(item)}</span>' for item in results)
    if not results_html:
        results_html = f'      <span class="result-tag">{esc(compact(case.get("summary", "成果情報は公式ページを参照"), 52))}</span>'
    products_html = "\n".join(
        f'      <span class="prod-tag pt-{esc(product)}">{esc(PROD_LABEL.get(product, product))}</span>'
        for product in products
    )
    if not products_html:
        products_html = '      <span class="prod-tag pt-other">製品情報確認中</span>'
    unlinked = '<div class="unlinked-note">公式詳細ページ未確認</div>' if not url else ""
    return f'''  <{tag} class="card{' unlinked' if not url else ''}" {attr_text}{target}>
    <div class="card-metrics">
{metrics_html}
    </div>
    <div class="card-top">
      <div>
        <div class="company-name">{esc(company)}</div>
        <div class="company-sub">{esc(sub)}</div>
        {unlinked}
      </div>
      <span class="ind-badge ind-{esc(ind_class)}">{esc(ind_label)}</span>
    </div>
    <div class="description">{esc(compact(description, 260))}</div>
    <div class="result-tags">
{results_html}
    </div>
    <div class="prod-tags">
{products_html}
    </div>
  </{tag}>'''


def replace_stat(text: str, element_id: str, value: int) -> str:
    return re.sub(
        rf'(<div class="stat-number" id="{re.escape(element_id)}">)[^<]*(</div>)',
        rf'\g<1>{value}\g<2>', text,
        count=1,
    )


def main() -> None:
    template = TEMPLATE.read_text(encoding="utf-8")
    cases = json.loads(CASES.read_text(encoding="utf-8"))
    cases = [case for case in cases if case.get("status") != "retired"]
    tosup_payload = json.loads(TOSUP.read_text(encoding="utf-8"))
    tosup_patterns = tosup_payload.get("seed_patterns", []) + tosup_payload.get("generated_patterns", [])
    cases_html = "\n\n".join(render_card(case) for case in cases)
    start_marker = "  <!-- CASES_START -->"
    end_marker = "  <!-- CASES_END -->"
    start = template.index(start_marker) + len(start_marker)
    end = template.index(end_marker, start)
    output = template[:start] + "\n" + cases_html + "\n  " + template[end:]
    marker = "__TOSUP_PATTERNS__"
    if marker not in output:
        raise RuntimeError("TOSUP pattern placeholder is missing from template.html")
    output = output.replace(marker, json.dumps(tosup_patterns, ensure_ascii=False, separators=(",", ":")), 1)

    industries = {item for case in cases for item in case.get("industries", []) if item}
    products = {item for case in cases for item in case.get("products", []) if item}
    output = replace_stat(output, "visible-count", len(cases))
    output = replace_stat(output, "total-count", len(cases))
    output = re.sub(r'(<div class="stat-number">)[^<]*(</div><div class="stat-label">業種</div>)', rf'\g<1>{len(industries)}\g<2>', output, count=1)
    output = re.sub(r'(<div class="stat-number">)[^<]*(</div><div class="stat-label">製品・機能区分</div>)', rf'\g<1>{len(products)}\g<2>', output, count=1)
    today = dt.datetime.now().strftime("%Y-%m-%d")
    output = output.replace('<span id="sync-date">自動同期</span>', f'<span id="sync-date">最終同期 {today}</span>')
    output = re.sub(r'\d{4}年\d{1,2}月時点の掲載情報をもとに作成', f'自動同期データ（{today}）', output)
    OUTPUT.write_text(output, encoding="utf-8")
    print(f"built {OUTPUT}: {len(cases)} cards, {len(industries)} industries, {len(products)} products")


if __name__ == "__main__":
    main()
