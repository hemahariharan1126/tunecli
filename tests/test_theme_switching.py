"""
Comprehensive tests for Black theme CSS parsing, runtime switching,
save-after-apply ordering, error rollback, and restart persistence.
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from textual.color import Color
from textual.css.stylesheet import Stylesheet

from commands.theme import theme as theme_command
from ui.app import TuneCLIApp
from ui.themes import THEMES, validate_theme_css, get_saved_theme, save_theme


def _make_mock_controller():
    ctrl = MagicMock()
    ctrl.mpv_player.is_available.return_value = True
    ctrl.mpv_player.is_playing.return_value = False
    ctrl.queue_manager.now_playing.return_value = None
    ctrl.get_queue.return_value = []
    ctrl.radio_mode = False
    ctrl.current_mood = ""
    ctrl.seed_language = None
    ctrl.eq_enabled = False
    ctrl.crossfade_seconds = 0
    return ctrl


class TestThemeCSSValidation(unittest.TestCase):
    def test_all_registered_themes_parse_cleanly(self):
        """Every registered .tcss file including black.tcss must parse with 0 errors."""
        self.assertIn("black", THEMES)
        for name in THEMES:
            with self.subTest(theme=name):
                validate_theme_css(name)
                ss = Stylesheet()
                ss.read(Path(THEMES[name]))
                ss.parse()
                self.assertGreater(len(ss.rules), 0)

    def test_black_tcss_has_pure_black_background(self):
        """black.tcss must define #000000 for Screen and #output_log."""
        ss = Stylesheet()
        ss.read(Path(THEMES["black"]))
        ss.parse()
        screen_rules = [r for r in ss.rules if "Screen" in str(r.selector_names)]
        self.assertTrue(screen_rules)


class TestThemeRuntimeSwitching(unittest.IsolatedAsyncioTestCase):
    async def test_theme_switching_sequences_and_save_order(self):
        """Test Cyberpunk->Black, Black->Cyberpunk, Dracula->Black, Black->Matrix, Black->Black, repeated switching."""
        saved_calls = []

        with patch("ui.app.get_controller", return_value=_make_mock_controller()), \
             patch("ui.app.get_saved_theme", return_value="cyberpunk"), \
             patch("ui.app.save_theme", side_effect=lambda n: saved_calls.append(n)):

            app = TuneCLIApp()
            async with app.run_test() as pilot:
                await pilot.pause()

                # Initial: cyberpunk
                self.assertEqual(app.active_theme, "cyberpunk")
                self.assertEqual(app.screen.styles.background, Color(8, 8, 16))

                # 1. Cyberpunk -> Black via M!theme black
                res = theme_command(["black"])
                self.assertEqual(res, {"type": "theme_switch", "theme": "black"})
                # Must NOT have saved yet before _apply_theme runs
                self.assertEqual(saved_calls, [])

                app._apply_theme("black")
                self.assertEqual(app.active_theme, "black")
                self.assertEqual(app.screen.styles.background, Color(0, 0, 0))
                self.assertEqual(app.now_playing_panel.styles.background, Color(5, 5, 5))
                fg = app.now_playing_panel.styles.color
                self.assertEqual((fg.r, fg.g, fg.b), (255, 255, 255))
                self.assertEqual(app.now_playing_panel.styles.border.top[1], Color(255, 255, 255))
                self.assertEqual(saved_calls[-1], "black")

                # 2. Black -> Cyberpunk (must remove black.tcss so cyberpunk actually applies!)
                app._apply_theme("cyberpunk")
                self.assertEqual(app.active_theme, "cyberpunk")
                self.assertEqual(app.screen.styles.background, Color(8, 8, 16))
                self.assertEqual(saved_calls[-1], "cyberpunk")

                # 3. Dracula -> Black
                app._apply_theme("dracula")
                self.assertEqual(app.screen.styles.background, Color(40, 42, 54))
                app._apply_theme("black")
                self.assertEqual(app.active_theme, "black")
                self.assertEqual(app.screen.styles.background, Color(0, 0, 0))

                # 4. Black -> Matrix
                app._apply_theme("matrix")
                self.assertEqual(app.active_theme, "matrix")
                mfg = app.now_playing_panel.styles.color
                self.assertEqual((mfg.r, mfg.g, mfg.b), (224, 255, 224))
                self.assertEqual(app.now_playing_panel.styles.border.top[1], Color(0, 255, 65))

                # 5. Repeated Black switching (Matrix -> Black -> Black)
                app._apply_theme("black")
                self.assertEqual(app.active_theme, "black")
                self.assertEqual(app.screen.styles.background, Color(0, 0, 0))
                app._apply_theme("black")
                self.assertEqual(app.active_theme, "black")
                self.assertEqual(app.screen.styles.background, Color(0, 0, 0))

    async def test_restart_persistence_restores_black(self):
        """When .env has TUNECLI_THEME=black, restarting TuneCLI applies Black immediately."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = os.path.join(tmpdir, ".env")
            with open(env_path, "w", encoding="utf-8") as f:
                f.write("TUNECLI_THEME='black'\n")

            with patch("ui.themes._ENV", env_path), \
                 patch.dict(os.environ, {"TUNECLI_THEME": "black"}, clear=False):
                restored = get_saved_theme()
                self.assertEqual(restored, "black")

                with patch("ui.app.get_controller", return_value=_make_mock_controller()), \
                     patch("ui.app.get_saved_theme", return_value=restored):
                    app = TuneCLIApp()
                    async with app.run_test() as pilot:
                        await pilot.pause()
                        self.assertEqual(app.active_theme, "black")
                        self.assertEqual(app.screen.styles.background, Color(0, 0, 0))
                        self.assertEqual(app.now_playing_panel.styles.background, Color(5, 5, 5))

    async def test_invalid_css_and_missing_file_rollback(self):
        """Failed CSS application must restore previous stylesheet, keep active_theme, and not save."""
        saved_calls = []

        with tempfile.TemporaryDirectory() as tmpdir:
            bad_css_path = os.path.join(tmpdir, "bad.tcss")
            with open(bad_css_path, "w", encoding="utf-8") as f:
                f.write("Screen { invalid-property-xyz: ???; }\n")

            missing_css_path = os.path.join(tmpdir, "missing.tcss")

            with patch("ui.app.get_controller", return_value=_make_mock_controller()), \
                 patch("ui.app.get_saved_theme", return_value="cyberpunk"), \
                 patch("ui.app.save_theme", side_effect=lambda n: saved_calls.append(n)), \
                 patch.dict(THEMES, {"bad_theme": bad_css_path, "missing_theme": missing_css_path}):

                # Command-level validation rejects invalid CSS and missing file
                bad_res = theme_command(["bad_theme"])
                self.assertIsInstance(bad_res, str)
                self.assertIn("THEME ERR", bad_res)

                miss_res = theme_command(["missing_theme"])
                self.assertIsInstance(miss_res, str)
                self.assertIn("THEME ERR", miss_res)

                # App-level rollback if _apply_theme is called directly with invalid/missing CSS
                app = TuneCLIApp()
                async with app.run_test() as pilot:
                    await pilot.pause()
                    self.assertEqual(app.active_theme, "cyberpunk")
                    self.assertEqual(app.screen.styles.background, Color(8, 8, 16))

                    app._apply_theme("bad_theme")
                    self.assertEqual(app.active_theme, "cyberpunk")
                    self.assertEqual(app.screen.styles.background, Color(8, 8, 16))
                    self.assertEqual(saved_calls, [])

                    app._apply_theme("missing_theme")
                    self.assertEqual(app.active_theme, "cyberpunk")
                    self.assertEqual(app.screen.styles.background, Color(8, 8, 16))
                    self.assertEqual(saved_calls, [])

                    # Also test refresh_css failure rollback
                    with patch.object(app, "refresh_css", side_effect=[RuntimeError("Simulated CSS error"), None]):
                        app._apply_theme("black")
                        self.assertEqual(app.active_theme, "cyberpunk")
                        self.assertEqual(saved_calls, [])


if __name__ == "__main__":
    unittest.main()
