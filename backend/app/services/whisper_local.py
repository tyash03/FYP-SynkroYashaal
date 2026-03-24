"""
Free local Whisper transcription service.
Uses OpenAI's open-source Whisper model running locally - no API key required!
"""
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Try to import whisper - gracefully handle if not installed
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    logger.warning("openai-whisper not installed. Install with: pip install openai-whisper")


def transcribe_audio_local(
    audio_file_path: str,
    model_size: str = "base",
    language: str = "en"
) -> dict:
    """
    Transcribe audio using FREE local Whisper model.

    Model sizes (from fastest to most accurate):
    - tiny: Fastest, least accurate (~1GB VRAM)
    - base: Good balance (~1GB VRAM) [DEFAULT]
    - small: Better accuracy (~2GB VRAM)
    - medium: High accuracy (~5GB VRAM)
    - large: Best accuracy (~10GB VRAM)

    Args:
        audio_file_path: Path to audio file
        model_size: Whisper model size (tiny, base, small, medium, large)
        language: Language code (en, es, fr, etc.)

    Returns:
        Dictionary with:
        - transcript: Full transcript text
        - duration: Audio duration in seconds
        - segments: List of timestamped segments

    Raises:
        RuntimeError: If whisper is not installed
        Exception: If transcription fails
    """
    if not WHISPER_AVAILABLE:
        raise RuntimeError(
            "openai-whisper package not installed. "
            "Install with: pip install openai-whisper"
        )

    if not os.path.exists(audio_file_path):
        raise FileNotFoundError(f"Audio file not found: {audio_file_path}")

    try:
        logger.info(f"Loading Whisper model: {model_size}")

        # Load model (will download on first use, then cache locally)
        model = whisper.load_model(model_size)

        logger.info(f"Transcribing audio file: {audio_file_path}")

        # Transcribe with word-level timestamps
        result = model.transcribe(
            audio_file_path,
            language=language,
            verbose=False,
            word_timestamps=True
        )

        # Format transcript with timestamps
        formatted_transcript = format_transcript_with_timestamps(result.get("segments", []))

        # Calculate duration
        duration_seconds = 0
        if result.get("segments"):
            last_segment = result["segments"][-1]
            duration_seconds = last_segment.get("end", 0)

        logger.info(f"Transcription complete. Duration: {duration_seconds:.1f}s, Length: {len(formatted_transcript)} chars")

        return {
            "transcript": formatted_transcript,
            "plain_text": result.get("text", "").strip(),
            "duration_seconds": duration_seconds,
            "duration_minutes": int(duration_seconds / 60),
            "segments": result.get("segments", []),
            "language": result.get("language", language)
        }

    except Exception as e:
        logger.error(f"Transcription failed: {str(e)}", exc_info=True)
        raise Exception(f"Local transcription failed: {str(e)}")


def format_transcript_with_timestamps(segments: list) -> str:
    """
    Format transcript segments with timestamps.

    Args:
        segments: List of segment dictionaries from Whisper

    Returns:
        Formatted transcript string
    """
    if not segments:
        return ""

    formatted_lines = []

    for segment in segments:
        start_time = segment.get("start", 0)
        text = segment.get("text", "").strip()

        if text:
            timestamp = format_timestamp(start_time)
            formatted_lines.append(f"[{timestamp}] {text}")

    return "\n".join(formatted_lines)


def format_timestamp(seconds: float) -> str:
    """Format seconds into MM:SS format"""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"


def check_whisper_availability() -> dict:
    """
    Check if Whisper is available and return status info.

    Returns:
        Dictionary with availability status and info
    """
    if not WHISPER_AVAILABLE:
        return {
            "available": False,
            "message": "openai-whisper not installed",
            "install_command": "pip install openai-whisper"
        }

    try:
        import torch
        has_cuda = torch.cuda.is_available()

        return {
            "available": True,
            "message": "Whisper is ready",
            "cuda_available": has_cuda,
            "device": "GPU (CUDA)" if has_cuda else "CPU",
            "recommended_model": "base" if not has_cuda else "small"
        }
    except ImportError:
        return {
            "available": True,
            "message": "Whisper is ready (CPU only)",
            "cuda_available": False,
            "device": "CPU",
            "recommended_model": "base"
        }
