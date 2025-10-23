import logging, sys

def setup_logger(name: str):
    handler = logging.StreamHandler(sys.stdout)
    fmt = logging.Formatter("%(asctime)s | ENGINE-B | %(levelname)s | %(message)s")
    handler.setFormatter(fmt)
    log = logging.getLogger(name)
    log.setLevel(logging.INFO)
    if not log.handlers:
        log.addHandler(handler)
    return log
