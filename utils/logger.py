"""
utils/logger.py
Lightweight logging — console only (no file output).
"""
import logging

_configured = set()


def get_logger(name: str) -> logging.Logger:
    """Get a console-only logger."""
    logger = logging.getLogger(f"pdfos.{name}")
    if name in _configured:
        return logger
    _configured.add(name)
    logger.setLevel(logging.DEBUG)
    if not logger.handlers:
        h = logging.StreamHandler()
        h.setLevel(logging.INFO)
        h.setFormatter(logging.Formatter(
            "[%(levelname)-8s] [%(name)-20s] %(message)s"
        ))
        logger.addHandler(h)
    return logger


def log_operation(module, operation, input_file=None, output_file=None,
                  success=True, details=None, error=None):
    """Log a PDF operation (console only)."""
    logger = get_logger(module)
    import os
    parts = [f"op={operation}"]
    if input_file:
        parts.append(f"input=\"{os.path.basename(input_file)}\"")
    if details:
        parts.append(f"details=\"{details}\"")
    msg = " | ".join(parts)
    if success:
        logger.info(f"✓ {msg}")
    else:
        logger.error(f"✗ {msg} | error=\"{error}\"")


def log_resource_usage(cpu, ram_mb, ram_pct):
    pass  # Disabled for production


def log_memory_cleanup(freed, module="gc"):
    pass  # Disabled for production
