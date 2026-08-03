#!/usr/bin/env python3
import requests
import re
import os
from datetime import datetime

# Your playlist URLs in order
URLS = [
    "https://l3.streamstar18.workers.dev",
    "https://raw.githubusercontent.com/doctor-8trange/zyphx8/refs/heads/main/data/fancode.m3u",
    "https://raw.githubusercontent.com/drmlive/sliv-live-events/refs/heads/main/sonyliv.m3u",
    "https://raw.githubusercontent.com/srhady/willow-event/refs/heads/main/live_sports.m3u",
    "https://raw.githubusercontent.com/srhady/willow-event/refs/heads/main/primevideo_sports.m3u",
    "https://raw.githubusercontent.com/sportlive18/jio-tv-auto-update-playlist/refs/heads/main/jtv2.m3u",
    "https://raw.githubusercontent.com/sportlive18/jio-tv-auto-update-playlist/refs/heads/main/zee.m3u",
    "https://raw.githubusercontent.com/sportlive18/jio-tv-auto-update-playlist/refs/heads/main/sony.m3u",
    "https://raw.githubusercontent.com/sportlive18/jio-tv-auto-update-playlist/refs/heads/main/sun.m3u"
]

# Section names for separators
SECTION_NAMES = [
    "📺 STREAMSTAR",
    "📺 FANCODE",
    "📺 SONYLIV",
    "📺 WILLOW",
    "📺 PRIMEVIDEO",
    "📺 JIO-TV",
    "📺 ZEE",
    "📺 SONY",
    "📺 SUN"
]

OUTPUT_FILE = "combined.m3u"
EPG_URL = "https://www.tsepg.cf/epg.xml.gz|https://avkb.short.gy/tsepg.xml.gz"

def fetch_playlist(url):
    """Fetch a playlist and return its lines"""
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        content = resp.text
        lines = content.replace('\r\n', '\n').split('\n')
        return lines
    except Exception as e:
        print(f"⚠️ Failed to fetch {url}: {e}")
        return []

def is_header_line(line):
    """Check if line is a header or metadata line"""
    line = line.strip()
    if not line:
        return False
    return line.startswith('#EXTM3U') or line.startswith('#KODIPROP')

def is_channel_line(line):
    """Check if line is a channel entry"""
    line = line.strip()
    return line.startswith('#EXTINF') or line.startswith('#KODIPROP')

def clean_line(line):
    """Clean and normalize a line"""
    return line.strip()

def get_section_header(name):
    """Generate section separator line"""
    return f'#EXTINF:-1 group-title="{name}",===== {name} CHANNELS ====='

def process_playlist(lines, section_name):
    """Process a playlist and return cleaned lines with section header"""
    if not lines:
        return []
    
    result = []
    header_added = False
    current_channel = []
    in_channel = False
    
    # Add section header
    result.append(get_section_header(section_name))
    
    for line in lines:
        line = clean_line(line)
        if not line:
            continue
            
        # Skip duplicate #EXTM3U headers
        if line.startswith('#EXTM3U'):
            continue
            
        # If we find #EXTINF, start a new channel
        if line.startswith('#EXTINF'):
            # If we have a previous channel, save it
            if current_channel:
                result.extend(current_channel)
                current_channel = []
            current_channel.append(line)
            in_channel = True
        # If we find KODIPROP, add to current channel
        elif line.startswith('#KODIPROP'):
            if current_channel:
                current_channel.append(line)
        # If we find a URL (not starting with #), add it
        elif not line.startswith('#') and in_channel:
            current_channel.append(line)
            # Channel complete - save it
            result.extend(current_channel)
            current_channel = []
            in_channel = False
        # Handle EXTVLCOPT and other tags
        elif line.startswith('#EXTVLCOPT') and in_channel:
            current_channel.append(line)
        # Handle other lines that might be part of a channel
        elif in_channel and line:
            current_channel.append(line)
    
    # Save any remaining channel
    if current_channel:
        result.extend(current_channel)
    
    # Add blank line after section
    result.append('')
    
    return result

def fix_group_titles(lines):
    """Ensure all channels have proper group-title format"""
    result = []
    for line in lines:
        if line.startswith('#EXTINF') and 'group-title="' not in line:
            # Add default group-title if missing
            line = line.replace('#EXTINF:-1', '#EXTINF:-1 group-title="Uncategorized"')
        result.append(line)
    return result

def main():
    print("🚀 Starting playlist merge...")
    all_lines = []
    
    # Add EPG header
    all_lines.append(f'#EXTM3U x-tvg-url="{EPG_URL}"')
    all_lines.append('')
    
    total_channels = 0
    
    for idx, url in enumerate(URLS):
        section_name = SECTION_NAMES[idx] if idx < len(SECTION_NAMES) else f"📺 SOURCE-{idx+1}"
        print(f"📥 Fetching: {url}")
        
        lines = fetch_playlist(url)
        if lines:
            processed = process_playlist(lines, section_name)
            all_lines.extend(processed)
            # Count channels in this section
            channels = sum(1 for l in processed if l.startswith('#EXTINF') and '=====' not in l)
            total_channels += channels
            print(f"   ✅ Added {channels} channels")
        else:
            # Add empty section if fetch failed
            all_lines.append(get_section_header(section_name))
            all_lines.append('')
            print(f"   ⚠️ No data fetched for this source")
    
    # Fix any missing group titles
    all_lines = fix_group_titles(all_lines)
    
    # Write output
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write('\n'.join(all_lines))
        print(f"\n✅ Successfully created {OUTPUT_FILE}")
        print(f"📊 Total channels: {total_channels}")
        print(f"📅 Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    except Exception as e:
        print(f"❌ Error writing file: {e}")

if __name__ == "__main__":
    main()
