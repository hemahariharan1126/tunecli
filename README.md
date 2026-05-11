<div align="center">

# 🎵 TuneCLI
### *The Ultimate AI-Driven Terminal Audio Engine*

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Rust](https://img.shields.io/badge/Rust-Compiled-orange.svg?style=flat-square&logo=rust)](https://www.rust-lang.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=flat-square)](LICENSE)
[![MPV](https://img.shields.io/badge/Engine-MPV-purple.svg?style=flat-square)](https://mpv.io/)
[![Textual](https://img.shields.io/badge/TUI-Textual-cyan.svg?style=flat-square)](https://textual.textualize.io/)

**TuneCLI** is an ultra-fast, intelligent, and highly experimental terminal music environment built for developers, audiophiles, and terminal purists.

By fusing **YouTube Music's vast library**, **Spotify's machine-learning audio features**, and **Rust-compiled Acoustic Fingerprinting**, TuneCLI delivers a seamless, mood-aware, and futuristic listening experience completely from the command line — now wrapped in a stunning **cyberpunk-themed Textual TUI**.

</div>

---

## ✨ Engineering Highlights

- 🎧 **Machine Learning & Audio Analysis**: Leverages Spotify's audio feature vectors and **Cosine Similarity** algorithms to curate mathematically perfect song transitions and recommendations based on track acoustics (valence, energy, tempo).
- ✨ **LLM-Driven Scenario Soundtracking**: Integrates **Google Gemini 2.0** to analyze free-form user stories. Describe your situation (e.g., "Driving through the rain in Tokyo"), and TuneCLI will extract the mood, tone, and language to build a tailored 5-track scenario queue.
- 🎙️ **Ambient Audio Fingerprinting**: Built-in Rust-powered acoustic recognition engine (`M!find`). Listen to your surroundings through your microphone, instantly identify the playing track via Shazam's hashing algorithms, and natively queue it or its nearest AI neighbors.
- 🖥️ **Cyberpunk Terminal UI**: A fully reactive, multi-zone **Textual TUI** with a live status bar HUD, animated visualizer, dynamic queue panel, Now Playing display, and interactive modal dialogs — all styled with a custom TCSS cyberpunk theme.
- 🚀 **High-Performance Architecture**:
  - Asynchronous event loops for non-blocking I/O.
  - Native `libmpv` hooks via ctypes for gapless playback without heavy unoptimized wrappers.
  - Rust-compiled core dependencies (`shazamio-core`) for CPU-efficient signal processing.

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
4. Launch TuneCLI:
   ```bash
   python main.py
   ```

---

## ⌨️ Command Interface

Navigate TuneCLI using an intuitive, context-aware command parser prefixed with `M!`.

| Command | Feature |
| :--- | :--- |
| `M!find` | **Ambient Recognition.** Records microphone audio, identifies the playing song, and allows instant native playback. |
| `M!scenario <story>`| **Story-Based Soundtrack.** Describe your situation, and LLM-driven AI will build a matching queue. |
| `M!play <query>` | AI-assisted search and instant gapless playback. |
| `M!recommend` | Computes acoustic vectors of the current track to fetch and queue its nearest Spotify neighbors. |
| `M!mood <mood>` | Mutate the queue using semantic mood filters (`sad`, `chill`, `party`, `focus`). |
| `M!radio <song>` | Infinite algorithmic generation of related tracks. |
| `M!pause` / `M!resume` | Control playback lifecycle. |
| `M!skip` / `M!prev` | Navigate the dynamic queue. |
| `M!queue` | View the up-next state tree. |
| `M!volume <0-100>` | Manipulate the MPV audio bus. |
| `M!help` | Advanced command syntax reference. |

---

## 🖥️ TUI Layout

TuneCLI features a fully reactive, multi-zone **Textual TUI** with a cyberpunk aesthetic:

| Zone | Component | Description |
| :--- | :--- | :--- |
| Top | **Status Bar HUD** | Live display of playback state, volume, and track metadata. |
| Center-Left | **Now Playing** | Album art (ASCII), track info, animated audio visualizer, and progress bar. |
| Center-Right | **Queue Panel** | Real-time up-next queue with track numbering and dynamic updates. |
| Bottom | **Input Bar** | Inline `M!` command input with history and context hints. |
| Overlay | **Modal Dialogs** | Confirmation and result modals for commands like `M!find` and `M!scenario`. |

The entire UI is powered by a custom **TCSS cyberpunk theme** (`ui/styles/theme.tcss`).

---

## 🛠️ System Architecture

### Data Flow

```mermaid
flowchart TD
    User(["👤 User  M! Command"]):::input

    subgraph Parsing ["🔍 Input Layer"]
        Parser["command_parser.py\nLexical Tokenizer"]
        Router["command_router.py\nDispatch Router"]
    end

    subgraph Commands ["⚙️ Command Handlers"]
        direction LR
        Play["M!play"]
        Recommend["M!recommend"]
        Mood["M!mood"]
        Radio["M!radio"]
        Scenario["M!scenario"]
        Find["M!find"]
        Controls["pause / skip / prev\nvolume / queue / help"]
    end

    subgraph APIs ["🌐 External APIs"]
        Spotify["Spotify REST API\naudio features & metadata"]
        YTMusic["YouTube Music\nstream search"]
        Gemini["Google Gemini 2.0\nLLM scenario analysis"]
        Shazam["Shazam / shazamio-core\nRust acoustic fingerprinting"]
    end

    subgraph Intelligence ["🧠 Intelligence Layer"]
        Recommender["recommender_engine.py\nCosine Similarity · Acoustic Vectors"]
    end

    subgraph Playback ["🎵 Playback Engine"]
        Controller["playback_controller.py\nlibmpv · Gapless Queue Sync"]
    end

    subgraph TUI ["🖥️ Textual TUI  ui/app.py"]
        direction LR
        StatusBar["Status Bar HUD"]
        NowPlaying["Now Playing\n+ Visualizer"]
        QueuePanel["Queue Panel"]
        InputBar["Input Bar"]
        Modal["Modal Dialogs"]
    end

    User --> Parser --> Router
    Router --> Play & Recommend & Mood & Radio & Scenario & Find & Controls
    Play & Radio --> YTMusic
    Recommend & Mood --> Spotify --> Recommender
    Scenario --> Gemini
    Find --> Shazam
    Gemini & Shazam & YTMusic --> Controller
    Recommender --> Controller
    Controls --> Controller
    Controller --> StatusBar & NowPlaying & QueuePanel
    User --> InputBar --> Parser
    Scenario & Find --> Modal

    classDef input fill:#7c3aed,stroke:#a855f7,color:#fff
    classDef default fill:#1e1e2e,stroke:#6366f1,color:#e2e8f0
```

### Module Reference

```text
tunecli/
├── api/                # Stateful HTTP clients (Spotify REST, YTMusic, LLM)
├── commands/           # Pluggable CLI command handlers (Controller layer)
├── conductor/          # UX planning and session orchestration notes
├── core/               # State machines and configuration management
├── parser/             # Lexical parsing and command dispatch routing
├── player/             # libmpv abstractions and queue synchronization
├── recommender/        # ML Vector processing for semantic/acoustic matching
├── search_engine/      # YouTube Music search abstraction
├── ui/                 # Textual TUI — app, components, and styles
│   ├── app.py          # Main Textual app entry point & event loop
│   ├── visualizer.py   # Animated multi-color audio visualizer
│   ├── components/     # Modular UI widgets
│   │   ├── status_bar.py   # Always-visible status HUD
│   │   ├── now_playing.py  # Now Playing panel
│   │   ├── queue.py        # Queue display widget
│   │   ├── input.py        # Command input bar
│   │   └── modal.py        # Dialog/modal overlays
│   └── styles/
│       └── theme.tcss      # Cyberpunk TCSS design system
├── utils/              # Shared helpers and command routing
└── main.py             # Application Entrypoint
```

---

<div align="center">
Built with ❤️ for the terminal.
<br>
<i>Empowering developers to never leave the CLI for their music again.</i>
</div>
