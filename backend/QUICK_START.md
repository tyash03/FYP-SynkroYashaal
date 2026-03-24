# Quick Start - FREE Whisper Setup

## Current Status:
✅ Python packages installed (whisper, torch, torchaudio)
⚠️ FFmpeg needs to be installed manually
✅ Code updated to use FREE local transcription

## To Start the Server:

### Step 1: Install FFmpeg (Required)

**Option A - Using Chocolatey (Easiest):**
```powershell
# Open PowerShell as Administrator and run:
choco install ffmpeg

# Then restart your terminal
```

**Option B - Manual Download:**
1. Download FFmpeg from: https://ffmpeg.org/download.html
2. Extract to a folder (e.g., `C:\ffmpeg`)
3. Add to PATH:
   - Search "Environment Variables" in Windows
   - Edit "Path" under System Variables
   - Add: `C:\ffmpeg\bin`
   - Restart terminal

**Option C - Skip for Now (Transcription will fail but server runs):**
You can start the server without FFmpeg to test other features.

### Step 2: Activate Virtual Environment & Start Server

```powershell
# Navigate to backend
cd "c:\Users\centu\OneDrive\Desktop\fyp synkro"

# Activate your existing venv
.\backend\venv\Scripts\Activate.ps1

# Go to backend directory
cd backend

# Start the server
uvicorn app.main:app --reload
```

### Step 3: Verify Setup

Once server starts, visit: http://127.0.0.1:8000/api/meetings/whisper-status

You should see:
```json
{
  "whisper": {
    "available": true,
    "message": "Whisper is ready",
    "device": "CPU",
    "recommended_model": "base"
  },
  "transcription_method": "FREE Local Whisper (no API key needed!)"
}
```

## Testing Transcription:

1. Go to frontend: http://localhost:3000/dashboard/meetings
2. Click "Upload Meeting"
3. Select a short audio file (MP3, WAV, etc.)
4. Wait 2-5 minutes
5. Refresh the page to see the transcript!

## Important Notes:

### About FFmpeg:
- **Required for**: Audio file processing (converting formats, extracting audio)
- **Without it**: Upload will work but transcription will fail with "ffmpeg not found" error
- **How to verify**: Run `ffmpeg -version` in terminal

### About the Setup:
- ✅ **FREE**: No OpenAI Whisper API key needed for transcription
- ✅ **No Redis**: No background services needed
- ✅ **No Celery**: Uses FastAPI background tasks
- ⏱️ **Slower**: Takes 2-5 minutes per 10-minute audio (vs instant with paid API)
- 💾 **First run**: Downloads Whisper model (~150MB) automatically

### If You Get Errors:

**"Module not found" errors:**
```powershell
cd backend
pip install -r requirements.txt
```

**"FFmpeg not found":**
Install FFmpeg (see Step 1 above)

**"Out of memory":**
Edit `backend/app/services/whisper_local.py` line 97:
```python
result = transcribe_audio_local(tmp_file_path, model_size="tiny")  # Change to tiny
```

**Transcription stuck at "Processing":**
Check backend terminal logs - transcription takes 2-5 minutes, be patient!

## What Changed vs Original Setup:

| Before | After |
|--------|-------|
| Paid OpenAI Whisper API | FREE Local Whisper |
| Redis + Docker required | No Redis needed |
| Celery worker required | FastAPI background tasks |
| Instant transcription | 2-5 min transcription |
| $0.006/min cost | $0 cost |

## Need Help?

- Check backend terminal for error logs
- Visit docs: http://127.0.0.1:8000/docs
- Check Whisper status: http://127.0.0.1:8000/api/meetings/whisper-status
