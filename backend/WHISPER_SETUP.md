# FREE Local Whisper Transcription Setup

Your Synkro app now uses **FREE local Whisper** for meeting transcription - no API keys, no Redis, no Celery required!

## What Changed?

✅ **Before**: Required paid OpenAI API + Redis + Celery
✅ **Now**: FREE open-source Whisper running locally

## Installation Steps

### 1. Install FFmpeg (Required for audio processing)

**Windows:**
```powershell
# Using chocolatey (recommended)
choco install ffmpeg

# OR download from: https://ffmpeg.org/download.html
# Add FFmpeg to your PATH
```

**Mac:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt update
sudo apt install ffmpeg
```

### 2. Install Python Packages

```powershell
cd backend
pip install -r requirements.txt
```

This will install:
- `openai-whisper` - FREE local transcription
- `torch` - PyTorch for ML
- `torchaudio` - Audio processing
- `ffmpeg-python` - Audio format conversion

**Note**: This will download about 500MB-1GB of packages. Be patient!

### 3. Start the Server

```powershell
cd backend
uvicorn app.main:app --reload
```

That's it! No Redis, no Celery, no API keys needed.

## How It Works

1. **Upload a meeting** - File is saved to local storage
2. **Background processing** - Whisper transcribes locally (takes 2-5 minutes)
3. **Auto-summarization** - Uses OpenAI API (requires OPENAI_API_KEY in `.env`)
4. **View results** - Transcript, summary, and action items appear in the UI

## Model Sizes

Whisper has different model sizes. Default is `base`:

- `tiny` - Fastest, least accurate (~1GB RAM)
- `base` - **DEFAULT** - Good balance (~1GB RAM)
- `small` - Better accuracy (~2GB RAM)
- `medium` - High accuracy (~5GB RAM)
- `large` - Best accuracy (~10GB RAM)

The model downloads automatically on first use and is cached locally.

## Testing Transcription

### Check Whisper Status

Visit: http://127.0.0.1:8000/docs

Look for the `/api/meetings/whisper-status` endpoint (if implemented)

### Upload a Test Meeting

1. Go to the Meetings page in your frontend
2. Click "Upload Meeting"
3. Select an audio file (MP3, WAV, M4A, etc.)
4. Give it a title
5. Click Upload

The meeting will show as "Processing" for a few minutes while Whisper transcribes locally.

## Troubleshooting

### Error: "openai-whisper not installed"
```powershell
pip install openai-whisper
```

### Error: "ffmpeg not found"
Install FFmpeg (see step 1 above) and restart your terminal.

### Meeting stuck in "Processing"
Check the backend terminal logs. The transcription may still be running (it can take 2-5 minutes for a 10-minute audio file).

### Out of Memory Error
Use a smaller Whisper model. Edit `backend/app/services/whisper_local.py` and change:
```python
result = transcribe_audio_local(tmp_file_path, model_size="tiny")  # Change to tiny
```

### Slow Transcription
- **CPU only**: Expect ~2-5 minutes for a 10-minute meeting with `base` model
- **GPU (CUDA)**: Expect ~30 seconds for a 10-minute meeting

To enable GPU:
```powershell
pip install torch --index-url https://download.pytorch.org/whl/cu118
```

## Summary Options

If you don't have an OpenAI API key, summarization will fail. Options:

1. **Get a free OpenAI API key**: https://platform.openai.com/api-keys
   - Add to `.env`: `OPENAI_API_KEY=sk-...`
   - Free tier includes $5 credit

2. **Disable summarization**: The transcript will still work, just no AI summary

3. **Use a different AI model**: Update `backend/app/services/ai_service.py` to use:
   - Anthropic Claude (requires API key)
   - Local LLM (Ollama, etc.)
   - Gemini (Google - has free tier)

## What About the Old Celery Setup?

You don't need it anymore! The old setup required:
- ❌ Redis server running
- ❌ Celery worker running
- ❌ Paid OpenAI API for Whisper

New setup:
- ✅ Just FastAPI
- ✅ FREE local Whisper
- ✅ No background services

The transcription now runs in FastAPI's built-in background tasks.

## Performance Notes

- **First run**: Downloads Whisper model (~150MB), takes extra time
- **Subsequent runs**: Model is cached, much faster
- **10-minute meeting**: ~2-5 minutes transcription on CPU
- **Longer meetings**: Proportionally longer (20-minute = 4-10 minutes)

This is slower than the paid OpenAI Whisper API but **completely free**!
