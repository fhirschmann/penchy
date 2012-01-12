import logging


def configure(level=logging.INFO):
    """
    Configure the root logger for our purposes.
    """
    logging.root.setLevel(level)
    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logging.root.addHandler(ch)
