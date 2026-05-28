import json
import math
import struct
import wave
from collections.abc import Callable
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "snd"

SAMPLE_RATE = 44100
TAU = math.tau

MAIN_MENU_DURATION = 64.0
TRANSITION_DURATION = 3.2
CARTRIDGE_SELECT_DURATION = 72.0
INSERT_SFX_DURATION = 3.0
SWITCHABLE_BGM_DURATION = 96.0

MAIN_MENU_WAV = OUT_DIR / "main_menu_dreamcore_loop.wav"
MAIN_MENU_META = OUT_DIR / "main_menu_dreamcore_loop.json"
TRANSITION_WAV = OUT_DIR / "start_to_cartridge_transition.wav"
TRANSITION_META = OUT_DIR / "start_to_cartridge_transition.json"
CARTRIDGE_SELECT_WAV = OUT_DIR / "cartridge_select_signal_loop.wav"
CARTRIDGE_SELECT_META = OUT_DIR / "cartridge_select_signal_loop.json"
INSERT_SFX_TRACKS = {
    "Cartridge1": (
        OUT_DIR / "cartridge1_insert.wav",
        OUT_DIR / "cartridge1_insert.json",
        "fries-fire-dream",
    ),
    "Cartridge2": (
        OUT_DIR / "cartridge2_insert.wav",
        OUT_DIR / "cartridge2_insert.json",
        "empty-stomach-crt",
    ),
    "Cartridge3": (
        OUT_DIR / "cartridge3_insert.wav",
        OUT_DIR / "cartridge3_insert.json",
        "bbs-green-refresh",
    ),
}
SWITCHABLE_BGM_TRACKS = {
    "lucent_slaps": (
        OUT_DIR / "dream_pop_switch_01_lucent_slaps.wav",
        OUT_DIR / "dream_pop_switch_01_lucent_slaps.json",
        "Lucent Hook Trial",
        "soft-floating-reader",
    ),
    "soft_orbit": (
        OUT_DIR / "dream_pop_switch_02_soft_orbit.wav",
        OUT_DIR / "dream_pop_switch_02_soft_orbit.json",
        "Soft Orbit",
        "active-choice-groove",
    ),
    "afterimage_pool": (
        OUT_DIR / "dream_pop_switch_03_afterimage_pool.wav",
        OUT_DIR / "dream_pop_switch_03_afterimage_pool.json",
        "Afterimage Pool",
        "unstable-afterimage",
    ),
}


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    _write_track(MAIN_MENU_WAV, MAIN_MENU_DURATION, _main_menu_sample)
    _write_json(MAIN_MENU_META, _main_menu_metadata())
    _write_track(TRANSITION_WAV, TRANSITION_DURATION, _transition_sample)
    _write_json(TRANSITION_META, _transition_metadata())
    _write_track(CARTRIDGE_SELECT_WAV, CARTRIDGE_SELECT_DURATION, _cartridge_select_sample)
    _write_json(CARTRIDGE_SELECT_META, _cartridge_select_metadata())
    for cart_name, (wav_path, meta_path, motif) in INSERT_SFX_TRACKS.items():
        _write_track(wav_path, INSERT_SFX_DURATION, lambda t, d, name=cart_name: _insert_sfx_sample(name, t, d))
        _write_json(meta_path, _insert_sfx_metadata(cart_name, motif))
    for track_id, (wav_path, meta_path, title, mood) in SWITCHABLE_BGM_TRACKS.items():
        _write_track(wav_path, SWITCHABLE_BGM_DURATION, lambda t, d, name=track_id: _switchable_bgm_sample(name, t, d))
        _write_json(meta_path, _switchable_bgm_metadata(track_id, title, mood))


def _write_track(path: Path, duration: float, synth: Callable[[float, float], tuple[float, float]]) -> None:
    frames = int(SAMPLE_RATE * duration)
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        wav.writeframes(_render_pcm(frames, duration, synth))


def _write_json(path: Path, metadata: dict) -> None:
    path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")


def _main_menu_metadata() -> dict:
    frames = int(SAMPLE_RATE * MAIN_MENU_DURATION)
    metadata = {
        "title": "X. WHEEL - Main Menu Dreamcore Loop",
        "version": "prototype-02",
        "role": "main menu",
        "duration_seconds": MAIN_MENU_DURATION,
        "sample_rate": SAMPLE_RATE,
        "channels": 2,
        "format": "16-bit PCM WAV",
        "loop": {
            "start_sample": 0,
            "end_sample": frames,
            "mode": "forward",
        },
        "melody_role": "green cursor title motif",
        "style_tags": ["psychedelic", "dreamcore", "denpa", "lo-fi", "y2k"],
        "production_notes": [
            "Original procedural synthesis; no samples copied from the reference OST.",
            "Version 2 raises the title motif above the pad while keeping the menu low-pressure.",
        ],
        "reference_mood": [
            "menu music.mp3",
            "room ambience.mp3",
            "night ambience.mp3",
            "thinking....mp3",
            "omnipresent.mp3",
        ],
    }
    return metadata


def _transition_metadata() -> dict:
    frames = int(SAMPLE_RATE * TRANSITION_DURATION)
    return {
        "title": "X. WHEEL - Start To Cartridge Bridge",
        "version": "prototype-01",
        "role": "start-game camera bridge",
        "duration_seconds": TRANSITION_DURATION,
        "sample_rate": SAMPLE_RATE,
        "channels": 2,
        "format": "16-bit PCM WAV",
        "loop": {
            "start_sample": 0,
            "end_sample": frames,
            "mode": "none",
        },
        "style_tags": ["dreamcore", "denpa", "lo-fi", "y2k", "transition"],
        "production_notes": [
            "Short one-shot bridge for the main menu camera push toward the desk.",
            "The title motif narrows into a cartridge boot chirp and lands on the cartridge select harmony.",
        ],
    }


def _cartridge_select_metadata() -> dict:
    frames = int(SAMPLE_RATE * CARTRIDGE_SELECT_DURATION)
    return {
        "title": "X. WHEEL - Cartridge Select Signal Loop",
        "version": "prototype-01",
        "role": "cartridge select screen",
        "duration_seconds": CARTRIDGE_SELECT_DURATION,
        "sample_rate": SAMPLE_RATE,
        "channels": 2,
        "format": "16-bit PCM WAV",
        "loop": {
            "start_sample": 0,
            "end_sample": frames,
            "mode": "forward",
        },
        "style_tags": ["psychedelic", "dreamcore", "denpa", "lo-fi", "y2k"],
        "melody_role": "three-cartridge selection motif",
        "script_motifs": [
            "fries/fire dream",
            "empty-stomach CRT dialogue",
            "BBS refresh green-light",
        ],
        "production_notes": [
            "Three 24-second sections map loosely to the three cartridges, then fold back into the opening.",
            "The loop remains quiet enough for drag-and-drop interaction but gives the selection screen a clearer melody.",
        ],
    }


def _insert_sfx_metadata(cart_name: str, motif: str) -> dict:
    frames = int(SAMPLE_RATE * INSERT_SFX_DURATION)
    return {
        "title": f"X. WHEEL - {cart_name} Insert SFX",
        "version": "prototype-01",
        "role": "cartridge insertion sfx",
        "cartridge": cart_name,
        "motif": motif,
        "duration_seconds": INSERT_SFX_DURATION,
        "sample_rate": SAMPLE_RATE,
        "channels": 2,
        "format": "16-bit PCM WAV",
        "loop": {
            "start_sample": 0,
            "end_sample": frames,
            "mode": "none",
        },
        "style_tags": ["mechanical", "lo-fi", "denpa", "y2k"],
        "production_notes": [
            "Original procedural synthesis for the cartridge insertion animation.",
            "Each cartridge has a distinct tail color while sharing a tactile plastic click.",
        ],
    }


def _switchable_bgm_metadata(track_id: str, title: str, mood: str) -> dict:
    frames = int(SAMPLE_RATE * SWITCHABLE_BGM_DURATION)
    metadata = {
        "title": f"X. WHEEL - {title}",
        "version": "prototype-02",
        "role": "switchable chapter bgm",
        "track_id": track_id,
        "mood": mood,
        "duration_seconds": SWITCHABLE_BGM_DURATION,
        "sample_rate": SAMPLE_RATE,
        "channels": 2,
        "format": "16-bit PCM WAV",
        "loop": {
            "start_sample": 0,
            "end_sample": frames,
            "mode": "forward",
        },
        "style_tags": ["dream_pop", "slap_bass", "melody_led", "light_noise", "lo-fi"],
        "noise_amount": "light",
        "bass_articulation": "slap",
        "hard_transients": "removed",
        "melody_role": "lead-forward",
        "production_notes": [
            "Original procedural synthesis for player-switchable chapter listening.",
            "Prototype 02 softens hard transient clicks and pushes the lead melody/harmony forward.",
        ],
    }
    if track_id == "lucent_slaps":
        metadata.update(
            {
                "version": "prototype-03",
                "style_tags": ["dream_pop", "bright_idol_pop", "anime_pop", "melody_led", "light_noise", "lo-fi"],
                "bass_articulation": "soft-pop",
                "melody_role": "catchy lead hook",
                "lead_hook": "16-second singable refrain",
                "reference_direction": "bright-original-idol-pop",
                "production_notes": [
                    "Original procedural synthesis inspired by the broad bright idol-pop feeling of the provided references.",
                    "Prototype 03 removes slap/click emphasis and centers a clear 16-second lead hook with soft bass support.",
                    "No melodies, samples, or arrangements are copied from reference tracks.",
                ],
            }
        )
    return metadata


def _render_pcm(
    frames: int,
    duration: float,
    synth: Callable[[float, float], tuple[float, float]],
) -> bytes:
    pcm = bytearray()
    phase_step = 1.0 / SAMPLE_RATE
    for frame in range(frames):
        t = frame * phase_step
        left, right = synth(t, duration)
        pcm.extend(struct.pack("<hh", _to_i16(left), _to_i16(right)))
    return bytes(pcm)


def _main_menu_sample(t: float, duration: float) -> tuple[float, float]:
    loop = t / duration
    room_breath = 0.65 + 0.35 * _lfo(loop, 2, 0.13)

    hum = 0.022 * math.sin(TAU * 60.0 * t)
    hum += 0.010 * math.sin(TAU * 120.0 * t + 0.4)

    pad = 0.0
    for chord_index, weight in _cyclic_chord_weights(t, duration, MAIN_CHORDS, 3.0):
        for freq, gain in MAIN_CHORDS[chord_index]:
            detune = 0.18 * _lfo(loop, 3 + chord_index, freq * 0.003)
            pad += weight * gain * _soft_triangle(_loop_freq(freq + detune, duration), t)
    pad *= 0.20 * room_breath

    bass = 0.075 * _soft_sine(_loop_freq(55.0, duration), t, loop, 5)
    bass += 0.025 * _soft_sine(_loop_freq(82.41, duration), t, loop, 7)

    bells = _main_title_motif(t, duration)
    chatter = 0.026 * _periodic_hiss(loop)
    tape = 0.018 * math.sin(TAU * 0.1875 * t + 1.2)

    dry = hum + pad + bass + bells + chatter + tape
    crushed = round(dry * 96.0) / 96.0
    sample = math.tanh(crushed * 1.65) * 0.55
    return _stereoize(sample, t, duration, 0.14)


def _transition_sample(t: float, duration: float) -> tuple[float, float]:
    progress = t / duration
    fade = _smoothstep(min(t / 0.05, 1.0)) * (1.0 - _smoothstep(max((t - duration + 0.25) / 0.25, 0.0)))
    charge = _smoothstep(progress)

    base = 0.030 * math.sin(TAU * 60.0 * t)
    base += 0.070 * _pitch_sweep(t, 146.83, 220.0, progress)
    base += 0.055 * _pitch_sweep(t, 293.66, 587.33, progress)
    base += _transition_boot_chirps(t)

    gate = 0.5 + 0.5 * math.sin(TAU * 19.0 * progress)
    hiss = 0.045 * round(_periodic_hiss(progress) * gate * 10.0) / 10.0
    sample = math.tanh((base + hiss) * (1.0 + charge * 1.2)) * 0.70 * fade
    pan = -0.35 + 0.70 * progress
    return sample * (1.0 - pan * 0.35), sample * (1.0 + pan * 0.35)


def _cartridge_select_sample(t: float, duration: float) -> tuple[float, float]:
    loop = t / duration
    weights = _section_weights(t, duration, 3, 3.5)
    breath = 0.70 + 0.30 * _lfo(loop, 3, 0.4)

    hum = 0.020 * math.sin(TAU * 60.0 * t)
    hum += 0.012 * math.sin(TAU * 90.0 * t + 0.5)

    pad = 0.0
    for chord_index, weight in _cyclic_chord_weights(t, duration, CARTRIDGE_CHORDS, 4.0):
        for freq, gain in CARTRIDGE_CHORDS[chord_index]:
            pad += weight * gain * _soft_triangle(_loop_freq(freq, duration), t)
    pad *= 0.17 * breath

    bass = 0.054 * _soft_sine(_loop_freq(48.999, duration), t, loop, 4)
    bass += 0.022 * _soft_sine(_loop_freq(73.416, duration), t, loop, 5)

    fries_fire = weights[0] * _fries_fire_motif(t, duration)
    empty_crt = weights[1] * _empty_stomach_crt_motif(t, duration)
    bbs_green = weights[2] * _bbs_refresh_motif(t, duration)
    shared = _selection_shared_motif(t, duration)

    refresh_noise = 0.020 * _periodic_hiss(loop) * (0.65 + 0.35 * weights[2])
    dry = hum + pad + bass + fries_fire + empty_crt + bbs_green + shared + refresh_noise
    crushed = round(dry * 84.0) / 84.0
    sample = math.tanh(crushed * 1.8) * 0.58
    return _stereoize(sample, t, duration, 0.20)


def _insert_sfx_sample(cart_name: str, t: float, duration: float) -> tuple[float, float]:
    progress = t / duration
    entry = _insert_mechanical_body(t, duration)
    if cart_name == "Cartridge1":
        color = _insert_fries_fire_tail(t, duration)
        width = 0.18
    elif cart_name == "Cartridge2":
        color = _insert_empty_crt_tail(t, duration)
        width = 0.10
    else:
        color = _insert_bbs_green_tail(t, duration)
        width = 0.24

    tail_fade = 1.0 - _smoothstep(max((t - duration + 0.25) / 0.25, 0.0))
    sample = math.tanh((entry + color) * 2.1) * 0.68 * tail_fade
    pan = width * math.sin(TAU * (1.0 + progress * 2.0) * progress)
    return sample * (1.0 - pan), sample * (1.0 + pan)


def _switchable_bgm_sample(track_id: str, t: float, duration: float) -> tuple[float, float]:
    if track_id == "lucent_slaps":
        return _bright_idol_trial_sample(t, duration)

    loop = t / duration
    config = DREAM_POP_TRACKS[track_id]
    breath = 0.68 + 0.32 * _lfo(loop, config["breath_cycles"], config["phase"])

    pad = _dream_pop_pad(t, duration, config["chords"]) * breath
    bass = _slap_bass_phrase(t, duration, config["bass_pattern"], config["bass_gain"])
    melody = _dream_pop_melody(t, duration, config["melody"], config["melody_gain"])
    harmony = _dream_pop_harmony(t, duration, config["melody"], config["melody_gain"] * 0.42, config["harmony_ratio"])
    shimmer = _dream_pop_shimmer(t, duration, config["shimmer_notes"], config["shimmer_gain"])
    drums = _soft_dream_pulse(t, duration, config["drum_gain"])
    noise = _light_dream_noise(t, duration, config["noise_gain"])

    dry = pad + bass + melody + harmony + shimmer + drums + noise
    compressed = math.tanh(dry * 1.55) * 0.62
    return _stereoize(compressed, t, duration, config["width"])


def _bright_idol_trial_sample(t: float, duration: float) -> tuple[float, float]:
    loop = t / duration
    breath = 0.78 + 0.22 * _lfo(loop, 4, 0.2)

    pad = _bright_idol_pad(t, duration) * breath
    bass = _soft_pop_bass_phrase(t, duration, BRIGHT_IDOL_BASS_PATTERN, 0.071)
    lead = _bright_idol_hook(t, duration, BRIGHT_IDOL_LEAD, 0.083)
    harmony = _bright_idol_hook(t, duration, BRIGHT_IDOL_HARMONY, 0.034)
    sparkle = _bright_idol_sparkles(t, duration)
    pulse = _soft_pop_pulse(t, duration, 0.0045)
    noise = _light_dream_noise(t, duration, 0.0035)

    dry = pad + bass + lead + harmony + sparkle + pulse + noise
    compressed = math.tanh(dry * 1.48) * 0.64
    return _stereoize(compressed, t, duration, 0.18)


def _bright_idol_pad(t: float, duration: float) -> float:
    pad = 0.0
    for chord_index, weight in _looping_chord_weights(t, duration, BRIGHT_IDOL_CHORDS, 4.0, 0.85):
        for freq, gain in BRIGHT_IDOL_CHORDS[chord_index]:
            wobble = 0.05 * math.sin(TAU * 5.0 * (t / duration) + freq * 0.011)
            tone = _soft_triangle(_loop_freq(freq + wobble, duration), t)
            tone += 0.11 * math.sin(TAU * _loop_freq(freq * 2.0, duration) * t + chord_index * 0.17)
            pad += weight * gain * tone
    return pad * 0.145


def _soft_pop_bass_phrase(
    t: float,
    duration: float,
    pattern: list[tuple[float, float, float]],
    gain: float,
) -> float:
    phrase = 0.0
    bar_start = math.floor(t / 8.0) * 8.0
    for offset, freq, weight in pattern:
        phrase += _soft_pop_bass_hit(t, bar_start + offset, _loop_freq(freq, duration), gain * weight)
    return phrase


def _soft_pop_bass_hit(t: float, start: float, freq: float, gain: float) -> float:
    age = t - start
    if age < 0.0 or age > 0.95:
        return 0.0
    attack = _smoothstep(min(age / 0.065, 1.0))
    decay = math.exp(age * -2.85)
    body = math.sin(TAU * freq * t)
    body += 0.13 * _soft_triangle(freq * 2.0, t)
    body += 0.08 * math.sin(TAU * freq * 0.5 * t + 0.4)
    return gain * attack * decay * body


def _bright_idol_hook(
    t: float,
    duration: float,
    events: list[tuple[float, float, float, float, float]],
    gain: float,
) -> float:
    phrase = 0.0
    for phrase_start in range(0, int(duration), 16):
        phrase += _bright_idol_events(t, duration, float(phrase_start), events, gain)
    return phrase


def _bright_idol_events(
    t: float,
    duration: float,
    phrase_start: float,
    events: list[tuple[float, float, float, float, float]],
    gain: float,
) -> float:
    phrase = 0.0
    for start, freq, weight, phase, hold in events:
        event_start = phrase_start + start
        age = t - event_start
        if 0.0 <= age <= hold:
            attack = _smoothstep(min(age / 0.055, 1.0))
            release_start = hold * 0.42
            release = math.exp(-max(age - release_start, 0.0) * 2.15)
            vibrato = 0.018 * math.sin(TAU * 5.3 * age)
            env = attack * release
            base = _loop_freq(freq, duration)
            tone = math.sin(TAU * base * t + phase + vibrato)
            tone += 0.20 * math.sin(TAU * _loop_freq(freq * 2.0, duration) * t + phase * 0.5)
            tone += 0.10 * _soft_triangle(_loop_freq(freq * 0.5, duration), t)
            phrase += gain * weight * env * tone
    return phrase


def _bright_idol_sparkles(t: float, duration: float) -> float:
    phrase = 0.0
    for phrase_start in range(0, int(duration), 16):
        for start, freq, weight in BRIGHT_IDOL_SPARKLES:
            age = t - (phrase_start + start)
            if 0.0 <= age <= 3.2:
                env = math.exp(-age * 1.18) * _smoothstep(min(age / 0.050, 1.0))
                tone = math.sin(TAU * _loop_freq(freq, duration) * t)
                tone += 0.28 * math.sin(TAU * _loop_freq(freq * 2.0, duration) * t + 0.3)
                phrase += 0.019 * weight * env * tone
    return phrase


def _soft_pop_pulse(t: float, duration: float, gain: float) -> float:
    bar_pos = t % 4.0
    kick = _rounded_pulse(bar_pos, 0.14, 0.44) * math.sin(TAU * _loop_freq(55.0, duration) * t)
    lift = _rounded_pulse(bar_pos, 1.92, 0.38) * _det_noise(t, duration, 1500.0) * 0.36
    hats = 0.22 * (0.5 + 0.5 * math.sin(TAU * 2.0 * t)) * _det_noise(t, duration, 4700.0)
    return gain * (kick + lift + hats)


def _insert_mechanical_body(t: float, duration: float) -> float:
    scrape_env = _window(t, 0.00, 0.52)
    scrape = 0.040 * _det_noise(t, duration, 1800.0) * scrape_env
    plastic = 0.055 * _sine_hit(t, 0.10, 190.0, 20.0)
    rail = 0.045 * _sine_hit(t, 0.31, 260.0, 17.0)
    latch = 0.090 * _sine_hit(t, 0.58, 96.0, 13.0)
    latch += 0.040 * _sine_hit(t, 0.60, 830.0, 22.0)
    return scrape + plastic + rail + latch


def _insert_fries_fire_tail(t: float, duration: float) -> float:
    ember = 0.030 * math.sin(TAU * _loop_freq(43.0, duration) * t) * _window(t, 0.52, 2.65)
    ember += 0.020 * math.sin(TAU * _loop_freq(86.0, duration) * t + 0.8) * _window(t, 0.70, 2.45)
    crackle = 0.030 * _det_noise(t, duration, 3100.0) * _pulse_train(t, 0.74, 0.19, 8, 18.0)
    fall = _falling_tone(t, 0.70, 2.15, 740.0, 392.0, 0.045)
    bone_click = 0.030 * _sine_hit(t, 1.42, 1175.0, 28.0)
    return ember + crackle + fall + bone_click


def _insert_empty_crt_tail(t: float, duration: float) -> float:
    crt = 0.030 * math.sin(TAU * 60.0 * t) * _window(t, 0.45, 2.85)
    crt += 0.018 * math.sin(TAU * 15750.0 * t) * _window(t, 0.60, 2.30)
    stomach = 0.060 * _sine_hit(t, 0.88, 54.0, 3.7)
    stomach += 0.035 * _sine_hit(t, 1.55, 63.0, 4.4)
    prompt = 0.042 * _sine_hit(t, 1.12, 660.0, 7.5)
    prompt += 0.035 * _sine_hit(t, 1.48, 524.0, 7.5)
    room = 0.026 * _det_noise(t, duration, 900.0) * _window(t, 1.0, 2.75)
    return crt + stomach + prompt + room


def _insert_bbs_green_tail(t: float, duration: float) -> float:
    refresh = 0.040 * _det_noise(t, duration, 4200.0) * _pulse_train(t, 0.64, 0.115, 12, 24.0)
    bit_gate = 0.5 + 0.5 * math.sin(TAU * 31.0 * (t / duration))
    arpeggio = 0.0
    for start, freq in ((0.72, 523.25), (0.92, 659.25), (1.12, 783.99), (1.46, 1046.50)):
        arpeggio += 0.045 * _sine_hit(t, start, freq, 9.0)
    fail = 0.035 * _falling_tone(t, 1.72, 2.45, 1175.0, 698.0, 0.030)
    square = 0.026 * _soft_square(1318.51, t) * bit_gate * _window(t, 0.95, 2.35)
    return round((refresh + arpeggio + fail + square) * 18.0) / 18.0


BRIGHT_IDOL_CHORDS = [
    [(110.00, 0.34), (164.81, 0.24), (220.00, 0.20), (277.18, 0.16), (329.63, 0.12), (493.88, 0.06)],
    [(103.83, 0.31), (123.47, 0.22), (164.81, 0.20), (207.65, 0.15), (246.94, 0.11), (329.63, 0.07)],
    [(92.50, 0.32), (138.59, 0.24), (185.00, 0.20), (220.00, 0.16), (277.18, 0.11), (329.63, 0.07)],
    [(146.83, 0.30), (185.00, 0.20), (220.00, 0.18), (293.66, 0.16), (369.99, 0.10), (440.00, 0.06)],
]

BRIGHT_IDOL_BASS_PATTERN = [
    (0.00, 55.00, 0.82),
    (0.88, 82.41, 0.42),
    (1.52, 110.00, 0.36),
    (2.02, 103.83, 0.56),
    (3.10, 123.47, 0.34),
    (4.00, 46.25, 0.74),
    (4.82, 69.30, 0.38),
    (5.65, 92.50, 0.34),
    (6.38, 73.42, 0.46),
    (7.18, 110.00, 0.32),
]

BRIGHT_IDOL_LEAD = [
    (0.18, 659.25, 0.74, 0.00, 0.70),
    (0.72, 739.99, 0.62, 0.08, 0.58),
    (1.18, 830.61, 0.70, -0.06, 0.62),
    (1.72, 987.77, 0.76, 0.10, 0.74),
    (2.52, 880.00, 0.72, -0.04, 0.72),
    (3.18, 830.61, 0.54, 0.05, 0.52),
    (3.70, 739.99, 0.52, -0.08, 0.56),
    (4.38, 659.25, 0.66, 0.03, 0.82),
    (5.18, 880.00, 0.70, 0.04, 0.62),
    (5.72, 987.77, 0.66, -0.05, 0.58),
    (6.22, 1108.73, 0.78, 0.08, 0.86),
    (7.18, 987.77, 0.62, 0.02, 0.62),
    (8.38, 739.99, 0.60, -0.04, 0.58),
    (8.88, 830.61, 0.70, 0.06, 0.60),
    (9.38, 880.00, 0.72, -0.02, 0.76),
    (10.18, 987.77, 0.62, 0.08, 0.54),
    (10.72, 1108.73, 0.74, -0.05, 0.80),
    (11.72, 987.77, 0.58, 0.04, 0.60),
    (12.38, 880.00, 0.68, -0.07, 0.72),
    (13.12, 830.61, 0.52, 0.05, 0.52),
    (13.72, 739.99, 0.54, 0.00, 0.58),
    (14.38, 659.25, 0.78, 0.09, 1.18),
]

BRIGHT_IDOL_HARMONY = [
    (1.84, 659.25, 0.36, 0.15, 0.64),
    (2.64, 739.99, 0.32, -0.12, 0.58),
    (5.34, 659.25, 0.38, 0.10, 0.58),
    (6.34, 830.61, 0.42, -0.08, 0.76),
    (9.50, 659.25, 0.36, 0.18, 0.64),
    (10.84, 880.00, 0.40, -0.06, 0.72),
    (12.50, 739.99, 0.34, 0.08, 0.62),
    (14.52, 493.88, 0.42, 0.20, 1.02),
]

BRIGHT_IDOL_SPARKLES = [
    (0.06, 1318.51, 0.34),
    (3.92, 1479.98, 0.42),
    (6.00, 1760.00, 0.50),
    (7.82, 1975.53, 0.36),
    (10.04, 1661.22, 0.44),
    (14.12, 1318.51, 0.38),
]


DREAM_POP_TRACKS = {
    "lucent_slaps": {
        "chords": [
            [(110.00, 0.35), (164.81, 0.26), (220.00, 0.22), (277.18, 0.18), (329.63, 0.10)],
            [(130.81, 0.32), (196.00, 0.25), (246.94, 0.21), (329.63, 0.16), (392.00, 0.09)],
            [(98.00, 0.34), (146.83, 0.27), (196.00, 0.22), (293.66, 0.14), (392.00, 0.08)],
            [(123.47, 0.32), (185.00, 0.24), (246.94, 0.20), (311.13, 0.14), (369.99, 0.08)],
        ],
        "bass_pattern": [
            (0.00, 55.00, 0.80),
            (0.75, 82.41, 0.45),
            (1.50, 55.00, 0.58),
            (2.50, 73.42, 0.52),
            (4.00, 49.00, 0.72),
            (5.25, 73.42, 0.50),
            (6.25, 82.41, 0.42),
        ],
        "melody": [
            (0.80, 659.25, 0.70, 0.0),
            (1.60, 739.99, 0.62, 0.1),
            (2.45, 880.00, 0.58, -0.1),
            (4.00, 739.99, 0.50, 0.0),
            (6.50, 587.33, 0.60, 0.2),
            (8.25, 659.25, 0.52, -0.2),
            (11.80, 987.77, 0.45, 0.0),
            (13.10, 880.00, 0.42, 0.1),
        ],
        "shimmer_notes": [1174.66, 1318.51, 987.77],
        "melody_gain": 0.073,
        "shimmer_gain": 0.024,
        "bass_gain": 0.080,
        "drum_gain": 0.002,
        "noise_gain": 0.006,
        "harmony_ratio": 1.25,
        "breath_cycles": 3,
        "phase": 0.3,
        "width": 0.17,
    },
    "soft_orbit": {
        "chords": [
            [(73.42, 0.38), (110.00, 0.28), (146.83, 0.23), (220.00, 0.18), (293.66, 0.09)],
            [(87.31, 0.34), (130.81, 0.27), (174.61, 0.21), (261.63, 0.15), (349.23, 0.08)],
            [(98.00, 0.36), (146.83, 0.26), (196.00, 0.22), (246.94, 0.16), (392.00, 0.08)],
            [(82.41, 0.34), (123.47, 0.26), (164.81, 0.22), (246.94, 0.15), (329.63, 0.08)],
        ],
        "bass_pattern": [
            (0.00, 73.42, 0.84),
            (0.50, 110.00, 0.42),
            (1.25, 73.42, 0.58),
            (2.00, 98.00, 0.52),
            (3.25, 110.00, 0.48),
            (4.00, 65.41, 0.72),
            (5.00, 98.00, 0.54),
            (6.50, 87.31, 0.52),
        ],
        "melody": [
            (0.50, 587.33, 0.58, 0.0),
            (1.00, 659.25, 0.50, 0.2),
            (1.75, 783.99, 0.55, -0.1),
            (3.00, 880.00, 0.48, 0.0),
            (5.20, 739.99, 0.46, 0.1),
            (7.10, 659.25, 0.44, -0.2),
            (9.00, 987.77, 0.50, 0.0),
            (10.30, 880.00, 0.44, 0.2),
            (12.20, 783.99, 0.42, -0.1),
        ],
        "shimmer_notes": [1046.50, 1174.66, 1567.98],
        "melody_gain": 0.072,
        "shimmer_gain": 0.023,
        "bass_gain": 0.083,
        "drum_gain": 0.003,
        "noise_gain": 0.005,
        "harmony_ratio": 1.3333333333,
        "breath_cycles": 4,
        "phase": 1.1,
        "width": 0.14,
    },
    "afterimage_pool": {
        "chords": [
            [(92.50, 0.34), (138.59, 0.26), (185.00, 0.22), (277.18, 0.16), (369.99, 0.09)],
            [(103.83, 0.32), (155.56, 0.24), (207.65, 0.21), (311.13, 0.15), (415.30, 0.08)],
            [(87.31, 0.34), (130.81, 0.25), (196.00, 0.20), (261.63, 0.14), (392.00, 0.08)],
            [(98.00, 0.33), (146.83, 0.25), (174.61, 0.18), (293.66, 0.16), (349.23, 0.08)],
        ],
        "bass_pattern": [
            (0.00, 46.25, 0.80),
            (0.85, 69.30, 0.42),
            (1.70, 92.50, 0.44),
            (2.50, 51.91, 0.58),
            (4.00, 43.65, 0.70),
            (5.15, 65.41, 0.48),
            (6.35, 77.78, 0.42),
        ],
        "melody": [
            (1.10, 622.25, 0.56, 0.0),
            (2.00, 739.99, 0.52, -0.2),
            (2.90, 830.61, 0.48, 0.2),
            (5.50, 698.46, 0.46, 0.0),
            (7.40, 554.37, 0.42, 0.1),
            (10.00, 932.33, 0.45, -0.1),
            (12.40, 830.61, 0.40, 0.2),
            (14.10, 739.99, 0.36, 0.0),
        ],
        "shimmer_notes": [1244.51, 1396.91, 1108.73],
        "melody_gain": 0.070,
        "shimmer_gain": 0.026,
        "bass_gain": 0.078,
        "drum_gain": 0.002,
        "noise_gain": 0.009,
        "harmony_ratio": 1.20,
        "breath_cycles": 5,
        "phase": 2.4,
        "width": 0.22,
    },
}


def _dream_pop_pad(t: float, duration: float, chords: list[list[tuple[float, float]]]) -> float:
    pad = 0.0
    for chord_index, weight in _looping_chord_weights(t, duration, chords, 8.0, 1.4):
        for freq, gain in chords[chord_index]:
            wobble = 0.10 * math.sin(TAU * 3.0 * (t / duration) + freq * 0.01)
            pad += weight * gain * _soft_triangle(_loop_freq(freq + wobble, duration), t)
    return pad * 0.23


def _slap_bass_phrase(
    t: float,
    duration: float,
    pattern: list[tuple[float, float, float]],
    gain: float,
) -> float:
    phrase = 0.0
    bar_start = math.floor(t / 8.0) * 8.0
    for offset, freq, weight in pattern:
        phrase += _slap_bass_hit(t, bar_start + offset, _loop_freq(freq, duration), gain * weight)
    return phrase


def _slap_bass_hit(t: float, start: float, freq: float, gain: float) -> float:
    age = t - start
    if age < 0.0 or age > 0.75:
        return 0.0
    attack = _smoothstep(min(age / 0.040, 1.0))
    decay = math.exp(-age * 4.2)
    snap = math.exp(-age * 18.0)
    pitch = freq * (1.0 + 0.08 * math.exp(-age * 12.0))
    body = math.sin(TAU * pitch * t)
    body += 0.14 * _soft_square(pitch * 2.0, t)
    click = 0.035 * math.sin(TAU * _loop_freq(820.0, 96.0) * t) * snap
    return gain * attack * decay * (body + click)


def _dream_pop_melody(
    t: float,
    duration: float,
    events: list[tuple[float, float, float, float]],
    gain: float,
) -> float:
    phrase = 0.0
    for phrase_start in range(0, int(duration), 16):
        phrase += _dream_pop_events(t, duration, float(phrase_start), events, gain, 2.9)
    return phrase


def _dream_pop_harmony(
    t: float,
    duration: float,
    events: list[tuple[float, float, float, float]],
    gain: float,
    ratio: float,
) -> float:
    harmony_events = [(start + 0.18, freq * ratio, weight * 0.72, phase + 0.35) for start, freq, weight, phase in events]
    phrase = 0.0
    for phrase_start in range(8, int(duration), 16):
        phrase += _dream_pop_events(t, duration, float(phrase_start), harmony_events, gain, 2.2)
    return phrase


def _dream_pop_shimmer(t: float, duration: float, notes: list[float], gain: float) -> float:
    phrase = 0.0
    for index, freq in enumerate(notes):
        offset = 3.5 + index * 4.0
        for phrase_start in range(0, int(duration), 16):
            age = t - (phrase_start + offset)
            if 0.0 <= age <= 4.0:
                env = math.exp(-age * 0.85) * _smoothstep(min(age / 0.05, 1.0))
                phrase += gain * env * math.sin(TAU * _loop_freq(freq, duration) * t + index * 0.7)
    return phrase


def _dream_pop_events(
    t: float,
    duration: float,
    phrase_start: float,
    events: list[tuple[float, float, float, float]],
    gain: float,
    tail: float,
) -> float:
    phrase = 0.0
    for start, freq, weight, phase in events:
        age = t - (phrase_start + start)
        if 0.0 <= age <= tail:
            env = math.exp(-age * 1.05) * _smoothstep(min(age / 0.045, 1.0))
            tone = math.sin(TAU * _loop_freq(freq, duration) * t + phase)
            tone += 0.22 * math.sin(TAU * _loop_freq(freq * 2.0, duration) * t + phase * 0.5)
            phrase += gain * weight * env * tone
    return phrase


def _soft_dream_pulse(t: float, duration: float, gain: float) -> float:
    bar_pos = t % 4.0
    down = gain * 0.70 * _rounded_pulse(bar_pos, 0.18, 0.52) * math.sin(TAU * 58.0 * t)
    ghost = gain * 0.35 * _rounded_pulse(bar_pos, 2.35, 0.42) * math.sin(TAU * 86.0 * t + 0.4)
    return down + ghost


def _rounded_pulse(position: float, center: float, half_width: float) -> float:
    distance = abs(position - center)
    if distance >= half_width:
        return 0.0
    return 0.5 + 0.5 * math.cos(math.pi * distance / half_width)


def _light_dream_noise(t: float, duration: float, gain: float) -> float:
    loop = t / duration
    tape = 0.55 * _periodic_hiss(loop)
    air = 0.45 * math.sin(TAU * 11.0 * loop + 0.6) * math.sin(TAU * 1700.0 * loop)
    gate = 0.75 + 0.25 * math.sin(TAU * 7.0 * loop + 1.7)
    return gain * (tape + air) * gate


MAIN_CHORDS = [
    [(146.83, 0.55), (220.00, 0.40), (293.66, 0.32), (329.63, 0.20)],
    [(130.81, 0.44), (196.00, 0.35), (261.63, 0.30), (392.00, 0.16)],
    [(123.47, 0.42), (185.00, 0.36), (246.94, 0.25), (369.99, 0.14)],
    [(110.00, 0.48), (164.81, 0.32), (220.00, 0.28), (277.18, 0.16)],
]

CARTRIDGE_CHORDS = [
    [(98.00, 0.46), (146.83, 0.33), (196.00, 0.28), (293.66, 0.16)],
    [(87.31, 0.42), (130.81, 0.30), (174.61, 0.24), (261.63, 0.15)],
    [(103.83, 0.40), (155.56, 0.29), (207.65, 0.22), (311.13, 0.16)],
    [(92.50, 0.44), (138.59, 0.30), (185.00, 0.24), (277.18, 0.15)],
]


def _cyclic_chord_weights(
    t: float,
    duration: float,
    chords: list[list[tuple[float, float]]],
    crossfade: float,
) -> list[tuple[int, float]]:
    segment = duration / len(chords)
    pos = t % duration
    index = int(pos // segment)
    local = pos - index * segment
    next_index = (index + 1) % len(chords)

    if local >= segment - crossfade:
        blend = (local - (segment - crossfade)) / crossfade
        smooth = _smoothstep(blend)
        return [(index, 1.0 - smooth), (next_index, smooth)]
    return [(index, 1.0)]


def _looping_chord_weights(
    t: float,
    duration: float,
    chords: list[list[tuple[float, float]]],
    segment: float,
    crossfade: float,
) -> list[tuple[int, float]]:
    cycle = segment * len(chords)
    pos = t % cycle
    index = int(pos // segment)
    local = pos - index * segment
    next_index = (index + 1) % len(chords)
    if local >= segment - crossfade:
        blend = _smoothstep((local - (segment - crossfade)) / crossfade)
        return [(index, 1.0 - blend), (next_index, blend)]
    return [(index, 1.0)]


def _section_weights(t: float, duration: float, count: int, crossfade: float) -> list[float]:
    segment = duration / count
    pos = t % duration
    index = int(pos // segment)
    local = pos - index * segment
    weights = [0.0] * count
    weights[index] = 1.0
    if local >= segment - crossfade:
        blend = _smoothstep((local - (segment - crossfade)) / crossfade)
        weights[index] = 1.0 - blend
        weights[(index + 1) % count] = blend
    return weights


def _main_title_motif(t: float, duration: float) -> float:
    phrase = 0.0
    events = [
        (1.00, 587.33, 0.050, -0.2),
        (1.50, 739.99, 0.052, 0.1),
        (2.25, 659.25, 0.044, 0.0),
        (3.00, 493.88, 0.040, 0.2),
        (5.50, 880.00, 0.038, -0.1),
        (6.25, 783.99, 0.035, 0.25),
        (9.00, 659.25, 0.030, -0.25),
        (10.25, 987.77, 0.034, 0.0),
    ]
    for phrase_start in (0.0, 16.0, 32.0, 48.0):
        phrase += _bell_events(t, duration, phrase_start, events, 2.8)
    return phrase


def _fries_fire_motif(t: float, duration: float) -> float:
    phrase = 0.0
    events = [
        (1.00, 783.99, 0.044, 0.0),
        (1.65, 659.25, 0.042, 0.2),
        (2.35, 587.33, 0.040, -0.1),
        (3.00, 493.88, 0.035, 0.1),
        (5.75, 698.46, 0.032, 0.0),
        (6.00, 523.25, 0.022, 0.3),
    ]
    for phrase_start in (0.0, 12.0):
        phrase += _bell_events(t, duration, phrase_start, events, 2.3)
    flame = 0.018 * math.sin(TAU * _loop_freq(31.0, duration) * t) * (0.5 + 0.5 * _lfo(t / duration, 12))
    return phrase + flame


def _empty_stomach_crt_motif(t: float, duration: float) -> float:
    events = [
        (24.50, 440.00, 0.034, 0.0),
        (26.00, 392.00, 0.030, 0.2),
        (29.00, 523.25, 0.026, -0.2),
        (32.75, 329.63, 0.030, 0.1),
        (36.00, 493.88, 0.024, 0.0),
        (41.25, 392.00, 0.026, 0.3),
    ]
    pulse = 0.018 * _soft_sine(_loop_freq(65.41, duration), t, t / duration, 6)
    return _bell_events(t, duration, 0.0, events, 3.8) + pulse


def _bbs_refresh_motif(t: float, duration: float) -> float:
    phrase = 0.0
    events = [
        (48.40, 659.25, 0.025, 0.1),
        (48.70, 739.99, 0.026, 0.3),
        (49.00, 880.00, 0.028, -0.2),
        (50.40, 987.77, 0.030, 0.0),
        (52.00, 739.99, 0.024, 0.2),
        (53.50, 1174.66, 0.026, -0.1),
        (58.25, 880.00, 0.022, 0.0),
        (60.00, 1318.51, 0.020, 0.25),
    ]
    phrase += _bell_events(t, duration, 0.0, events, 1.6)
    square = 0.018 * _soft_square(_loop_freq(1046.50, duration), t)
    gate = 0.5 + 0.5 * math.sin(TAU * 36.0 * (t / duration))
    return phrase + square * gate


def _selection_shared_motif(t: float, duration: float) -> float:
    events = [
        (8.00, 587.33, 0.018, 0.0),
        (18.50, 493.88, 0.018, 0.1),
        (31.00, 659.25, 0.018, -0.1),
        (44.00, 523.25, 0.018, 0.2),
        (64.00, 739.99, 0.016, 0.0),
    ]
    return _bell_events(t, duration, 0.0, events, 4.2)


def _bell_events(
    t: float,
    duration: float,
    phrase_start: float,
    events: list[tuple[float, float, float, float]],
    tail: float,
) -> float:
    phrase = 0.0
    for start, freq, gain, phase in events:
        event_start = phrase_start + start
        age = t - event_start
        if 0.0 <= age <= tail:
            env = math.exp(-age * 1.55) * _smoothstep(min(age / 0.06, 1.0))
            tone = math.sin(TAU * _loop_freq(freq, duration) * t + phase)
            tone += 0.35 * math.sin(TAU * _loop_freq(freq * 2.01, duration) * t + phase * 0.5)
            phrase += gain * env * tone
    return phrase


def _transition_boot_chirps(t: float) -> float:
    events = [
        (0.42, 587.33, 0.060, 0.40),
        (0.78, 783.99, 0.055, 0.36),
        (1.24, 987.77, 0.050, 0.28),
        (2.05, 659.25, 0.045, 0.42),
        (2.46, 440.00, 0.038, 0.35),
    ]
    phrase = 0.0
    for start, freq, gain, tail in events:
        age = t - start
        if 0.0 <= age <= tail:
            env = math.exp(-age * 4.8) * _smoothstep(min(age / 0.025, 1.0))
            tone = math.sin(TAU * freq * t) + 0.4 * _soft_square(freq * 2.0, t)
            phrase += gain * env * tone
    return phrase


def _sine_hit(t: float, start: float, freq: float, decay: float) -> float:
    age = t - start
    if age < 0.0:
        return 0.0
    env = math.exp(-age * decay) * _smoothstep(min(age / 0.02, 1.0))
    return math.sin(TAU * freq * t) * env


def _falling_tone(t: float, start: float, end: float, high: float, low: float, gain: float) -> float:
    if t < start or t > end:
        return 0.0
    local = (t - start) / (end - start)
    freq = high + (low - high) * _smoothstep(local)
    env = math.sin(math.pi * local) ** 0.55
    return gain * math.sin(TAU * freq * t) * env


def _det_noise(t: float, duration: float, base: float) -> float:
    loop = t / duration
    value = 0.0
    value += 0.55 * math.sin(TAU * (base * 0.97) * loop + 0.3)
    value += 0.34 * math.sin(TAU * (base * 1.71) * loop + 2.1)
    value += 0.25 * math.sin(TAU * (base * 2.43) * loop + 4.4)
    value += 0.17 * math.sin(TAU * (base * 3.19) * loop + 1.2)
    return round(value * 14.0) / 14.0


def _pulse_train(t: float, start: float, interval: float, count: int, decay: float) -> float:
    value = 0.0
    for index in range(count):
        value += math.exp(-max(t - (start + index * interval), 0.0) * decay) if t >= start + index * interval else 0.0
    return min(value, 1.0)


def _window(t: float, start: float, end: float) -> float:
    if t < start or t > end:
        return 0.0
    attack = _smoothstep(min((t - start) / 0.08, 1.0))
    release = 1.0 - _smoothstep(max((t - end + 0.18) / 0.18, 0.0))
    return attack * release


def _periodic_hiss(loop: float) -> float:
    raw = 0.0
    raw += 0.50 * math.sin(TAU * 731.0 * loop + 0.3)
    raw += 0.32 * math.sin(TAU * 1459.0 * loop + 2.0)
    raw += 0.24 * math.sin(TAU * 2879.0 * loop + 1.1)
    raw += 0.16 * math.sin(TAU * 4093.0 * loop + 4.4)
    gate = 0.45 + 0.55 * (0.5 + 0.5 * math.sin(TAU * 23.0 * loop + 1.6))
    return round(raw * gate * 12.0) / 12.0


def _stereoize(sample: float, t: float, duration: float, width: float) -> tuple[float, float]:
    loop = t / duration
    pan = width * math.sin(TAU * 5.0 * loop) + 0.05 * math.sin(TAU * 13.0 * loop)
    left = sample * (1.0 - pan)
    right = sample * (1.0 + pan)
    return left, right


def _soft_sine(freq: float, t: float, loop: float, lfo_cycles: int) -> float:
    wobble = 0.08 * math.sin(TAU * lfo_cycles * loop)
    return math.sin(TAU * freq * t + wobble)


def _soft_triangle(freq: float, t: float) -> float:
    sine = math.sin(TAU * freq * t)
    third = math.sin(TAU * freq * 3.0 * t) / 9.0
    return sine - third


def _soft_square(freq: float, t: float) -> float:
    return math.tanh(math.sin(TAU * freq * t) * 4.0)


def _pitch_sweep(t: float, start_freq: float, end_freq: float, progress: float) -> float:
    freq = start_freq + (end_freq - start_freq) * _smoothstep(progress)
    phase = TAU * (start_freq * t + (end_freq - start_freq) * progress * t * 0.35)
    return math.sin(phase) * (0.7 + 0.3 * math.sin(TAU * freq * t))


def _loop_freq(freq: float, duration: float) -> float:
    return round(freq * duration) / duration


def _lfo(loop: float, cycles: int, phase: float = 0.0) -> float:
    return math.sin(TAU * cycles * loop + phase)


def _smoothstep(value: float) -> float:
    x = max(0.0, min(1.0, value))
    return x * x * (3.0 - 2.0 * x)


def _to_i16(value: float) -> int:
    clipped = max(-0.98, min(0.98, value))
    return int(clipped * 32767)


if __name__ == "__main__":
    main()
