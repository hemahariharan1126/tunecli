import sys
import logging
sys.path.insert(0, 'c:/Users/harih/Documents/tunecli')
logging.basicConfig(level=logging.INFO)

from search_engine.yt_search import search_song

queries = [
    "aga naga song from ko movie",
    "bily gen maikal jakson",
    "that one song from titanic where she sings on the boat",
    "shape of u ed shiran"
]

print("--- STARTING GAUNTLET TEST SUITE ---")
success_count = 0

for q in queries:
    print(f"\n[TESTING QUERY] => '{q}'")
    song = search_song(q)
    if song:
        print(f"[RESULT] Found: {song.title} | Channel: {song.artist}")
        success_count += 1
    else:
        print(f"[RESULT] FAILED to find official song for: {q}")

print(f"\n--- GAUNTLET RESULTS: {success_count}/{len(queries)} SUCCESSFUL ---")
