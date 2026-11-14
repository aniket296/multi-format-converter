"""Application entrypoint for Multi-Format Document Batch Converter."""
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)

from src.gui.app import MultiFormatConverterApp, enable_windows_high_dpi
from src.utils.logger import get_logger


def main() -> None:
    """Initializes High-DPI desktop studio and starts the application loop."""
    enable_windows_high_dpi()
    logger = get_logger("main")
    logger.info("Launching Multi-Format Document Batch Converter Desktop Studio...")
    app = MultiFormatConverterApp()
    app.run()


if __name__ == "__main__":
    main()
