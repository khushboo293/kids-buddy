from typing import Deque
from collections import deque
import av
import numpy as np
import soundfile as sf
from streamlit_webrtc import WebRtcMode, webrtc_streamer

def record_audio_session(key: str = "stt_webrtc"):
    audio_frames: Deque[av.AudioFrame] = deque(maxlen=2000)

    def callback(frame: av.AudioFrame):
        audio_frames.append(frame)
        return frame

    ctx = webrtc_streamer(
        key=key,
        mode=WebRtcMode.SENDONLY,
        audio_receiver_size=1024,
        media_stream_constraints={"audio": True, "video": False},
        async_processing=True,
        sendback_audio=False
    )

    wav_path = None
    if ctx.state.playing is False and len(audio_frames) > 0:
        samples = []
        sample_rate = None
        while audio_frames:
            f = audio_frames.popleft()
            arr = f.to_ndarray()
            if arr.ndim > 1:
                arr = arr.mean(axis=0)
            samples.append(arr.astype(np.float32) / 32768.0 if arr.dtype == np.int16 else arr.astype(np.float32))
            if sample_rate is None:
                sample_rate = f.sample_rate
        if samples and sample_rate:
            audio = np.concatenate(samples, axis=0)
            wav_path = "/mnt/data/webrtc_recording.wav"
            sf.write(wav_path, audio, sample_rate)
    return ctx, wav_path
