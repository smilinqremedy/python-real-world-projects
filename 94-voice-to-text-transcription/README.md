# Project 94: AI-Powered Voice-to-Text Transcription System

## Overview

The **AI-Powered Voice-to-Text Transcription System** converts spoken speech recordings into structured, readable transcripts and synchronized subtitles.

Key capabilities include:
1. **Multi-Format Audio Handling:** Ingests standard WAV PCM natively, with support for MP3, FLAC, and OGG.
2. **Audio Preprocessing & Silence Gating:** Root-Mean-Square (RMS) energy thresholding removes background noise and silent intervals.
3. **Speech-to-Text Engine:** Integrates Whisper architectures, providing timestamped speech segments and confidence metrics.
4. **Accuracy Benchmarking:** Automated calculation of Word Error Rate (WER) and Character Error Rate (CER) via Levenshtein edit distance.
5. **Multi-Format Exporters:** Export transcripts to Plain Text (`.txt`), Structured Metadata (`.json`), and SubRip Subtitle (`.srt`) formats.

---

## Technical Foundations

### Speech Recognition Pipeline
1. **Signal Digitization:** Audio waveforms sampled at 16,000 Hz, converted to mono float32 arrays in range `[-1.0, 1.0]`.
2. **Silence Gating:** Suppresses silent frames below RMS dB threshold (e.g. -45 dB) to focus computation on vocal utterances.
3. **Acoustic Modeling:** Transforms acoustic spectro-temporal representations into phonetic likelihood distributions.
4. **SubRip Subtitle Timestamping:** Generates HH:MM:SS,mmm timecodes aligned to speech bursts.

### Word Error Rate (WER) Formula
$$\\text{WER} = \\frac{S + D + I}{N}$$
Where:
- $S$ = Number of word substitutions
- $D$ = Number of word deletions
- $I$ = Number of word insertions
- $N$ = Total words in reference transcript

---

## Architecture

```text
94-voice-to-text-transcription/
├── app.py                   # Streamlit web application & player
├── audio_preprocessor.py    # PCM decoding, silence suppression, normalization
├── main.py                  # CLI command runner
├── metrics.py               # Levenshtein distance, WER, CER calculations
├── requirements.txt         # Dependencies
├── speech_recognizer.py     # Speech-to-text inference & segment aligner
├── test_transcription.py    # Automated test suite
├── transcript_exporter.py   # TXT, JSON, and SRT subtitle formatting
└── README.md                # Documentation & usage guide
```

---

## Installation & Setup

1. Navigate to the project directory:
   ```bash
   cd 94-voice-to-text-transcription
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## Usage

### 1. Generate Synthetic Sample Audio
```bash
python3 main.py --generate-sample sample_voice.wav
```

### 2. Transcribe Audio File via CLI
```bash
# Export as Plain Text:
python3 main.py --transcribe sample_voice.wav --format txt --output transcript.txt

# Export as SubRip Subtitles:
python3 main.py --transcribe sample_voice.wav --format srt --output subtitles.srt

# Export as JSON:
python3 main.py --transcribe sample_voice.wav --format json --output metadata.json
```

### 3. Evaluate WER & CER
```bash
python3 main.py --evaluate "the quick brown fox" "the fast brown fox"
```

### 4. Launch Streamlit Web UI
```bash
streamlit run app.py
```

---

## Running Automated Tests

Run the test suite using `unittest`:
```bash
python3 -m unittest test_transcription.py -v
```
