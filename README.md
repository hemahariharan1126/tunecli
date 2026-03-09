<div align="center">

# 🎵 TuneCLI
### *Intelligent Terminal Music Player*

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=flat-square)](LICENSE)
[![MPV](https://img.shields.io/badge/Engine-MPV-orange?style=flat-square)](https://mpv.io/)

**TuneCLI** is a lightweight, AI-driven terminal music player designed for audiophiles who love the command line. It combines the power of YouTube Music with Spotify's intelligence to provide a seamless, mood-aware listening experience.

</div>

---

## ✨ Key Features

- 🎧 **Adaptive Streaming**: Automatically adjusts audio quality based on your network speed (High, Medium, Low).
- 🧠 **AI Recommendations**: Leverages Spotify audio features and Cosine Similarity to suggest tracks you'll actually love.
- 🎭 **Mood-Aware Filtering**: Instantly pivot your queue with mood filters like `sad`, `chill`, `party`, `focus`, or `romantic`.
- 🌐 **Cross-Language Discovery**: Built-in heuristics to detect and filter music in multiple languages (English, Tamil, Hindi, etc.).
- 💻 **Stunning Terminal UI**: A minimalist, high-refresh-rate interface powered by `Rich` and `Textual`.

---

## 🚀 Quick Start

### Prerequisites
Make sure you have the following installed on your system:
- **Python 3.10+**
- **[MPV](https://mpv.io/)**: The core media engine.
- **[FFmpeg](https://ffmpeg.org/)**: Required for audio processing.

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/tunecli.git
   cd tunecli
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Setup
TuneCLI requires Spotify API credentials for its recommendation engine. 
1. Create a `.env` file in the root directory.
2. Add your credentials:
   ```env
   SPOTIFY_CLIENT_ID='your_id'
   SPOTIFY_CLIENT_SECRET='your_secret'
   ```

---

## ⌨️ Command Guide

Interact with TuneCLI using simple commands prefixed with `M!`.

| Command | Description |
| :--- | :--- |
| `M!play <query>` | Search and play a song from YouTube Music |
| `M!pause` / `M!resume` | Control current playback |
| `M!skip` / `M!prev` | Navigate your queue |
| `M!queue` | View upcoming tracks |
| `M!recommend` | Get AI-powered suggestions based on current track |
| `M!mood <mood>` | Filter recommendations by mood |
| `M!volume <0-100>` | Adjust system volume |
| `M!radio <song>` | Start a radio station based on a song |
| `M!help` | Discover more terminal secrets |

---

## 🛠️ Project Structure

```text
tunecli/
├── api/            # Spotify & YTMusic API bridges
├── commands/       # Terminal command implementations
├── core/           # Core engine logic
├── player/         # MPV controller & Queue management
├── recommender/    # AI/ML logic for song matching
├── ui/             # Rich-based terminal interface
└── main.py         # Entry point
```

---

<div align="center">
Built with ❤️ for the terminal.
</div>
