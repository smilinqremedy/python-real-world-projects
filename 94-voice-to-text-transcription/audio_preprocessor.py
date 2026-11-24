"""
Audio Preprocessing, Validation, Silence Gating, and Normalization Module.
Decodes 16-bit PCM WAV natively, performs RMS silence suppression,
and interfaces with external decoders (pydub/ffmpeg) for MP3/FLAC/OGG.
"""
import os
import wave
import struct
import math
import numpy as np
from typing import Tuple, Dict, Any, Optional

SUPPORTED_AUDIO_EXTS = {".wav", ".mp3", ".ogg", ".flac", ".m4a"}


class AudioValidationError(Exception):
    """Raised when an audio recording is corrupted, empty, or unsupported."""
    pass


class AudioPreprocessor:
    def __init__(self, target_sample_rate: int = 16000):
        self.target_sample_rate = target_sample_rate

    def validate_file(self, file_path: str) -> None:
        """Validates file existence, non-zero size, and recognized extension."""
        if not os.path.exists(file_path):
            raise AudioValidationError(f"Audio file not found: {file_path}")
        if os.path.getsize(file_path) == 0:
            raise AudioValidationError(f"Audio file is empty (0 bytes): {file_path}")
        _, ext = os.path.splitext(file_path.lower())
        if ext not in SUPPORTED_AUDIO_EXTS:
            raise AudioValidationError(
                f"Unsupported format '{ext}'. Supported: {', '.join(sorted(SUPPORTED_AUDIO_EXTS))}"
            )

    def load_wav(self, file_path: str) -> Tuple[np.ndarray, int]:
        """
        Natively loads a PCM WAV file without requiring heavy C libraries.
        Returns normalized float32 samples in range [-1.0, 1.0] and sample rate.
        """
        self.validate_file(file_path)
        try:
            with wave.open(file_path, "rb") as wf:
                n_channels = wf.getnchannels()
                sampwidth = wf.getsampwidth()
                framerate = wf.getframerate()
                n_frames = wf.getnframes()
                raw_bytes = wf.readframes(n_frames)

            if n_frames == 0 or len(raw_bytes) == 0:
                raise AudioValidationError("Audio file contains no frames (silent/empty).")

            # Parse 16-bit signed PCM
            if sampwidth == 2:
                total_samples = n_frames * n_channels
                samples = struct.unpack(f"<{total_samples}h", raw_bytes)
                arr = np.array(samples, dtype=np.float32) / 32768.0
            elif sampwidth == 1:
                # 8-bit unsigned PCM
                samples = np.frombuffer(raw_bytes, dtype=np.uint8).astype(np.float32)
                arr = (samples - 128.0) / 128.0
            else:
                samples = np.frombuffer(raw_bytes, dtype=np.int32).astype(np.float32)
                arr = samples / 2147483648.0

            # Convert stereo to mono by averaging channels
            if n_channels > 1:
                arr = arr.reshape(-1, n_channels).mean(axis=1)

            return arr, framerate

        except wave.Error as e:
            # Fallback for MP3 or non-standard WAV using external pydub if installed
            return self._load_via_pydub_fallback(file_path)
        except Exception as e:
            raise AudioValidationError(f"Failed to decode audio: {str(e)}")

    def _load_via_pydub_fallback(self, file_path: str) -> Tuple[np.ndarray, int]:
        try:
            from pydub import AudioSegment
            seg = AudioSegment.from_file(file_path)
            seg = seg.set_frame_rate(self.target_sample_rate).set_channels(1)
            raw = np.array(seg.get_array_of_samples(), dtype=np.float32)
            max_val = float(2**(seg.sample_width * 8 - 1))
            return raw / max_val, seg.frame_rate
        except Exception:
            raise AudioValidationError(
                f"Cannot decode compressed audio '{file_path}'. Standard PCM WAV is natively supported; install pydub+ffmpeg for MP3/FLAC."
            )

    def suppress_silence(
        self,
        samples: np.ndarray,
        sample_rate: int,
        frame_ms: int = 30,
        threshold_db: float = -45.0
    ) -> np.ndarray:
        """
        Gating filter that removes leading and trailing silence based on RMS energy.
        """
        if len(samples) == 0:
            return samples

        frame_size = int(sample_rate * (frame_ms / 1000.0))
        if frame_size <= 0 or len(samples) < frame_size:
            return samples

        n_frames = len(samples) // frame_size
        rms_values = []
        for i in range(n_frames):
            frame = samples[i * frame_size:(i + 1) * frame_size]
            rms = np.sqrt(np.mean(frame**2) + 1e-9)
            db = 20.0 * np.log10(rms)
            rms_values.append(db)

        # Identify non-silent start and end frame indices
        active_indices = [i for i, db in enumerate(rms_values) if db > threshold_db]
        if not active_indices:
            # All frames below threshold
            return samples

        start_sample = active_indices[0] * frame_size
        end_sample = min(len(samples), (active_indices[-1] + 1) * frame_size)
        return samples[start_sample:end_sample]

    @staticmethod
    def generate_synthetic_speech_wav(
        file_path: str,
        duration_sec: float = 2.0,
        sample_rate: int = 16000,
        base_freq: float = 220.0
    ) -> str:
        """
        Generates a valid 16-bit PCM WAV audio file with harmonic formant frequencies.
        Used for automated tests and offline demonstrations.
        """
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        t = np.linspace(0, duration_sec, int(sample_rate * duration_sec), endpoint=False)
        # Fundamental tone + speech formant harmonics (F1, F2)
        signal = 0.5 * np.sin(2 * np.pi * base_freq * t)
        signal += 0.3 * np.sin(2 * np.pi * (base_freq * 2.5) * t)
        signal += 0.2 * np.sin(2 * np.pi * (base_freq * 3.8) * t)

        # Apply amplitude envelope (syllable modulation)
        envelope = 0.5 * (1.0 + np.sin(2 * np.pi * 3.0 * t))
        audio = signal * envelope

        # Convert to 16-bit PCM integers
        pcm16 = (audio * 32767.0).astype(np.int16)

        with wave.open(file_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(pcm16.tobytes())

        return file_path
