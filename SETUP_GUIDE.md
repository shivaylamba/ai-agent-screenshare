# AI Agent Screen Share Assistant - Complete Setup Guide

## 🎯 Overview

This guide will walk you through setting up and testing your AI agent that joins Google Meet calls, analyzes screens, provides voice guidance, and displays visual annotations.

## ✅ Prerequisites Checklist

### System Requirements
- [ ] macOS (Darwin 25.2.0 or higher)
- [ ] Python 3.9+
- [ ] 8GB RAM minimum
- [ ] Stable internet connection (for APIs)
- [ ] Admin access (for installing dependencies)

### API Keys Required
- [ ] **Anthropic API Key** - Get from https://console.anthropic.com/
- [ ] **OpenAI API Key** - Get from https://platform.openai.com/api-keys
- [ ] **ElevenLabs API Key** - Get from https://elevenlabs.io/

### macOS Permissions Needed
- [ ] Screen Recording
- [ ] Microphone Access
- [ ] Accessibility (for overlay)

---

## 📦 Installation Steps

### Step 1: Navigate to Project Directory

```bash
cd /Users/pulkit.midha/Desktop/check/AI-agent-screenshare
```

### Step 2: Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

**Verify activation:**
```bash
which python
# Should output: /Users/pulkit.midha/Desktop/check/AI-agent-screenshare/venv/bin/python
```

### Step 3: Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**This installs:**
- Playwright (browser automation)
- Anthropic SDK (Claude AI)
- OpenAI SDK (Whisper STT)
- ElevenLabs (TTS)
- mss, opencv-python (screen capture)
- PyQt6 (overlay)
- And more...

### Step 4: Install Playwright Browsers

```bash
playwright install chromium
```

This downloads Chromium browser for automation.

### Step 5: Install macOS System Dependencies

```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install audio libraries
brew install portaudio
brew install ffmpeg
```

### Step 6: Configure Environment Variables

```bash
# Copy the example file
cp .env.example .env

# Edit the .env file
nano .env
```

**Required configuration in `.env`:**

```bash
# Anthropic (Claude AI)
ANTHROPIC_API_KEY=sk-ant-api03-your-actual-key-here

# OpenAI (Whisper STT)
OPENAI_API_KEY=sk-your-actual-openai-key-here

# ElevenLabs (TTS)
ELEVENLABS_API_KEY=your-elevenlabs-key-here

# Google Meet URL (optional - can enter at runtime)
MEET_URL=https://meet.google.com/your-meeting-code

# Logging
LOG_LEVEL=INFO
DEBUG_MODE=false
```

**Save and exit:** Press `Ctrl+O`, `Enter`, then `Ctrl+X`

### Step 7: Verify Installation

```bash
python -c "import playwright; import anthropic; import openai; import elevenlabs; print('All imports successful!')"
```

---

## 🔐 Setting up macOS Permissions

### Screen Recording Permission

1. Go to **System Preferences** → **Security & Privacy** → **Privacy** tab
2. Click **Screen Recording** in the left sidebar
3. Click the lock icon (bottom left) to make changes
4. Add and check:
   - Terminal (or iTerm2)
   - Python

### Microphone Permission

1. Same **Security & Privacy** panel
2. Click **Microphone** in the left sidebar
3. Add and check:
   - Terminal
   - Google Chrome/Chromium

### Accessibility Permission

1. Same **Security & Privacy** panel
2. Click **Accessibility** in the left sidebar
3. Add and check:
   - Terminal
   - Python

---

## 🧪 Testing the System

### Test 1: Basic Setup Validation

```bash
python main.py --help
```

**Expected:** Should show usage information (or gracefully handle if not implemented).

### Test 2: API Key Validation

```bash
python main.py
```

**Expected:**
- Should validate all API keys
- If keys are missing, shows which ones are needed
- If keys are present, proceeds to join Meet

### Test 3: Join Google Meet (Phase 1)

**Preparation:**
1. Create a test Google Meet at https://meet.google.com/
2. Copy the Meet URL (e.g., `https://meet.google.com/abc-defg-hij`)
3. Add it to your `.env` file or be ready to paste it

**Run:**
```bash
python main.py
```

**Expected Behavior:**
1. ✅ Browser window opens
2. ✅ Automatically navigates to Meet URL
3. ✅ Clicks "Join now" button
4. ✅ Shows "Successfully joined the meeting!"
5. ✅ Browser stays open

**Troubleshooting:**
- If browser doesn't open: Check Playwright installation
- If join fails: Manually click "Join now" in the browser
- If permissions denied: Check macOS permissions

### Test 4: Screen Capture (Phase 2)

**Once in the meeting:**
1. Click **Present** → **Your entire screen** (or a window)
2. Share your screen in the Meet

**Expected Behavior:**
1. ✅ Console shows "Waiting for screen share..."
2. ✅ After you share: "Screen share detected! Bounds: {x, y, width, height}"
3. ✅ Console shows "Starting continuous screen capture..."
4. ✅ Every 5 seconds: Frame statistics appear
   ```
   Frames captured: 20, Changed: 15, Buffer: 100%
   ```

**Debugging:**
- Enable debug mode: Set `DEBUG_MODE=true` in `.env`
- Check `debug_frames/` directory for saved frames
- Verify screen share is active in Meet

### Test 5: Audio Pipeline (Phase 3)

**Note:** Audio is complex and may need refinement.

**Test voice detection:**
1. Unmute yourself in the Meet
2. Say something clearly: "Hello, can you hear me?"

**Expected (when fully integrated):**
- Console shows transcription: `User said: 'Hello, can you hear me?'`
- AI responds with voice

**Current Status:** Audio components are implemented but need integration testing.

### Test 6: AI Vision Analysis (Phase 4)

**When screen sharing + audio working:**
1. Share a screen with visible UI elements (buttons, forms)
2. Ask: "Where is the submit button?"

**Expected:**
- AI analyzes the screen
- Responds with guidance
- Voice response plays

**Test Manually:**
```python
# Test script
import asyncio
from ai.claude_client import ClaudeClient

async def test():
    client = ClaudeClient()
    result = await client.analyze_screen(
        image_data=open('test_image.jpg', 'rb').read(),
        user_query="What do you see?"
    )
    print(result)

asyncio.run(test())
```

### Test 7: Overlay System (Phase 5)

**Note:** Overlay requires Qt event loop integration.

**Manual test:**
```bash
python -c "
from overlay.macos_overlay import create_overlay_app, Annotation
app, overlay = create_overlay_app()
ann = Annotation('arrow', (100, 100, 200, 200), color='#FF0000')
overlay.add_annotation(ann)
overlay.show_overlay()
app.exec()
"
```

**Expected:**
- Transparent window appears
- Red arrow visible
- Clicks pass through to underlying apps

---

## 🐛 Common Issues & Solutions

### Issue: "Module not found"

**Solution:**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Issue: "Playwright browser not found"

**Solution:**
```bash
playwright install chromium
```

### Issue: "Permission denied" for screen recording

**Solution:**
1. Go to System Preferences → Security & Privacy → Screen Recording
2. Add Terminal and Python
3. Restart Terminal
4. Run again

### Issue: "API key invalid"

**Solution:**
1. Verify API key is correct (no extra spaces)
2. Check key has sufficient credits
3. Test key directly:
```bash
python -c "from anthropic import Anthropic; print(Anthropic(api_key='your-key').messages.create(model='claude-3-5-sonnet-20241022', max_tokens=10, messages=[{'role':'user','content':'hi'}]))"
```

### Issue: "Screen share not detected"

**Solution:**
1. Ensure you clicked "Share" in Meet
2. Share your **entire screen** (not just a window)
3. Wait up to 60 seconds for detection
4. Check browser console for errors

### Issue: "Audio not working"

**Solution:**
1. Check microphone permissions
2. Verify ffmpeg installed: `ffmpeg -version`
3. Test audio devices: `python -c "import pyaudio; print(pyaudio.PyAudio().get_device_count())"`

### Issue: "High CPU usage"

**Solution:**
- Lower FPS in config.py: `fps: int = 1`
- Reduce image quality: `jpeg_quality: int = 70`
- Increase change threshold: `change_threshold: float = 0.20`

---

## 📊 Performance Monitoring

### View Logs

```bash
# Real-time logs
tail -f logs/ai_agent_$(date +%Y-%m-%d).log

# Error logs only
tail -f logs/errors_$(date +%Y-%m-%d).log

# Debug logs (if DEBUG_MODE=true)
tail -f logs/debug_$(date +%Y-%m-%d).log
```

### Check Performance Stats

Stats are logged automatically at shutdown. Look for:
```
=== Performance Statistics ===
capture_frame: count=100, avg=0.045s, min=0.032s, max=0.089s
stt_transcribe: count=5, avg=0.412s
claude_vision_analysis: count=5, avg=0.753s
```

### Monitor Resource Usage

```bash
# CPU and Memory
top -pid $(pgrep -f "python main.py")

# Detailed monitoring
python -c "
import psutil
import os
p = psutil.Process(os.getpid())
print(f'CPU: {p.cpu_percent()}%')
print(f'Memory: {p.memory_info().rss / 1024 / 1024:.1f} MB')
"
```

---

## 🚀 Running in Production

### Optimize for Performance

**Edit `config.py`:**
```python
class ScreenCaptureConfig:
    fps: int = 1  # Lower FPS
    change_threshold: float = 0.15  # Higher threshold
    jpeg_quality: int = 75  # Lower quality

class AIConfig:
    max_context_messages: int = 5  # Fewer messages
```

### Run in Background

```bash
nohup python main.py > output.log 2>&1 &
```

**Check status:**
```bash
ps aux | grep "python main.py"
```

**Stop:**
```bash
pkill -f "python main.py"
```

---

## 🎓 Next Steps

### Phase-by-Phase Testing

1. **Phase 1:** Join Meet ✅
2. **Phase 2:** Capture screen ✅
3. **Phase 3:** Audio I/O ⚠️ (needs integration)
4. **Phase 4:** AI analysis ⚠️ (needs integration)
5. **Phase 5:** Overlay ⚠️ (needs Qt loop)
6. **Phase 6:** Full orchestration 🚧
7. **Phase 7:** Optimization & polish 📋

### Integration Todos

- [ ] Integrate audio capture from Meet browser
- [ ] Connect STT → AI → TTS pipeline
- [ ] Implement Qt overlay in main event loop
- [ ] Test end-to-end: Voice → AI → Visual guidance
- [ ] Performance tuning and optimization

---

## 💡 Tips for Success

1. **Start Simple:** Test each phase independently
2. **Use Debug Mode:** Set `DEBUG_MODE=true` to save frames and see detailed logs
3. **Check Logs:** Always check logs when something doesn't work
4. **Test APIs Separately:** Verify each API key works before full integration
5. **Monitor Performance:** Watch CPU/memory usage and adjust config
6. **Ask for Help:** Check logs, error messages, and troubleshooting guide

---

## 📞 Getting Help

**Check logs first:**
```bash
tail -n 50 logs/ai_agent_$(date +%Y-%m-%d).log
```

**Common log locations:**
- Application logs: `logs/ai_agent_YYYY-MM-DD.log`
- Error logs: `logs/errors_YYYY-MM-DD.log`
- Debug logs: `logs/debug_YYYY-MM-DD.log`
- Saved frames: `debug_frames/frame_*.jpg`

**Test individual components:**
```bash
# Test Claude API
python -c "from ai.claude_client import ClaudeClient; import asyncio; print(asyncio.run(ClaudeClient().chat('hello')))"

# Test screen capture
python -c "from capture.screen_capturer import ScreenCapturer; import asyncio; sc = ScreenCapturer(); print(asyncio.run(sc.capture_frame()))"
```

---

## ✅ Pre-Flight Checklist

Before running the full system:

- [ ] Virtual environment activated
- [ ] All dependencies installed
- [ ] Playwright browsers downloaded
- [ ] All three API keys configured in `.env`
- [ ] macOS permissions granted (Screen Recording, Microphone, Accessibility)
- [ ] Test Google Meet created and URL ready
- [ ] Logs directory exists and writable
- [ ] Enough disk space (500MB minimum)

**Ready to launch!** 🚀

```bash
python main.py
```
