import logging


# Define color codes for log levels
class LogFormatter(logging.Formatter):
    COLORS = {
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "RESET": "\033[39m",  # Reset color
    }

    def format(self, record: logging.LogRecord):
        log_message = super().format(record)
        levelname = record.levelname

        # Colorize log level (INFO, WARNING, ERROR)
        if levelname in self.COLORS:
            color = self.COLORS[levelname]
            log_message = log_message.replace(
                levelname, f"{color}{levelname}{self.COLORS['RESET']}"
            )

        return log_message


# Set up the logger
def setup_logger():
    # Define the format to exclude milliseconds and use HH:MM:SS format
    formatter = LogFormatter(
        "%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Create a custom StreamHandler for console output
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)

    # Set up the logger and add the custom handler
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(ch)

    return logger


logger = setup_logger()

# Example log messages
if __name__ == "__main__":
    logger = setup_logger()
    logger.info("This is an info message.")
    logger.warning("This is a warning message.")
    logger.error("This is an error message.")
