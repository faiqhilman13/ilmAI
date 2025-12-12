"""
Script to download Quran data from Tanzil.net

This downloads:
1. Arabic text (Uthmani script)
2. Malay translation (Abdullah Muhammad Basmeih)
3. English translation (Sahih International)
"""

import os
import urllib.request
from pathlib import Path

# Base URLs
TANZIL_BASE = "https://tanzil.net/trans"

# Files to download
FILES = [
    {
        "name": "quran-uthmani.xml",
        "url": "https://tanzil.net/pub/download/index.php?quranType=uthmani&outType=xml",
        "description": "Arabic text (Uthmani script)",
    },
    {
        "name": "ms.basmeih.xml",
        "url": "https://tanzil.net/trans/?transID=ms.basmeih&type=xml",
        "description": "Malay translation (Basmeih)",
    },
    {
        "name": "en.sahih.xml",
        "url": "https://tanzil.net/trans/?transID=en.sahih&type=xml",
        "description": "English translation (Sahih International)",
    },
]


def download_file(url: str, output_path: Path, description: str):
    """Download a file with progress indication."""
    print(f"Downloading: {description}")
    print(f"  URL: {url}")
    print(f"  Output: {output_path}")

    try:
        urllib.request.urlretrieve(url, output_path)
        print(f"  ✓ Downloaded successfully ({output_path.stat().st_size / 1024:.1f} KB)")
    except Exception as e:
        print(f"  ✗ Error: {e}")
        print("  Note: You may need to download manually from tanzil.net/download")


def main():
    # Create output directory
    output_dir = Path(__file__).parent.parent / "raw" / "quran"
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("IlmuAI - Quran Data Downloader")
    print("=" * 60)
    print()
    print(f"Output directory: {output_dir}")
    print()

    for file_info in FILES:
        output_path = output_dir / file_info["name"]

        if output_path.exists():
            print(f"Skipping (already exists): {file_info['name']}")
            continue

        download_file(
            url=file_info["url"],
            output_path=output_path,
            description=file_info["description"],
        )
        print()

    print("=" * 60)
    print("Download complete!")
    print()
    print("Note: Tanzil.net may require manual download for some files.")
    print("Visit https://tanzil.net/download/ to download manually if needed.")
    print("=" * 60)


if __name__ == "__main__":
    main()
