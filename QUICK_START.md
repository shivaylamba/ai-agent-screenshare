# Quick Start Guide - AI Agent Screen Share Assistant

## 🚀 Get Started in 5 Minutes

### Prerequisites
- macOS computer
- Python 3.9+
- API keys for Anthropic, OpenAI, and ElevenLabs

---

## Step 1: Install Dependencies (2 minutes)

```bash
cd /Users/pulkit.midha/Desktop/check/AI-agent-screenshare

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python packages
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Install system dependencies (if not installed)
brew install portaudio ffmpeg
```

---

## Step 2: Configure API Keys (1 minute)

```bash
# Copy example environment file
cp .env.example .env

# Edit .env file (use nano, vim, or any editor)
nano .env
```

**Add your API keys:**
```bash
ANTHROPIC_API_KEY=sk-ant-your-key-here
OPENAI_API_KEY=sk-your-openai-key-here
ELEVENLABS_API_KEY=your-elevenlabs-key-here
MEET_URL=https://meet.google.com/your-meeting-code  # Optional
```

Save and exit (Ctrl+O, Enter, Ctrl+X for nano).

---

## Step 3: Grant macOS Permissions (1 minute)

1. **System Preferences** → **Security & Privacy** → **Privacy**
2. Enable **Screen Recording** for Terminal
3. Enable **Microphone** for Terminal
4. Enable **Accessibility** for Terminal

---

## Step 4: Run the Agent (1 minute)

```bash
python main.py
```

**What happens:**
1. ✅ Browser opens automatically
2. ✅ Joins your Google Meet call
3. ✅ Waits for you to share your screen
4. ✅ Starts capturing and analyzing

---

## Test the System

### Test 1: Join Meet
- Browser should open and join the meeting
- Look for: "Successfully joined the meeting!"

### Test 2: Screen Share
- Click "Present" in Meet
- Share your screen
- Look for: "Screen share detected! Bounds: {x, y, width, height}"

### Test 3: Capture Working
- Every 5 seconds, see frame statistics:
  ```
  Frames captured: 20, Changed: 15, Buffer: 100%
  ```

---

## 🐛 Quick Troubleshooting

### Problem: "Module not found"
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Problem: "API key invalid"
- Check `.env` file has correct keys
- Verify no extra spaces in keys

### Problem: "Screen share not detected"
- Make sure you clicked "Share" in Meet
- Share your **entire screen** (not just a window)
- Wait up to 60 seconds

### Problem: "Permission denied"
- Go to System Preferences → Security & Privacy
- Add Terminal to Screen Recording and Microphone
- Restart Terminal and try again

---

## 📖 Full Documentation

For detailed setup, testing, and troubleshooting:
- **Setup Guide:** `SETUP_GUIDE.md` (comprehensive, 1000+ lines)
- **Project Summary:** `PROJECT_SUMMARY.md` (architecture and status)
- **Main README:** `README.md` (features and configuration)

---

## 🎯 What's Working Now

✅ **Phase 1-2:** Join Meet + Screen Capture
- Automatically joins Google Meet calls
- Detects and captures shared screens at 2 FPS
- Frame differencing to reduce API calls
- Performance monitoring and logging

🚧 **Phase 3-6:** Full AI Agent
- Audio, AI, and overlay components implemented
- Needs end-to-end integration testing
- See `PROJECT_SUMMARY.md` for details

---

## 📞 Need Help?

**Check logs:**
```bash
tail -f logs/ai_agent_$(date +%Y-%m-%d).log
```

**Enable debug mode:**
```bash
# In .env file
DEBUG_MODE=true
LOG_LEVEL=DEBUG
```

**Test individual components:**
```bash
# Test Claude API
python -c "from ai.claude_client import ClaudeClient; print('Claude client OK')"

# Test screen capture
python -c "from capture.screen_capturer import ScreenCapturer; print('Screen capturer OK')"
```

---

## 🚀 You're Ready!

```bash
python main.py
```

Enjoy your AI agent! 🤖✨
