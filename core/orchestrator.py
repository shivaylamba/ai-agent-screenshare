"""Main orchestrator coordinating all components."""
import asyncio
from typing import Optional
from simple_logger import logger
from core.event_bus import EventBus, Event
from core.state_manager import StateManager
from browser.meet_controller import MeetController
from browser.audio_injector import AudioInjector
from capture.screen_capturer import ScreenCapturer
from capture.frame_buffer import FrameBuffer
from audio.audio_manager import AudioManager
from ai.vision_analyzer import VisionAnalyzer
from ai.context_manager import ContextManager
from overlay.annotation_manager import AnnotationManager
from config import config


class Orchestrator:
    """Main orchestrator for the AI agent system."""

    def __init__(self):
        """Initialize orchestrator."""
        # Core components
        self.event_bus = EventBus()
        self.state = StateManager()

        # Component instances (will be initialized in start())
        self.meet_controller: Optional[MeetController] = None
        self.audio_injector: Optional[AudioInjector] = None
        self.screen_capturer: Optional[ScreenCapturer] = None
        self.frame_buffer: Optional[FrameBuffer] = None
        self.audio_manager: Optional[AudioManager] = None
        self.vision_analyzer: Optional[VisionAnalyzer] = None
        self.context_manager: Optional[ContextManager] = None
        self.annotation_manager: Optional[AnnotationManager] = None

        # Task handles
        self._tasks = []
        self._running = False

        logger.info("Orchestrator initialized")

    async def start(self, meet_url: str):
        """
        Start the orchestrator and all components.

        Args:
            meet_url: Google Meet URL to join
        """
        logger.info("=" * 60)
        logger.info("Starting AI Agent Orchestrator")
        logger.info("=" * 60)

        try:
            # Initialize all components
            await self._initialize_components(meet_url)

            # Set up event subscriptions
            self._setup_event_subscriptions()

            # Start all async loops
            await self._start_loops()

            self._running = True
            logger.success("Orchestrator started successfully")

        except Exception as e:
            logger.error(f"Error starting orchestrator: {e}")
            await self.stop()
            raise

    async def _initialize_components(self, meet_url: str):
        """Initialize all system components."""
        logger.info("Initializing components...")

        # 1. Join Meet
        self.meet_controller = MeetController()
        success = await self.meet_controller.join_meeting(meet_url)
        if not success:
            raise Exception("Failed to join Meet")

        await self.state.set_meeting_state(in_meeting=True)

        # 2. Initialize audio injector
        if self.meet_controller.page:
            self.audio_injector = AudioInjector(self.meet_controller.page)
            await self.audio_injector.initialize_audio_context()

        # 3. Wait for screen share
        logger.info("Waiting for screen share...")
        screen_bounds = await self._wait_for_screen_share()

        if screen_bounds:
            # 4. Initialize screen capture
            self.screen_capturer = ScreenCapturer(region=screen_bounds)
            self.frame_buffer = FrameBuffer(max_size=config.ai.max_context_frames)
            await self.state.set_meeting_state(in_meeting=True, screen_share=True)

        # 5. Initialize AI components
        self.vision_analyzer = VisionAnalyzer()
        self.context_manager = ContextManager()

        # 6. Initialize audio
        self.audio_manager = AudioManager()

        # 7. Initialize overlay (simplified - needs Qt event loop)
        self.annotation_manager = AnnotationManager()

        logger.success("All components initialized")

    async def _wait_for_screen_share(self, max_attempts: int = 30) -> Optional[dict]:
        """Wait for screen share to be detected."""
        for attempt in range(max_attempts):
            await asyncio.sleep(2)
            bounds = await self.meet_controller.get_screen_share_bounds()
            if bounds:
                logger.success(f"Screen share detected: {bounds}")
                return bounds
            logger.debug(f"Waiting for screen share... ({attempt + 1}/{max_attempts})")

        logger.warning("Screen share not detected")
        return None

    def _setup_event_subscriptions(self):
        """Set up event subscriptions between components."""
        logger.info("Setting up event subscriptions...")

        # Subscribe to user speech events
        asyncio.create_task(self._handle_user_speech())

        # Subscribe to AI response events
        asyncio.create_task(self._handle_ai_responses())

        # Subscribe to screen change events
        asyncio.create_task(self._handle_screen_changes())

        logger.info("Event subscriptions configured")

    async def _handle_user_speech(self):
        """Handle user speech events."""
        queue = self.event_bus.subscribe(['user_spoke'])

        while self._running:
            event: Event = await queue.get()
            try:
                text = event.data
                logger.info(f"User said: '{text}'")

                # Add to context
                self.context_manager.add_user_message(text)

                # Get current screen
                screen = await self.state.get_current_screen()

                if screen is not None:
                    # Analyze with AI
                    await self.state.set_processing(True)
                    result = await self.vision_analyzer.analyze_frame(
                        frame=screen,
                        query=text,
                        context=self.context_manager.get_context()
                    )

                    # Publish AI response
                    await self.event_bus.publish('ai_response', result)
                    await self.state.set_processing(False)

            except Exception as e:
                logger.error(f"Error handling user speech: {e}")

    async def _handle_ai_responses(self):
        """Handle AI response events."""
        queue = self.event_bus.subscribe(['ai_response'])

        while self._running:
            event: Event = await queue.get()
            try:
                result = event.data
                response_text = result.get('text', '')

                logger.info(f"AI response: '{response_text[:100]}...'")

                # Add to context
                self.context_manager.add_assistant_message(response_text)

                # Synthesize and play audio
                if self.audio_manager:
                    await self.audio_manager.synthesize_and_play(response_text)

                # Handle annotations (if any)
                annotations = result.get('annotations', [])
                if annotations and self.annotation_manager:
                    await self.annotation_manager.add_annotations(annotations)

            except Exception as e:
                logger.error(f"Error handling AI response: {e}")

    async def _handle_screen_changes(self):
        """Handle screen change events."""
        queue = self.event_bus.subscribe(['screen_changed'])

        while self._running:
            event: Event = await queue.get()
            try:
                frame = event.data
                await self.state.update_screen(frame)

            except Exception as e:
                logger.error(f"Error handling screen change: {e}")

    async def _start_loops(self):
        """Start all async loops."""
        logger.info("Starting async loops...")

        # Start screen capture loop
        if self.screen_capturer:
            task = asyncio.create_task(self._screen_capture_loop())
            self._tasks.append(task)

        # Set up audio callbacks
        if self.audio_manager:
            self.audio_manager.set_transcription_callback(self._on_transcription)
            self.audio_manager.set_audio_generated_callback(self._on_audio_generated)

        logger.info(f"Started {len(self._tasks)} async loops")

    async def _screen_capture_loop(self):
        """Continuous screen capture loop."""
        logger.info("Screen capture loop started")

        try:
            while self._running:
                # Capture frame
                frame = await self.screen_capturer.capture_frame_optimized()

                if frame is not None:
                    # Check for changes
                    if self.screen_capturer.detect_significant_change(frame):
                        # Add to buffer
                        await self.frame_buffer.add_frame(frame, changed=True)

                        # Publish event
                        await self.event_bus.publish('screen_changed', frame)

                # Maintain FPS
                await asyncio.sleep(1.0 / config.screen.fps)

        except asyncio.CancelledError:
            logger.info("Screen capture loop cancelled")
        except Exception as e:
            logger.error(f"Error in screen capture loop: {e}")

    async def _on_transcription(self, text: str):
        """Callback for transcribed text."""
        await self.state.update_transcription(text)
        await self.event_bus.publish('user_spoke', text)

    async def _on_audio_generated(self, audio_data: bytes):
        """Callback for generated audio."""
        if self.audio_injector:
            await self.audio_injector.inject_audio(audio_data)

    async def stop(self):
        """Stop the orchestrator and clean up."""
        logger.info("Stopping orchestrator...")

        self._running = False

        # Cancel all tasks
        for task in self._tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        # Clean up components
        if self.meet_controller:
            await self.meet_controller.cleanup()

        if self.screen_capturer:
            self.screen_capturer.cleanup()

        logger.info("Orchestrator stopped")

    def is_running(self) -> bool:
        """
        Check if orchestrator is running.

        Returns:
            True if running
        """
        return self._running
