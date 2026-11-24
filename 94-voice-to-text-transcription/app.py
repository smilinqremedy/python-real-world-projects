"""
Streamlit Web Interface for AI Voice-to-Text Transcription System.
Supports audio upload, transcription progress, transcript editor, and multi-format exports.
"""
import io
import os
import tempfile
import streamlit as st

from speech_recognizer import SpeechRecognizer
from transcript_exporter import TranscriptExporter
from metrics import compute_wer, compute_cer
from audio_preprocessor import AudioValidationError

st.set_page_config(
    page_title="Voice-to-Text Transcription",
    page_icon="🎙️",
    layout="wide"
)

st.title("🎙️ AI-Powered Voice-to-Text Transcription System")
st.markdown("Speech recognition pipeline supporting WAV, MP3, FLAC, audio normalization, and SRT subtitle export.")

recognizer = SpeechRecognizer()

tabs = st.tabs(["🎧 Transcribe Audio", "📊 Accuracy Evaluation (WER/CER)", "ℹ️ Architecture & Guide"])

with tabs[0]:
    st.subheader("Upload or Record Audio")
    audio_file = st.file_uploader("Select Audio File (WAV, MP3, FLAC, OGG)", type=["wav", "mp3", "flac", "ogg"])

    noise_reduction = st.checkbox("Apply RMS Silence Suppression & Gating", value=True)

    if audio_file is not None:
        st.audio(audio_file)

        if st.button("🚀 Transcribe Audio"):
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(audio_file.name)[1]) as tmp:
                tmp.write(audio_file.getvalue())
                tmp_path = tmp.name

            try:
                progress_bar = st.progress(10)
                st.info("Preprocessing audio signal...")
                progress_bar.progress(40)
                st.info("Running speech recognition inference...")
                progress_bar.progress(70)

                result = recognizer.transcribe(tmp_path, apply_noise_reduction=noise_reduction)
                progress_bar.progress(100)
                st.success("Transcription Complete!")

                col1, col2, col3 = st.columns(3)
                col1.metric("Audio Duration", f"{result.duration_sec:.1f} sec")
                col2.metric("Mean Confidence", f"{result.confidence * 100:.1f}%")
                col3.metric("Segments Count", len(result.segments))

                st.subheader("Editable Transcript Output")
                user_edited_text = st.text_area("Review and Edit Generated Text:", value=result.full_text, height=180)

                st.subheader("Timestamped Speech Segments")
                seg_data = [{"Start": f"{s.start_time:.1f}s", "End": f"{s.end_time:.1f}s", "Segment Text": s.text, "Confidence": f"{s.confidence * 100:.1f}%"} for s in result.segments]
                st.table(seg_data)

                # Export downloads
                st.subheader("Download Transcripts")
                d1, d2, d3 = st.columns(3)
                d1.download_button("📄 Plain Text (.txt)", data=user_edited_text, file_name="transcript.txt", mime="text/plain")
                d2.download_button("📊 JSON Metadata (.json)", data=TranscriptExporter.to_json(result), file_name="transcript.json", mime="application/json")
                d3.download_button("🎬 Subtitle (.srt)", data=TranscriptExporter.to_srt(result), file_name="subtitles.srt", mime="text/plain")

            except AudioValidationError as ave:
                st.error(f"Validation Error: {ave}")
            except Exception as e:
                st.error(f"Transcription Error: {e}")
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

with tabs[1]:
    st.subheader("Speech Transcription Benchmark Evaluation")
    st.markdown("Measure the Word Error Rate (WER) and Character Error Rate (CER) against ground truth references.")

    ref_text = st.text_area("Ground Truth Reference:", "Artificial intelligence and deep learning speech recognition.")
    hyp_text = st.text_area("System Hypothesis:", "Artificial intelligence and deep learning speech recognition.")

    if st.button("Compute Error Metrics"):
        wer_res = compute_wer(ref_text, hyp_text)
        cer_res = compute_cer(ref_text, hyp_text)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Word Error Rate (WER)", f"{wer_res['wer'] * 100:.1f}%")
        c2.metric("Character Error Rate (CER)", f"{cer_res['cer'] * 100:.1f}%")
        c3.metric("Word Substitutions", wer_res["substitutions"])
        c4.metric("Word Deletions / Insertions", f"{wer_res['deletions']} / {wer_res['insertions']}")

with tabs[2]:
    st.subheader("Speech-to-Text Pipeline Overview")
    st.markdown("""
    1. **Signal Processing:** Audio signals are converted to mono, normalized into float32, and filtered with RMS energy thresholds to gate background ambient silence.
    2. **Acoustic Feature Extraction:** Computes spectral envelopes and harmonic frequency representations.
    3. **Decoding & Language Modeling:** Acoustic representations are matched to linguistic token sequences.
    4. **SubRip Generation:** Segments are automatically timestamp-aligned for standard video player integration.
    """)
