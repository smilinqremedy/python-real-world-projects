"""
Transcript Exporter Module: Exports speech recognition outputs
to Plain Text (TXT), Structured JSON, and SubRip Subtitle (SRT) format.
"""
import json
import os
from speech_recognizer import TranscriptionResult


def format_srt_timestamp(seconds: float) -> str:
    """Formats seconds into standard SubRip timestamp: HH:MM:SS,mmm"""
    total_ms = int(round(seconds * 1000))
    hours = total_ms // 3600000
    remainder = total_ms % 3600000
    minutes = remainder // 60000
    remainder %= 60000
    secs = remainder // 1000
    millis = remainder % 1000
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


class TranscriptExporter:
    @staticmethod
    def to_txt(result: TranscriptionResult, output_path: str = None) -> str:
        """Exports transcript as continuous readable text."""
        txt = result.full_text
        if output_path:
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(txt)
        return txt

    @staticmethod
    def to_json(result: TranscriptionResult, output_path: str = None) -> str:
        """Exports full metadata and timestamped segments as JSON."""
        data = result.to_dict()
        json_str = json.dumps(data, indent=2)
        if output_path:
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(json_str)
        return json_str

    @staticmethod
    def to_srt(result: TranscriptionResult, output_path: str = None) -> str:
        """Generates standard SubRip Subtitle (SRT) output for video synchronization."""
        lines = []
        for idx, seg in enumerate(result.segments, start=1):
            start_str = format_srt_timestamp(seg.start_time)
            end_str = format_srt_timestamp(seg.end_time)
            lines.append(f"{idx}\n{start_str} --> {end_str}\n{seg.text}\n")

        srt_str = "\n".join(lines)
        if output_path:
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(srt_str)
        return srt_str
