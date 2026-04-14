import logging
import logging.handlers
import sys


def setup_logging(level: str = 'INFO'):
    """ Настройка логирования для вывода в консоль """

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Консольный обработчик
    console_handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S'
                                  )
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)