#!/usr/bin/env python3
"""One-shot Parler-TTS Tiny voice designer for Ashen Voice Studio.

Reads one JSON request from stdin and returns JSON containing several WAV candidates.
The model loads once per design session, then generates all requested candidates.
"""
from __future__ import annotations

import base64
import io
import json
import os
import sys
import traceback
import wave

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("OMP_NUM_THREADS", "2")
os.environ.setdefault("MKL_NUM_THREADS", "2")

MODEL_ID = "parler-tts/parler-tts-tiny-v1"


def wav_bytes(samples, sample_rate: int) -> bytes:
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


def build_description(req: dict) -> str:
    free = str(req.get("description") or "").strip()
    parts = []
    if free:
        parts.append(free.rstrip(". "))

    gender = str(req.get("gender") or "").strip()
    age = str(req.get("age") or "").strip()
    accent = str(req.get("accent") or "").strip()
    pitch = str(req.get("pitch") or "").strip()
    texture = str(req.get("texture") or "").strip()
    pace = str(req.get("pace") or "").strip()
    volume = str(req.get("volume") or "").strip()
    energy = str(req.get("energy") or "").strip()

    traits = []
    if age and age.lower() != "unspecified":
        traits.append(age)
    if gender and gender.lower() != "unspecified":
        traits.append(gender)
    if traits:
        parts.append("The speaker is " + " ".join(traits))
    if accent and accent.lower() != "unspecified":
        parts.append(f"The speaker has a {accent} accent")
    if pitch and pitch.lower() != "unspecified":
        parts.append(f"The voice has a {pitch} pitch")
    if texture and texture.lower() != "unspecified":
        parts.append(f"The vocal timbre is {texture}")
    if pace and pace.lower() != "unspecified":
        parts.append(f"The speaking rate is {pace}")
    if volume and volume.lower() != "unspecified":
        parts.append(f"The delivery volume is {volume}")
    if energy and energy.lower() != "unspecified":
        parts.append(f"The delivery energy is {energy}")

    # Parler's own model card recommends this phrase for clean output.
    parts.append("The recording is very clear audio, close-miked, with no background noise")
    return ". ".join(p.strip(". ") for p in parts if p.strip()) + "."


def main() -> int:
    try:
        req = json.loads(sys.stdin.read() or "{}")
        text = str(req.get("text") or "This is the voice I will use throughout the story.").strip()
        count = max(1, min(6, int(req.get("count") or 4)))
        seed = int(req.get("seed") or 4400)
        description = build_description(req)

        import torch
        from parler_tts import ParlerTTSForConditionalGeneration
        from transformers import AutoTokenizer

        torch.set_num_threads(max(1, min(2, os.cpu_count() or 1)))
        device = "cpu"
        model = ParlerTTSForConditionalGeneration.from_pretrained(MODEL_ID).to(device)
        tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
        input_ids = tokenizer(description, return_tensors="pt").input_ids.to(device)
        prompt_ids = tokenizer(text, return_tensors="pt").input_ids.to(device)

        candidates = []
        with torch.inference_mode():
            for i in range(count):
                candidate_seed = seed + i * 997
                torch.manual_seed(candidate_seed)
                generation = model.generate(
                    input_ids=input_ids,
                    prompt_input_ids=prompt_ids,
                )
                audio = generation.detach().cpu().numpy().squeeze()
                wav = wav_bytes(audio, int(model.config.sampling_rate))
                candidates.append({
                    "id": i + 1,
                    "seed": candidate_seed,
                    "wav_b64": base64.b64encode(wav).decode("ascii"),
                })

        sys.stdout.write(json.dumps({
            "ok": True,
            "model": MODEL_ID,
            "description": description,
            "candidates": candidates,
        }, separators=(",", ":")))
        return 0
    except Exception as exc:
        sys.stdout.write(json.dumps({
            "ok": False,
            "error": str(exc),
            "detail": traceback.format_exc(limit=10),
        }, separators=(",", ":")))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
