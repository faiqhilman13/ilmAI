"""
Script to download Hadith data from various sources.

Sources:
1. sunnah.com API (requires API key)
2. HadithAPI.com
3. Pre-compiled datasets from GitHub

Collections to download:
- Sahih al-Bukhari
- Sahih Muslim
- Sunan Abu Dawud
- Jami at-Tirmidhi
- Sunan an-Nasa'i
- Sunan Ibn Majah
"""

import os
import json
import urllib.request
from pathlib import Path
from typing import Optional

# Output directory
OUTPUT_DIR = Path(__file__).parent.parent / "raw" / "hadith"

# GitHub repositories with hadith datasets
GITHUB_SOURCES = {
    "bukhari": {
        "url": "https://raw.githubusercontent.com/A7med3bdworeth/hadith-json/main/db/by_book/bukhari.json",
        "name": "Sahih al-Bukhari",
        "description": "Collection by Imam Bukhari - most authentic",
    },
    "muslim": {
        "url": "https://raw.githubusercontent.com/A7med3bdworeth/hadith-json/main/db/by_book/muslim.json",
        "name": "Sahih Muslim",
        "description": "Collection by Imam Muslim - second most authentic",
    },
    "abudawud": {
        "url": "https://raw.githubusercontent.com/A7med3bdworeth/hadith-json/main/db/by_book/abudawud.json",
        "name": "Sunan Abu Dawud",
        "description": "Collection by Imam Abu Dawud",
    },
    "tirmidhi": {
        "url": "https://raw.githubusercontent.com/A7med3bdworeth/hadith-json/main/db/by_book/tirmidhi.json",
        "name": "Jami at-Tirmidhi",
        "description": "Collection by Imam Tirmidhi",
    },
    "nasai": {
        "url": "https://raw.githubusercontent.com/A7med3bdworeth/hadith-json/main/db/by_book/nasai.json",
        "name": "Sunan an-Nasa'i",
        "description": "Collection by Imam Nasa'i",
    },
    "ibnmajah": {
        "url": "https://raw.githubusercontent.com/A7med3bdworeth/hadith-json/main/db/by_book/ibnmajah.json",
        "name": "Sunan Ibn Majah",
        "description": "Collection by Imam Ibn Majah",
    },
}

# Alternative: sunnah.com API (requires registration)
SUNNAH_API_BASE = "https://api.sunnah.com/v1"


def download_file(url: str, output_path: Path, description: str) -> bool:
    """Download a file with progress indication."""
    print(f"Downloading: {description}")
    print(f"  URL: {url}")
    print(f"  Output: {output_path}")

    try:
        urllib.request.urlretrieve(url, output_path)
        size_kb = output_path.stat().st_size / 1024
        print(f"  ✓ Downloaded successfully ({size_kb:.1f} KB)")
        return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def download_from_github():
    """Download hadith collections from GitHub repositories."""
    print("=" * 60)
    print("Downloading Hadith Collections from GitHub")
    print("=" * 60)
    print()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    success_count = 0
    for key, source in GITHUB_SOURCES.items():
        output_path = OUTPUT_DIR / f"{key}.json"

        if output_path.exists():
            print(f"Skipping (already exists): {source['name']}")
            success_count += 1
            continue

        if download_file(source["url"], output_path, source["name"]):
            success_count += 1
        print()

    print(f"Downloaded {success_count}/{len(GITHUB_SOURCES)} collections")
    return success_count


def download_from_sunnah_api(api_key: Optional[str] = None):
    """
    Download hadith from sunnah.com API.

    To get an API key:
    1. Visit https://sunnah.com/developers
    2. Register for an account
    3. Request API access
    """
    if not api_key:
        api_key = os.environ.get("SUNNAH_API_KEY")

    if not api_key:
        print("=" * 60)
        print("Sunnah.com API Download")
        print("=" * 60)
        print()
        print("No API key provided. To use sunnah.com API:")
        print("1. Visit https://sunnah.com/developers")
        print("2. Register and request API access")
        print("3. Set SUNNAH_API_KEY environment variable")
        print("   or pass api_key parameter")
        print()
        print("Skipping sunnah.com API download.")
        return

    # Collections available on sunnah.com
    collections = [
        "bukhari",
        "muslim",
        "abudawud",
        "tirmidhi",
        "nasai",
        "ibnmajah",
        "malik",
        "riyadussalihin",
    ]

    print("=" * 60)
    print("Downloading from Sunnah.com API")
    print("=" * 60)
    print()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for collection in collections:
        output_path = OUTPUT_DIR / f"sunnah_{collection}.json"

        if output_path.exists():
            print(f"Skipping (already exists): {collection}")
            continue

        try:
            # Get collection info
            url = f"{SUNNAH_API_BASE}/collections/{collection}/hadiths"
            request = urllib.request.Request(
                url,
                headers={"X-API-Key": api_key}
            )

            print(f"Fetching: {collection}")

            # Note: This is a simplified version
            # Real implementation would need pagination
            with urllib.request.urlopen(request) as response:
                data = json.loads(response.read().decode())

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            print(f"  ✓ Saved {collection}")

        except Exception as e:
            print(f"  ✗ Error fetching {collection}: {e}")

        print()


def create_sample_data():
    """Create sample hadith data for testing if downloads fail."""
    print("=" * 60)
    print("Creating Sample Hadith Data (for testing)")
    print("=" * 60)
    print()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    sample_hadiths = [
        {
            "collection": "Sahih al-Bukhari",
            "book": "Revelation",
            "hadith_number": "1",
            "text_en": "The Prophet (ﷺ) said, 'The reward of deeds depends upon the intentions and every person will get the reward according to what he has intended.'",
            "text_ar": "إِنَّمَا الأَعْمَالُ بِالنِّيَّاتِ، وَإِنَّمَا لِكُلِّ امْرِئٍ مَا نَوَى",
            "grading": "sahih",
            "narrator": "Umar ibn Al-Khattab"
        },
        {
            "collection": "Sahih al-Bukhari",
            "book": "Belief",
            "hadith_number": "8",
            "text_en": "The Prophet (ﷺ) said, 'Islam is built on five pillars: testifying that there is no god but Allah and that Muhammad is the Messenger of Allah, performing the prayers, paying the zakat, making the pilgrimage to the House, and fasting in Ramadan.'",
            "text_ar": "بُنِيَ الإِسْلاَمُ عَلَى خَمْسٍ شَهَادَةِ أَنْ لاَ إِلَهَ إِلاَّ اللَّهُ وَأَنَّ مُحَمَّدًا رَسُولُ اللَّهِ",
            "grading": "sahih",
            "narrator": "Ibn Umar"
        },
        {
            "collection": "Sahih Muslim",
            "book": "Purification",
            "hadith_number": "223",
            "text_en": "The Prophet (ﷺ) said, 'Cleanliness is half of faith.'",
            "text_ar": "الطُّهُورُ شَطْرُ الإِيمَانِ",
            "grading": "sahih",
            "narrator": "Abu Malik al-Ash'ari"
        },
        {
            "collection": "Jami at-Tirmidhi",
            "book": "Righteousness",
            "hadith_number": "1987",
            "text_en": "The Prophet (ﷺ) said, 'The best among you are those who have the best manners and character.'",
            "text_ar": "إِنَّ مِنْ خِيَارِكُمْ أَحْسَنَكُمْ أَخْلاَقًا",
            "grading": "sahih",
            "narrator": "Abdullah ibn Amr"
        },
        {
            "collection": "Sunan Abu Dawud",
            "book": "Prayer",
            "hadith_number": "864",
            "text_en": "The Prophet (ﷺ) said, 'Pray as you have seen me praying.'",
            "text_ar": "صَلُّوا كَمَا رَأَيْتُمُونِي أُصَلِّي",
            "grading": "sahih",
            "narrator": "Malik ibn al-Huwayrith"
        },
    ]

    output_path = OUTPUT_DIR / "sample_hadiths.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(sample_hadiths, f, ensure_ascii=False, indent=2)

    print(f"Created sample data with {len(sample_hadiths)} hadiths")
    print(f"Output: {output_path}")


def main():
    print("=" * 60)
    print("IlmuAI - Hadith Data Downloader")
    print("=" * 60)
    print()
    print(f"Output directory: {OUTPUT_DIR}")
    print()

    # Try GitHub sources first (no API key needed)
    success = download_from_github()

    if success == 0:
        print()
        print("GitHub downloads failed. Creating sample data for testing...")
        create_sample_data()

    # Optionally try sunnah.com API
    # download_from_sunnah_api()

    print()
    print("=" * 60)
    print("Download complete!")
    print()
    print("Note: For comprehensive hadith data with grading,")
    print("consider using sunnah.com API with an API key.")
    print("=" * 60)


if __name__ == "__main__":
    main()
