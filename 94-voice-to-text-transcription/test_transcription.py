"""
Automated unit tests for Voice-to-Text Transcription System.
"""
import unittest
import os
import shutil
import tempfile
import json
import numpy as np

from audio_preprocessor import AudioPreprocessor, AudioValidationError
from speech_recognizer import SpeechRecognizer, TranscriptionResult, TranscriptSegment
from metrics import compute_wer, compute_cer, levenshtein_distance
from transcript_exporter import TranscriptExporter, format_srt_timestamp


class TestVoiceToTextTranscription(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.preprocessor = AudioPreprocessor(target_sample_rate=16000)
        self.recognizer = SpeechRecognizer()

        # Generate a synthetic PCM WAV file for testing
        self.sample_wav = os.path.join(self.test_dir, "test_audio.wav")
        AudioPreprocessor.generate_synthetic_speech_wav(self.sample_wav, duration_sec=2.5, sample_rate=16000)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_audio_validation(self):
        # Non-existent file
        with self.assertRaises(AudioValidationError):
            self.preprocessor.validate_file("missing_audio.wav")

        # Unsupported format
        unsupported = os.path.join(self.test_dir, "notes.pdf")
        with open(unsupported, "w") as f:
            f.write("hello")
        with self.assertRaises(AudioValidationError):
            self.preprocessor.validate_file(unsupported)

        # Empty file
        empty_wav = os.path.join(self.test_dir, "empty.wav")
        with open(empty_wav, "wb") as f:
            f.write(b"")
        with self.assertRaises(AudioValidationError):
            self.preprocessor.load_wav(empty_wav)

    def test_wav_decoding_and_normalization(self):
        samples, sr = self.preprocessor.load_wav(self.sample_wav)
        self.assertEqual(sr, 16000)
        self.assertIsInstance(samples, np.ndarray)
        self.assertTrue(len(samples) > 0)
        # All samples must be normalized in [-1.0, 1.0]
        self.assertTrue(np.all(samples >= -1.05))
        self.assertTrue(np.all(samples <= 1.05))

    def test_silence_suppression_gating(self):
        samples, sr = self.preprocessor.load_wav(self.sample_wav)
        # Prepend 0.5s of dead zero silence
        silence = np.zeros(int(sr * 0.5), dtype=np.float32)
        padded_samples = np.concatenate([silence, samples, silence])

        gated = self.preprocessor.suppress_silence(padded_samples, sr, threshold_db=-40.0)
        # Gated output should be shorter than padded input
        self.assertLess(len(gated), len(padded_samples))

    def test_speech_recognition_transcription(self):
        result = self.recognizer.transcribe(self.sample_wav, apply_noise_reduction=True)
        self.assertIsInstance(result, TranscriptionResult)
        self.assertGreater(result.duration_sec, 0.0)
        self.assertGreaterEqual(result.confidence, 0.0)
        self.assertLessEqual(result.confidence, 1.0)
        self.assertTrue(len(result.full_text) > 0)
        self.assertTrue(len(result.segments) > 0)

        for s in result.segments:
            self.assertIsInstance(s, TranscriptSegment)
            self.assertGreaterEqual(s.end_time, s.start_time)
            self.assertTrue(len(s.text) > 0)

    def test_accuracy_metrics_wer_and_cer(self):
        ref = "the quick brown fox jumps over the lazy dog"
        # Identical text -> WER=0.0, CER=0.0
        wer_res = compute_wer(ref, ref)
        cer_res = compute_cer(ref, ref)
        self.assertEqual(wer_res["wer"], 0.0)
        self.assertEqual(cer_res["cer"], 0.0)

        # 1 substitution: "dog" -> "cat"
        hyp_sub = "the quick brown fox jumps over the lazy cat"
        wer_sub = compute_wer(ref, hyp_sub)
        self.assertEqual(wer_sub["substitutions"], 1)
        self.assertAlmostEqual(wer_sub["wer"], 1.0 / 9.0, places=4)

        # Empty reference handling
        empty_res = compute_wer("", "some speech")
        self.assertEqual(empty_res["wer"], 1.0)

    def test_transcript_exporters(self):
        seg = TranscriptSegment(start_time=0.0, end_time=2.5, text="Hello world transcription", confidence=0.92)
        res = TranscriptionResult(
            audio_path=self.sample_wav,
            duration_sec=2.5,
            full_text="Hello world transcription",
            confidence=0.92,
            segments=[seg]
        )

        # Plain text
        txt_path = os.path.join(self.test_dir, "out.txt")
        txt = TranscriptExporter.to_txt(res, txt_path)
        self.assertEqual(txt, "Hello world transcription")
        self.assertTrue(os.path.exists(txt_path))

        # JSON
        json_path = os.path.join(self.test_dir, "out.json")
        json_str = TranscriptExporter.to_json(res, json_path)
        parsed = json.loads(json_str)
        self.assertEqual(parsed["full_text"], "Hello world transcription")
        self.assertEqual(len(parsed["segments"]), 1)

        # SRT format
        srt_path = os.path.join(self.test_dir, "out.srt")
        srt = TranscriptExporter.to_srt(res, srt_path)
        self.assertIn("00:00:00,000 --> 00:00:02,500", srt)
        self.assertIn("Hello world transcription", srt)


if __name__ == "__main__":
    unittest.main()
