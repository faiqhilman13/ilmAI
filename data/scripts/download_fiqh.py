"""
Script to download Shafi'i Fiqh data.

Primary Source:
- Al-Fiqh Al-Manhaji (JAKIM Edition) from Internet Archive
  https://archive.org/details/Fiqhmanhaji1

Additional Sources:
- Al-Fiqh Al-Manhaji Malay Translation
  https://archive.org/details/fiqhmanhaji1_202004
- IslamQA Shafi'i section (web scraping - manual)
"""

import os
import urllib.request
from pathlib import Path

# Output directory
OUTPUT_DIR = Path(__file__).parent.parent / "raw" / "fiqh"

# Internet Archive sources
ARCHIVE_SOURCES = {
    "fiqh_manhaji_jakim": {
        "url": "https://archive.org/download/Fiqhmanhaji1/Fiqh%20manhaji%20jilid%201.pdf",
        "filename": "fiqh_manhaji_jilid_1.pdf",
        "description": "Al-Fiqh Al-Manhaji Jilid 1 (JAKIM Edition)",
        "language": "ms",
        "topics": ["Taharah", "Solat"],
    },
    "fiqh_manhaji_jilid2": {
        "url": "https://archive.org/download/Fiqhmanhaji1/Fiqh%20manhaji%20jilid%202.pdf",
        "filename": "fiqh_manhaji_jilid_2.pdf",
        "description": "Al-Fiqh Al-Manhaji Jilid 2 (JAKIM Edition)",
        "language": "ms",
        "topics": ["Puasa", "Zakat", "Haji"],
    },
    "fiqh_manhaji_translation": {
        "url": "https://archive.org/download/fiqhmanhaji1_202004/Fiqh%20Manhaji%201.pdf",
        "filename": "fiqh_manhaji_terjemahan_1.pdf",
        "description": "Al-Fiqh Al-Manhaji Terjemahan (Malay)",
        "language": "ms",
        "topics": ["General"],
    },
}

# Direct download links (alternative mirrors)
ALTERNATIVE_SOURCES = {
    "fiqh_ibadah_shafii": {
        "description": "Shafi'i Fiqh of Worship (if available)",
        "manual_url": "https://archive.org/details/Fiqhmanhaji1",
    }
}


def download_file(url: str, output_path: Path, description: str) -> bool:
    """Download a file with progress indication."""
    print(f"Downloading: {description}")
    print(f"  URL: {url}")
    print(f"  Output: {output_path}")

    try:
        # Add headers to avoid blocking
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            }
        )

        with urllib.request.urlopen(request, timeout=60) as response:
            with open(output_path, "wb") as f:
                f.write(response.read())

        size_mb = output_path.stat().st_size / (1024 * 1024)
        print(f"  ✓ Downloaded successfully ({size_mb:.1f} MB)")
        return True

    except Exception as e:
        print(f"  ✗ Error: {e}")
        print(f"  Try manual download from: {url}")
        return False


def download_from_archive():
    """Download fiqh books from Internet Archive."""
    print("=" * 60)
    print("Downloading Shafi'i Fiqh Books from Internet Archive")
    print("=" * 60)
    print()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    success_count = 0
    for key, source in ARCHIVE_SOURCES.items():
        output_path = OUTPUT_DIR / source["filename"]

        if output_path.exists():
            print(f"Skipping (already exists): {source['description']}")
            success_count += 1
            continue

        if download_file(source["url"], output_path, source["description"]):
            success_count += 1
        print()

    return success_count


def create_sample_fiqh_data():
    """Create sample fiqh data for testing."""
    print("=" * 60)
    print("Creating Sample Fiqh Data (for testing)")
    print("=" * 60)
    print()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Sample fiqh rulings from Shafi'i madhab
    sample_fiqh = [
        {
            "topic": "Wuduk (Ablution)",
            "category": "Taharah",
            "madhab": "shafii",
            "ruling_bm": """Rukun Wuduk dalam mazhab Syafi'i ada enam:
1. Niat - Berniat di dalam hati ketika membasuh muka
2. Membasuh muka - Dari tempat tumbuh rambut hingga ke dagu, dan dari telinga ke telinga
3. Membasuh kedua-dua tangan hingga siku
4. Menyapu sebahagian kepala
5. Membasuh kedua-dua kaki hingga buku lali
6. Tertib - Mengikut susunan di atas""",
            "ruling_en": """The pillars of Wudu in the Shafi'i school are six:
1. Intention - Making intention in the heart when washing the face
2. Washing the face - From the hairline to the chin, and ear to ear
3. Washing both hands up to the elbows
4. Wiping part of the head
5. Washing both feet up to the ankles
6. Order - Following the sequence above""",
            "evidence": "Based on Quran 5:6 and various hadith",
            "source": "Al-Fiqh Al-Manhaji",
        },
        {
            "topic": "Solat (Prayer)",
            "category": "Ibadah",
            "madhab": "shafii",
            "ruling_bm": """Rukun Solat dalam mazhab Syafi'i ada 13:
1. Niat
2. Takbiratul ihram
3. Berdiri bagi yang mampu
4. Membaca al-Fatihah
5. Rukuk dengan tuma'ninah
6. I'tidal dengan tuma'ninah
7. Sujud dua kali dengan tuma'ninah
8. Duduk antara dua sujud dengan tuma'ninah
9. Duduk akhir
10. Membaca tasyahhud akhir
11. Membaca selawat ke atas Nabi
12. Memberi salam
13. Tertib""",
            "ruling_en": """The pillars of Prayer in the Shafi'i school are 13:
1. Intention
2. Opening takbir
3. Standing for those able
4. Reciting al-Fatihah
5. Bowing with tranquility
6. Rising from bowing with tranquility
7. Two prostrations with tranquility
8. Sitting between two prostrations with tranquility
9. Final sitting
10. Final tashahhud
11. Sending blessings upon the Prophet
12. Giving salam
13. Order""",
            "evidence": "Based on various hadith including 'Pray as you have seen me pray'",
            "source": "Al-Fiqh Al-Manhaji",
        },
        {
            "topic": "Puasa (Fasting)",
            "category": "Ibadah",
            "madhab": "shafii",
            "ruling_bm": """Rukun Puasa dalam mazhab Syafi'i ada dua:
1. Niat - Wajib berniat pada malam hari sebelum fajar untuk puasa wajib
2. Menahan diri dari segala yang membatalkan puasa dari terbit fajar hingga terbenam matahari

Perkara yang membatalkan puasa:
1. Makan dan minum dengan sengaja
2. Muntah dengan sengaja
3. Bersetubuh
4. Keluar mani dengan sengaja
5. Haid dan nifas
6. Gila
7. Murtad""",
            "ruling_en": """The pillars of Fasting in the Shafi'i school are two:
1. Intention - Must make intention at night before dawn for obligatory fasts
2. Abstaining from all that breaks the fast from dawn until sunset

Things that break the fast:
1. Eating and drinking intentionally
2. Intentional vomiting
3. Sexual intercourse
4. Intentional ejaculation
5. Menstruation and post-natal bleeding
6. Insanity
7. Apostasy""",
            "evidence": "Based on Quran 2:187 and various hadith",
            "source": "Al-Fiqh Al-Manhaji",
        },
        {
            "topic": "Zakat",
            "category": "Ibadah",
            "madhab": "shafii",
            "ruling_bm": """Syarat wajib zakat:
1. Islam
2. Merdeka
3. Milik sempurna
4. Cukup nisab
5. Cukup haul (satu tahun qamariah) untuk harta tertentu

Nisab zakat emas: 85 gram emas
Nisab zakat perak: 595 gram perak
Kadar zakat: 2.5%""",
            "ruling_en": """Conditions for obligatory zakat:
1. Being Muslim
2. Being free
3. Complete ownership
4. Reaching nisab threshold
5. Completion of one lunar year for certain wealth

Nisab for gold: 85 grams
Nisab for silver: 595 grams
Zakat rate: 2.5%""",
            "evidence": "Based on Quran 9:60 and various hadith",
            "source": "Al-Fiqh Al-Manhaji",
        },
        {
            "topic": "Aurat dalam Solat",
            "category": "Solat",
            "madhab": "shafii",
            "ruling_bm": """Aurat dalam solat menurut mazhab Syafi'i:

Lelaki: Antara pusat dan lutut
Wanita: Seluruh badan kecuali muka dan tapak tangan

Menutup aurat adalah syarat sah solat. Jika terbuka aurat dengan sengaja, solat menjadi batal.""",
            "ruling_en": """Awrah in prayer according to Shafi'i school:

Men: Between navel and knees
Women: Entire body except face and palms

Covering awrah is a condition for valid prayer. If awrah is exposed intentionally, prayer becomes invalid.""",
            "evidence": "Based on various hadith about proper dress in prayer",
            "source": "Al-Fiqh Al-Manhaji",
        },
    ]

    import json
    output_path = OUTPUT_DIR / "sample_fiqh.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(sample_fiqh, f, ensure_ascii=False, indent=2)

    print(f"Created sample data with {len(sample_fiqh)} fiqh rulings")
    print(f"Output: {output_path}")


def print_manual_instructions():
    """Print instructions for manual download."""
    print()
    print("=" * 60)
    print("Manual Download Instructions")
    print("=" * 60)
    print()
    print("If automatic downloads fail, please download manually:")
    print()
    print("1. Al-Fiqh Al-Manhaji (JAKIM Edition):")
    print("   https://archive.org/details/Fiqhmanhaji1")
    print("   Download all PDF files and place in:")
    print(f"   {OUTPUT_DIR}")
    print()
    print("2. Al-Fiqh Al-Manhaji (Malay Translation):")
    print("   https://archive.org/details/fiqhmanhaji1_202004")
    print()
    print("3. For English Shafi'i fiqh resources:")
    print("   - Reliance of the Traveller (Umdat al-Salik)")
    print("   - Minhaj al-Talibin")
    print()


def main():
    print("=" * 60)
    print("IlmuAI - Shafi'i Fiqh Data Downloader")
    print("=" * 60)
    print()
    print(f"Output directory: {OUTPUT_DIR}")
    print()

    # Try downloading from Internet Archive
    success = download_from_archive()

    # Create sample data for testing regardless
    print()
    create_sample_fiqh_data()

    # Print manual instructions
    print_manual_instructions()

    print()
    print("=" * 60)
    print("Download process complete!")
    print()
    print("Next steps:")
    print("1. Run process_fiqh.py to extract text from PDFs")
    print("2. Review and clean extracted text")
    print("3. Generate embeddings and seed database")
    print("=" * 60)


if __name__ == "__main__":
    main()
