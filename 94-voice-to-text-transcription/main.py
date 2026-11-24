"""
Command-Line Interface for Voice-to-Text Transcription System.
"""
import argparse
import sys
import os
from speech_recognizer import SpeechRecognizer
from transcript_exporter import TranscriptExporter
from metrics import compute_wer, compute_cer
from audio_preprocessor import AudioValidationError, AudioPreprocessor


def main():
    parser = argparse.ArgumentParser(description="AI Voice-to-Text Transcription System")
    parser.add_argument("--transcribe", type=str, help="Path to audio file (WAV, MP3, FLAC)")
    parser.add_argument("--output", type=str, default=None, help="Output destination path")
    parser.add_argument("--format", choices=["txt", "json", "srt"], default="txt", help="Export format")
    parser.add_argument("--no-noise-gate", action="store_true", help="Disable silence suppression filter")
    parser.add_argument("--generate-sample", type=str, help="Generate synthetic WAV speech tone for testing")
    parser.add_argument("--evaluate", nargs=2, metavar=("REF_TEXT", "HYP_TEXT"), help="Compute WER/CER metrics")

    args = parser.parse_args()

    if args.generate_sample:
        p = AudioPreprocessor.generate_synthetic_speech_wav(args.generate_sample, duration_sec=3.0)
        print(f"Generated sample audio: {p}")
        return

    if args.evaluate:
        ref, hyp = args.evaluate
        wer = compute_wer(ref, hyp)
        cer = compute_cer(ref, hyp)
        print(f"WER: {wer['wer'] * 100:.2f}% (Edits: {wer['edit_distance']}, Ref words: {wer['ref_words']})")
        print(f"CER: {cer['cer'] * 100:.2f}% (Edits: {cer['edit_distance']}, Ref chars: {cer['ref_chars']})")
        return

    if args.transcribe:
        recognizer = SpeechRecognizer()
        try:
            res = recognizer.transcribe(args.transcribe, apply_noise_reduction=not args.no_noise_gate)
            print(f"Duration: {res.duration_sec:.2f}s | Confidence: {res.confidence * 100:.1f}%")
            print("\nTranscription:\n" + res.full_text)

            if args.format == "txt":
                out = TranscriptExporter.to_txt(res, args.output)
            elif args.format == "json":
                out = TranscriptExporter.to_json(res, args.output)
            elif args.format == "srt":
                out = TranscriptExporter.to_srt(res, args.output)

            if args.output:
                print(f"\nSaved {args.format.upper()} transcript to: {args.output}")

        except AudioValidationError as e:
            print(f"Audio Error: {e}", file=sys.stderr)
            sys.exit(1)
        return

    parser.print_help()


if __name__ == "__main__":
    main()
