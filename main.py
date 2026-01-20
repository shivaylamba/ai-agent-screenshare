"""Main entry point for AI Agent Screen Share Assistant."""
import asyncio
import sys
from pathlib import Path
from config import config
from browser.meet_controller import MeetController
from capture.screen_capturer import ScreenCapturer
from capture.frame_buffer import FrameBuffer, FrameRateController
from utils.performance import perf_monitor


# Global variables for screen capture
screen_capturer = None
frame_buffer = None
capture_task = None


async def on_frame_captured(frame):
    """Callback for when a new frame is captured."""
    # Add frame to buffer
    await frame_buffer.add_frame(frame, changed=True)

    # Log buffer stats periodically
    if frame_buffer.current_frame_number % 10 == 0:
        stats = await frame_buffer.get_buffer_stats()
        print(f"Buffer stats: {stats}")

        # Log performance stats
        perf_monitor.log_stats()

    # Save a sample frame for debugging (every 20 frames)
    if config.debug_mode and frame_buffer.current_frame_number % 20 == 0:
        save_dir = Path("debug_frames")
        save_dir.mkdir(exist_ok=True)
        filename = save_dir / f"frame_{frame_buffer.current_frame_number}.jpg"
        screen_capturer.save_frame(frame, str(filename))


async def start_screen_capture(controller: MeetController):
    """Start screen capture of the shared screen."""
    global screen_capturer, frame_buffer, capture_task

    print("\n" + "=" * 60)
    print("Phase 2: Starting Screen Capture")
    print("=" * 60)

    # Wait a bit for screen share to start
    print("Waiting for screen share to be detected...")
    print("Please start sharing your screen in the Meet call")

    # Try to find screen share element
    max_attempts = 30
    for attempt in range(max_attempts):
        await asyncio.sleep(2)

        bounds = await controller.get_screen_share_bounds()
        if bounds:
            print("SUCCESS:",f"Screen share detected! Bounds: {bounds}")

            # Initialize screen capturer with the detected region
            screen_capturer = ScreenCapturer(region=bounds)

            # Initialize frame buffer
            frame_buffer = FrameBuffer(max_size=config.ai.max_context_frames)

            # Start continuous capture
            print("Starting continuous screen capture...")
            capture_task = asyncio.create_task(
                screen_capturer.start_continuous_capture(
                    callback=on_frame_captured,
                    check_for_changes=True
                )
            )

            return True

        print("DEBUG:",f"Attempt {attempt + 1}/{max_attempts}: No screen share detected yet")

    print("WARNING:","Screen share not detected after waiting")
    print("You can continue without screen capture, or restart after starting screen share")
    return False


async def main():
    """Main application entry point."""
    global screen_capturer, frame_buffer, capture_task

    # Setup logger
    print("=" * 60)
    print("AI Agent Screen Share Assistant")
    print("=" * 60)

    # Validate API keys
    missing_keys = config.validate_api_keys()
    if missing_keys:
        print("ERROR:","Missing required API keys:")
        for key in missing_keys:
            print("ERROR:",f"  - {key}")
        print("ERROR:","Please configure these in your .env file")
        print("See .env.example for reference")
        return 1

    # Check for Meet URL
    meet_url = config.meet_url
    if not meet_url:
        print("WARNING:","No MEET_URL configured in .env file")
        meet_url = input("Please enter the Google Meet URL: ").strip()

        if not meet_url:
            print("ERROR:","No Meet URL provided. Exiting.")
            return 1

    # Validate Meet URL
    if not meet_url.startswith('https://meet.google.com/'):
        print("ERROR:","Invalid Meet URL. Must start with https://meet.google.com/")
        return 1

    print(f"Meet URL: {meet_url}")

    # Phase 1: Browser automation and joining Meet
    print("\n" + "=" * 60)
    print("Phase 1: Joining Google Meet")
    print("=" * 60)

    async with MeetController() as controller:
        # Join the meeting
        success = await controller.join_meeting(meet_url)

        if not success:
            print("ERROR:","Failed to join Google Meet")
            return 1

        print("SUCCESS:","Successfully joined the meeting!")

        # Phase 2: Start screen capture
        await start_screen_capture(controller)

        print("\nApplication is running. Press Ctrl+C to exit.")

        # Keep the application running
        try:
            while True:
                await asyncio.sleep(5)

                # Check if still in meeting
                if not controller.is_joined:
                    print("WARNING:","No longer in meeting")
                    break

                # Log frame buffer stats
                if frame_buffer:
                    stats = await frame_buffer.get_buffer_stats()
                    print(f"Frames captured: {stats['current_frame_number']}, "
                              f"Changed: {stats['changed_frames']}, "
                              f"Buffer: {stats['buffer_utilization']}")

        except KeyboardInterrupt:
            print("\nShutting down gracefully...")

            # Cancel screen capture task
            if capture_task:
                capture_task.cancel()
                try:
                    await capture_task
                except asyncio.CancelledError:
                    pass

            # Cleanup screen capturer
            if screen_capturer:
                screen_capturer.cleanup()

    # Final performance stats
    print("\n" + "=" * 60)
    print("Final Performance Statistics")
    print("=" * 60)
    perf_monitor.log_stats()

    print("Application terminated")
    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        print("EXCEPTION:",f"Unexpected error: {e}")
        sys.exit(1)
