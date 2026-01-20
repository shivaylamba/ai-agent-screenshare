"""Configuration management for AI Agent Screen Share Assistant."""
import os
from typing import Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv()


class AudioConfig(BaseModel):
    """Audio processing configuration."""
    sample_rate: int = Field(default=16000, description="Audio sample rate in Hz")
    chunk_size: int = Field(default=1024, description="Audio chunk size for processing")
    channels: int = Field(default=1, description="Number of audio channels (1=mono)")
    vad_aggressiveness: int = Field(default=2, ge=0, le=3, description="Voice activity detection aggressiveness (0-3)")
    silence_duration: float = Field(default=0.5, description="Duration of silence to consider end of speech (seconds)")


class ScreenCaptureConfig(BaseModel):
    """Screen capture configuration."""
    fps: int = Field(default=2, ge=1, le=10, description="Frames per second for screen capture")
    change_threshold: float = Field(default=0.10, ge=0.01, le=1.0, description="Minimum change threshold (0-1) to trigger new AI analysis")
    max_width: int = Field(default=1280, description="Maximum width for captured images (maintains aspect ratio)")
    jpeg_quality: int = Field(default=85, ge=1, le=100, description="JPEG compression quality (1-100)")


class AIConfig(BaseModel):
    """AI model configuration."""
    anthropic_api_key: str = Field(default_factory=lambda: os.getenv('ANTHROPIC_API_KEY', ''))
    model: str = Field(default="claude-3-5-sonnet-20241022", description="Claude model ID")
    max_tokens: int = Field(default=1024, description="Maximum tokens for AI responses")
    temperature: float = Field(default=0.7, ge=0.0, le=1.0, description="Temperature for AI responses")
    max_context_messages: int = Field(default=10, description="Maximum number of messages in context history")
    max_context_frames: int = Field(default=5, description="Maximum number of screen frames to keep in context")


class TTSConfig(BaseModel):
    """Text-to-speech configuration."""
    provider: str = Field(default="elevenlabs", description="TTS provider (elevenlabs or google)")
    elevenlabs_api_key: str = Field(default_factory=lambda: os.getenv('ELEVENLABS_API_KEY', ''))
    voice_id: str = Field(default="Rachel", description="Voice ID for TTS")
    model: str = Field(default="eleven_monolingual_v1", description="TTS model")


class STTConfig(BaseModel):
    """Speech-to-text configuration."""
    provider: str = Field(default="whisper", description="STT provider (whisper)")
    openai_api_key: str = Field(default_factory=lambda: os.getenv('OPENAI_API_KEY', ''))
    model: str = Field(default="whisper-1", description="Whisper model ID")
    language: str = Field(default="en", description="Language code for transcription")


class OverlayConfig(BaseModel):
    """Visual overlay configuration."""
    opacity: float = Field(default=0.8, ge=0.0, le=1.0, description="Overlay opacity (0-1)")
    arrow_color: str = Field(default="#FF0000", description="Arrow color (hex)")
    highlight_color: str = Field(default="#FFFF00", description="Highlight color (hex)")
    text_color: str = Field(default="#FFFFFF", description="Text color (hex)")
    text_size: int = Field(default=16, ge=8, le=72, description="Text font size")
    arrow_thickness: int = Field(default=3, ge=1, le=10, description="Arrow line thickness")
    default_duration: float = Field(default=5.0, description="Default duration for annotations (seconds)")
    refresh_rate: int = Field(default=30, description="Overlay refresh rate (FPS)")


class BrowserConfig(BaseModel):
    """Browser automation configuration."""
    headless: bool = Field(default=False, description="Run browser in headless mode")
    user_agent: Optional[str] = Field(default=None, description="Custom user agent string")
    viewport_width: int = Field(default=1920, description="Browser viewport width")
    viewport_height: int = Field(default=1080, description="Browser viewport height")
    timeout: int = Field(default=30000, description="Default timeout for browser operations (ms)")


class AppConfig(BaseModel):
    """Main application configuration."""
    # Sub-configurations
    audio: AudioConfig = Field(default_factory=AudioConfig)
    screen: ScreenCaptureConfig = Field(default_factory=ScreenCaptureConfig)
    ai: AIConfig = Field(default_factory=AIConfig)
    tts: TTSConfig = Field(default_factory=TTSConfig)
    stt: STTConfig = Field(default_factory=STTConfig)
    overlay: OverlayConfig = Field(default_factory=OverlayConfig)
    browser: BrowserConfig = Field(default_factory=BrowserConfig)

    # General settings
    meet_url: str = Field(default_factory=lambda: os.getenv('MEET_URL', ''))
    log_level: str = Field(default_factory=lambda: os.getenv('LOG_LEVEL', 'INFO'))
    debug_mode: bool = Field(default_factory=lambda: os.getenv('DEBUG_MODE', 'false').lower() == 'true')

    def validate_api_keys(self) -> list[str]:
        """Validate that all required API keys are present."""
        missing_keys = []

        if not self.ai.anthropic_api_key:
            missing_keys.append('ANTHROPIC_API_KEY')

        if not self.stt.openai_api_key:
            missing_keys.append('OPENAI_API_KEY')

        if self.tts.provider == 'elevenlabs' and not self.tts.elevenlabs_api_key:
            missing_keys.append('ELEVENLABS_API_KEY')

        return missing_keys


# Global configuration instance
config = AppConfig()
