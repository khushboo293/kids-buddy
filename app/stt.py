import os
from typing import Optional, Tuple
from faster_whisper import WhisperModel

_model_cache = {}

def load_model(size: str = "small") -> WhisperModel:
    if size not in _model_cache:
        _model_cache[size] = WhisperModel(size, device="auto", compute_type="default")
    return _model_cache[size]

def transcribe(audio_path: str, model_size: str = "small") -> Tuple[str, Optional[float]]:
    model = load_model(model_size)
    segments, info = model.transcribe(audio_path, beam_size=1)
    texts = []
    for seg in segments:
        texts.append(seg.text.strip())
    text = " ".join(t for t in texts if t)
    return text.strip(), None
