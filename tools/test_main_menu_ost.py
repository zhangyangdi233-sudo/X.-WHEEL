import json
import math
import re
import struct
import unittest
import wave
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MENU_OST_WAV = ROOT / "snd" / "main_menu_dreamcore_loop.wav"
MENU_OST_META = ROOT / "snd" / "main_menu_dreamcore_loop.json"
TRANSITION_OST_WAV = ROOT / "snd" / "start_to_cartridge_transition.wav"
TRANSITION_OST_META = ROOT / "snd" / "start_to_cartridge_transition.json"
CARTRIDGE_OST_WAV = ROOT / "snd" / "cartridge_select_signal_loop.wav"
CARTRIDGE_OST_META = ROOT / "snd" / "cartridge_select_signal_loop.json"
INSERT_SFX = {
    "Cartridge1": ROOT / "snd" / "cartridge1_insert.wav",
    "Cartridge2": ROOT / "snd" / "cartridge2_insert.wav",
    "Cartridge3": ROOT / "snd" / "cartridge3_insert.wav",
}
INSERT_SFX_META = {
    "Cartridge1": ROOT / "snd" / "cartridge1_insert.json",
    "Cartridge2": ROOT / "snd" / "cartridge2_insert.json",
    "Cartridge3": ROOT / "snd" / "cartridge3_insert.json",
}
SWITCHABLE_TRACKS = [
    ROOT / "snd" / "dream_pop_switch_01_lucent_slaps.wav",
    ROOT / "snd" / "dream_pop_switch_02_soft_orbit.wav",
    ROOT / "snd" / "dream_pop_switch_03_afterimage_pool.wav",
]
SWITCHABLE_TRACK_META = [
    ROOT / "snd" / "dream_pop_switch_01_lucent_slaps.json",
    ROOT / "snd" / "dream_pop_switch_02_soft_orbit.json",
    ROOT / "snd" / "dream_pop_switch_03_afterimage_pool.json",
]
MENU_CONTROLLER = ROOT / "scripts" / "ui" / "menu_controller.gd"
CARTRIDGE_SELECT_CONTROLLER = ROOT / "scripts" / "gameplay" / "cartridge_select_controller.gd"
AUDIO_MANAGER = ROOT / "scripts" / "autoload" / "audio_manager.gd"
PROJECT_GODOT = ROOT / "project.godot"


class MainMenuOstTest(unittest.TestCase):
    def test_menu_ost_asset_is_loop_ready_wav(self):
        self.assert_loop_ready_wav(MENU_OST_WAV, 60.0, 75.0)

    def test_transition_ost_asset_is_short_one_shot_wav(self):
        duration = self.assert_basic_wav(TRANSITION_OST_WAV)
        self.assertGreaterEqual(duration, 2.5)
        self.assertLessEqual(duration, 4.5)

    def test_cartridge_select_ost_asset_is_loop_ready_wav(self):
        self.assert_loop_ready_wav(CARTRIDGE_OST_WAV, 68.0, 78.0)

    def test_cartridge_insert_sfx_are_three_distinct_short_wavs(self):
        hashes = set()
        for path in INSERT_SFX.values():
            duration = self.assert_basic_wav(path)
            self.assertGreaterEqual(duration, 2.6)
            self.assertLessEqual(duration, 3.4)
            hashes.add(hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertEqual(len(hashes), 3)

    def test_cartridge_insert_sfx_metadata_documents_identity(self):
        expected_motifs = {
            "Cartridge1": "fries-fire-dream",
            "Cartridge2": "empty-stomach-crt",
            "Cartridge3": "bbs-green-refresh",
        }
        for cart_name, path in INSERT_SFX_META.items():
            metadata = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(metadata["cartridge"], cart_name)
            self.assertEqual(metadata["role"], "cartridge insertion sfx")
            self.assertEqual(metadata["version"], "prototype-01")
            self.assertEqual(metadata["motif"], expected_motifs[cart_name])

    def test_switchable_dream_pop_tracks_are_distinct_loop_ready_wavs(self):
        hashes = set()
        for path in SWITCHABLE_TRACKS:
            self.assert_loop_ready_wav(path, 88.0, 100.0)
            hashes.add(hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertEqual(len(hashes), 3)

    def test_switchable_dream_pop_tracks_avoid_gunshot_like_transients(self):
        for path in SWITCHABLE_TRACKS:
            with wave.open(str(path), "rb") as wav:
                data = wav.readframes(wav.getnframes())
            self.assertLess(_max_adjacent_channel_delta(data), 0.16, path.name)
            self.assertLess(_window_rms_ratio(data), 2.65, path.name)

    def test_switchable_dream_pop_metadata_documents_style(self):
        expected_tracks = [
            {
                "mood": "soft-floating-reader",
                "version": "prototype-03",
                "bass_articulation": "soft-pop",
                "melody_role": "catchy lead hook",
                "tags": ("dream_pop", "bright_idol_pop", "anime_pop", "melody_led"),
                "reference_direction": "bright-original-idol-pop",
                "lead_hook": "16-second singable refrain",
            },
            {
                "mood": "active-choice-groove",
                "version": "prototype-02",
                "bass_articulation": "slap",
                "melody_role": "lead-forward",
                "tags": ("dream_pop", "slap_bass", "melody_led"),
            },
            {
                "mood": "unstable-afterimage",
                "version": "prototype-02",
                "bass_articulation": "slap",
                "melody_role": "lead-forward",
                "tags": ("dream_pop", "slap_bass", "melody_led"),
            },
        ]
        for path, expected in zip(SWITCHABLE_TRACK_META, expected_tracks):
            metadata = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(metadata["role"], "switchable chapter bgm")
            self.assertEqual(metadata["version"], expected["version"])
            self.assertEqual(metadata["mood"], expected["mood"])
            self.assertEqual(metadata["noise_amount"], "light")
            self.assertEqual(metadata["bass_articulation"], expected["bass_articulation"])
            self.assertEqual(metadata["hard_transients"], "removed")
            self.assertEqual(metadata["melody_role"], expected["melody_role"])
            for tag in expected["tags"]:
                self.assertIn(tag, metadata["style_tags"])
            if "reference_direction" in expected:
                self.assertEqual(metadata["reference_direction"], expected["reference_direction"])
                self.assertEqual(metadata["lead_hook"], expected["lead_hook"])

    def test_ost_metadata_documents_melody_and_script_intent(self):
        metadata = json.loads(MENU_OST_META.read_text(encoding="utf-8"))
        self.assertEqual(metadata["title"], "X. WHEEL - Main Menu Dreamcore Loop")
        self.assertEqual(metadata["version"], "prototype-02")
        self.assertIn("dreamcore", metadata["style_tags"])
        self.assertIn("lo-fi", metadata["style_tags"])
        self.assertIn("y2k", metadata["style_tags"])
        self.assertEqual(metadata["melody_role"], "green cursor title motif")

        transition = json.loads(TRANSITION_OST_META.read_text(encoding="utf-8"))
        self.assertEqual(transition["role"], "start-game camera bridge")
        self.assertEqual(transition["loop"]["mode"], "none")

        cartridge = json.loads(CARTRIDGE_OST_META.read_text(encoding="utf-8"))
        self.assertEqual(cartridge["title"], "X. WHEEL - Cartridge Select Signal Loop")
        self.assertEqual(cartridge["version"], "prototype-01")
        self.assertEqual(cartridge["role"], "cartridge select screen")
        for motif in ("fries/fire dream", "empty-stomach CRT dialogue", "BBS refresh green-light"):
            self.assertIn(motif, cartridge["script_motifs"])

    def test_main_menu_starts_looped_bgm_and_transition_stinger(self):
        source = MENU_CONTROLLER.read_text(encoding="utf-8")
        self.assertIn('preload("res://snd/main_menu_dreamcore_loop.wav")', source)
        self.assertIn('preload("res://snd/start_to_cartridge_transition.wav")', source)
        self.assertRegex(source, r"MENU_BGM\.loop_mode\s*=\s*AudioStreamWAV\.LOOP_FORWARD")
        self.assertRegex(source, r"AudioManager\.play_bgm\(\s*MENU_BGM")
        self.assertRegex(source, r"AudioManager\.play_bgm_stinger\(\s*START_GAME_TRANSITION")

    def test_cartridge_select_starts_looped_bgm(self):
        source = CARTRIDGE_SELECT_CONTROLLER.read_text(encoding="utf-8")
        self.assertIn('preload("res://snd/cartridge_select_signal_loop.wav")', source)
        self.assertRegex(source, r"CARTRIDGE_SELECT_BGM\.loop_mode\s*=\s*AudioStreamWAV\.LOOP_FORWARD")
        self.assertRegex(source, r"AudioManager\.play_bgm\(\s*CARTRIDGE_SELECT_BGM")

    def test_cartridge_select_plays_per_cartridge_insert_sfx(self):
        source = CARTRIDGE_SELECT_CONTROLLER.read_text(encoding="utf-8")
        self.assertIn('preload("res://snd/cartridge1_insert.wav")', source)
        self.assertIn('preload("res://snd/cartridge2_insert.wav")', source)
        self.assertIn('preload("res://snd/cartridge3_insert.wav")', source)
        self.assertRegex(source, r"INSERT_SFX\.get\(\s*cart_name")
        self.assertRegex(source, r"AudioManager\.play_sfx\(\s*insert_sfx")

    def test_audio_manager_bgm_playback_is_audible(self):
        source = AUDIO_MANAGER.read_text(encoding="utf-8")
        play_bgm = re.search(r"func play_bgm\(.*?\n(?=\nfunc |\Z)", source, re.S)
        self.assertIsNotNone(play_bgm)
        self.assertNotIn("linear_to_db(0.0)", play_bgm.group(0))
        self.assertIn("GlobalState.bgm_volume", play_bgm.group(0))
        self.assertIn("func play_bgm_stinger", source)
        self.assertRegex(source, r"_bgm_stinger_player\.bus\s*=\s*\"BGM\"")

    def test_audio_manager_exposes_global_switchable_playlist(self):
        source = AUDIO_MANAGER.read_text(encoding="utf-8")
        for path in SWITCHABLE_TRACKS:
            self.assertIn(f'preload("res://snd/{path.name}")', source)
        self.assertIn("SWITCHABLE_BGM_TRACKS", source)
        self.assertIn("func play_switchable_track", source)
        self.assertIn("func next_switchable_track", source)
        self.assertRegex(source, r"event\.is_action_pressed\(\s*\"music_next\"")

    def test_project_defines_f8_music_next_action(self):
        source = PROJECT_GODOT.read_text(encoding="utf-8")
        self.assertIn("music_next={", source)
        self.assertIn('"physical_keycode":4194337', source)

    def assert_basic_wav(self, path: Path) -> float:
        self.assertTrue(path.exists(), f"{path.name} should be generated")
        with wave.open(str(path), "rb") as wav:
            self.assertEqual(wav.getnchannels(), 2)
            self.assertEqual(wav.getsampwidth(), 2)
            self.assertEqual(wav.getframerate(), 44100)
            duration = wav.getnframes() / wav.getframerate()
            self.assertGreater(_rms(wav.readframes(wav.getnframes())), 0.01)
        return duration

    def assert_loop_ready_wav(self, path: Path, min_duration: float, max_duration: float) -> None:
        self.assertTrue(path.exists(), f"{path.name} should be generated")
        with wave.open(str(path), "rb") as wav:
            self.assertEqual(wav.getnchannels(), 2)
            self.assertEqual(wav.getsampwidth(), 2)
            self.assertEqual(wav.getframerate(), 44100)
            duration = wav.getnframes() / wav.getframerate()
            self.assertGreaterEqual(duration, min_duration)
            self.assertLessEqual(duration, max_duration)
            self.assertGreater(_rms(wav.readframes(wav.getnframes())), 0.01)

            window = int(wav.getframerate() * 0.05)
            wav.rewind()
            start = wav.readframes(window)
            wav.setpos(wav.getnframes() - window)
            end = wav.readframes(window)

        self.assertLess(_edge_delta(start, end), 0.02, "loop seam should avoid a click")


def _edge_delta(left_bytes: bytes, right_bytes: bytes) -> float:
    left = _unpack_pcm16(left_bytes)
    right = _unpack_pcm16(right_bytes)
    if not left or not right:
        return math.inf
    return max(
        abs(left[0] - right[-2]),
        abs(left[1] - right[-1]),
    )


def _rms(data: bytes) -> float:
    samples = _unpack_pcm16(data)
    if not samples:
        return 0.0
    return math.sqrt(sum(sample * sample for sample in samples) / len(samples))


def _max_adjacent_channel_delta(data: bytes) -> float:
    samples = _unpack_pcm16(data)
    if len(samples) < 3:
        return 0.0
    return max(abs(samples[index] - samples[index - 2]) for index in range(2, len(samples)))


def _window_rms_ratio(data: bytes) -> float:
    samples = _unpack_pcm16(data)
    window = 441 * 2
    if len(samples) < window * 2:
        return 1.0
    rms_values = []
    for start in range(0, len(samples) - window, window):
        segment = samples[start:start + window]
        rms_values.append(math.sqrt(sum(sample * sample for sample in segment) / len(segment)))
    sorted_values = sorted(rms_values)
    median = sorted_values[len(sorted_values) // 2]
    return max(rms_values) / max(median, 1e-9)


def _unpack_pcm16(data: bytes) -> tuple[float, ...]:
    if len(data) % 2:
        data = data[:-1]
    sample_count = len(data) // 2
    values = struct.unpack("<" + "h" * sample_count, data)
    return tuple(value / 32768.0 for value in values)


if __name__ == "__main__":
    unittest.main()
