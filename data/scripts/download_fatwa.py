"""
Download Malaysian fatwa/fiqh articles from Pejabat Mufti Wilayah Persekutuan (MuftiWP).

MuftiWP runs a Joomla site (no public WP JSON API). This script crawls category listing
pages (using ?start= pagination) to collect article URLs, then downloads each article.

Default target: Irsyad Hukum (Umum) series, which has the largest volume.

Output:
  data/raw/fatwa/muftiwp_posts.json
"""

import argparse
import json
import random
import re
import time
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request, urlopen

BASE_URL = "https://muftiwp.gov.my"
OUTPUT_DIR = Path(__file__).parent.parent / "raw" / "fatwa"

# Category slugs under /ms/artikel/<slug>
DEFAULT_CATEGORIES = [
    ("irsyad-hukum/umum", "Irsyad Hukum (Umum)"),
    ("irsyad-hukum/edisi-ramadhan", "Irsyad Hukum (Edisi Ramadan)"),
    ("irsyad-hukum/edisi-haji-korban", "Irsyad Hukum (Edisi Haji/Korban)"),
]

START_STEP = 25


def fetch_url(url: str, max_retries: int = 3, sleep_range: tuple[float, float] = (0.5, 1.5)) -> str:
    """Fetch URL content with retries and polite throttling."""
    for attempt in range(max_retries):
        try:
            req = Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"},
            )
            with urlopen(req, timeout=30) as response:
                html = response.read().decode("utf-8", errors="ignore")
            time.sleep(random.uniform(*sleep_range))
            return html
        except Exception as exc:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            print(f"  ✗ Failed to fetch {url}: {exc}")
            return ""
    return ""


def extract_article_links(html: str, category_slug: str) -> list[str]:
    """Extract article links from a category listing page."""
    if not html:
        return []
    escaped = re.escape(f"/ms/artikel/{category_slug}/")
    pattern = rf'href="({escaped}\d+-[^"]+)"'
    links = re.findall(pattern, html)
    # De-duplicate while preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for link in links:
        if link not in seen:
            seen.add(link)
            unique.append(link)
    return unique


def crawl_category(category_slug: str, max_pages: int | None = None) -> list[str]:
    """Crawl a category listing and return article URLs (relative)."""
    urls: list[str] = []
    start = 0
    page_count = 0
    while True:
        list_url = f"{BASE_URL}/ms/artikel/{category_slug}"
        if start:
            list_url += f"?start={start}"
        html = fetch_url(list_url)
        page_links = extract_article_links(html, category_slug)
        if not page_links:
            break
        new_links = [link for link in page_links if link not in urls]
        if not new_links:
            break
        urls.extend(new_links)
        start += START_STEP
        page_count += 1
        if max_pages and page_count >= max_pages:
            break
    return urls


def extract_field(pattern: str, html: str) -> str:
    match = re.search(pattern, html, flags=re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else ""


def extract_article_body_html(html: str) -> str:
    idx = html.find('itemprop="articleBody"')
    if idx == -1:
        return ""
    start = html.find(">", idx)
    if start == -1:
        return ""
    body_start = start + 1
    body_end = html.find("</div>", body_start)
    if body_end == -1:
        body_end = len(html)
    return html[body_start:body_end].strip()


def parse_article(url: str, category_name: str) -> dict | None:
    html = fetch_url(url)
    if not html:
        return None

    title = extract_field(r'itemprop="headline"[^>]*>(.*?)<', html)
    if not title:
        title = extract_field(r"<title>(.*?)</title>", html)
        title = title.replace("Pejabat Mufti Wilayah Persekutuan -", "").strip()

    date_iso = extract_field(r'<time[^>]*datetime="([^"]+)"', html)
    body_html = extract_article_body_html(html)

    if not body_html:
        return None

    return {
        "url": url,
        "category": category_name,
        "title": title,
        "date": date_iso,
        "body_html": body_html,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Max listing pages per category (25 posts/page).",
    )
    parser.add_argument(
        "--max-articles",
        type=int,
        default=None,
        help="Max articles total across all categories.",
    )
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    all_article_urls: list[tuple[str, str]] = []
    for slug, name in DEFAULT_CATEGORIES:
        print(f"== Crawling category: {name} ==")
        rel_links = crawl_category(slug, max_pages=args.max_pages)
        print(f"  Found {len(rel_links)} article links")
        all_article_urls.extend([(urljoin(BASE_URL, rel), name) for rel in rel_links])

    # De-duplicate URLs while preserving category preference
    seen_abs: set[str] = set()
    deduped: list[tuple[str, str]] = []
    for abs_url, cat_name in all_article_urls:
        if abs_url in seen_abs:
            continue
        seen_abs.add(abs_url)
        deduped.append((abs_url, cat_name))

    if args.max_articles:
        deduped = deduped[: args.max_articles]

    print(f"\nDownloading {len(deduped)} articles...")
    posts: list[dict] = []
    for index, (abs_url, cat_name) in enumerate(deduped, start=1):
        print(f"[{index}/{len(deduped)}] {abs_url}")
        post = parse_article(abs_url, cat_name)
        if post:
            posts.append(post)

    out_path = OUTPUT_DIR / "muftiwp_posts.json"
    out_path.write_text(json.dumps(posts, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✓ Saved {len(posts)} posts to {out_path}")


if __name__ == "__main__":
    main()

