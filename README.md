# AI Agent Screen Share Assistant

An AI-powered assistant that joins Google Meet calls, analyzes your shared screen in real-time, provides voice interaction, and displays visual guidance through transparent overlay annotations.

## Features

- **Automated Meet Joining**: Automatically joins Google Meet calls via browser automation
- **Real-time Screen Analysis**: Captures and analyzes your screen share using Claude's vision AI
- **Bidirectional Voice Communication**: Talk to the AI agent and hear responses in natural voice
- **Visual Overlay Guidance**: See arrows, highlights, and instructions directly on your screen
- **Context-Aware Assistance**: Maintains conversation history and screen context for intelligent guidance

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│           Main Orchestrator (asyncio event loop)        │
└────┬──────────┬──────────┬──────────┬─────────────────┘
     │          │          │          │
     ▼          ▼          ▼          ▼
┌─────────┐ ┌────────┐ ┌────────┐ ┌──────────┐
│ Browser │ │ Screen │ │ Audio  │ │ Overlay  │
│Automator│ │Capture │ │Manager │ │ Renderer │
└────┬────┘ └───┬────┘ └───┬────┘ └────┬─────┘
     │          │          │          │
     └──────────┴──────────┴──────────┘
                    │
              ┌─────▼──────┐
              │ AI Engine  │
              │  (Claude)  │
              └────────────┘
```

## Prerequisites

### System Requirements
- **OS**: macOS (tested on Darwin 25.2.0+)
- **Python**: 3.9 or higher
- **RAM**: 4GB minimum, 8GB recommended
- **Internet**: Stable broadband connection

### Required Permissions (macOS)
You'll need to grant these permissions when prompted:

1. **Screen Recording**: System Preferences → Security & Privacy → Screen Recording
2. **Microphone**: System Preferences → Security & Privacy → Microphone
3. **Accessibility**: System Preferences → Security & Privacy → Accessibility

### API Keys
You'll need API keys from:
- [Anthropic](https://console.anthropic.com/) - For Claude AI
- [OpenAI](https://platform.openai.com/) - For Whisper speech-to-text
- [ElevenLabs](https://elevenlabs.io/) - For text-to-speech

## Installation

### 1. Clone the Repository
```bash
cd /Users/pulkit.midha/Desktop/check/AI-agent-screenshare
```

### 2. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Install Playwright Browsers
```bash
playwright install chromium
```

### 5. Install System Audio Libraries (macOS)
```bash
brew install portaudio
brew install ffmpeg
```

### 6. Configure Environment Variables
```bash
cp .env.example .env
```

Edit `.env` and add your API keys:
```bash
ANTHROPIC_API_KEY=sk-ant-your-key-here
OPENAI_API_KEY=sk-your-key-here
ELEVENLABS_API_KEY=your-elevenlabs-key-here
MEET_URL=https://meet.google.com/your-meeting-code
```

## Usage

### Basic Usage
```bash
python main.py
```

The application will:
1. Validate your API keys
2. Join the specified Google Meet call
3. Wait for you to share your screen
4. Start analyzing and providing guidance

### With Custom Meet URL
If you don't have `MEET_URL` in your `.env` file, you'll be prompted:
```bash
python main.py
# Enter Meet URL when prompted
```

### Exiting
Press `Ctrl+C` to gracefully shut down the application.

## Project Status

### ✅ Phase 1: Foundation & Browser Automation (COMPLETED)
- [x] Project structure created
- [x] Configuration management with Pydantic
- [x] Logging infrastructure with Loguru
- [x] Browser automation with Playwright
- [x] Google Meet joining functionality
- [x] Performance monitoring utilities

### ✅ Phase 2: Screen Capture Pipeline (COMPLETED)
- [x] Screen capturer implementation with mss
- [x] Frame buffer with change detection
- [x] Frame differencing algorithm (>10% threshold)
- [x] Image optimization for AI processing
- [x] JPEG compression and base64 encoding
- [x] Frame quality analysis utilities
- [x] Continuous capture loop with FPS control
- [x] Debug frame saving for troubleshooting

### ✅ Phase 3: Audio Pipeline (COMPLETED)
- [x] Voice Activity Detection (VAD) with webrtcvad
- [x] Speech-to-text (Whisper API integration)
- [x] Text-to-speech (ElevenLabs integration with caching)
- [x] Audio manager coordinator
- [x] Browser audio injector with Web Audio API
- [x] Audio buffer management with silence detection

### ✅ Phase 4: AI Integration (COMPLETED)
- [x] Claude API client with vision support
- [x] Vision analyzer for screen content
- [x] Context manager with sliding window
- [x] Conversation history management
- [x] Base64 image encoding for API transmission
- [x] Response parsing and annotation extraction

### ✅ Phase 5: Transparent Overlay (COMPLETED)
- [x] macOS overlay window with PyQt6
- [x] Click-through functionality (WindowTransparentForInput)
- [x] Drawing engine (arrows, highlights, boxes, text)
- [x] Annotation manager with lifecycle
- [x] Automatic expiration of annotations
- [x] 30 FPS refresh rate

### ✅ Phase 6: Orchestration (COMPLETED)
- [x] Event bus with pub/sub pattern
- [x] State manager with async-safe locking
- [x] Main orchestrator coordinating all components
- [x] Event-driven data flow
- [x] Async loops for screen, audio, and AI processing
- [x] Graceful shutdown and cleanup

### 🚧 Phase 7: Integration & Testing (IN PROGRESS)
- [x] All components implemented
- [x] Comprehensive setup guide created
- [ ] End-to-end integration testing needed
- [ ] Audio capture from browser refinement
- [ ] Qt overlay event loop integration
- [ ] Performance optimization and tuning

## Configuration

### Audio Settings
Edit `config.py` to adjust audio parameters:
```python
class AudioConfig(BaseModel):
    sample_rate: int = 16000  # Hz
    vad_aggressiveness: int = 2  # 0-3
    silence_duration: float = 0.5  # seconds
```

### Screen Capture Settings
```python
class ScreenCaptureConfig(BaseModel):
    fps: int = 2  # Frames per second
    change_threshold: float = 0.10  # 10% change to trigger analysis
    max_width: int = 1280  # Max image width
    jpeg_quality: int = 85  # Compression quality
```

### AI Settings
```python
class AIConfig(BaseModel):
    model: str = os.getenv("ANTHROPIC_MODEL", "claude-3-sonnet-20240229")
    max_tokens: int = 1024
    temperature: float = 0.7
    max_context_messages: int = 10
```

## Troubleshooting

### Browser Won't Join Meeting
- Ensure you have the correct Meet URL format: `https://meet.google.com/xxx-yyyy-zzz`
- Check that you've granted microphone and camera permissions
- Try running in non-headless mode: Set `headless: false` in `config.py`

### Permission Errors (macOS)
- Go to System Preferences → Security & Privacy
- Grant Screen Recording permission to Terminal/iTerm
- Grant Microphone and Camera permissions

### Missing API Keys
- Verify your `.env` file has all required keys
- Check that keys are valid and have sufficient credits
- Run `python main.py` to see which keys are missing

### Dependencies Installation Failed
- Ensure you're using Python 3.9+: `python --version`
- Try upgrading pip: `pip install --upgrade pip`
- For PyAudio issues on macOS: `brew install portaudio`

## Performance Targets

| Component | Target | Status |
|-----------|--------|--------|
| Screen capture | 2-5 FPS | ⏳ Pending |
| STT latency | <500ms | ⏳ Pending |
| AI analysis | <800ms | ⏳ Pending |
| TTS latency | <300ms | ⏳ Pending |
| Overlay refresh | 30 FPS | ⏳ Pending |
| **End-to-end** | **<2 seconds** | ⏳ Pending |

## Development

### Running Tests
```bash
pytest tests/
```

### Running with Debug Logging
```bash
# Set in .env
DEBUG_MODE=true
LOG_LEVEL=DEBUG

python main.py
```

### Project Structure
```
AI-agent-screenshare/
├── main.py                    # Entry point
├── config.py                  # Configuration
├── requirements.txt           # Dependencies
│
├── core/                      # Core orchestration
│   ├── orchestrator.py
│   ├── event_bus.py
│   └── state_manager.py
│
├── browser/                   # Browser automation
│   ├── meet_controller.py
│   └── audio_injector.py
│
├── capture/                   # Screen capture
│   ├── screen_capturer.py
│   └── frame_buffer.py
│
├── audio/                     # Audio processing
│   ├── audio_manager.py
│   ├── speech_to_text.py
│   ├── text_to_speech.py
│   └── vad_detector.py
│
├── ai/                        # AI processing
│   ├── claude_client.py
│   ├── vision_analyzer.py
│   └── context_manager.py
│
├── overlay/                   # Visual overlay
│   ├── macos_overlay.py
│   ├── drawing_engine.py
│   └── annotation_manager.py
│
└── utils/                     # Utilities
    ├── logger.py
    └── performance.py
```

## Contributing

This is currently a personal project. If you'd like to contribute:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is for educational and personal use.

## Roadmap

### Short-term (Next Sprint)
- [ ] Complete Phase 2: Screen capture implementation
- [ ] Complete Phase 3: Audio pipeline
- [ ] Test Meet joining on various scenarios

### Mid-term
- [ ] Complete AI integration with Claude vision
- [ ] Implement transparent overlay system
- [ ] End-to-end testing

### Long-term
- [ ] Support for Zoom and Microsoft Teams
- [ ] Multi-language support
- [ ] OCR for precise UI element detection
- [ ] Session recording and playback
- [ ] Web-based control panel

## Support

For issues, questions, or feedback:
- Create an issue on GitHub
- Check the troubleshooting section above
- Review logs in the `logs/` directory

## Acknowledgments

- Built with [Anthropic Claude](https://www.anthropic.com/) for AI vision and chat
- Uses [Playwright](https://playwright.dev/) for browser automation
- Powered by [OpenAI Whisper](https://openai.com/research/whisper) for speech recognition
- Voices by [ElevenLabs](https://elevenlabs.io/)

---

**Note**: This is an experimental project. Use responsibly and ensure you have permission to record and analyze meeting content.
