"""
Process MuftiWP fatwa/fiqh raw posts into embedding-ready chunks.

Input:
  data/raw/fatwa/muftiwp_posts.json

Output:
  data/processed/fatwa/fatwa_chunks.json
"""

import json
import re
from html.parser import HTMLParser
from pathlib import Path

RAW_DIR = Path(__file__).parent.parent / "raw" / "fatwa"
PROCESSED_DIR = Path(__file__).parent.parent / "processed" / "fatwa"


class SimpleHTMLToText(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.in_script = False
        self.in_style = False

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self.in_script = True
        if tag in {"p", "br", "li", "h2", "h3"}:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in {"script", "style"}:
            self.in_script = False
        if tag in {"p", "li"}:
            self.parts.append("\n")

    def handle_data(self, data):
        if self.in_script or self.in_style:
            return
        text = data.strip()
        if text:
            self.parts.append(text)

    def get_text(self) -> str:
        text = " ".join(self.parts)
        text = re.sub(r"\s+\n", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()


def strip_html(html: str) -> str:
    parser = SimpleHTMLToText()
    parser.feed(html)
    return parser.get_text()


def chunk_text(text: str, chunk_size: int = 1200, overlap: int = 200) -> list[str]:
    if not text:
        return []
    chunks: list[str] = []
    cursor = 0
    text_len = len(text)
    while cursor < text_len:
        end = min(text_len, cursor + chunk_size)
        if end < text_len:
            back = text.rfind(" ", cursor, end)
            if back > cursor + int(chunk_size * 0.6):
                end = back
        chunk = text[cursor:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= text_len:
            break
        cursor = max(end - overlap, cursor + 1)
    return chunks


def classify_topic_ms(text: str) -> str:
    lowered = text.lower()
    mapping = {
        "taharah": ["wuduk", "wudu", "mandi", "najis", "tayammum", "hadas"],
        "solat": ["solat", "sujud", "rukuk", "imam", "makmum", "azan"],
        "puasa": ["puasa", "ramadan", "sahur", "iftar", "zakat fitrah"],
        "zakat": ["zakat", "nisab", "haul", "sedekah"],
        "haji": ["haji", "umrah", "tawaf", "sa'i", "ihram", "miqat"],
        "muamalat": ["jual beli", "riba", "hutang", "akad", "pinjaman", "kontrak"],
        "munakahat": ["nikah", "kahwin", "talaq", "cerai", "nafkah", "iddah"],
        "jenazah": ["jenazah", "kafan", "kubur", "mayat", "mandi jenazah"],
        "makanan": ["halal", "haram", "arak", "alkohol", "sembelih", "makanan"],
    }
    best = "general"
    best_score = 0
    for cat, keywords in mapping.items():
        score = sum(1 for kw in keywords if kw in lowered)
        if score > best_score:
            best = cat
            best_score = score
    return best


def extract_fatwa_number(title: str) -> str | None:
    match = re.search(r"siri\\s*ke[-\\s]*([0-9]{1,5})", title, flags=re.IGNORECASE)
    return match.group(1) if match else None


def process_posts(posts: list[dict]) -> list[dict]:
    chunks: list[dict] = []
    for post in posts:
        title = post.get("title", "").strip()
        body_text = strip_html(post.get("body_html", ""))
        if not body_text:
            continue

        full_text = f"Tajuk: {title}\n\n{body_text}".strip()
        topic = classify_topic_ms(full_text)
        fatwa_number = extract_fatwa_number(title)

        for idx, piece in enumerate(chunk_text(full_text)):
            chunks.append(
                {
                    "source_type": "fatwa",
                    "text_content": piece,
                    "text_arabic": "",
                    "text_translation": "",
                    "metadata": {
                        "topic": topic,
                        "category": topic,
                        "madhab": "shafii",
                        "issuing_authority": "Mufti Wilayah Persekutuan",
                        "authority": "MuftiWP",
                        "fatwa_number": fatwa_number,
                        "series": post.get("category"),
                        "title": title,
                        "url": post.get("url"),
                        "date": post.get("date"),
                        "language": "ms",
                        "chunk_index": idx,
                        "source": "MuftiWP",
                        "source_name": "MuftiWP",
                    },
                }
            )
    return chunks


def main() -> None:
    raw_path = RAW_DIR / "muftiwp_posts.json"
    if not raw_path.exists():
        raise SystemExit(f"Raw fatwa file not found: {raw_path}")

    posts = json.loads(raw_path.read_text(encoding="utf-8"))
    if not isinstance(posts, list):
        raise SystemExit("Expected a list of posts in raw file")

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    chunks = process_posts(posts)

    out_path = PROCESSED_DIR / "fatwa_chunks.json"
    out_path.write_text(json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✓ Saved {len(chunks)} fatwa chunks to {out_path}")


if __name__ == "__main__":
    main()

