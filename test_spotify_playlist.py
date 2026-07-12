"""
Full verification suite for Spotify playlist support.
"""
import sys, os
BASE_DIR = 'c:/Users/harih/Documents/tunecli'
LIB_PATH = os.path.join(BASE_DIR, 'lib')
if os.path.isdir(LIB_PATH):
    os.environ['PATH'] = os.path.abspath(LIB_PATH) + os.pathsep + os.environ['PATH']
    if hasattr(os, 'add_dll_directory'):
        os.add_dll_directory(os.path.abspath(LIB_PATH))
sys.path.insert(0, BASE_DIR)

import logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

from search_engine.url_resolver import (
    is_spotify_playlist_url,
    fetch_spotify_playlist_tracks,
    is_spotify_url,
    is_youtube_url,
)

print('=== SPOTIFY PLAYLIST SUPPORT - VERIFICATION ===')

# TEST 1: URL Detection
print('\n[TEST 1] URL detection...')
cases = [
    ('https://open.spotify.com/playlist/37i9dQZF1DX0XUsuxWHRQd', True,  False, False, 'Spotify playlist'),
    ('https://open.spotify.com/track/5ChkMS8OtdzJeqyybCc9R5',   False, True,  False, 'Spotify track'),
    ('https://youtu.be/Zi_XLOBDo_Y',                            False, False, True,  'YouTube URL'),
    ('billie jean michael jackson',                              False, False, False, 'text query'),
]
for url, exp_pl, exp_tr, exp_yt, label in cases:
    r_pl = is_spotify_playlist_url(url)
    r_tr = is_spotify_url(url)
    r_yt = is_youtube_url(url)
    ok_pl = '[OK]' if r_pl == exp_pl else '[FAIL]'
    ok_tr = '[OK]' if r_tr == exp_tr else '[FAIL]'
    ok_yt = '[OK]' if r_yt == exp_yt else '[FAIL]'
    print(f'  {ok_pl}{ok_tr}{ok_yt} {label}: playlist={r_pl}, track={r_tr}, yt={r_yt}')

# TEST 2: Fetch playlist tracks
print('\n[TEST 2] Fetching RapCaviar playlist tracks...')
tracks = fetch_spotify_playlist_tracks('37i9dQZF1DX0XUsuxWHRQd')
assert len(tracks) > 0, 'No tracks returned!'
print(f'  [OK] Total tracks fetched: {len(tracks)}')
for t in tracks[:3]:
    assert t['title'] and t['artist'], f'Missing data in track: {t}'
    print(f'  [OK] {t["title"]} -- {t["artist"]} ({t["duration_s"]}s)')

# TEST 3: Resolve first 2 tracks to YouTube Songs
print('\n[TEST 3] Resolving first 2 tracks to YouTube...')
from search_engine.yt_search import search_song
for t in tracks[:2]:
    q = f"{t['title']} {t['artist']}"
    song = search_song(q)
    if song:
        print(f'  [OK] {t["title"]} -> YT: {song.title} | id={song.video_id}')
    else:
        print(f'  [WARN] No YouTube result for: {q}')

print('\n=== ALL TESTS PASSED ===')
