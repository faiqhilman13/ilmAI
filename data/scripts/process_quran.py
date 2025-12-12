"""
Script to process downloaded Quran data from Tanzil.net XML files.

This script:
1. Parses Arabic text (Uthmani script)
2. Parses Malay translation (Basmeih)
3. Parses English translation (Sahih International)
4. Combines them into structured chunks for embedding
5. Outputs JSON ready for database insertion
"""

import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

# Directories
RAW_DIR = Path(__file__).parent.parent / "raw" / "quran"
PROCESSED_DIR = Path(__file__).parent.parent / "processed" / "quran"

# Surah names in Arabic, English and Malay
SURAH_NAMES = {
    1: {"ar": "الفاتحة", "en": "Al-Fatihah", "ms": "Al-Fatihah"},
    2: {"ar": "البقرة", "en": "Al-Baqarah", "ms": "Al-Baqarah"},
    3: {"ar": "آل عمران", "en": "Ali 'Imran", "ms": "Ali 'Imran"},
    4: {"ar": "النساء", "en": "An-Nisa", "ms": "An-Nisa'"},
    5: {"ar": "المائدة", "en": "Al-Ma'idah", "ms": "Al-Ma'idah"},
    6: {"ar": "الأنعام", "en": "Al-An'am", "ms": "Al-An'am"},
    7: {"ar": "الأعراف", "en": "Al-A'raf", "ms": "Al-A'raf"},
    8: {"ar": "الأنفال", "en": "Al-Anfal", "ms": "Al-Anfal"},
    9: {"ar": "التوبة", "en": "At-Tawbah", "ms": "At-Taubah"},
    10: {"ar": "يونس", "en": "Yunus", "ms": "Yunus"},
    11: {"ar": "هود", "en": "Hud", "ms": "Hud"},
    12: {"ar": "يوسف", "en": "Yusuf", "ms": "Yusuf"},
    13: {"ar": "الرعد", "en": "Ar-Ra'd", "ms": "Ar-Ra'd"},
    14: {"ar": "ابراهيم", "en": "Ibrahim", "ms": "Ibrahim"},
    15: {"ar": "الحجر", "en": "Al-Hijr", "ms": "Al-Hijr"},
    16: {"ar": "النحل", "en": "An-Nahl", "ms": "An-Nahl"},
    17: {"ar": "الإسراء", "en": "Al-Isra", "ms": "Al-Isra'"},
    18: {"ar": "الكهف", "en": "Al-Kahf", "ms": "Al-Kahf"},
    19: {"ar": "مريم", "en": "Maryam", "ms": "Maryam"},
    20: {"ar": "طه", "en": "Ta-Ha", "ms": "Ta Ha"},
    21: {"ar": "الأنبياء", "en": "Al-Anbiya", "ms": "Al-Anbiya'"},
    22: {"ar": "الحج", "en": "Al-Hajj", "ms": "Al-Hajj"},
    23: {"ar": "المؤمنون", "en": "Al-Mu'minun", "ms": "Al-Mu'minun"},
    24: {"ar": "النور", "en": "An-Nur", "ms": "An-Nur"},
    25: {"ar": "الفرقان", "en": "Al-Furqan", "ms": "Al-Furqan"},
    26: {"ar": "الشعراء", "en": "Ash-Shu'ara", "ms": "Asy-Syu'ara'"},
    27: {"ar": "النمل", "en": "An-Naml", "ms": "An-Naml"},
    28: {"ar": "القصص", "en": "Al-Qasas", "ms": "Al-Qasas"},
    29: {"ar": "العنكبوت", "en": "Al-'Ankabut", "ms": "Al-'Ankabut"},
    30: {"ar": "الروم", "en": "Ar-Rum", "ms": "Ar-Rum"},
    31: {"ar": "لقمان", "en": "Luqman", "ms": "Luqman"},
    32: {"ar": "السجدة", "en": "As-Sajdah", "ms": "As-Sajdah"},
    33: {"ar": "الأحزاب", "en": "Al-Ahzab", "ms": "Al-Ahzab"},
    34: {"ar": "سبإ", "en": "Saba", "ms": "Saba'"},
    35: {"ar": "فاطر", "en": "Fatir", "ms": "Fatir"},
    36: {"ar": "يس", "en": "Ya-Sin", "ms": "Ya Sin"},
    37: {"ar": "الصافات", "en": "As-Saffat", "ms": "As-Saffat"},
    38: {"ar": "ص", "en": "Sad", "ms": "Sad"},
    39: {"ar": "الزمر", "en": "Az-Zumar", "ms": "Az-Zumar"},
    40: {"ar": "غافر", "en": "Ghafir", "ms": "Ghafir"},
    41: {"ar": "فصلت", "en": "Fussilat", "ms": "Fussilat"},
    42: {"ar": "الشورى", "en": "Ash-Shura", "ms": "Asy-Syura"},
    43: {"ar": "الزخرف", "en": "Az-Zukhruf", "ms": "Az-Zukhruf"},
    44: {"ar": "الدخان", "en": "Ad-Dukhan", "ms": "Ad-Dukhan"},
    45: {"ar": "الجاثية", "en": "Al-Jathiyah", "ms": "Al-Jathiyah"},
    46: {"ar": "الأحقاف", "en": "Al-Ahqaf", "ms": "Al-Ahqaf"},
    47: {"ar": "محمد", "en": "Muhammad", "ms": "Muhammad"},
    48: {"ar": "الفتح", "en": "Al-Fath", "ms": "Al-Fath"},
    49: {"ar": "الحجرات", "en": "Al-Hujurat", "ms": "Al-Hujurat"},
    50: {"ar": "ق", "en": "Qaf", "ms": "Qaf"},
    51: {"ar": "الذاريات", "en": "Adh-Dhariyat", "ms": "Adz-Dzariyat"},
    52: {"ar": "الطور", "en": "At-Tur", "ms": "At-Tur"},
    53: {"ar": "النجم", "en": "An-Najm", "ms": "An-Najm"},
    54: {"ar": "القمر", "en": "Al-Qamar", "ms": "Al-Qamar"},
    55: {"ar": "الرحمن", "en": "Ar-Rahman", "ms": "Ar-Rahman"},
    56: {"ar": "الواقعة", "en": "Al-Waqi'ah", "ms": "Al-Waqi'ah"},
    57: {"ar": "الحديد", "en": "Al-Hadid", "ms": "Al-Hadid"},
    58: {"ar": "المجادلة", "en": "Al-Mujadila", "ms": "Al-Mujadilah"},
    59: {"ar": "الحشر", "en": "Al-Hashr", "ms": "Al-Hasyr"},
    60: {"ar": "الممتحنة", "en": "Al-Mumtahanah", "ms": "Al-Mumtahanah"},
    61: {"ar": "الصف", "en": "As-Saff", "ms": "As-Saff"},
    62: {"ar": "الجمعة", "en": "Al-Jumu'ah", "ms": "Al-Jumu'ah"},
    63: {"ar": "المنافقون", "en": "Al-Munafiqun", "ms": "Al-Munafiqun"},
    64: {"ar": "التغابن", "en": "At-Taghabun", "ms": "At-Taghabun"},
    65: {"ar": "الطلاق", "en": "At-Talaq", "ms": "At-Talaq"},
    66: {"ar": "التحريم", "en": "At-Tahrim", "ms": "At-Tahrim"},
    67: {"ar": "الملك", "en": "Al-Mulk", "ms": "Al-Mulk"},
    68: {"ar": "القلم", "en": "Al-Qalam", "ms": "Al-Qalam"},
    69: {"ar": "الحاقة", "en": "Al-Haqqah", "ms": "Al-Haqqah"},
    70: {"ar": "المعارج", "en": "Al-Ma'arij", "ms": "Al-Ma'arij"},
    71: {"ar": "نوح", "en": "Nuh", "ms": "Nuh"},
    72: {"ar": "الجن", "en": "Al-Jinn", "ms": "Al-Jinn"},
    73: {"ar": "المزمل", "en": "Al-Muzzammil", "ms": "Al-Muzzammil"},
    74: {"ar": "المدثر", "en": "Al-Muddaththir", "ms": "Al-Muddaththir"},
    75: {"ar": "القيامة", "en": "Al-Qiyamah", "ms": "Al-Qiyamah"},
    76: {"ar": "الانسان", "en": "Al-Insan", "ms": "Al-Insan"},
    77: {"ar": "المرسلات", "en": "Al-Mursalat", "ms": "Al-Mursalat"},
    78: {"ar": "النبإ", "en": "An-Naba", "ms": "An-Naba'"},
    79: {"ar": "النازعات", "en": "An-Nazi'at", "ms": "An-Nazi'at"},
    80: {"ar": "عبس", "en": "'Abasa", "ms": "'Abasa"},
    81: {"ar": "التكوير", "en": "At-Takwir", "ms": "At-Takwir"},
    82: {"ar": "الإنفطار", "en": "Al-Infitar", "ms": "Al-Infitar"},
    83: {"ar": "المطففين", "en": "Al-Mutaffifin", "ms": "Al-Mutaffifin"},
    84: {"ar": "الإنشقاق", "en": "Al-Inshiqaq", "ms": "Al-Insyiqaq"},
    85: {"ar": "البروج", "en": "Al-Buruj", "ms": "Al-Buruj"},
    86: {"ar": "الطارق", "en": "At-Tariq", "ms": "At-Tariq"},
    87: {"ar": "الأعلى", "en": "Al-A'la", "ms": "Al-A'la"},
    88: {"ar": "الغاشية", "en": "Al-Ghashiyah", "ms": "Al-Ghasyiyah"},
    89: {"ar": "الفجر", "en": "Al-Fajr", "ms": "Al-Fajr"},
    90: {"ar": "البلد", "en": "Al-Balad", "ms": "Al-Balad"},
    91: {"ar": "الشمس", "en": "Ash-Shams", "ms": "Asy-Syams"},
    92: {"ar": "الليل", "en": "Al-Layl", "ms": "Al-Lail"},
    93: {"ar": "الضحى", "en": "Ad-Duha", "ms": "Ad-Dhuha"},
    94: {"ar": "الشرح", "en": "Ash-Sharh", "ms": "Asy-Syarh"},
    95: {"ar": "التين", "en": "At-Tin", "ms": "At-Tin"},
    96: {"ar": "العلق", "en": "Al-'Alaq", "ms": "Al-'Alaq"},
    97: {"ar": "القدر", "en": "Al-Qadr", "ms": "Al-Qadr"},
    98: {"ar": "البينة", "en": "Al-Bayyinah", "ms": "Al-Bayyinah"},
    99: {"ar": "الزلزلة", "en": "Az-Zalzalah", "ms": "Az-Zalzalah"},
    100: {"ar": "العاديات", "en": "Al-'Adiyat", "ms": "Al-'Adiyat"},
    101: {"ar": "القارعة", "en": "Al-Qari'ah", "ms": "Al-Qari'ah"},
    102: {"ar": "التكاثر", "en": "At-Takathur", "ms": "At-Takathur"},
    103: {"ar": "العصر", "en": "Al-'Asr", "ms": "Al-'Asr"},
    104: {"ar": "الهمزة", "en": "Al-Humazah", "ms": "Al-Humazah"},
    105: {"ar": "الفيل", "en": "Al-Fil", "ms": "Al-Fil"},
    106: {"ar": "قريش", "en": "Quraysh", "ms": "Quraisy"},
    107: {"ar": "الماعون", "en": "Al-Ma'un", "ms": "Al-Ma'un"},
    108: {"ar": "الكوثر", "en": "Al-Kawthar", "ms": "Al-Kauthar"},
    109: {"ar": "الكافرون", "en": "Al-Kafirun", "ms": "Al-Kafirun"},
    110: {"ar": "النصر", "en": "An-Nasr", "ms": "An-Nasr"},
    111: {"ar": "المسد", "en": "Al-Masad", "ms": "Al-Lahab"},
    112: {"ar": "الإخلاص", "en": "Al-Ikhlas", "ms": "Al-Ikhlas"},
    113: {"ar": "الفلق", "en": "Al-Falaq", "ms": "Al-Falaq"},
    114: {"ar": "الناس", "en": "An-Nas", "ms": "An-Nas"},
}


def parse_tanzil_xml(file_path: Path) -> dict:
    """
    Parse a Tanzil.net XML file.

    Returns dict with structure:
    {
        surah_number: {
            ayah_number: text
        }
    }
    """
    if not file_path.exists():
        print(f"File not found: {file_path}")
        return {}

    result = {}

    try:
        # Read file content and normalize line endings to fix CRLF parsing issues
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Normalize CRLF to LF
        content = content.replace('\r\n', '\n')

        # Remove the problematic comment block (lines before <quran> tag)
        # This fixes XML parsing issues with Tanzil.net files that have # characters in comments
        import re
        content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)

        # Parse from string instead of file
        root = ET.fromstring(content)

        # Handle both quran XML and translation XML formats
        for sura in root.findall('.//sura'):
            sura_num = int(sura.get('index'))
            result[sura_num] = {}

            for aya in sura.findall('.//aya'):
                aya_num = int(aya.get('index'))
                text = aya.get('text', '')
                result[sura_num][aya_num] = text

    except ET.ParseError as e:
        print(f"Error parsing XML {file_path}: {e}")
        return {}

    return result


def create_ayah_chunk(
    surah_num: int,
    ayah_num: int,
    arabic: str,
    translation_ms: Optional[str],
    translation_en: Optional[str]
) -> dict:
    """Create a single ayah chunk for embedding."""
    surah_names = SURAH_NAMES.get(surah_num, {"ar": "", "en": "", "ms": ""})

    # Create combined text for embedding
    # Format: Surah Name (Num:Ayah) - Translation
    text_parts = []

    # Add surah and ayah reference
    reference = f"Surah {surah_names['en']} ({surah_num}:{ayah_num})"
    text_parts.append(reference)

    # Add translations (prefer Malay for embedding as target audience is Malaysian)
    if translation_ms:
        text_parts.append(f"Terjemahan: {translation_ms}")
    if translation_en:
        text_parts.append(f"Translation: {translation_en}")

    text_content = "\n".join(text_parts)

    return {
        "source_type": "quran",
        "text_content": text_content,
        "text_arabic": arabic,
        "text_translation": translation_ms or translation_en or "",
        "metadata": {
            "surah_number": surah_num,
            "surah_name_ar": surah_names["ar"],
            "surah_name_en": surah_names["en"],
            "surah_name_ms": surah_names["ms"],
            "ayah_number": ayah_num,
            "reference": f"{surah_num}:{ayah_num}",
            "translation_source_ms": "ms.basmeih",
            "translation_source_en": "en.sahih",
        }
    }


def create_grouped_chunks(
    arabic_data: dict,
    ms_data: dict,
    en_data: dict,
    group_size: int = 3
) -> list:
    """
    Create chunks by grouping consecutive ayahs.

    This is useful for context - some ayahs make more sense together.
    """
    chunks = []

    for surah_num in sorted(arabic_data.keys()):
        ayahs = sorted(arabic_data[surah_num].keys())
        surah_names = SURAH_NAMES.get(surah_num, {"ar": "", "en": "", "ms": ""})

        # Group ayahs
        for i in range(0, len(ayahs), group_size):
            group = ayahs[i:i + group_size]

            # Collect texts for the group
            arabic_texts = []
            ms_texts = []
            en_texts = []

            for ayah_num in group:
                arabic_texts.append(f"({ayah_num}) {arabic_data[surah_num].get(ayah_num, '')}")
                if ms_data and surah_num in ms_data:
                    ms_texts.append(f"({ayah_num}) {ms_data[surah_num].get(ayah_num, '')}")
                if en_data and surah_num in en_data:
                    en_texts.append(f"({ayah_num}) {en_data[surah_num].get(ayah_num, '')}")

            # Create reference range
            if len(group) == 1:
                ref = f"{surah_num}:{group[0]}"
            else:
                ref = f"{surah_num}:{group[0]}-{group[-1]}"

            # Create combined text for embedding
            text_parts = [f"Surah {surah_names['en']} ({ref})"]

            if ms_texts:
                text_parts.append("Terjemahan Basmeih:")
                text_parts.extend(ms_texts)

            if en_texts:
                text_parts.append("Sahih International Translation:")
                text_parts.extend(en_texts)

            chunk = {
                "source_type": "quran",
                "text_content": "\n".join(text_parts),
                "text_arabic": "\n".join(arabic_texts),
                "text_translation": "\n".join(ms_texts) if ms_texts else "\n".join(en_texts),
                "metadata": {
                    "surah_number": surah_num,
                    "surah_name_ar": surah_names["ar"],
                    "surah_name_en": surah_names["en"],
                    "surah_name_ms": surah_names["ms"],
                    "ayah_start": group[0],
                    "ayah_end": group[-1],
                    "reference": ref,
                    "translation_source_ms": "ms.basmeih",
                    "translation_source_en": "en.sahih",
                    "chunk_type": "grouped",
                    "group_size": len(group),
                }
            }

            chunks.append(chunk)

    return chunks


def process_quran_data():
    """Main processing function."""
    print("=" * 60)
    print("IlmuAI - Quran Data Processor")
    print("=" * 60)
    print()

    # Create output directory
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # Parse XML files
    print("Parsing XML files...")

    arabic_file = RAW_DIR / "quran-uthmani.xml"
    ms_file = RAW_DIR / "ms.basmeih.xml"
    en_file = RAW_DIR / "en.sahih.xml"

    arabic_data = parse_tanzil_xml(arabic_file)
    ms_data = parse_tanzil_xml(ms_file)
    en_data = parse_tanzil_xml(en_file)

    if not arabic_data:
        print("ERROR: Arabic Quran data not found!")
        print(f"Please run download_quran.py first or download manually from tanzil.net")
        print(f"Expected file: {arabic_file}")
        return

    print(f"  Arabic: {len(arabic_data)} surahs loaded")
    print(f"  Malay (Basmeih): {len(ms_data)} surahs loaded")
    print(f"  English (Sahih): {len(en_data)} surahs loaded")
    print()

    # Create individual ayah chunks
    print("Creating individual ayah chunks...")
    ayah_chunks = []

    for surah_num in sorted(arabic_data.keys()):
        for ayah_num in sorted(arabic_data[surah_num].keys()):
            arabic = arabic_data[surah_num][ayah_num]
            ms_trans = ms_data.get(surah_num, {}).get(ayah_num)
            en_trans = en_data.get(surah_num, {}).get(ayah_num)

            chunk = create_ayah_chunk(surah_num, ayah_num, arabic, ms_trans, en_trans)
            ayah_chunks.append(chunk)

    print(f"  Created {len(ayah_chunks)} individual ayah chunks")

    # Create grouped chunks (3 ayahs per chunk for better context)
    print("Creating grouped chunks (3 ayahs per group)...")
    grouped_chunks = create_grouped_chunks(arabic_data, ms_data, en_data, group_size=3)
    print(f"  Created {len(grouped_chunks)} grouped chunks")

    # Save individual ayah chunks
    ayah_output = PROCESSED_DIR / "quran_ayah_chunks.json"
    with open(ayah_output, "w", encoding="utf-8") as f:
        json.dump(ayah_chunks, f, ensure_ascii=False, indent=2)
    print(f"\nSaved individual chunks to: {ayah_output}")

    # Save grouped chunks (recommended for RAG)
    grouped_output = PROCESSED_DIR / "quran_grouped_chunks.json"
    with open(grouped_output, "w", encoding="utf-8") as f:
        json.dump(grouped_chunks, f, ensure_ascii=False, indent=2)
    print(f"Saved grouped chunks to: {grouped_output}")

    # Create surah index for reference
    surah_index = []
    for surah_num, names in SURAH_NAMES.items():
        ayah_count = len(arabic_data.get(surah_num, {}))
        surah_index.append({
            "number": surah_num,
            "name_ar": names["ar"],
            "name_en": names["en"],
            "name_ms": names["ms"],
            "ayah_count": ayah_count
        })

    index_output = PROCESSED_DIR / "surah_index.json"
    with open(index_output, "w", encoding="utf-8") as f:
        json.dump(surah_index, f, ensure_ascii=False, indent=2)
    print(f"Saved surah index to: {index_output}")

    # Print summary
    print()
    print("=" * 60)
    print("Processing Complete!")
    print("=" * 60)
    print()
    print("Files created:")
    print(f"  1. {ayah_output.name} - {len(ayah_chunks)} individual ayah chunks")
    print(f"  2. {grouped_output.name} - {len(grouped_chunks)} grouped chunks (recommended for RAG)")
    print(f"  3. {index_output.name} - Surah reference index")
    print()
    print("Next steps:")
    print("  1. Run generate_embeddings.py to create vector embeddings")
    print("  2. Seed the database with the processed chunks")
    print()
    print("Recommended: Use grouped chunks for RAG to provide better context")


if __name__ == "__main__":
    process_quran_data()
