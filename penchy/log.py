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


def configure_for_tests():
    """
    Configure the root logger to be silent.
    """
    logging.root.handlers = []
    logging.root.addHandler(NullHandler())


class NullHandler(logging.Handler):  # pragma: no cover
    """
    Handler that does nothing.
    """
    def handle(self, record):
        pass

    def emit(self, record):
        pass

    def createLock(self):
        self.lock = None
