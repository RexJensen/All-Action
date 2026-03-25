#!/usr/bin/env python3
"""Download Met Museum images for chapters 11-16 of gambling history book."""

import requests
import time
import os
import re

SEARCH_URL = "https://collectionapi.metmuseum.org/public/collection/v1/search"
OBJECT_URL = "https://collectionapi.metmuseum.org/public/collection/v1/objects"
SAVE_DIR = "/home/user/All-Action/images"

os.makedirs(SAVE_DIR, exist_ok=True)

CHAPTERS = {
    11: {
        "title": "The Islamic World: Prohibition, Practice, and Paradox",
        "searches": [
            "Ottoman coffeehouse",
            "Islamic backgammon",
            "Arab horse racing",
            "Ottoman chess",
            "Islamic tiles game",
            "Persian manuscript gambling",
            "Ottoman miniature",
        ],
        "target": 3,
    },
    12: {
        "title": "Thousands of Years Without Probability",
        "searches": [
            "Roman dice",
            "ancient dice bone",
            "Greek mathematics",
            "Roman game",
            "medieval dice",
        ],
        "target": 3,
    },
    13: {
        "title": "Cardano's Liber de Ludo Aleae",
        "searches": [
            "Cardano portrait",
            "Renaissance dice",
            "16th century Italian manuscript",
            "Renaissance gambling",
            "Italian physician portrait",
        ],
        "target": 3,
    },
    14: {
        "title": "The Problem of Points",
        "searches": [
            "Pascal portrait",
            "17th century French mathematics",
            "Fermat",
            "French coins 17th century",
            "calculating machine",
        ],
        "target": 3,
    },
    15: {
        "title": "From Pascal to Bernoulli",
        "searches": [
            "pendulum clock Huygens",
            "17th century astronomy",
            "Dutch golden age science",
            "London mortality bills",
            "Dutch mathematician",
        ],
        "target": 3,
    },
    16: {
        "title": "Expected Value, the House Edge, and the Long Run",
        "searches": [
            "Monte Carlo casino",
            "roulette",
            "European gambling 19th century",
            "Casino Monte Carlo",
            "playing cards European",
        ],
        "target": 3,
    },
}


def sanitize_filename(name):
    """Make a safe filename from a string."""
    name = re.sub(r'[^\w\s-]', '', name)
    name = re.sub(r'\s+', '_', name.strip())
    return name[:80]


def search_met(query):
    """Search the Met API, return list of object IDs."""
    try:
        resp = requests.get(SEARCH_URL, params={"q": query, "hasImages": True}, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if data.get("total", 0) > 0:
            return data.get("objectIDs", [])[:10]  # first 10 candidates
    except Exception as e:
        print(f"  Search error for '{query}': {e}")
    return []


def get_object(obj_id):
    """Get object details from Met API."""
    try:
        resp = requests.get(f"{OBJECT_URL}/{obj_id}", timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"  Object fetch error for {obj_id}: {e}")
    return None


def download_image(url, filepath):
    """Download an image from URL to filepath."""
    try:
        resp = requests.get(url, timeout=30, stream=True)
        resp.raise_for_status()
        with open(filepath, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"  Download error: {e}")
    return False


def process_chapter(ch_num, ch_info):
    """Download images for one chapter."""
    print(f"\n{'='*60}")
    print(f"Chapter {ch_num}: {ch_info['title']}")
    print(f"{'='*60}")

    downloaded = []
    used_ids = set()

    for query in ch_info["searches"]:
        if len(downloaded) >= ch_info["target"]:
            break

        print(f"\n  Searching: '{query}'")
        obj_ids = search_met(query)
        if not obj_ids:
            print(f"  No results for '{query}'")
            time.sleep(0.5)
            continue

        for obj_id in obj_ids:
            if len(downloaded) >= ch_info["target"]:
                break
            if obj_id in used_ids:
                continue

            obj = get_object(obj_id)
            if not obj:
                time.sleep(0.3)
                continue

            image_url = obj.get("primaryImage") or obj.get("primaryImageSmall")
            if not image_url:
                continue

            title = obj.get("title", "untitled")
            # Determine file extension
            ext = ".jpg"
            if ".png" in image_url.lower():
                ext = ".png"

            safe_title = sanitize_filename(title)
            filename = f"ch{ch_num}_{safe_title}{ext}"
            filepath = os.path.join(SAVE_DIR, filename)

            if os.path.exists(filepath):
                print(f"  Already exists: {filename}")
                downloaded.append(filename)
                used_ids.add(obj_id)
                continue

            print(f"  Downloading: {title} (ID: {obj_id})")
            # Prefer primaryImageSmall for faster downloads, fall back to primaryImage
            small_url = obj.get("primaryImageSmall") or image_url
            if download_image(small_url, filepath):
                fsize = os.path.getsize(filepath)
                print(f"  Saved: {filename} ({fsize:,} bytes)")
                downloaded.append(filename)
                used_ids.add(obj_id)
            else:
                # Try the other URL if small failed
                if small_url != image_url:
                    if download_image(image_url, filepath):
                        fsize = os.path.getsize(filepath)
                        print(f"  Saved (full): {filename} ({fsize:,} bytes)")
                        downloaded.append(filename)
                        used_ids.add(obj_id)

            time.sleep(0.3)

        time.sleep(0.5)

    # Write summary file
    summary_path = os.path.join(SAVE_DIR, f"chapter{ch_num}_images.txt")
    with open(summary_path, 'w') as f:
        f.write(f"Chapter {ch_num}: {ch_info['title']}\n")
        f.write(f"Images downloaded: {len(downloaded)}\n\n")
        for fn in downloaded:
            f.write(f"  {fn}\n")

    print(f"\n  Chapter {ch_num} complete: {len(downloaded)} images downloaded")
    return downloaded


def main():
    print("Met Museum Image Downloader - Chapters 11-16")
    print("=" * 60)

    all_downloaded = {}
    for ch_num in sorted(CHAPTERS.keys()):
        ch_info = CHAPTERS[ch_num]
        downloaded = process_chapter(ch_num, ch_info)
        all_downloaded[ch_num] = downloaded

    print("\n\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    total = 0
    for ch_num in sorted(all_downloaded.keys()):
        count = len(all_downloaded[ch_num])
        total += count
        print(f"  Chapter {ch_num}: {count} images")
        for fn in all_downloaded[ch_num]:
            print(f"    - {fn}")
    print(f"\n  Total: {total} images downloaded")


if __name__ == "__main__":
    main()
