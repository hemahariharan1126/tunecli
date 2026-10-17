"""
Find Command — Records audio and identifies songs via Shazam.
Integrated with the TUI via background workers and selection modals.
Supports microphone capture and system audio loopback (Stereo Mix).
"""

import asyncio
import tempfile
import os
import logging
import numpy as np
try:
    import sounddevice as sd
    import soundfile as sf
    from shazamio import Shazam
    AUDIO_CAPTURE_AVAILABLE = True
except ImportError:
    sd = None
    sf = None
    Shazam = None
    AUDIO_CAPTURE_AVAILABLE = False


def _find_loopback_device() -> int | None:
    """Locate a Stereo Mix or loopback device for recording system audio."""
    try:
        devices = sd.query_devices()
        for idx, dev in enumerate(devices):
            if dev.get("max_input_channels", 0) > 0:
                name = dev.get("name", "").lower()
                if any(k in name for k in ["stereo mix", "what u hear", "wave out", "loopback"]):
                    return idx
    except Exception:
        pass
    return None


def find(args: list[str] | None = None):
    """
    M!find [duration_sec] [sys]
    Records audio and identifies the track via Shazam.
    - Default: 7 seconds from microphone
    - M!find 10: Records for 10 seconds
    - M!find sys: Records internal audio from Stereo Mix
    """
    args = args or []
    if not AUDIO_CAPTURE_AVAILABLE:
        return (
            "[yellow]⚠️ Audio recognition is disabled in this environment.[/yellow]\n"
            "[dim]PortAudio / sounddevice is not installed. Use 'M!play <song name>' instead.[/dim]"
        )
    args_lower = [a.lower() for a in args]

    # Parse duration (default: 7 seconds, clamped between 4 and 15)
    duration = 7
    for a in args:
        if a.isdigit():
            duration = max(4, min(15, int(a)))
            break

    # Determine input device
    use_system_audio = any(a in ("sys", "system", "loopback", "pc") for a in args_lower)
    device_idx = None
    device_name = "Default Microphone"

    if use_system_audio:
        loop_idx = _find_loopback_device()
        if loop_idx is not None:
            device_idx = loop_idx
            device_name = sd.query_devices(loop_idx).get("name", "Stereo Mix")
        else:
            return (
                "[yellow]⚠️ Stereo Mix / Loopback device not found.[/yellow]\n"
                "[dim]To identify internal PC audio, enable 'Stereo Mix' in Windows Sound Settings,\n"
                "or use your microphone with speakers turned up: [bold]M!find[/bold][/dim]"
            )

    # Query device parameters
    try:
        dev_info = sd.query_devices(device_idx) if device_idx is not None else sd.query_devices(sd.default.device[0])
        samplerate = int(dev_info.get("default_samplerate", 44100))
        max_channels = int(dev_info.get("max_input_channels", 1))
        channels = 2 if max_channels >= 2 else 1
    except Exception as e:
        return f"[red]ERR.AUDIO_CONFIG: Failed to configure audio device: {e}[/red]"

    # 1. Record Audio synchronously via sounddevice
    try:
        total_frames = int(duration * samplerate)
        recording = sd.rec(
            total_frames,
            samplerate=samplerate,
            channels=channels,
            device=device_idx,
            blocking=True,
        )
    except Exception as e:
        return f"[red]ERR.MIC: Could not access audio device '{device_name}': {e}[/red]"

    # Downmix to mono if stereo
    if channels > 1:
        audio_data = np.mean(recording, axis=1)
    else:
        audio_data = recording.flatten()

    raw_peak = float(np.max(np.abs(audio_data))) if len(audio_data) > 0 else 0.0

    # 2. Check for silence or near-inaudible volume
    if raw_peak < 0.012:
        return (
            f"[yellow]⚠️ AUDIO INPUT TOO FAINT (Peak: {raw_peak * 100:.1f}%)[/yellow]\n"
            f"[dim]The recording captured near-silence. Shazam requires audible music landmarks.\n"
            f" • If using a microphone: bring the speaker closer or turn up the volume.\n"
            f" • Check that your microphone is unmuted in Windows settings.\n"
            f" • If playing audio directly on this PC, try: [bold]M!find sys[/bold]\n"
            f" • You can also record longer: [bold]M!find 10[/bold][/dim]"
        )

    # 3. Peak Normalization: scale audio so peaks reach 0.95 for optimal Shazam landmarking
    normalized_audio = (audio_data / raw_peak * 0.95).astype(np.float32)

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_filename = tmp.name

    try:
        sf.write(tmp_filename, normalized_audio, samplerate)

        # 4. Identify track via Shazam
        async def identify():
            shazam = Shazam()
            return await shazam.recognize(tmp_filename)

        result = asyncio.run(identify())
    except Exception as e:
        return f"[red]ERR.SHAZAM: Identification failed: {e}[/red]"
    finally:
        if os.path.exists(tmp_filename):
            try:
                os.remove(tmp_filename)
            except Exception:
                pass

    if not result or "track" not in result:
        return (
            f"[yellow]WARN: NO_MATCH_FOUND (Captured Peak: {raw_peak * 100:.0f}%)[/yellow]\n"
            f"[dim]Shazam couldn't match the acoustic fingerprint.\n"
            f" • Try recording a longer sample: [bold]M!find 10[/bold]\n"
            f" • Wait for a recognizable section (vocals or main hook).\n"
            f" • If music is playing on this PC, run: [bold]M!find sys[/bold][/dim]"
        )

    track = result["track"]
    title = track.get("title", "Unknown Title")
    artist = track.get("subtitle", "Unknown Artist")

    # 5. Fetch Similar Recommendations
    from player.playback_controller import get_controller
    controller = get_controller()
    options = [{"title": title, "artist": artist, "type": "Identified"}]

    try:
        from recommender.recommender_engine import RecommenderEngine
        recommender = RecommenderEngine()
        recs = recommender.get_spotify_recommendations(
            f"{title} {artist}",
            target_lang=controller.seed_language,
        )
        if recs:
            for r in recs[:4]:
                options.append({"title": r["title"], "artist": r["artist"], "type": "Similar"})
    except Exception:
        logging.warning("Find command: Recommender unavailable for extra options.")

    return {
        "type": "selection",
        "title": f"IDENTIFIED: {title}",
        "options": options,
    }
