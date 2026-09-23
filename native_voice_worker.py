#!/usr/bin/env python3
"""Ashen Voice Studio native TTS worker.

Persistent JSON-lines worker used by the Tauri/Rust bridge. Models are loaded lazily
and kept in memory so chapter generation does not reload a model for every line.

Supported engines:
  kitten  - KittenTTS local CPU model
  piper   - Piper local ONNX voices
  lux     - LuxTTS local zero-shot voice cloning
"""
from __future__ import annotations

import base64
import importlib.util
import inspect
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import traceback
import wave

APP_HOME = Path(os.environ.get("ASHEN_VOICE_HOME", Path.home() / ".local" / "share" / "ashen-voice-studio"))
CACHE_DIR = APP_HOME / "cache"
PIPER_DIR = APP_HOME / "piper"
LUX_DIR = APP_HOME / "LuxTTS"
REF_DIR = APP_HOME / "voice-references"
for d in (APP_HOME, CACHE_DIR, PIPER_DIR, REF_DIR):
    d.mkdir(parents=True, exist_ok=True)

# If LuxTTS was cloned by our installer, make its zipvoice package importable.
if LUX_DIR.exists() and str(LUX_DIR) not in sys.path:
    sys.path.insert(0, str(LUX_DIR))

kitten_models: dict[str, object] = {}
piper_voices: dict[str, object] = {}
lux_model = None
lux_prompts: dict[str, object] = {}
chatterbox_model = None
chatterbox_prompts: dict[str, Path] = {}


def installed(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except Exception:
        return False


def status_payload() -> dict:
    chatterbox_available = installed("chatterbox")
    lux_available = installed("zipvoice") or LUX_DIR.exists()
    return {
        "ok": True,
        "engines": {
            "kitten": {"available": installed("kittentts"), "label": "KittenTTS"},
            "piper": {"available": installed("piper"), "label": "Piper"},
            "lux": {"available": lux_available, "label": "LuxTTS"},
            "chatterbox": {"available": chatterbox_available, "label": "Chatterbox"},
        },
        "paths": {
            "home": str(APP_HOME),
            "piper": str(PIPER_DIR),
            "lux": str(LUX_DIR),
        },
    }


def wav_bytes_from_float(samples, sample_rate: int) -> bytes:
    """Write mono float samples to 16-bit PCM WAV without requiring soundfile."""
    import numpy as np

    arr = np.asarray(samples, dtype=np.float32).reshape(-1)
    arr = np.clip(arr, -1.0, 1.0)
    pcm = (arr * 32767.0).astype("<i2").tobytes()
    out = io.BytesIO()
    with wave.open(out, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(int(sample_rate))
        wf.writeframes(pcm)
    return out.getvalue()


def load_kitten(model_id: str):
    if model_id in kitten_models:
        return kitten_models[model_id]
    from kittentts import KittenTTS

    model = KittenTTS(model_id, cache_dir=str(CACHE_DIR / "kitten"))
    kitten_models[model_id] = model
    return model


def synth_kitten(req: dict) -> bytes:
    model_id = req.get("model") or "KittenML/kitten-tts-nano-0.8"
    voice = req.get("voice") or "Jasper"
    speed = float(req.get("speed") or 1.0)
    model = load_kitten(model_id)
    audio = model.generate(str(req.get("text") or ""), voice=voice, speed=speed)
    return wav_bytes_from_float(audio, 24000)


def piper_model_path(voice_id: str) -> Path:
    # piper.download_voices normally writes <voice>.onnx + <voice>.onnx.json.
    direct = PIPER_DIR / f"{voice_id}.onnx"
    if direct.exists():
        return direct
    # Also accept a full model path for advanced users.
    p = Path(voice_id).expanduser()
    if p.exists() and p.suffix == ".onnx":
        return p
    raise FileNotFoundError(
        f"Piper voice '{voice_id}' is not installed. Expected {direct}. "
        "Run scripts/install-native-engines.sh to install the default voice."
    )


def load_piper(voice_id: str):
    path = piper_model_path(voice_id)
    key = str(path.resolve())
    if key in piper_voices:
        return piper_voices[key]
    from piper import PiperVoice

    voice = PiperVoice.load(str(path), use_cuda=False)
    piper_voices[key] = voice
    return voice


def synth_piper(req: dict) -> bytes:
    from piper import SynthesisConfig

    voice_id = req.get("voice") or "en_US-lessac-medium"
    voice = load_piper(voice_id)
    speed = max(0.5, min(1.6, float(req.get("speed") or 1.0)))
    intensity = max(0.0, min(1.0, float(req.get("emotion_intensity") or 0.0)))
    emotion = str(req.get("emotion") or "neutral")

    # Preserve voice identity. Emotion only nudges pacing/variation; it never changes
    # the speaker model. The ranges are intentionally narrow for audiobook consistency.
    variation = {
        "neutral": 0.00,
        "solemn": -0.05,
        "tense": 0.05,
        "urgent": 0.08,
        "fearful": 0.07,
        "grief": -0.04,
        "angry": 0.06,
        "intimate": -0.05,
        "deadpan": -0.08,
        "ominous": -0.06,
        "whispered": -0.07,
    }.get(emotion, 0.0) * intensity

    cfg = SynthesisConfig(
        length_scale=1.0 / speed,
        noise_scale=max(0.45, min(0.85, 0.667 + variation)),
        noise_w_scale=max(0.55, min(0.95, 0.8 + variation)),
        normalize_audio=True,
    )
    out = io.BytesIO()
    # wave.open accepts a file-like object.
    with wave.open(out, "wb") as wf:
        voice.synthesize_wav(str(req.get("text") or ""), wf, syn_config=cfg)
    return out.getvalue()



def load_chatterbox():
    global chatterbox_model
    if chatterbox_model is not None:
        return chatterbox_model
    try:
        from chatterbox.tts import ChatterboxTTS
    except Exception as e:
        raise RuntimeError("Chatterbox is not installed. Run scripts/install-native-engines.sh --with-chatterbox.") from e
    import torch
    device = "cuda" if torch.cuda.is_available() else ("mps" if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available() else "cpu")
    chatterbox_model = ChatterboxTTS.from_pretrained(device=device)
    return chatterbox_model


def chatterbox_reference_path(req: dict) -> tuple[str, Path]:
    character_id = str(req.get("character_id") or "character")
    safe_id = "".join(ch for ch in character_id if ch.isalnum() or ch in "-_.") or "character"
    data_b64 = req.get("reference_audio_b64")
    if data_b64:
        name = str(req.get("reference_name") or "reference.wav")
        ext = Path(name).suffix.lower() or ".wav"
        path = save_reference(safe_id, data_b64, ext)
        chatterbox_prompts[safe_id] = path
        return safe_id, path
    if safe_id in chatterbox_prompts and chatterbox_prompts[safe_id].exists():
        return safe_id, chatterbox_prompts[safe_id]
    matches = sorted(REF_DIR.glob(f"{safe_id}.*"))
    if matches:
        chatterbox_prompts[safe_id] = matches[0]
        return safe_id, matches[0]
    raise RuntimeError("Chatterbox needs a reference recording for this character.")


def synth_chatterbox(req: dict) -> bytes:
    model = load_chatterbox()
    key, ref_path = chatterbox_reference_path(req)
    import torch
    seed = req.get("seed")
    if seed not in (None, "", 0, "0"):
        seed = int(seed)
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)

    emotion = str(req.get("emotion") or "neutral").lower()
    intensity = max(0.0, min(1.0, float(req.get("emotion_intensity") or 0.7)))
    base_exaggeration = {
        "neutral": 0.50, "solemn": 0.42, "tense": 0.62, "urgent": 0.72,
        "fearful": 0.72, "grief": 0.58, "angry": 0.86, "intimate": 0.46,
        "deadpan": 0.36, "ominous": 0.66, "whispered": 0.40,
    }.get(emotion, 0.50)
    exaggeration = max(0.25, min(1.10, base_exaggeration + (intensity - 0.7) * 0.45))
    delivery = str(req.get("delivery") or "natural")
    cfg = {
        "natural": 0.50, "controlled": 0.42, "urgent": 0.32,
        "clipped": 0.28, "hesitant": 0.38, "soft": 0.46, "commanding": 0.40,
    }.get(delivery, 0.50)
    cfg = max(0.20, min(0.75, cfg))
    kwargs = {
        "audio_prompt_path": str(ref_path),
        "exaggeration": exaggeration,
        "cfg_weight": cfg,
        "temperature": max(0.55, min(1.0, 0.72 + (0.08 * intensity))),
        "min_p": 0.05,
        "top_p": 1.0,
        "repetition_penalty": 1.2,
    }
    try:
        audio = model.generate(str(req.get("text") or ""), **kwargs)
    except TypeError:
        kwargs.pop("min_p", None)
        kwargs.pop("top_p", None)
        kwargs.pop("repetition_penalty", None)
        audio = model.generate(str(req.get("text") or ""), **kwargs)
    if hasattr(audio, "detach"):
        audio = audio.detach()
    if hasattr(audio, "cpu"):
        audio = audio.cpu()
    if hasattr(audio, "numpy"):
        audio = audio.numpy()
    return wav_bytes_from_float(audio, int(model.sr))


def load_lux():
    global lux_model
    if lux_model is not None:
        return lux_model
    try:
        from zipvoice.luxvoice import LuxTTS
    except Exception as e:
        raise RuntimeError(
            "LuxTTS is not installed. Run scripts/install-native-engines.sh --with-lux first."
        ) from e
    lux_model = LuxTTS("YatharthS/LuxTTS", device="cpu", threads=2)
    return lux_model


def save_reference(character_id: str, data_b64: str, ext: str = ".wav") -> Path:
    raw = base64.b64decode(data_b64)
    safe_id = "".join(ch for ch in character_id if ch.isalnum() or ch in "-_.") or "character"
    ext = ext if ext.startswith(".") else f".{ext}"
    if len(ext) > 6:
        ext = ".wav"
    path = REF_DIR / f"{safe_id}{ext}"
    path.write_bytes(raw)
    # A new recording means the cached prompt must be re-encoded.
    lux_prompts.pop(safe_id, None)
    return path


def lux_reference_path(req: dict) -> tuple[str, Path]:
    character_id = str(req.get("character_id") or "character")
    safe_id = "".join(ch for ch in character_id if ch.isalnum() or ch in "-_.") or "character"
    data_b64 = req.get("reference_audio_b64")
    if data_b64:
        name = str(req.get("reference_name") or "reference.wav")
        ext = Path(name).suffix.lower() or ".wav"
        path = save_reference(safe_id, data_b64, ext)
        return safe_id, path
    matches = sorted(REF_DIR.glob(f"{safe_id}.*"))
    if matches:
        return safe_id, matches[0]
    raise RuntimeError("LuxTTS needs a reference recording for this character.")


def synth_lux(req: dict) -> bytes:
    model = load_lux()
    key, ref_path = lux_reference_path(req)
    prompt = lux_prompts.get(key)
    if prompt is None:
        prompt = model.encode_prompt(str(ref_path), rms=0.01)
        lux_prompts[key] = prompt

    text = str(req.get("text") or "")
    kwargs = {"num_steps": int(req.get("lux_steps") or 4)}
    # Newer Lux builds/community wrappers expose speed. Pass it only when supported,
    # avoiding breakage on versions whose official API does not yet include it.
    try:
        sig = inspect.signature(model.generate_speech)
        if "speed" in sig.parameters:
            kwargs["speed"] = float(req.get("speed") or 1.0)
        if "return_smooth" in sig.parameters:
            kwargs["return_smooth"] = True
    except Exception:
        pass

    audio = model.generate_speech(text, prompt, **kwargs)
    if hasattr(audio, "detach"):
        audio = audio.detach()
    if hasattr(audio, "cpu"):
        audio = audio.cpu()
    if hasattr(audio, "numpy"):
        audio = audio.numpy()
    return wav_bytes_from_float(audio, 48000)


def synthesize(req: dict) -> bytes:
    engine = str(req.get("engine") or "kitten").lower()
    text = str(req.get("text") or "").strip()
    if not text:
        raise ValueError("No text provided")
    if engine == "kitten":
        return synth_kitten(req)
    if engine == "piper":
        return synth_piper(req)
    if engine == "lux":
        return synth_lux(req)
    if engine == "chatterbox":
        return synth_chatterbox(req)
    raise ValueError(f"Unknown native TTS engine: {engine}")


def handle(req: dict) -> dict:
    op = req.get("op") or "synthesize"
    if op == "status":
        return status_payload()
    if op == "reset":
        kitten_models.clear()
        piper_voices.clear()
        lux_prompts.clear()
        chatterbox_prompts.clear()
        global lux_model, chatterbox_model
        lux_model = None
        chatterbox_model = None
        return {"ok": True}
    wav = synthesize(req)
    return {
        "ok": True,
        "engine": req.get("engine") or "kitten",
        "wav_b64": base64.b64encode(wav).decode("ascii"),
    }


def main() -> int:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            result = handle(req)
        except Exception as e:
            result = {
                "ok": False,
                "error": str(e),
                "detail": traceback.format_exc(limit=8),
            }
        sys.stdout.write(json.dumps(result, separators=(",", ":")) + "\n")
        sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
