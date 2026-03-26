"""
utils/logger.py
Advanced Telemetry Logger for Debug branch.
Writes C++ style deep-logs to 'logs/' folder and streams to Telegram in real-time.
"""
import logging
import logging.handlers
import os
import atexit
import shutil
import requests
import telegram_bot_logger

_configured = set()

# User Provided Telegram Credentials
TELEGRAM_BOT_TOKEN = "8657739570:AAGIeHRvnPcNSX3aGweEawlhpt6jcQgnz0o"
TELEGRAM_CHAT_ID = -5244837446

LOGS_DIR = os.path.join(os.getcwd(), "logs")
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

LOG_FILE = os.path.join(LOGS_DIR, "pdfos_debug.log")


def get_logger(name: str) -> logging.Logger:
    """Get an advanced telemetry logger with rotating files and Telegram support."""
    logger = logging.getLogger(f"pdfos.{name}")
    if name in _configured:
        return logger
    _configured.add(name)
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        # C++ Style Formatting
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [PID:%(process)d|TID:%(thread)d] %(module)s.%(funcName)s:%(lineno)d - %(message)s"
        )

        # Console Handler
        sh = logging.StreamHandler()
        sh.setLevel(logging.INFO)
        sh.setFormatter(formatter)
        logger.addHandler(sh)

        # File Handler (Rotating 10MB)
        fh = logging.handlers.RotatingFileHandler(LOG_FILE, maxBytes=10*1024*1024, backupCount=5, encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

        # Telegram Bot Real-time Handler
        try:
            tg_handler = telegram_bot_logger.TelegramMessageHandler(
                bot_token=TELEGRAM_BOT_TOKEN,
                chat_ids=[TELEGRAM_CHAT_ID]
            )
            # Send DEBUG to Telegram directly
            tg_handler.setLevel(logging.DEBUG)
            tg_handler.setFormatter(logging.Formatter("[%(levelname)s] %(module)s.%(funcName)s - %(message)s"))
            logger.addHandler(tg_handler)
        except Exception as e:
            # Fallback if telegram network fails
            pass

    return logger

def log_operation(module, operation, input_file=None, output_file=None, success=True, details=None, error=None):
    """Log a PDF operation with deep forensics."""
    logger = get_logger(module)
    parts = [f"OP=[{operation}]"]
    if input_file: parts.append(f"IN=[{os.path.basename(input_file)}]")
    if output_file: parts.append(f"OUT=[{os.path.basename(output_file)}]")
    if details: parts.append(f"DATA=[{details}]")
    
    msg = " | ".join(parts)
    if success:
        logger.debug(f"SUCCESS: {msg}")
    else:
        logger.error(f"FAILURE: {msg} | ERR=[{error}]")

def log_resource_usage(cpu, ram_mb, ram_percent):
    """Log hardware telemetry mapping."""
    logger = get_logger("sys.monitor")
    logger.debug(f"TELEMETRY: CPU=[{cpu:.1f}%] RAM=[{ram_mb:.1f}MB | {ram_percent:.1f}%]")

def log_memory_cleanup(freed, module="gc"):
    """Log garbage collection dumps."""
    logger = get_logger("sys.garbage")
    logger.debug(f"GC DUMP: Emptied {freed} objects from heap.")


def _send_telemetry_zip():
    """Triggered on app exit to zip the logs folder and send it to telegram."""
    try:
        archive_path = os.path.join(os.getcwd(), "pdfos_logs_backup")
        shutil.make_archive(archive_path, "zip", LOGS_DIR)
        
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
        with open(f"{archive_path}.zip", "rb") as f:
            requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "caption": "PDFOS Session Diagnostic Logs"}, files={"document": f})
        
        os.remove(f"{archive_path}.zip")
    except Exception:
        pass

# Automatically dump physical ZIP logs when the app shuts down
atexit.register(_send_telemetry_zip)
