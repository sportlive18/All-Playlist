#!/usr/bin/env python3
import requests
import re
import os
from datetime import datetime

# ------------------ CONFIGURATION ------------------
PLAYLISTS = [
    {"name": "Live Events", "icon": "📺", "url": "https://l3.streamstar18.workers.dev"},          # renamed
    {"name": "FANCODE", "icon": "🏏", "url": "https://raw.githubusercontent.com/doctor-8trange/zyphx8/refs/heads/main/data/fancode.m3u"},
    {"name": "SONYLIV", "icon": "📺", "url": "https://raw.githubusercontent.com/drmlive/sliv-live-events/refs/heads/main/sonyliv.m3u"},
    {"name": "WILLOW", "icon": "🏏", "url": "https://raw.githubusercontent.com/srhady/willow-event/refs/heads/main/live_sports.m3u"},
    {"name": "PRIMEVIDEO", "icon": "📺", "url": "https://raw.githubusercontent.com/srhady/willow-event/refs/heads/main/primevideo_sports.m3u"},
    {"name": "AXSPORTS", "icon": "🏏", "url": "https://raw.githubusercontent.com/srhady/axsports/refs/heads/main/playlist.m3u"},
    {"name": "JIO-TV", "icon": "📡", "url": "https://raw.githubusercontent.com/sportlive18/jio-tv-auto-update-playlist/refs/heads/main/jtv2.m3u"},
    {"name": "ZEE", "icon": "📺", "url": "https://raw.githubusercontent.com/sportlive18/jio-tv-auto-update-playlist/refs/heads/main/zee.m3u"},
    {"name": "SONY", "icon": "📺", "url": "https://raw.githubusercontent.com/sportlive18/jio-tv-auto-update-playlist/refs/heads/main/sony.m3u"},
    {"name": "SUN", "icon": "☀️", "url": "https://raw.githubusercontent.com/sportlive18/jio-tv-auto-update-playlist/refs/heads/main/sun.m3u"},
]

OUTPUT_FILE = "combined.m3u"
EPG_URL = "https://www.tsepg.cf/epg.xml.gz|https://avkb.short.gy/tsepg.xml.gz"

# ------------------ CATEGORY OVERRIDE PER SOURCE ------------------
# For these playlist names, all channels will be placed in the given category.
SOURCE_CATEGORY_OVERRIDE = {
    "Live Events": "Live Events",   # all channels from streamstar go here
    "FANCODE":     "Fancode",
    "SONYLIV":     "SonyLIV",
    "WILLOW":      "Willow",
    "PRIMEVIDEO":  "Prime Video",
    "AXSPORTS":    "AXS",
}
# These sources will use keyword-based categorization (below)
# JIO-TV, ZEE, SONY, SUN

# ------------------ KEYWORD CATEGORY MAPPING ------------------
# Used for sources NOT in the override list.
CATEGORY_MAP = {
    # Regional languages
    "Assamese":   ["assamese", "asomiya"],
    "Bengali":    ["bengali", "bangla", "bn"],
    "Bhojpuri":   ["bhojpuri", "bho"],
    "Gujarati":   ["gujarati", "guj"],
    "Haryanvi":   ["haryanvi"],
    "Kannada":    ["kannada", "kn"],
    "Malayalam":  ["malayalam", "ml"],
    "Marathi":    ["marathi", "mr"],
    "Odia":       ["odia", "oriya"],
    "Punjabi":    ["punjabi", "pa"],
    "Tamil":      ["tamil", "ta"],
    "Telugu":     ["telugu", "te"],
    "Urdu":       ["urdu"],
    "English":    ["english", "en"],
    "French":     ["french", "fr"],
    # Broadcast networks
    "Sun":        ["sun tv", "surya", "sun music", "sun news", "sun action", "sun life"],
    "Zee":        ["zee", "zee tv", "zee cinema", "zee news", "zee marathi", "zee bangla"],
    "Sony":       ["sony", "set", "sab", "sony liv", "sony max"],
    "Star":       ["star", "star plus", "star sports", "star movies", "star gold"],
    "Colors":     ["colors", "viacom", "mtv"],
    "Discovery":  ["discovery", "dci"],
    "Nat Geo":    ["nat geo", "national geographic"],
    "Cartoon":    ["cartoon", "cn", "pogo", "nick"],
    "News":       ["news", "ndtv", "republic", "times now", "cnn", "bbc"],
    # Sports & other genres
    "Cricket":    ["cricket"],
    "Football":   ["football", "soccer"],
    "Boxing":     ["boxing"],
    "Baseball":   ["baseball"],
    "Business":   ["business", "finance", "cnbc", "bloomberg"],
    "Devotional": ["devotional", "bhakti", "god"],
    "Entertainment": ["entertainment", "ent", "tv", "movies", "series"],
    "Infotainment":  ["infotainment", "documentary", "history", "discovery", "national geographic"],
    "Knowledge":     ["knowledge", "learning", "education"],
}
DEFAULT_CATEGORY = "Other"

# ------------------ CATEGORY ORDER (first = top) ------------------
# Sports networks first, then all others alphabetically.
# We'll sort categories: first those in this list (in order), then the rest alphabetically.
CATEGORY_ORDER = [
    "Live Events",
    "Fancode",
    "SonyLIV",
    "Willow",
    "Prime Video",
    "AXS",
]

# ------------------ HELPERS ------------------
def fetch_playlist(url):
    try:
        print(f"  📥 Fetching: {url}")
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        lines = resp.text.replace('\r\n', '\n').split('\n')
        print(f"  ✅ Fetched {len(lines)} lines")
        return lines
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        return []

def clean_line(line):
    return line.strip()

def extract_channel_blocks(lines):
    """Yield each channel as a list of lines (including #EXTINF, KODIPROP, URL, etc.)"""
    block = []
    for line in lines:
        line = clean_line(line)
        if not line:
            continue
        if line.startswith('#EXTM3U'):
            continue
        if line.startswith('#EXTINF') and block:
            yield block
            block = []
        block.append(line)
    if block:
        yield block

def get_channel_title(block):
    """Extract the channel title from the #EXTINF line"""
    for line in block:
        if line.startswith('#EXTINF'):
            parts = line.rsplit(',', 1)
            if len(parts) > 1:
                return parts[1].strip()
    return None

def categorize_channel(title):
    """Determine category based on channel title using keywords (case‑insensitive)"""
    if not title:
        return DEFAULT_CATEGORY
    title_lower = title.lower()
    for category, keywords in CATEGORY_MAP.items():
        for kw in keywords:
            if kw in title_lower:
                return category
    return DEFAULT_CATEGORY

def fix_channel_block(block, category):
    """
    Rewrite a channel block: ensure #EXTINF has group-title="category".
    Preserve all other tags.
    """
    new_block = []
    for line in block:
        if line.startswith('#EXTINF'):
            # If group-title already exists, replace it; otherwise insert
            if 'group-title=' in line:
                line = re.sub(r'group-title="[^"]*"', f'group-title="{category}"', line)
            else:
                # Insert group-title after the #EXTINF tag and before any attributes
                line = re.sub(r'(#EXTINF:[^,]+)', r'\1 group-title="' + category + '"', line)
            new_block.append(line)
        else:
            new_block.append(line)
    return new_block

# ------------------ MAIN ------------------
def main():
    print("🚀 Starting playlist merge with category grouping...")
    print("=" * 50)

    all_channels = []  # each entry: (category, block)

    for playlist in PLAYLISTS:
        name = playlist["name"]
        icon = playlist["icon"]
        url = playlist["url"]
        print(f"\n📺 Processing: {icon} {name}")
        lines = fetch_playlist(url)
        if not lines:
            continue

        # Determine if we override category for this source
        override_cat = SOURCE_CATEGORY_OVERRIDE.get(name)

        for block in extract_channel_blocks(lines):
            if override_cat:
                category = override_cat
            else:
                title = get_channel_title(block)
                category = categorize_channel(title)
            all_channels.append((category, block))

    # Group by category
    groups = {}
    for cat, block in all_channels:
        groups.setdefault(cat, []).append(block)

    # Sort categories: first those in CATEGORY_ORDER (preserving order), then rest alphabetically
    ordered_cats = []
    for cat in CATEGORY_ORDER:
        if cat in groups:
            ordered_cats.append(cat)
    remaining = sorted([cat for cat in groups.keys() if cat not in CATEGORY_ORDER])
    ordered_cats.extend(remaining)

    # Build final playlist
    out_lines = [f'#EXTM3U x-tvg-url="{EPG_URL}"', '']

    total = 0
    for cat in ordered_cats:
        blocks = groups[cat]
        count = len(blocks)
        total += count
        # Section header (comment line)
        out_lines.append(f'#EXTINF:-1 group-title="{cat}",===== {cat} ({count}) =====')
        out_lines.append('')
        for block in blocks:
            fixed = fix_channel_block(block, cat)
            out_lines.extend(fixed)
            out_lines.append('')  # blank line after each channel

    # Write output
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write('\n'.join(out_lines))
        print("\n" + "=" * 50)
        print(f"✅ Successfully created {OUTPUT_FILE}")
        print(f"📊 Total channels: {total}")
        print(f"📅 Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"📁 File size: {os.path.getsize(OUTPUT_FILE)} bytes")
        print(f"\n📂 Categories (in order): {', '.join(ordered_cats)}")
    except Exception as e:
        print(f"❌ Error writing file: {e}")

if __name__ == "__main__":
    main()
