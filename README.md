<div align="center">

# 🎵 TuneCLI
### *The Ultimate AI-Driven Terminal Audio Engine*

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Rust](https://img.shields.io/badge/Rust-Compiled-orange.svg?style=flat-square&logo=rust)](https://www.rust-lang.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=flat-square)](LICENSE)
[![MPV](https://img.shields.io/badge/Engine-MPV-purple.svg?style=flat-square)](https://mpv.io/)
[![Textual](https://img.shields.io/badge/TUI-Textual-cyan.svg?style=flat-square)](https://textual.textualize.io/)
[![Themes](https://img.shields.io/badge/Themes-8_Built--in-ff79c6.svg?style=flat-square)](#-theme-system)

**TuneCLI** is an ultra-fast, intelligent, and highly experimental terminal music environment built for developers, audiophiles, and terminal purists.

By fusing **YouTube Music's vast library**, **Spotify's machine-learning audio features**, and **Rust-compiled Acoustic Fingerprinting**, TuneCLI delivers a seamless, mood-aware, and futuristic listening experience completely from the command line — now wrapped in a stunning **multi-theme Textual TUI** with 8 built-in colour themes.

</div>

---

## ✨ Engineering Highlights

- 🎧 **Machine Learning & Audio Analysis**: Leverages Spotify's audio feature vectors and **Cosine Similarity** algorithms to curate mathematically perfect song transitions and recommendations based on track acoustics (valence, energy, tempo).
- ✨ **LLM-Driven Scenario Soundtracking**: Integrates **Google Gemini 2.0** to analyze free-form user stories. Describe your situation (e.g., "Driving through the rain in Tokyo"), and TuneCLI will extract the mood, tone, and language to build a tailored 5-track scenario queue.
- 🎙️ **Ambient Audio Fingerprinting**: Built-in Rust-powered acoustic recognition engine (`M!find`). Listen to your surroundings through your microphone, instantly identify the playing track via Shazam's hashing algorithms, and natively queue it or its nearest AI neighbors.
- 🖥️ **Multi-Theme Terminal UI**: A fully reactive, multi-zone **Textual TUI** with a live status bar HUD, animated visualizer, dynamic queue panel, block-character logo banner, Now Playing display, and interactive modal dialogs — switchable across **8 built-in colour themes** at runtime with `M!theme`.
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
| `M!theme <name>` | **Switch colour theme at runtime.** 8 built-in themes, persisted across restarts. |
| `M!help` | Advanced command syntax reference. |

---

## 🖥️ TUI Layout

TuneCLI features a fully reactive, multi-zone **Textual TUI**:

```
┌─────────────────────────────────────────────────────┐
│  ⚡ M! TuneCLI  │  RADIO:OFF  │  QUEUE: 0  │  VOL  │  ← Status Bar HUD
├─────────────────────────────────────────────────────┤
│  ████████╗██╗   ██╗███╗   ██╗███████╗               │
│  ╚══██╔══╝██║   ██║████╗  ██║██╔════╝               │  ← Logo Banner
│     ██║   ...                                        │
├─────────────────────────┬───────────────────────────┤
│  ◈  NOW PLAYING         │  ◈  UP NEXT               │
│                         │                           │
│  ▶  Song Title          │  1. Track One             │  ← Main Panels
│     🎤 Artist Name      │  2. Track Two             │
│  ▓▓▓▓▓░░░░░  03:42      │  ...                      │
│  ████░░░░░░  80%  🔊    │                           │
├─────────────────────────┴───────────────────────────┤
│  [ ⚡  M!play <song>  ·  M!help  ·  M!theme black ] │  ← Command Input
├─────────────────────────────────────────────────────┤
│  ⚡ M! TuneCLI — Ready                              │
│  ◈  THEME → DRACULA  applied & saved.               │  ← Output Log (RichLog)
└─────────────────────────────────────────────────────┘
```

| Zone | Component | Description |
| :--- | :--- | :--- |
| Top | **Status Bar HUD** | Live display of playback state, volume, queue count, and radio mode. |
| Top+1 | **Logo Banner** | Block-character TUNE logo — always visible, theme-aware accent colour. |
| Centre-Left | **Now Playing** | Track info, animated audio visualizer, progress bar, volume bar, mood badge. |
| Centre-Right | **Queue Panel** | Real-time up-next queue with track numbering and dynamic updates. |
| Bottom | **Command Input** | Inline `M!` command input with autocomplete suggestions. |
| Log | **Output Log** | Rich-rendered command output, errors, and system messages. |
| Overlay | **Modal Dialogs** | Confirmation and result modals for commands like `M!find` and `M!scenario`. |

---

## 🎨 Theme System

TuneCLI ships with **8 built-in colour themes**, switchable at runtime with `M!theme <name>`. The selected theme persists across restarts via `.env`.

```bash
M!theme cyberpunk    # default — neon cyan synthwave
M!theme black        # pure black monochrome
M!theme red_velvet   # deep crimson luxe
M!theme ocean        # teal abyss
M!theme forest       # emerald forest night
M!theme sunset       # warm amber glow
M!theme rose_gold    # soft blush pink
M!theme dracula      # classic dev dark
```

### Theme Showcase

| Theme | Accent | Background | Vibe |
| :--- | :---: | :---: | :--- |
| `cyberpunk` ⚡ | `#00d4ff` neon cyan | `#080810` deep navy | Synthwave default |
| `black` 🖤 | `#ffffff` white | `#000000` true black | Minimal monochrome |
| `red_velvet` 🍷 | `#e8234a` crimson | `#1a0008` burgundy | Warm dark luxe |
| `ocean` 🌊 | `#00e5cc` teal | `#020d1a` abyss navy | Cold calm depth |
| `forest` 🌿 | `#39d353` emerald | `#050f06` dark pine | Nature night mode |
| `sunset` 🌇 | `#ff8c00` amber | `#120a00` dark charcoal | Golden hour glow |
| `rose_gold` 🌸 | `#e8a0b0` blush | `#120d0f` dark charcoal | Soft elegant |
| `dracula` 🧛 | `#ff79c6` pink | `#282a36` Dracula bg | Classic dev dark |

> Theme choice is saved to `.env` as `TUNECLI_THEME=<name>` and auto-restored on next launch.

---

## 🏗️ TUI Component Architecture

```mermaid
graph TD
    App["🖥️ TuneCLIApp\nui/app.py"]

    App --> StatusBar["StatusBar\nTop HUD — 1 row"]
    App --> LogoPanel["LogoPanel\nBlock-char banner"]
    App --> MainContainer["#main_container"]
    App --> CmdInput["#cmd_input\nInput widget"]
    App --> OutputLog["#output_log\nRichLog widget"]
    App --> ThemeSystem["🎨 ui/themes.py\nTheme Registry"]

    MainContainer --> NowPlaying["NowPlayingPanel\nTrack · Progress · Visualizer"]
    MainContainer --> QueuePanel["QueuePanel\nUp-Next Queue"]

    ThemeSystem --> T1["cyberpunk.tcss"]
    ThemeSystem --> T2["black.tcss"]
    ThemeSystem --> T3["red_velvet.tcss"]
    ThemeSystem --> T4["ocean.tcss"]
    ThemeSystem --> T5["forest.tcss"]
    ThemeSystem --> T6["sunset.tcss"]
    ThemeSystem --> T7["rose_gold.tcss"]
    ThemeSystem --> T8["dracula.tcss"]

    App --> Modal["SelectionModal\nOverlay screen"]

    style App fill:#1e1e2e,stroke:#00d4ff,color:#e2e8f0
    style ThemeSystem fill:#1e1e2e,stroke:#ff79c6,color:#e2e8f0
    style MainContainer fill:#1e1e2e,stroke:#9b30ff,color:#e2e8f0
    style NowPlaying fill:#0d0d1e,stroke:#00d4ff,color:#e2e8f0
    style QueuePanel fill:#0d0d1e,stroke:#9b30ff,color:#e2e8f0
    style StatusBar fill:#0d0d1e,stroke:#6a6a9a,color:#e2e8f0
    style LogoPanel fill:#0d0d1e,stroke:#00d4ff,color:#e2e8f0
    style CmdInput fill:#0d0d1e,stroke:#00d4ff,color:#e2e8f0
    style OutputLog fill:#080818,stroke:#2a2a45,color:#6a6a9a
    style Modal fill:#0c0c22,stroke:#00d4ff,color:#e2e8f0
```

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
        Theme["M!theme"]
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
        LogoBanner["Logo Banner"]
        NowPlaying["Now Playing\n+ Visualizer"]
        QueuePanel["Queue Panel"]
        InputBar["Input Bar"]
        Modal["Modal Dialogs"]
        ThemeEngine["🎨 Theme Engine\n8 built-in themes"]
    end

    User --> Parser --> Router
    Router --> Play & Recommend & Mood & Radio & Scenario & Find & Theme & Controls
    Play & Radio --> YTMusic
    Recommend & Mood --> Spotify --> Recommender
    Scenario --> Gemini
    Find --> Shazam
    Theme --> ThemeEngine
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
│   ├── theme.py        # M!theme — runtime theme switcher
│   └── ...             # play, pause, skip, mood, recommend, scenario, find…
├── conductor/          # UX planning and session orchestration notes
├── core/               # State machines and configuration management
├── parser/             # Lexical parsing and command dispatch routing
├── player/             # libmpv abstractions and queue synchronization
├── recommender/        # ML Vector processing for semantic/acoustic matching
├── search_engine/      # YouTube Music search abstraction
├── ui/                 # Textual TUI — app, components, styles, and themes
│   ├── app.py          # Main Textual app entry point & event loop
│   ├── themes.py       # Theme registry, hot-swap & .env persistence
│   ├── visualizer.py   # Animated multi-color audio visualizer
│   ├── components/     # Modular UI widgets
│   │   ├── logo.py         # LogoPanel — block-char TUNE banner
│   │   ├── status_bar.py   # Always-visible status HUD
│   │   ├── now_playing.py  # Now Playing panel
│   │   ├── queue.py        # Queue display widget
│   │   ├── input.py        # Command input bar
│   │   └── modal.py        # Dialog/modal overlays
│   └── styles/             # TCSS theme stylesheets (8 themes)
│       ├── theme.tcss          # Cyberpunk / Synthwave (default)
│       ├── black.tcss          # Pure Black
│       ├── red_velvet.tcss     # Red Velvet
│       ├── ocean.tcss          # Ocean Deep
│       ├── forest.tcss         # Forest Night
│       ├── sunset.tcss         # Sunset Amber
│       ├── rose_gold.tcss      # Rose Gold
│       └── dracula.tcss        # Dracula
├── utils/              # Shared helpers and command routing
├── logo.txt            # Block-character TUNE logo (loaded by LogoPanel)
└── main.py             # Application Entrypoint
```

---

<div align="center">
Built with ❤️ for the terminal.
<br>
<i>Empowering developers to never leave the CLI for their music again.</i>
</div>
