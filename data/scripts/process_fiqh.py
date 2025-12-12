"""
Script to process Shafi'i Fiqh data.

This script:
1. Processes sample fiqh JSON data (from download script)
2. Extracts text from PDF files (if PyMuPDF is available)
3. Chunks text by topic/section
4. Creates structured data for embedding
5. Outputs JSON ready for database insertion

Note: PDF extraction requires PyMuPDF (fitz) library:
  pip install PyMuPDF
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional

# Directories
RAW_DIR = Path(__file__).parent.parent / "raw" / "fiqh"
PROCESSED_DIR = Path(__file__).parent.parent / "processed" / "fiqh"

# Fiqh categories for classification
FIQH_CATEGORIES = {
    "taharah": {
        "name_en": "Purification",
        "name_ms": "Taharah (Bersuci)",
        "keywords": [
            "wuduk",
            "wudu",
            "ablution",
            "mandi",
            "bath",
            "najis",
            "tayammum",
            "istinja",
            "طهارة",
            "وضوء",
            "غسل",
            "تيمم",
            "نجاسة",
            "استنجاء",
        ],
    },
    "solat": {
        "name_en": "Prayer",
        "name_ms": "Solat",
        "keywords": [
            "solat",
            "salat",
            "prayer",
            "rukuk",
            "sujud",
            "takbir",
            "tasyahhud",
            "salam",
            "صلاة",
            "ركوع",
            "سجود",
            "تكبير",
            "تشهد",
            "سلام",
        ],
    },
    "puasa": {
        "name_en": "Fasting",
        "name_ms": "Puasa",
        "keywords": [
            "puasa",
            "fasting",
            "ramadan",
            "sahur",
            "iftar",
            "berbuka",
            "qadha",
            "صوم",
            "صيام",
            "رمضان",
            "إفطار",
            "سحور",
            "قضاء",
        ],
    },
    "zakat": {
        "name_en": "Zakat",
        "name_ms": "Zakat",
        "keywords": ["zakat", "nisab", "haul", "fitrah", "sedekah", "زكاة", "نصاب", "حول", "صدقة"],
    },
    "haji": {
        "name_en": "Pilgrimage",
        "name_ms": "Haji dan Umrah",
        "keywords": [
            "haji",
            "hajj",
            "umrah",
            "tawaf",
            "sa'i",
            "ihram",
            "miqat",
            "wukuf",
            "حج",
            "عمرة",
            "طواف",
            "سعي",
            "إحرام",
            "ميقات",
            "وقوف",
        ],
    },
    "muamalat": {
        "name_en": "Transactions",
        "name_ms": "Muamalat",
        "keywords": [
            "jual beli",
            "trade",
            "riba",
            "interest",
            "hutang",
            "debt",
            "akad",
            "contract",
            "بيع",
            "ربا",
            "قرض",
            "دين",
            "عقد",
        ],
    },
    "munakahat": {
        "name_en": "Marriage",
        "name_ms": "Munakahat (Perkahwinan)",
        "keywords": [
            "nikah",
            "marriage",
            "talaq",
            "divorce",
            "iddah",
            "mahar",
            "nafkah",
            "walimah",
            "نكاح",
            "طلاق",
            "عدة",
            "مهر",
            "نفقة",
        ],
    },
    "jenazah": {
        "name_en": "Funeral",
        "name_ms": "Jenazah",
        "keywords": [
            "jenazah",
            "funeral",
            "mati",
            "death",
            "kafan",
            "solat jenazah",
            "kubur",
            "جنائز",
            "ميت",
            "كفن",
            "دفن",
            "غسل الميت",
        ],
    },
    "makanan": {
        "name_en": "Food",
        "name_ms": "Makanan dan Minuman",
        "keywords": [
            "halal",
            "haram",
            "makanan",
            "food",
            "minuman",
            "drink",
            "sembelihan",
            "حلال",
            "حرام",
            "أطعمة",
            "شراب",
            "ذبيحة",
        ],
    },
}

# Arabic Digital Humanities Fiqh Corpus (OpenITI markup)
ADH_DIR = RAW_DIR / "adh_fiqh_corpus" / "txt"


def parse_openiti_metadata(lines: List[str]) -> Dict[str, str]:
    """Extract OpenITI #META# header key-values."""
    meta: Dict[str, str] = {}
    for line in lines:
        if not line.startswith("#META#"):
            continue
        match = re.match(r"#META#\s*([^\s]+)\s*::\s*(.*)$", line)
        if not match:
            continue
        raw_key = match.group(1).strip()
        key = raw_key.split(".")[-1]  # e.g., 010.AuthorNAME -> AuthorNAME
        value = match.group(2).strip()
        if key and value:
            meta[key] = value
    return meta


def clean_openiti_text(raw_text: str) -> str:
    """Remove OpenITI headers/markers and normalize whitespace."""
    text = raw_text
    text = re.sub(r"^######OpenITI#.*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^#META#.*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^#\s*.*$", "", text, flags=re.MULTILINE)
    # Remove page/milestone markers
    text = re.sub(r"PageV\d+P\d+", " ", text)
    text = re.sub(r"Milestone\d+", " ", text)
    # Remove bracketed section markers but keep content
    text = re.sub(r"^###\s*\|{1,3}.*$", " ", text, flags=re.MULTILINE)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def chunk_text_sliding(text: str, chunk_size: int = 1200, overlap: int = 200) -> List[str]:
    """Chunk text with character sliding window and overlap."""
    if not text:
        return []
    chunks: List[str] = []
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


def detect_madhab(meta: Dict[str, str], filename: str, head_text: str) -> str:
    """Best-effort madhab detection for filtering."""
    haystack = " ".join(
        [
            filename,
            meta.get("BookURI", ""),
            meta.get("AuthorNAME", ""),
            meta.get("AuthorAKA", ""),
            head_text,
        ]
    )
    if re.search(r"الشافعي|شافعي|Shafici|Shafii|Shafi", haystack, flags=re.IGNORECASE):
        return "shafii"
    return "general"


def process_adh_fiqh_corpus(max_files: int | None = None) -> List[dict]:
    """Process ADH/OpenITI fiqh corpus into chunks."""
    if not ADH_DIR.exists():
        print("  ADH corpus not found, skipping.")
        return []

    corpus_files = sorted(ADH_DIR.glob("*.txt"))
    if max_files:
        corpus_files = corpus_files[:max_files]

    print(f"Processing ADH fiqh corpus ({len(corpus_files)} files)...")
    chunks: List[dict] = []
    for file_path in corpus_files:
        try:
            raw_text = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            print(f"  Skipping {file_path.name}: {e}")
            continue

        lines = raw_text.splitlines()
        meta = parse_openiti_metadata(lines[:300])
        cleaned = clean_openiti_text(raw_text)
        if not cleaned:
            continue

        file_head = cleaned[:2000]
        madhab = detect_madhab(meta, file_path.name, file_head)
        file_chunks = chunk_text_sliding(cleaned, chunk_size=1200, overlap=200)

        author_name = meta.get("AuthorNAME") or meta.get("AuthorAKA") or ""
        book_uri = meta.get("BookURI") or file_path.stem

        for idx, chunk_text in enumerate(file_chunks):
            category = classify_topic(chunk_text)
            cat_info = FIQH_CATEGORIES.get(category, {})
            topic_label = cat_info.get("name_ms", category.title())
            chunks.append(
                {
                    "source_type": "fiqh",
                    "text_content": chunk_text,
                    "text_arabic": chunk_text,
                    "text_translation": "",
                    "metadata": {
                        "topic": topic_label,
                        "category": category,
                        "madhab": madhab,
                        "source": "ADH Fiqh Corpus",
                        "source_name": "ADH Fiqh Corpus",
                        "author": author_name,
                        "book_uri": book_uri,
                        "language": "ar",
                        "chunk_index": idx,
                    },
                }
            )

    print(f"  Created {len(chunks)} ADH fiqh chunks")
    return chunks


def classify_topic(text: str) -> str:
    """Classify fiqh text into a category based on keywords."""
    text_lower = text.lower()

    scores = {}
    for category, info in FIQH_CATEGORIES.items():
        score = sum(1 for kw in info["keywords"] if kw in text_lower)
        if score > 0:
            scores[category] = score

    if scores:
        return max(scores, key=scores.get)

    return "general"


def process_sample_fiqh(file_path: Path) -> list:
    """Process the sample fiqh JSON from download script."""
    if not file_path.exists():
        return []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"  Error parsing JSON: {e}")
        return []

    chunks = []

    for item in data:
        topic = item.get("topic", "")
        category = item.get("category", "").lower()

        # Classify if category not provided
        if not category or category == "ibadah":
            category = classify_topic(topic + " " + item.get("ruling_bm", ""))

        # Get category info
        cat_info = FIQH_CATEGORIES.get(category, {})

        # Create text content for embedding
        text_parts = []

        # Add topic header
        text_parts.append(f"Topik: {topic}")
        text_parts.append(f"Kategori: {cat_info.get('name_ms', category.title())}")
        text_parts.append(f"Mazhab: Syafi'i")
        text_parts.append("")

        # Add Malay ruling
        if item.get("ruling_bm"):
            text_parts.append("Hukum (Bahasa Melayu):")
            text_parts.append(item["ruling_bm"])
            text_parts.append("")

        # Add English ruling
        if item.get("ruling_en"):
            text_parts.append("Ruling (English):")
            text_parts.append(item["ruling_en"])
            text_parts.append("")

        # Add evidence
        if item.get("evidence"):
            text_parts.append(f"Dalil: {item['evidence']}")

        text_content = "\n".join(text_parts)

        chunk = {
            "source_type": "fiqh",
            "text_content": text_content,
            "text_arabic": "",  # Arabic text if available
            "text_translation": item.get("ruling_bm", ""),
            "metadata": {
                "topic": topic,
                "category": category,
                "category_name_en": cat_info.get("name_en", category.title()),
                "category_name_ms": cat_info.get("name_ms", category.title()),
                "madhab": item.get("madhab", "shafii"),
                "source": item.get("source", ""),
                "evidence": item.get("evidence", ""),
                "language": "ms",
            }
        }

        chunks.append(chunk)

    return chunks


def extract_pdf_text(file_path: Path) -> Optional[str]:
    """
    Extract text from a PDF file using PyMuPDF.

    Returns None if PyMuPDF is not installed or extraction fails.
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        return None

    try:
        doc = fitz.open(file_path)
        text_parts = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            if text.strip():
                text_parts.append(f"--- Page {page_num + 1} ---")
                text_parts.append(text)

        doc.close()
        return "\n".join(text_parts)

    except Exception as e:
        print(f"  Error extracting PDF: {e}")
        return None


def chunk_pdf_text(text: str, source_name: str, chunk_size: int = 1000, overlap: int = 200) -> list:
    """
    Chunk PDF text into smaller pieces for embedding.

    Uses a sliding window approach with overlap for context preservation.
    """
    chunks = []

    # Split by pages first
    pages = text.split("--- Page ")

    current_chunk = ""
    chunk_index = 0

    for page in pages:
        if not page.strip():
            continue

        # Clean page marker
        page_text = re.sub(r"^\d+ ---\n?", "", page).strip()

        # If page is small enough, add to current chunk
        if len(current_chunk) + len(page_text) < chunk_size:
            current_chunk += "\n\n" + page_text if current_chunk else page_text
        else:
            # Save current chunk if non-empty
            if current_chunk.strip():
                topic = classify_topic(current_chunk)
                cat_info = FIQH_CATEGORIES.get(topic, {})

                chunk = {
                    "source_type": "fiqh",
                    "text_content": current_chunk,
                    "text_arabic": "",
                    "text_translation": "",
                    "metadata": {
                        "topic": cat_info.get("name_ms", topic.title()),
                        "category": topic,
                        "category_name_en": cat_info.get("name_en", topic.title()),
                        "category_name_ms": cat_info.get("name_ms", topic.title()),
                        "madhab": "shafii",
                        "source": source_name,
                        "chunk_index": chunk_index,
                        "language": "ms",
                    }
                }
                chunks.append(chunk)
                chunk_index += 1

            # Start new chunk with overlap
            words = current_chunk.split()
            overlap_text = " ".join(words[-overlap:]) if len(words) > overlap else ""
            current_chunk = overlap_text + "\n\n" + page_text

    # Don't forget the last chunk
    if current_chunk.strip():
        topic = classify_topic(current_chunk)
        cat_info = FIQH_CATEGORIES.get(topic, {})

        chunk = {
            "source_type": "fiqh",
            "text_content": current_chunk,
            "text_arabic": "",
            "text_translation": "",
            "metadata": {
                "topic": cat_info.get("name_ms", topic.title()),
                "category": topic,
                "category_name_en": cat_info.get("name_en", topic.title()),
                "category_name_ms": cat_info.get("name_ms", topic.title()),
                "madhab": "shafii",
                "source": source_name,
                "chunk_index": chunk_index,
                "language": "ms",
            }
        }
        chunks.append(chunk)

    return chunks


def process_fiqh_pdfs() -> list:
    """Process PDF files from the raw fiqh directory."""
    chunks = []

    pdf_files = list(RAW_DIR.glob("*.pdf"))

    if not pdf_files:
        print("  No PDF files found")
        return chunks

    try:
        import fitz  # noqa
        print(f"  Found {len(pdf_files)} PDF files")
    except ImportError:
        print("  PyMuPDF not installed. Skipping PDF processing.")
        print("  To enable PDF processing: pip install PyMuPDF")
        return chunks

    for pdf_path in pdf_files:
        print(f"  Processing: {pdf_path.name}")

        text = extract_pdf_text(pdf_path)
        if text:
            pdf_chunks = chunk_pdf_text(text, pdf_path.stem)
            print(f"    Created {len(pdf_chunks)} chunks")
            chunks.extend(pdf_chunks)
        else:
            print(f"    Could not extract text")

    return chunks


def process_fiqh_data():
    """Main processing function."""
    print("=" * 60)
    print("IlmuAI - Fiqh Data Processor")
    print("=" * 60)
    print()

    # Create output directory
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    all_chunks = []

    # Process sample fiqh JSON
    print("Processing sample fiqh data...")
    sample_file = RAW_DIR / "sample_fiqh.json"
    sample_chunks = process_sample_fiqh(sample_file)

    if sample_chunks:
        print(f"  Loaded {len(sample_chunks)} sample fiqh rulings")
        all_chunks.extend(sample_chunks)
    else:
        print("  No sample data found")

    print()

    # Process ADH/OpenITI fiqh corpus
    adh_chunks = process_adh_fiqh_corpus()
    if adh_chunks:
        all_chunks.extend(adh_chunks)
    print()

    # Process PDF files
    print("Processing PDF files...")
    pdf_chunks = process_fiqh_pdfs()

    if pdf_chunks:
        all_chunks.extend(pdf_chunks)

    print()

    if not all_chunks:
        print("No fiqh data found!")
        print("Please run download_fiqh.py first")
        print()
        print("For sample data, the download script creates sample_fiqh.json")
        print("For PDF data, install PyMuPDF: pip install PyMuPDF")
        return

    # Save processed chunks
    chunks_output = PROCESSED_DIR / "fiqh_chunks.json"
    with open(chunks_output, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)
    print(f"Saved fiqh chunks to: {chunks_output}")

    # Create category summary
    category_counts = {}
    for chunk in all_chunks:
        cat = chunk["metadata"].get("category", "general")
        category_counts[cat] = category_counts.get(cat, 0) + 1

    summary = {
        "total_chunks": len(all_chunks),
        "categories": category_counts,
        "madhab": "shafii",
        "sources": list(set(c["metadata"].get("source", "") for c in all_chunks if c["metadata"].get("source"))),
    }

    summary_output = PROCESSED_DIR / "fiqh_summary.json"
    with open(summary_output, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"Saved summary to: {summary_output}")

    # Print summary
    print()
    print("=" * 60)
    print("Processing Complete!")
    print("=" * 60)
    print()
    print(f"Total chunks created: {len(all_chunks)}")
    print()
    print("Chunks by category:")
    for cat, count in sorted(category_counts.items(), key=lambda x: -x[1]):
        cat_info = FIQH_CATEGORIES.get(cat, {})
        name = cat_info.get("name_ms", cat.title())
        print(f"  {name}: {count}")

    print()
    print("Files created:")
    print(f"  1. {chunks_output.name} - Fiqh chunks ready for embedding")
    print(f"  2. {summary_output.name} - Processing summary")
    print()
    print("Next steps:")
    print("  1. Run generate_embeddings.py to create vector embeddings")
    print("  2. Seed the database with the processed chunks")
    print()
    print("Notes:")
    print("  - Sample data provides basic Shafi'i fiqh rulings")
    print("  - For comprehensive data, consider:")
    print("    * Digitizing Al-Fiqh Al-Manhaji manually")
    print("    * Obtaining official JAKIM content")
    print("    * Academic Islamic law databases")


if __name__ == "__main__":
    process_fiqh_data()
