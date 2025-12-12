"""
Script to process downloaded Hadith data from various JSON sources.

This script:
1. Parses hadith collections from GitHub datasets
2. Normalizes grading (sahih/hasan/daif)
3. Extracts metadata (collection, number, narrator chain)
4. Creates chunks for embedding
5. Outputs JSON ready for database insertion
"""

import json
import re
from pathlib import Path
from typing import Optional

# Directories
RAW_DIR = Path(__file__).parent.parent / "raw" / "hadith"
PROCESSED_DIR = Path(__file__).parent.parent / "processed" / "hadith"

# Collection metadata
COLLECTIONS = {
    "bukhari": {
        "name_en": "Sahih al-Bukhari",
        "name_ar": "صحيح البخاري",
        "author": "Imam Muhammad ibn Ismail al-Bukhari",
        "default_grading": "sahih",
        "description": "The most authentic collection of hadith",
    },
    "muslim": {
        "name_en": "Sahih Muslim",
        "name_ar": "صحيح مسلم",
        "author": "Imam Muslim ibn al-Hajjaj",
        "default_grading": "sahih",
        "description": "The second most authentic collection of hadith",
    },
    "abudawud": {
        "name_en": "Sunan Abu Dawud",
        "name_ar": "سنن أبي داود",
        "author": "Imam Abu Dawud Sulayman ibn al-Ash'ath",
        "default_grading": "mixed",
        "description": "Collection focusing on legal hadith",
    },
    "tirmidhi": {
        "name_en": "Jami at-Tirmidhi",
        "name_ar": "جامع الترمذي",
        "author": "Imam Abu Isa Muhammad at-Tirmidhi",
        "default_grading": "mixed",
        "description": "Collection with grading commentary",
    },
    "nasai": {
        "name_en": "Sunan an-Nasa'i",
        "name_ar": "سنن النسائي",
        "author": "Imam Ahmad an-Nasa'i",
        "default_grading": "mixed",
        "description": "Collection known for strict narrator criteria",
    },
    "ibnmajah": {
        "name_en": "Sunan Ibn Majah",
        "name_ar": "سنن ابن ماجه",
        "author": "Imam Ibn Majah al-Qazwini",
        "default_grading": "mixed",
        "description": "The sixth of the major hadith collections",
    },
}

# Grading normalization map
GRADING_MAP = {
    # Sahih variants
    "sahih": "sahih",
    "صحيح": "sahih",
    "authentic": "sahih",
    "sound": "sahih",

    # Hasan variants
    "hasan": "hasan",
    "حسن": "hasan",
    "good": "hasan",
    "fair": "hasan",
    "hasan sahih": "hasan",

    # Daif variants
    "daif": "daif",
    "da'if": "daif",
    "ضعيف": "daif",
    "weak": "daif",

    # Maudu variants
    "maudu": "maudu",
    "fabricated": "maudu",
    "موضوع": "maudu",
}


def normalize_grading(grading: Optional[str], collection: str) -> str:
    """Normalize hadith grading to standard categories."""
    if not grading:
        # Default based on collection
        return COLLECTIONS.get(collection, {}).get("default_grading", "unknown")

    grading_lower = grading.lower().strip()

    # Check direct matches
    if grading_lower in GRADING_MAP:
        return GRADING_MAP[grading_lower]

    # Check partial matches
    for key, value in GRADING_MAP.items():
        if key in grading_lower:
            return value

    return "unknown"


def extract_narrator(text: str) -> Optional[str]:
    """Extract narrator name from hadith text if present."""
    # Common patterns for narrators
    patterns = [
        r"Narrated (?:by )?([^:]+?):",
        r"عن ([^:،]+?) قال",
        r"([A-Z][a-z]+ (?:ibn |bin )?[A-Z][a-z]+) reported",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()

    return None


def parse_github_hadith(file_path: Path, collection_key: str) -> list:
    """
    Parse hadith from GitHub dataset JSON format.

    Expected format varies, but commonly:
    [
        {
            "hadithNumber": 1,
            "hadithArabic": "...",
            "hadithEnglish": "...",
            "book": "...",
            "chapter": "...",
            ...
        }
    ]
    """
    if not file_path.exists():
        print(f"  File not found: {file_path}")
        return []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"  Error parsing JSON: {e}")
        return []

    hadiths = []
    collection_info = COLLECTIONS.get(collection_key, {})

    # Handle different JSON structures
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        # Some datasets have nested structure
        items = data.get("hadiths", data.get("data", []))
        if isinstance(items, dict):
            items = list(items.values())
    else:
        print(f"  Unknown data structure in {file_path}")
        return []

    for idx, item in enumerate(items):
        if not isinstance(item, dict):
            continue

        # Extract fields (handle various key names)
        hadith_num = (
            item.get("hadithNumber") or
            item.get("number") or
            item.get("id") or
            idx + 1
        )

        arabic_text = (
            item.get("hadithArabic") or
            item.get("arabic") or
            item.get("text_ar") or
            ""
        )

        english_text = (
            item.get("hadithEnglish") or
            item.get("english") or
            item.get("text_en") or
            item.get("text") or
            ""
        )

        book = (
            item.get("book") or
            item.get("bookName") or
            item.get("chapter") or
            ""
        )

        chapter = (
            item.get("chapter") or
            item.get("chapterName") or
            ""
        )

        grading = (
            item.get("grading") or
            item.get("grade") or
            item.get("status") or
            None
        )

        narrator = (
            item.get("narrator") or
            item.get("narratedBy") or
            extract_narrator(english_text) or
            None
        )

        # Create hadith entry
        hadith = {
            "collection": collection_key,
            "collection_name": collection_info.get("name_en", collection_key),
            "collection_name_ar": collection_info.get("name_ar", ""),
            "hadith_number": hadith_num,
            "book": book,
            "chapter": chapter,
            "text_arabic": arabic_text,
            "text_english": english_text,
            "grading": normalize_grading(grading, collection_key),
            "narrator": narrator,
        }

        hadiths.append(hadith)

    return hadiths


def create_hadith_chunk(hadith: dict) -> dict:
    """Create a chunk from a hadith for embedding."""
    collection_info = COLLECTIONS.get(hadith["collection"], {})

    # Create text content for embedding
    text_parts = []

    # Add reference
    ref = f"{hadith['collection_name']} #{hadith['hadith_number']}"
    text_parts.append(ref)

    # Add book/chapter if available
    if hadith.get("book"):
        text_parts.append(f"Book: {hadith['book']}")
    if hadith.get("chapter") and hadith["chapter"] != hadith.get("book"):
        text_parts.append(f"Chapter: {hadith['chapter']}")

    # Add grading
    grading = hadith.get("grading", "unknown")
    grading_display = {
        "sahih": "Sahih (Authentic)",
        "hasan": "Hasan (Good)",
        "daif": "Da'if (Weak)",
        "maudu": "Maudu' (Fabricated)",
        "unknown": "Grading Unknown",
    }.get(grading, grading)
    text_parts.append(f"Grading: {grading_display}")

    # Add narrator if available
    if hadith.get("narrator"):
        text_parts.append(f"Narrated by: {hadith['narrator']}")

    # Add hadith text
    if hadith.get("text_english"):
        text_parts.append("")
        text_parts.append(hadith["text_english"])

    text_content = "\n".join(text_parts)

    return {
        "source_type": "hadith",
        "text_content": text_content,
        "text_arabic": hadith.get("text_arabic", ""),
        "text_translation": hadith.get("text_english", ""),
        "metadata": {
            "collection": hadith["collection"],
            "collection_name": hadith["collection_name"],
            "collection_name_ar": hadith.get("collection_name_ar", ""),
            "hadith_number": hadith["hadith_number"],
            "book": hadith.get("book", ""),
            "chapter": hadith.get("chapter", ""),
            "grading": hadith.get("grading", "unknown"),
            "narrator": hadith.get("narrator"),
            "reference": f"{hadith['collection']}:{hadith['hadith_number']}",
        }
    }


def parse_sample_hadith(file_path: Path) -> list:
    """Parse the sample hadith file created by download script."""
    if not file_path.exists():
        return []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        return []

    hadiths = []
    for item in data:
        collection = item.get("collection", "Unknown")
        collection_key = collection.lower().replace(" ", "").replace("al-", "").replace("-", "")

        # Map to standard collection keys
        if "bukhari" in collection_key:
            collection_key = "bukhari"
        elif "muslim" in collection_key:
            collection_key = "muslim"
        elif "tirmidhi" in collection_key:
            collection_key = "tirmidhi"
        elif "abudawud" in collection_key or "dawud" in collection_key:
            collection_key = "abudawud"
        elif "nasai" in collection_key:
            collection_key = "nasai"
        elif "ibnmajah" in collection_key or "majah" in collection_key:
            collection_key = "ibnmajah"

        collection_info = COLLECTIONS.get(collection_key, {})

        hadith = {
            "collection": collection_key,
            "collection_name": collection_info.get("name_en", item.get("collection")),
            "collection_name_ar": collection_info.get("name_ar", ""),
            "hadith_number": item.get("hadith_number", ""),
            "book": item.get("book", ""),
            "chapter": "",
            "text_arabic": item.get("text_ar", ""),
            "text_english": item.get("text_en", ""),
            "grading": normalize_grading(item.get("grading"), collection_key),
            "narrator": item.get("narrator"),
        }
        hadiths.append(hadith)

    return hadiths


def process_hadith_data():
    """Main processing function."""
    print("=" * 60)
    print("IlmuAI - Hadith Data Processor")
    print("=" * 60)
    print()

    # Create output directory
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    all_hadiths = []
    all_chunks = []

    # Process each collection
    print("Processing hadith collections...")
    print()

    for collection_key, collection_info in COLLECTIONS.items():
        file_path = RAW_DIR / f"{collection_key}.json"

        print(f"Processing: {collection_info['name_en']}")

        hadiths = parse_github_hadith(file_path, collection_key)

        if hadiths:
            print(f"  Loaded {len(hadiths)} hadiths")
            all_hadiths.extend(hadiths)

            # Create chunks
            for hadith in hadiths:
                chunk = create_hadith_chunk(hadith)
                all_chunks.append(chunk)
        else:
            print(f"  No data found or could not parse")

        print()

    # Check for sample data if no collections were loaded
    if not all_hadiths:
        print("No collection data found. Checking for sample data...")
        sample_file = RAW_DIR / "sample_hadiths.json"
        sample_hadiths = parse_sample_hadith(sample_file)

        if sample_hadiths:
            print(f"Loaded {len(sample_hadiths)} sample hadiths")
            all_hadiths.extend(sample_hadiths)

            for hadith in sample_hadiths:
                chunk = create_hadith_chunk(hadith)
                all_chunks.append(chunk)
        else:
            print("No hadith data found!")
            print("Please run download_hadith.py first")
            return

    # Save processed hadiths (full data)
    hadiths_output = PROCESSED_DIR / "hadiths_processed.json"
    with open(hadiths_output, "w", encoding="utf-8") as f:
        json.dump(all_hadiths, f, ensure_ascii=False, indent=2)
    print(f"Saved processed hadiths to: {hadiths_output}")

    # Save chunks for embedding
    chunks_output = PROCESSED_DIR / "hadith_chunks.json"
    with open(chunks_output, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)
    print(f"Saved hadith chunks to: {chunks_output}")

    # Create collection summary
    summary = {}
    for hadith in all_hadiths:
        collection = hadith["collection"]
        if collection not in summary:
            summary[collection] = {
                "name": hadith["collection_name"],
                "count": 0,
                "gradings": {"sahih": 0, "hasan": 0, "daif": 0, "unknown": 0},
            }
        summary[collection]["count"] += 1
        grading = hadith.get("grading", "unknown")
        if grading in summary[collection]["gradings"]:
            summary[collection]["gradings"][grading] += 1
        else:
            summary[collection]["gradings"]["unknown"] += 1

    summary_output = PROCESSED_DIR / "collection_summary.json"
    with open(summary_output, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"Saved collection summary to: {summary_output}")

    # Print summary
    print()
    print("=" * 60)
    print("Processing Complete!")
    print("=" * 60)
    print()
    print("Summary by collection:")
    for collection, info in summary.items():
        print(f"  {info['name']}: {info['count']} hadiths")
        print(f"    - Sahih: {info['gradings']['sahih']}")
        print(f"    - Hasan: {info['gradings']['hasan']}")
        print(f"    - Da'if: {info['gradings']['daif']}")
        print(f"    - Unknown: {info['gradings']['unknown']}")
        print()

    print(f"Total hadiths processed: {len(all_hadiths)}")
    print(f"Total chunks created: {len(all_chunks)}")
    print()
    print("Files created:")
    print(f"  1. {hadiths_output.name} - Full processed hadith data")
    print(f"  2. {chunks_output.name} - Chunks ready for embedding")
    print(f"  3. {summary_output.name} - Collection statistics")
    print()
    print("Next steps:")
    print("  1. Run generate_embeddings.py to create vector embeddings")
    print("  2. Seed the database with the processed chunks")
    print()
    print("Note: For production, consider using sunnah.com API for")
    print("more comprehensive data with better grading information.")


if __name__ == "__main__":
    process_hadith_data()
