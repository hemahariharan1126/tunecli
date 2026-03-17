<div align="center">

# 🎵 TuneCLI
### *The Ultimate AI-Driven Terminal Audio Engine*

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Rust](https://img.shields.io/badge/Rust-Compiled-orange.svg?style=flat-square&logo=rust)](https://www.rust-lang.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=flat-square)](LICENSE)
[![MPV](https://img.shields.io/badge/Engine-MPV-purple.svg?style=flat-square)](https://mpv.io/)

**TuneCLI** is an ultra-fast, intelligent, and highly experimental terminal music environment built for developers, audiophiles, and terminal purists.

By fusing **YouTube Music's vast library**, **Spotify's machine-learning audio features**, and **Rust-compiled Acoustic Fingerprinting**, TuneCLI delivers a seamless, mood-aware, and futuristic listening experience completely from the command line.

</div>

---

## ✨ Engineering Highlights

- 🎧 **Machine Learning & Audio Analysis**: Leverages Spotify's audio feature vectors and **Cosine Similarity** algorithms to curate mathematically perfect song transitions and recommendations based on track acoustics (valence, energy, tempo).
- ✨ **LLM-Driven Scenario Soundtracking**: Integrates **Google Gemini 2.0** to analyze free-form user stories. Describe your situation (e.g., "Driving through the rain in Tokyo"), and TuneCLI will extract the mood, tone, and language to build a tailored 5-track scenario queue.
- 🎙️ **Ambient Audio Fingerprinting**: Built-in Rust-powered acoustic recognition engine (`M!find`). Listen to your surroundings through your microphone, instantly identify the playing track via Shazam's hashing algorithms, and natively queue it or its nearest AI neighbors.
- 🚀 **High-Performance Architecture**: 
  - Asynchronous event loops for non-blocking I/O.
  - Native `libmpv` hooks via ctypes for gapless playback without heavy unoptimized wrappers.
  - Rust-compiled core dependencies (`shazamio-core`) for CPU-efficient signal processing.
- 💻 **Stunning Terminal UI**: A high-refresh minimalist interface engineered using `Rich` for dynamic buffer rendering.

---

## 🚀 Quick Start & Installation

### Prerequisites
- **Python 3.10+** (Python 3.13 supported)
- **Rust Toolchain (`Cargo`)**: Required for compiling the audio processing core.
- **MPV Core**: Required for hardware-accelerated playback.

### Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/hemahariharan1126/tunecli.git
   cd tunecli
   ```
2. Install dependencies (this will automatically compile the Rust acoustic engines if pre-built wheels are unavailable on your architecture):
   ```bash
   pip install -r requirements.txt
   ```
3. Initialize API Secrets (Optional but recommended for AI Recommendations):
   Create a `.env` file in the root directory.
   ```env
   SPOTIFY_CLIENT_ID='your_id'
   SPOTIFY_CLIENT_SECRET='your_secret'
   GEMINI_API_KEY='your_gemini_api_key'
   ```

---

## ⌨️ Command Interface

Navigate TuneCLI using an intuitive, context-aware command parser prefixed with `M!`.

| Command | Feature |
| :--- | :--- |
| `M!find` | **[NEW] Ambient Recognition.** Records microphone audio, identifies the playing song, and allows instant native playback. |
| `M!scenario <story>`| **[NEW] Story-Based Soundtrack.** Describe your situation, and LLM-driven AI will build a matching queue. |
| `M!play <query>` | AI-assisted search and instant gapless playback. |
| `M!recommend` | Computes acoustic vectors of the current track to fetch and queue its nearest Spotify neighbors. |
| `M!mood <mood>` | Mutate the queue using semantic mood filters (`sad`, `chill`, `party`, `focus`). |
| `M!radio <song>` | Infinite algorithmic generation of related tracks. |
| `M!pause` / `M!resume` | Control playback lifecycle. |
| `M!skip` / `M!prev` | Navigate the dynamic queue. |
| `M!queue` | View the up-next state tree. |
| `M!volume <0-100>` | Manipulate the MPV audio bus. |
| `M!help` | Advanced command syntax. |

---

## 🛠️ System Architecture

```text
tunecli/
├── api/            # Stateful HTTP clients (Spotify REST, YTMusic)
├── commands/       # Pluggable CLI command handlers (Controller layer)
├── core/           # State machines and configuration management
├── parser/         # Lexical parsing and command dispatch routing
├── player/         # libmpv abstractions and queue synchronization
├── recommender/    # ML Vector processing for semantic/acoustic matching
├── ui/             # Dynamic buffer logic for terminal rendering
└── main.py         # Application Entrypoint & Event Loop
```

---

<div align="center">
Built with ❤️ for the terminal.
<br>
<i>Empowering developers to never leave the CLI for their music again.</i>
</div>
