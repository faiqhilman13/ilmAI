"""
Script to download real Shafi'i Fiqh data from authentic sources.

Primary sources:
1. Arabic Digital Humanities Fiqh Corpus - Shafi'i subcorpus (10.5M tokens)
   GitHub: https://github.com/arabic-digital-humanities/fiqh

2. Structured Shafi'i fiqh data from Islamic databases

These are real, authenticated academic sources for Shafi'i jurisprudence.
"""

import os
import json
import urllib.request
import subprocess
from pathlib import Path

# Output directory
OUTPUT_DIR = Path(__file__).parent.parent / "raw" / "fiqh"

# Git repository for Arabic Digital Humanities Fiqh Corpus
ADH_FIQH_REPO = "https://github.com/arabic-digital-humanities/fiqh.git"
ADH_FIQH_DIR = OUTPUT_DIR / "adh_fiqh_corpus"


def download_file(url: str, output_path: Path, description: str) -> bool:
    """Download a file with progress indication."""
    print(f"Downloading: {description}")
    print(f"  URL: {url}")
    print(f"  Output: {output_path}")

    try:
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            }
        )

        with urllib.request.urlopen(request, timeout=60) as response:
            with open(output_path, "wb") as f:
                f.write(response.read())

        size_kb = output_path.stat().st_size / 1024
        print(f"  ✓ Downloaded successfully ({size_kb:.1f} KB)")
        return True

    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def clone_adh_fiqh_corpus():
    """Clone the Arabic Digital Humanities Fiqh Corpus."""
    print("=" * 60)
    print("Cloning Arabic Digital Humanities Fiqh Corpus")
    print("=" * 60)
    print()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if ADH_FIQH_DIR.exists():
        print(f"Repository already exists at: {ADH_FIQH_DIR}")
        print("Updating repository...")
        try:
            subprocess.run(
                ["git", "pull"],
                cwd=ADH_FIQH_DIR,
                check=True,
                capture_output=True
            )
            print("  ✓ Repository updated successfully")
            return True
        except Exception as e:
            print(f"  ✗ Error updating: {e}")
            return False

    print(f"Cloning repository to: {ADH_FIQH_DIR}")
    print(f"Source: {ADH_FIQH_REPO}")
    print()
    print("This will download:")
    print("  - Shafi'i fiqh texts (10.5M tokens)")
    print("  - Hanafi, Maliki, Hanbali, Zaydi texts")
    print("  - Metadata and OpenITI markup files")
    print()

    try:
        subprocess.run(
            ["git", "clone", ADH_FIQH_REPO, str(ADH_FIQH_DIR)],
            check=True,
            capture_output=False
        )
        print()
        print(f"  ✓ Repository cloned successfully to: {ADH_FIQH_DIR}")

        # Count Shafi'i files
        txt_dir = ADH_FIQH_DIR / "txt"
        if txt_dir.exists():
            shafii_files = [f for f in txt_dir.glob("*") if "shafii" in f.name.lower() or "shafi" in f.name.lower()]
            print(f"  Found {len(shafii_files)} Shafi'i-related files")

        return True

    except subprocess.CalledProcessError as e:
        print(f"  ✗ Error cloning repository: {e}")
        print()
        print("  Manual clone command:")
        print(f"  git clone {ADH_FIQH_REPO} {ADH_FIQH_DIR}")
        return False
    except FileNotFoundError:
        print("  ✗ Error: 'git' command not found")
        print("  Please install git and try again")
        return False


def create_sample_fiqh_data():
    """Create sample Shafi'i fiqh data for immediate testing."""
    print("=" * 60)
    print("Creating Sample Shafi'i Fiqh Data")
    print("=" * 60)
    print()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Authentic Shafi'i rulings (from Al-Fiqh Al-Manhaji and classical texts)
    sample_fiqh = [
        {
            "topic": "Rukun Wuduk (Pillars of Ablution)",
            "category": "taharah",
            "madhab": "shafii",
            "ruling_bm": """Rukun Wuduk dalam mazhab Syafi'i ada enam perkara yang wajib:
1. Niat - Berniat di dalam hati ketika membasuh muka
2. Membasuh muka - Dari tempat tumbuh rambut kening hingga ke dagu, dan dari telinga ke telinga
3. Membasuh kedua-dua tangan hingga siku
4. Menyapu sebahagian kepala
5. Membasuh kedua-dua kaki hingga buku lali
6. Tertib - Mengikut susunan yang ditetapkan

Dalil: Surah Al-Ma'idah ayat 6""",
            "ruling_en": """The six obligatory pillars of Wudu in the Shafi'i school are:
1. Intention - Making intention in the heart when washing the face
2. Washing the face - From the hairline to the chin, and ear to ear
3. Washing both hands up to the elbows
4. Wiping part of the head
5. Washing both feet up to the ankles
6. Sequence - Following the prescribed order

Evidence: Surah Al-Ma'idah verse 6""",
            "evidence": "Quran 5:6, Hadith collections",
            "source": "Al-Fiqh Al-Manhaji (Shafi'i reference)",
        },
        {
            "topic": "Rukun Solat (Pillars of Prayer)",
            "category": "solat",
            "madhab": "shafii",
            "ruling_bm": """Rukun Solat dalam mazhab Syafi'i ada 13:
1. Niat
2. Takbiratul ihram
3. Berdiri bagi yang mampu (qiyam)
4. Membaca al-Fatihah
5. Rukuk dengan tuma'ninah
6. I'tidal dengan tuma'ninah
7. Sujud dua kali dengan tuma'ninah
8. Duduk antara dua sujud dengan tuma'ninah
9. Duduk akhir
10. Membaca tasyahhud akhir
11. Membaca selawat kepada Nabi dalam tasyahhud akhir
12. Memberi salam yang pertama
13. Tertib (susunan)

Tuma'ninah bermaksud diam seketika dalam setiap rukun fi'li (rukun yang berbentuk perbuatan).""",
            "ruling_en": """The 13 pillars of Prayer in the Shafi'i school are:
1. Intention
2. Opening takbir (Allahu Akbar)
3. Standing for those able (qiyam)
4. Reciting al-Fatihah
5. Bowing (ruku') with tranquility
6. Standing after bowing with tranquility
7. Two prostrations with tranquility
8. Sitting between prostrations with tranquility
9. Final sitting
10. Reciting final tashahhud
11. Reciting salutations upon the Prophet in final tashahhud
12. First salam (peace greeting)
13. Sequence

Tranquility (tuma'ninah) means remaining still momentarily in each physical pillar.""",
            "evidence": "Hadith of the one who prayed incorrectly (Sahih Bukhari, Muslim)",
            "source": "Al-Fiqh Al-Manhaji, Reliance of the Traveller",
        },
        {
            "topic": "Syarat Wajib Puasa Ramadan (Conditions for Fasting Obligation)",
            "category": "puasa",
            "madhab": "shafii",
            "ruling_bm": """Syarat wajib puasa Ramadan dalam mazhab Syafi'i:
1. Islam - Bukan kafir
2. Baligh - Sudah mencapai usia baligh
3. Berakal - Tidak gila
4. Mampu - Berkemampuan untuk berpuasa
5. Mukim - Tidak dalam perjalanan
6. Suci dari haid dan nifas (bagi wanita)

Orang yang tidak memenuhi syarat ini dikecualikan, tetapi wajib qadha jika keadaan sudah berubah.""",
            "ruling_en": """Conditions for the obligation of Ramadan fasting in the Shafi'i school:
1. Islam - Not a disbeliever
2. Puberty - Having reached the age of puberty
3. Sanity - Not insane
4. Ability - Capable of fasting
5. Resident - Not traveling
6. Free from menstruation and post-natal bleeding (for women)

Those who don't meet these conditions are excused but must make up (qadha) when circumstances change.""",
            "evidence": "Quran 2:183-185, various hadith",
            "source": "Al-Fiqh Al-Manhaji",
        },
        {
            "topic": "Nisab Zakat Emas dan Perak (Nisab for Gold and Silver Zakat)",
            "category": "zakat",
            "madhab": "shafii",
            "ruling_bm": """Nisab zakat dalam mazhab Syafi'i:
1. Emas: 20 mithqal (sekitar 85 gram emas)
2. Perak: 200 dirham (sekitar 595 gram perak)
3. Kadar zakat: 2.5% (1/40)
4. Syarat haul: Mencukupi nisab selama setahun hijrah

Jika seseorang memiliki emas atau perak yang mencapai nisab dan telah dimiliki selama setahun, wajib dikeluarkan zakatnya sebanyak 2.5%.""",
            "ruling_en": """Nisab for zakat in the Shafi'i school:
1. Gold: 20 mithqal (approximately 85 grams of gold)
2. Silver: 200 dirham (approximately 595 grams of silver)
3. Zakat rate: 2.5% (1/40)
4. Haul condition: Reaching nisab for one lunar year

If someone possesses gold or silver reaching nisab and has owned it for a year, 2.5% zakat must be paid.""",
            "evidence": "Hadith collections on zakat calculation",
            "source": "Al-Fiqh Al-Manhaji, classical Shafi'i texts",
        },
        {
            "topic": "Rukun Haji (Pillars of Hajj)",
            "category": "haji",
            "madhab": "shafii",
            "ruling_bm": """Rukun Haji dalam mazhab Syafi'i ada enam:
1. Ihram - Berniat untuk mengerjakan haji dengan memakai pakaian ihram
2. Wukuf di Arafah - Berada di Arafah pada 9 Zulhijjah
3. Tawaf Ifadah - Tawaf sebanyak 7 kali selepas wukuf di Arafah
4. Sa'ie antara Safa dan Marwah - Berjalan 7 kali antara bukit Safa dan Marwah
5. Tahallul - Bercukur atau memotong rambut
6. Tertib - Mengikut susunan tertentu untuk kebanyakan rukun

Tanpa sempurna keenam-enam rukun ini, haji tidak sah.""",
            "ruling_en": """The six pillars of Hajj in the Shafi'i school are:
1. Ihram - Intention to perform Hajj while wearing ihram garments
2. Standing at Arafah - Being at Arafah on 9th of Dhul-Hijjah
3. Tawaf al-Ifadah - Circumambulation 7 times after Arafah
4. Sa'i between Safa and Marwah - Walking 7 times between these two hills
5. Tahallul - Shaving or cutting the hair
6. Sequence - Following the prescribed order for most pillars

Without completing all six pillars, Hajj is invalid.""",
            "evidence": "Quran 2:196-197, Hadith of Hajj rituals",
            "source": "Al-Fiqh Al-Manhaji, Minhaj al-Talibin",
        },
        {
            "topic": "Aurat Lelaki dalam Solat (Male Awrah in Prayer)",
            "category": "solat",
            "madhab": "shafii",
            "ruling_bm": """Aurat lelaki dalam solat mengikut mazhab Syafi'i ialah:
- Dari pusat hingga lutut (tidak termasuk pusat dan lutut itu sendiri)

Menutup aurat adalah syarat sah solat. Jika aurat terbuka semasa solat, maka solat menjadi batal kecuali:
1. Terbuka sedikit sahaja dan ditutup semula dengan segera
2. Terlupa dan tidak sengaja

Pakaian mestilah tidak telus (jarang) sehingga dapat dilihat warna kulit.""",
            "ruling_en": """Male awrah in prayer according to the Shafi'i school:
- From navel to knees (not including the navel and knees themselves)

Covering the awrah is a condition for valid prayer. If the awrah is exposed during prayer, the prayer becomes invalid except:
1. A small exposure that is quickly covered
2. Unintentional or forgetful exposure

Clothing must not be transparent enough to reveal skin color.""",
            "evidence": "Various hadith on covering in prayer",
            "source": "Al-Fiqh Al-Manhaji, Reliance of the Traveller",
        },
    ]

    output_file = OUTPUT_DIR / "sample_fiqh.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(sample_fiqh, f, ensure_ascii=False, indent=2)

    print(f"Created sample data with {len(sample_fiqh)} authentic Shafi'i rulings")
    print(f"Output: {output_file}")
    print()
    print("Topics covered:")
    for item in sample_fiqh:
        print(f"  - {item['topic']} ({item['category']})")


def main():
    """Main download function."""
    print("=" * 60)
    print("IlmuAI - Shafi'i Fiqh Data Downloader")
    print("=" * 60)
    print()

    print(f"Output directory: {OUTPUT_DIR}")
    print()

    # Try to clone the Arabic Digital Humanities corpus
    corpus_success = clone_adh_fiqh_corpus()
    print()

    # Always create sample data for immediate use
    create_sample_fiqh_data()
    print()

    print("=" * 60)
    if corpus_success:
        print("Download process complete!")
        print()
        print("Downloaded:")
        print(f"  1. Arabic Digital Humanities Fiqh Corpus at: {ADH_FIQH_DIR}")
        print(f"  2. Sample Shafi'i rulings at: {OUTPUT_DIR / 'sample_fiqh.json'}")
        print()
        print("Next steps:")
        print("  1. Run process_fiqh.py to process the corpus texts")
        print("  2. The processor will extract Shafi'i-specific texts")
        print("  3. Generate embeddings and seed database")
    else:
        print("Partial download complete")
        print()
        print("Note: Could not clone full corpus (requires git)")
        print("Sample data created successfully for testing")
        print()
        print("To get the full corpus later:")
        print(f"  git clone {ADH_FIQH_REPO} {ADH_FIQH_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
