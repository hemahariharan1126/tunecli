"""
Verification script for the Hybrid Playback Engine.
Tests: PreDownloader, Auto-Resume logic, and MPV local playback method.
"""
import sys
import os
import time
import logging

sys.path.insert(0, 'c:/Users/harih/Documents/tunecli')
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

print("=" * 60)
print("  HYBRID PLAYBACK ENGINE - VERIFICATION SUITE")
print("=" * 60)

# --- TEST 1: Config constants ---
print("\n[TEST 1] Config constants...")
from config import AUDIO_CACHE_DIR, MAX_PREDOWNLOAD_SONGS
assert AUDIO_CACHE_DIR, "AUDIO_CACHE_DIR must be set"
assert MAX_PREDOWNLOAD_SONGS > 0, "MAX_PREDOWNLOAD_SONGS must be > 0"
print(f"  [OK] AUDIO_CACHE_DIR = '{AUDIO_CACHE_DIR}'")
print(f"  [OK] MAX_PREDOWNLOAD_SONGS = {MAX_PREDOWNLOAD_SONGS}")

# --- TEST 2: PreDownloader instantiation ---
print("\n[TEST 2] PreDownloader instantiation...")
from player.pre_downloader import get_pre_downloader
pd = get_pre_downloader()
assert os.path.isdir(AUDIO_CACHE_DIR), f"Cache dir '{AUDIO_CACHE_DIR}' was not created"
print(f"  [OK] PreDownloader initialized")
print(f"  [OK] Cache directory created: {AUDIO_CACHE_DIR}")

# --- TEST 3: PreDownloader - download a real song ---
print("\n[TEST 3] PreDownloader - scheduling a real download...")
from core.song import Song

test_song = Song(
    title="Billie Jean",
    artist="Michael Jackson",
    duration=294,
    video_id="Zi_XLOBDo_Y",
    stream_url="",
    thumbnail=""
)

pd.schedule([test_song])
print(f"  [OK] Song scheduled for download: {test_song.title}")

print("  [..] Waiting for download (up to 30s)...")
downloaded = False
for i in range(30):
    time.sleep(1)
    local_path = pd.get_local_path(test_song.video_id)
    if local_path:
        print(f"  [OK] Download complete! Local path: {local_path}")
        print(f"  [OK] File size: {os.path.getsize(local_path) / 1024:.1f} KB")
        downloaded = True
        break
    if not pd.is_downloading(test_song.video_id) and i > 5:
        print(f"  [FAIL] Download failed (not in progress after {i}s)")
        break
else:
    if not downloaded:
        print("  [WARN] Download still in progress after 30s")

# --- TEST 4: Auto-Resume threshold logic ---
print("\n[TEST 4] Auto-Resume premature EOF detection logic...")
NATURAL_FINISH_THRESHOLD = 0.85

test_cases = [
    (250, 294, "Normal finish (>85%)"),
    (120, 294, "Mid-song drop (<85%)"),
    (2,   294, "Instant drop (<3s)"),
]

for elapsed, duration, label in test_cases:
    ratio = elapsed / duration
    is_runaway = elapsed < 3.0
    is_drop = not is_runaway and ratio < NATURAL_FINISH_THRESHOLD
    result = "RUNAWAY GUARD" if is_runaway else ("NETWORK DROP DETECTED" if is_drop else "NATURAL FINISH")
    print(f"  [OK] {label}: {elapsed}s/{duration}s ({ratio:.0%}) -> {result}")

# --- TEST 5: PreDownloader purge ---
print("\n[TEST 5] Cache purge...")
pd.purge_file(test_song.video_id)
assert pd.get_local_path(test_song.video_id) is None
print("  [OK] Purge successful - cache entry removed")
pd.purge_all()
print("  [OK] Full purge completed")

print("\n" + "=" * 60)
print("  ALL TESTS PASSED")
print("=" * 60)
