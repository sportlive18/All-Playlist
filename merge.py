#!/usr/bin/env python3
import requests
import re
import os
from datetime import datetime

# Your playlists - now with AXSPORTS added
PLAYLISTS = [
    {
        "name": "STREAMSTAR",
        "icon": "📺",
        "url": "https://l3.streamstar18.workers.dev"
    },
    {
        "name": "FANCODE",
        "icon": "🏏",
        "url": "https://raw.githubusercontent.com/doctor-8trange/zyphx8/refs/heads/main/data/fancode.m3u"
    },
    {
        "name": "SONYLIV",
        "icon": "📺",
        "url": "https://raw.githubusercontent.com/drmlive/sliv-live-events/refs/heads/main/sonyliv.m3u"
    },
    {
        "name": "WILLOW",
        "icon": "🏏",
        "url": "https://raw.githubusercontent.com/srhady/willow-event/refs/heads/main/live_sports.m3u"
    },
    {
        "name": "PRIMEVIDEO",
        "icon": "📺",
        "url": "https://raw.githubusercontent.com/srhady/willow-event/refs/heads/main/primevideo_sports.m3u"
    },
    {
        "name": "AXSPORTS",  # ✅ NEWLY ADDED
        "icon": "🏏",
        "url": "https://raw.githubusercontent.com/srhady/axsports/refs/heads/main/playlist.m3u"
    },
    {
        "name": "JIO-TV",
        "icon": "📡",
        "url": "https://raw.githubusercontent.com/sportlive18/jio-tv-auto-update-playlist/refs/heads/main/jtv2.m3u"
    },
    {
        "name": "ZEE",
        "icon": "📺",
        "url": "https://raw.githubusercontent.com/sportlive18/jio-tv-auto-update-playlist/refs/heads/main/zee.m3u"
    },
    {
        "name": "SONY",
        "icon": "📺",
        "url": "https://raw.githubusercontent.com/sportlive18/jio-tv-auto-update-playlist/refs/heads/main/sony.m3u"
    },
    {
        "name": "SUN",
        "icon": "☀️",
        "url": "https://raw.githubusercontent.com/sportlive18/jio-tv-auto-update-playlist/refs/heads/main/sun.m3u"
    }
]

OUTPUT_FILE = "combined.m3u"
EPG_URL = "https://www.tsepg.cf/epg.xml.gz|https://avkb.short.gy/tsepg.xml.gz"

def fetch_playlist(url):
    """Fetch a playlist and return its lines"""
    try:
        print(f"  📥 Fetching: {url}")
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        content = resp.text
        lines = content.replace('\r\n', '\n').split('\n')
        print(f"  ✅ Fetched {len(lines)} lines")
        return lines
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        return []

def clean_line(line):
    """Clean a line"""
    return line.strip()

def extract_channels(lines):
    """Extract channels from playlist lines, preserving ALL metadata"""
    channels = []
    current_channel = []
    
    for line in lines:
        line = clean_line(line)
        if not line:
            if current_channel:
                channels.append(current_channel)
                current_channel = []
            continue
        
        # Skip duplicate EXT M3U headers
        if line.startswith('#EXTM3U'):
            continue
        
        # Start of a new channel
        if line.startswith('#EXTINF'):
            # Save previous channel if exists
            if current_channel:
                channels.append(current_channel)
                current_channel = []
            current_channel.append(line)
        # KODIPROP lines (DRM info)
        elif line.startswith('#KODIPROP'):
            current_channel.append(line)
        # EXTVLCOPT lines
        elif line.startswith('#EXTVLCOPT'):
            current_channel.append(line)
        # URL line (doesn't start with #)
        elif not line.startswith('#') and current_channel:
            current_channel.append(line)
        # Any other line that might be part of a channel
        elif current_channel:
            current_channel.append(line)
    
    # Don't forget the last channel
    if current_channel:
        channels.append(current_channel)
    
    return channels

def fix_channel_block(channel_lines):
    """Ensure proper ordering: #EXTINF, #KODIPROP, #EXTVLCOPT, URL"""
    extinf = []
    kodiprop = []
    extvlcopt = []
    url = None
    
    for line in channel_lines:
        if line.startswith('#EXTINF'):
            extinf.append(line)
        elif line.startswith('#KODIPROP'):
            kodiprop.append(line)
        elif line.startswith('#EXTVLCOPT'):
            extvlcopt.append(line)
        elif not line.startswith('#') and not url:
            url = line
    
    # Build proper order
    result = []
    if extinf:
        result.extend(extinf)
    if kodiprop:
        result.extend(kodiprop)
    if extvlcopt:
        result.extend(extvlcopt)
    if url:
        result.append(url)
    
    return result

def create_section(name, icon, channels, channel_count):
    """Create a section with proper formatting"""
    section_lines = []
    
    # Section header with separator
    section_lines.append(f'#EXTINF:-1 group-title="{icon} {name}",===== {icon} {name} CHANNELS ({channel_count}) =====')
    section_lines.append('')
    
    # Add channels
    for channel in channels:
        fixed = fix_channel_block(channel)
        section_lines.extend(fixed)
        section_lines.append('')  # Blank line between channels
    
    return section_lines

def main():
    print("🚀 Starting playlist merge...")
    print("=" * 50)
    
    all_lines = []
    
    # Add EPG header
    all_lines.append(f'#EXTM3U x-tvg-url="{EPG_URL}"')
    all_lines.append('')
    
    total_channels = 0
    
    for playlist in PLAYLISTS:
        name = playlist["name"]
        icon = playlist["icon"]
        url = playlist["url"]
        
        print(f"\n📺 Processing: {icon} {name}")
        
        lines = fetch_playlist(url)
        
        if lines:
            # Extract channels from this playlist
            channels = extract_channels(lines)
            channel_count = len(channels)
            total_channels += channel_count
            
            print(f"  📊 Found {channel_count} channels")
            
            # Create section for this playlist
            section = create_section(name, icon, channels, channel_count)
            all_lines.extend(section)
        else:
            # Add empty section if failed
            all_lines.append(f'#EXTINF:-1 group-title="{icon} {name}",===== {icon} {name} CHANNELS (0) =====')
            all_lines.append('')
            print(f"  ⚠️ No data available")
    
    # Write output
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write('\n'.join(all_lines))
        
        print("\n" + "=" * 50)
        print(f"✅ Successfully created {OUTPUT_FILE}")
        print(f"📊 Total channels: {total_channels}")
        print(f"📅 Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"📁 File size: {os.path.getsize(OUTPUT_FILE)} bytes")
    except Exception as e:
        print(f"❌ Error writing file: {e}")

if __name__ == "__main__":
    main()
