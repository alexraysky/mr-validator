import logging
import sys

logger = logging.getLogger("mr-validator")

class ColorFormatter(logging.Formatter):
    ANSI_RED = "\033[91m"
    ANSI_GREEN = "\033[92m"
    ANSI_YELLOW = "\033[93m"
    ANSI_BLUE = "\033[94m"
    ANSI_RESET = "\033[0m"

    def __init__(self, fmt=None, datefmt=None, use_color=True):
        super().__init__(fmt, datefmt)
        self.use_color = use_color

    def format(self, record):
        orig_msg = record.msg
        
        # Apply colors if enabled
        if self.use_color:
            if record.levelno == logging.ERROR:
                record.msg = f"{self.ANSI_RED}{orig_msg}{self.ANSI_RESET}"
            elif record.levelno == logging.WARNING:
                record.msg = f"{self.ANSI_YELLOW}{orig_msg}{self.ANSI_RESET}"
            elif record.levelno == logging.INFO:
                msg_str = str(orig_msg)
                if msg_str.startswith("[PASS]"):
                    record.msg = f"{self.ANSI_GREEN}{orig_msg}{self.ANSI_RESET}"
                elif msg_str.startswith("[FAIL]"):
                    record.msg = f"{self.ANSI_RED}{orig_msg}{self.ANSI_RESET}"
                elif "Result: PASS" in msg_str:
                    record.msg = f"{self.ANSI_GREEN}{orig_msg}{self.ANSI_RESET}"
                elif "Result: FAIL" in msg_str:
                    record.msg = f"{self.ANSI_RED}{orig_msg}{self.ANSI_RESET}"
        
        result = super().format(record)
        record.msg = orig_msg
        return result

def setup_logging(verbose: bool = False, quiet: bool = False, force_color: bool = None):
    """
    Configure logging for the mr-validator application.
    If quiet, set to ERROR.
    If verbose, set to DEBUG and print detailed formatting (timestamps, level names).
    Otherwise, set to INFO and print only the message.
    """
    if quiet:
        level = logging.ERROR
    elif verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO

    logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    for handler in list(logger.handlers):
        logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stderr)
    
    # Auto-detect color unless forced by parameter
    if force_color is not None:
        use_color = force_color
    else:
        use_color = sys.stderr.isatty()

    if verbose:
        fmt = "%(asctime)s [%(levelname)s] %(message)s"
    else:
        fmt = "%(message)s"

    formatter = ColorFormatter(fmt=fmt, datefmt="%Y-%m-%d %H:%M:%S", use_color=use_color)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
