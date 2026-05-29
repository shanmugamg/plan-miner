import logging
import os
import sys

LOG_NAME = "planminer"

def setup_logger(log_dir, level=logging.INFO):
    logger = logging.getLogger(LOG_NAME)
    if logger.handlers:
        return logger

    logger.setLevel(level)
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S"
    )

    # Security Audit Fix: Disable local log file creation in PyInstaller compiled builds
    is_compiled = getattr(sys, 'frozen', False)

    if not is_compiled:
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, "planminer.log")
        
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setLevel(level)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)
    else:
        from logging.handlers import RotatingFileHandler
        import re
        
        class RedactingFilter(logging.Filter):
            def filter(self, record):
                if isinstance(record.msg, str):
                    record.msg = re.sub(r'C:\\Users\\[^\\]+\\', r'C:\\Users\\<REDACTED>\\', record.msg, flags=re.IGNORECASE)
                return True
                
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, "planminer.log")
        
        file_handler = RotatingFileHandler(log_path, maxBytes=5*1024*1024, backupCount=2, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        file_handler.addFilter(RedactingFilter())
        logger.addHandler(file_handler)

    logger.propagate = False
    return logger

def get_logger():
    return logging.getLogger(LOG_NAME)
