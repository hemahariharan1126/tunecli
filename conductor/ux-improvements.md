# UX Improvement Plan: Reactive Textual UI

## Objective
Transition TuneCLI from a blocking terminal input loop to a fully reactive, event-driven Terminal User Interface (TUI) using the Textual framework. This will eliminate UI flickering, enable real-time playback progress updates, and provide global hotkeys for a seamless user experience.

## Key Files & Context
- `main.py`: Currently handles the blocking `while True` loop. Will be updated to launch `TuneCLIApp`.
- `ui/terminal_ui.py`: Contains the `TuneCLIApp` Textual application. Will be enhanced with timers and hotkeys.
- `ui/progress_bar.py` & `ui/visualizer.py`: Existing UI assets that will be integrated into the reactive layout.

## Implementation Steps

1. **Refactor `main.py` Entry Point:**
   - Remove the `while True` console input loop.
   - Import and instantiate `TuneCLIApp` from `ui/terminal_ui.py`.
   - Start the application using `app.run()`.

2. **Enhance `terminal_ui.py` (Real-Time Updates):**
   - Add a `set_interval` timer to `TuneCLIApp` or `NowPlayingPanel` to fetch playback position from `self.controller` every 1 second.
   - Update reactive properties (like progress, duration, and visualizer frame) so the UI repaints automatically without flickering.

3. **Implement Global Hotkeys:**
   - Add Textual `BINDINGS` for common actions:
     - `Space`: Pause/Resume
     - `n`: Next Track
     - `p`: Previous Track
     - `+` / `-`: Volume up/down
   - Create action methods (e.g., `action_toggle_playback`) that call the respective `PlaybackController` methods.

4. **Integrate Visualizer & Progress:**
   - Add the ASCII visualizer from `ui/visualizer.py` into the `NowPlayingPanel`.
   - Draw a simple dynamic progress bar based on the current playback percentage.

## Verification & Testing
- Run `python main.py` and verify the Textual UI launches properly.
- Play a track and confirm the progress timer and visualizer update seamlessly while allowing text input simultaneously.
- Press global hotkeys (Space, n, +, -) and verify the player responds immediately without needing to press Enter.
