#!/usr/bin/env python3
"""Download Met Museum images for chapters 11-16 - refined searches with relevance filtering."""

import requests
import time
import os
import re

SEARCH_URL = "https://collectionapi.metmuseum.org/public/collection/v1/search"
OBJECT_URL = "https://collectionapi.metmuseum.org/public/collection/v1/objects"
SAVE_DIR = "/home/user/All-Action/images"

os.makedirs(SAVE_DIR, exist_ok=True)


def sanitize_filename(name):
    name = re.sub(r'[^\w\s-]', '', name)
    name = re.sub(r'\s+', '_', name.strip())
    return name[:80]


def search_met(query, dept_id=None):
    """Search the Met API."""
    params = {"q": query, "hasImages": True}
    if dept_id:
        params["departmentId"] = dept_id
    try:
        resp = requests.get(SEARCH_URL, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if data.get("total", 0) > 0:
            return data.get("objectIDs", [])[:20]
    except Exception as e:
        print(f"  Search error for '{query}': {e}")
    return []


def get_object(obj_id):
    try:
        resp = requests.get(f"{OBJECT_URL}/{obj_id}", timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"  Object fetch error for {obj_id}: {e}")
    return None


def download_image(url, filepath):
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


def is_relevant(obj, keywords):
    """Check if object metadata contains any of the relevance keywords."""
    text = " ".join([
        str(obj.get("title", "")),
        str(obj.get("objectName", "")),
        str(obj.get("department", "")),
        str(obj.get("culture", "")),
        str(obj.get("period", "")),
        str(obj.get("artistDisplayName", "")),
        str(obj.get("medium", "")),
        str(obj.get("tags", "")),
        str(obj.get("objectDate", "")),
    ]).lower()
    return any(kw.lower() in text for kw in keywords)


def download_for_chapter(ch_num, searches, relevance_keywords, target=3):
    """Try searches in order, filtering by relevance keywords."""
    downloaded = []
    used_ids = set()

    for query, dept_id in searches:
        if len(downloaded) >= target:
            break
        print(f"  Searching: '{query}'" + (f" (dept {dept_id})" if dept_id else ""))
        obj_ids = search_met(query, dept_id)
        if not obj_ids:
            print(f"    No results")
            time.sleep(0.3)
            continue

        for obj_id in obj_ids:
            if len(downloaded) >= target:
                break
            if obj_id in used_ids:
                continue
            used_ids.add(obj_id)

            obj = get_object(obj_id)
            if not obj:
                time.sleep(0.2)
                continue

            image_url = obj.get("primaryImageSmall") or obj.get("primaryImage")
            if not image_url:
                continue

            # Check relevance
            if relevance_keywords and not is_relevant(obj, relevance_keywords):
                continue

            title = obj.get("title", "untitled")
            ext = ".jpg"
            safe_title = sanitize_filename(title)
            filename = f"ch{ch_num}_{safe_title}{ext}"
            filepath = os.path.join(SAVE_DIR, filename)

            print(f"    -> {title} | {obj.get('objectDate','')} | {obj.get('culture','')}")
            if download_image(image_url, filepath):
                fsize = os.path.getsize(filepath)
                print(f"    Saved: {filename} ({fsize:,} bytes)")
                downloaded.append((filename, title, obj.get("objectDate", ""), obj_id))

            time.sleep(0.2)

        time.sleep(0.3)

    return downloaded


def main():
    # Remove old ch11-16 files first
    for f in os.listdir(SAVE_DIR):
        if f.startswith(("ch11_", "ch12_", "ch13_", "ch14_", "ch15_", "ch16_")) or \
           f.startswith(("chapter11_", "chapter12_", "chapter13_", "chapter14_", "chapter15_", "chapter16_")):
            os.remove(os.path.join(SAVE_DIR, f))
            print(f"Removed old file: {f}")

    all_results = {}

    # ==================== CHAPTER 11 ====================
    print(f"\n{'='*60}\nChapter 11: The Islamic World\n{'='*60}")
    ch11 = download_for_chapter(11, [
        ("Ottoman coffeehouse", None),
        ("backgammon Islamic", None),
        ("chess Islamic", None),
        ("horse racing Arab", None),
        ("Islamic game", None),
        ("Ottoman miniature painting", None),
        ("Persian miniature", 13),  # dept 13 = Islamic Art
        ("Islamic chess piece", None),
        ("coffeehouse Ottoman", 13),
        ("dice Islamic", None),
        ("mancala", None),
    ], ["islam", "ottoman", "persian", "arab", "iran", "turkey", "turk", "mughal",
        "game", "chess", "backgammon", "horse", "coffee", "dice", "card", "miniature",
        "mancala", "manuscript", "folio"])
    all_results[11] = ch11

    # ==================== CHAPTER 12 ====================
    print(f"\n{'='*60}\nChapter 12: Thousands of Years Without Probability\n{'='*60}")
    ch12 = download_for_chapter(12, [
        ("dice Roman", None),
        ("knucklebones dice", None),
        ("astragalus bone", None),
        ("medieval dice", None),
        ("ancient dice", None),
        ("Roman game board", None),
        ("Euclid mathematics", None),
    ], ["dice", "game", "knuckle", "astragal", "bone", "roman", "greek",
        "ancient", "medieval", "mathematics", "euclid"])
    all_results[12] = ch12

    # ==================== CHAPTER 13 ====================
    print(f"\n{'='*60}\nChapter 13: Cardano's Liber de Ludo Aleae\n{'='*60}")
    ch13 = download_for_chapter(13, [
        ("Italian Renaissance portrait physician", None),
        ("16th century Italian scholar", None),
        ("Renaissance Italy manuscript", None),
        ("Italian Renaissance gambling", None),
        ("Renaissance playing cards", None),
        ("Italian Renaissance dice", None),
        ("Milan 16th century", None),
        ("Renaissance portrait Italian 16th century", None),
    ], ["italian", "italy", "renaissance", "16th", "1500", "milan", "portrait",
        "physician", "scholar", "manuscript", "dice", "card", "game", "gambling"])
    all_results[13] = ch13

    # ==================== CHAPTER 14 ====================
    print(f"\n{'='*60}\nChapter 14: The Problem of Points\n{'='*60}")
    ch14 = download_for_chapter(14, [
        ("Pascal calculating machine", None),
        ("Blaise Pascal", None),
        ("Fermat mathematician", None),
        ("French mathematician 17th century", None),
        ("Pascaline", None),
        ("17th century French coins", None),
        ("French 17th century portrait scholar", None),
        ("arithmetic 17th century", None),
    ], ["pascal", "fermat", "french", "france", "17th", "1600", "mathematic",
        "calculat", "coin", "arithmetic", "scholar", "portrait"])
    all_results[14] = ch14

    # ==================== CHAPTER 15 ====================
    print(f"\n{'='*60}\nChapter 15: From Pascal to Bernoulli\n{'='*60}")
    ch15 = download_for_chapter(15, [
        ("pendulum clock", None),
        ("Huygens", None),
        ("Dutch golden age science", None),
        ("17th century astronomy instruments", None),
        ("astronomical clock", None),
        ("Dutch 17th century scientist", None),
        ("mortality bills London", None),
        ("probability mathematics", None),
    ], ["clock", "pendulum", "huygens", "dutch", "holland", "netherland",
        "astronomy", "scientific", "instrument", "mathematic", "17th", "1600",
        "mortality", "bernoulli"])
    all_results[15] = ch15

    # ==================== CHAPTER 16 ====================
    print(f"\n{'='*60}\nChapter 16: Expected Value, the House Edge, and the Long Run\n{'='*60}")
    ch16 = download_for_chapter(16, [
        ("roulette wheel", None),
        ("casino gambling", None),
        ("Monte Carlo", None),
        ("playing cards European", None),
        ("European gambling", None),
        ("roulette table", None),
        ("card game 19th century", None),
        ("gambling 19th century", None),
    ], ["roulette", "casino", "gambl", "card", "playing card", "game", "dice",
        "monte carlo", "betting", "wager"])
    all_results[16] = ch16

    # Write summary files
    print(f"\n\n{'='*60}\nSUMMARY\n{'='*60}")
    total = 0
    for ch_num in sorted(all_results.keys()):
        items = all_results[ch_num]
        total += len(items)
        print(f"  Chapter {ch_num}: {len(items)} images")
        summary_path = os.path.join(SAVE_DIR, f"chapter{ch_num}_images.txt")
        with open(summary_path, 'w') as f:
            f.write(f"Chapter {ch_num}\nImages: {len(items)}\n\n")
            for fn, title, date, oid in items:
                f.write(f"  {fn}\n    Title: {title}\n    Date: {date}\n    Met ID: {oid}\n\n")
                print(f"    - {fn}")
    print(f"\n  Total: {total} images")


if __name__ == "__main__":
    main()
