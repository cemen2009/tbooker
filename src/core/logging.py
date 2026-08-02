import logging
import sys


def setup_logging(debug: bool) -> None:
    level = logging.DEBUG if debug else logging.INFO
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    if not root_logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setLevel(level)
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s - %(name)s - [%(levelname)s] - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        root_logger.addHandler(handler)
    else:
        # if the level was changed during a second call, update it
        root_logger.handlers[0].setLevel(level)
    
    # here we can quit third party libraries, because they're noisy at INFO/DEBUG
    # e.g. logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    # e.g. logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
