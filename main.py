"""Main entry point for AI Agent Screen Share Assistant."""
import asyncio
import sys
from config import config
from core.orchestrator import Orchestrator
from simple_logger import logger


async def main():
    """Main application entry point."""
    logger.info("=" * 60)
    logger.info("AI Agent Screen Share Assistant")
    logger.info("=" * 60)

    # Validate API keys
    missing_keys = config.validate_api_keys()
    if missing_keys:
        logger.error("Missing required API keys:")
        for key in missing_keys:
            logger.error(f"  - {key}")
        logger.error("Please configure these in your .env file")
        logger.error("See .env.example for reference")
        return 1

    # Check for Meet URL
    meet_url = config.meet_url
    if not meet_url:
        logger.warning("No MEET_URL configured in .env file")
        meet_url = input("Please enter the Google Meet URL: ").strip()

        if not meet_url:
            logger.error("No Meet URL provided. Exiting.")
            return 1

    # Validate Meet URL
    if not meet_url.startswith('https://meet.google.com/'):
        logger.error("Invalid Meet URL. Must start with https://meet.google.com/")
        return 1

    logger.info(f"Meet URL: {meet_url}")

    # Create and start orchestrator
    orchestrator = Orchestrator()

    try:
        # Start the full orchestrator workflow
        await orchestrator.start(meet_url)

        logger.success("Application is running. Press Ctrl+C to exit.")

        # Keep the application running
        while orchestrator.is_running():
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        logger.info("\nShutting down gracefully...")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Stop orchestrator
        await orchestrator.stop()

    logger.info("Application terminated")
    return 0


if __name__ == "__main__":
    try:
        # Run playwright install before starting the main loop
        import subprocess
        subprocess.run(["playwright", "install"], check=True)
        
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        print("EXCEPTION:",f"Unexpected error: {e}")
        sys.exit(1)
