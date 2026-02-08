import logging
from logging.handlers import RotatingFileHandler


def create_logger(logger_name: str = __name__):
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)

    console_handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s" )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


    # File handler
    file_handler = RotatingFileHandler('logs/bot.log', maxBytes=1000000, backupCount=3)
    file_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    return logger
