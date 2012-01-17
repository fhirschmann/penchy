import logging


def configure(level=logging.INFO):
    """
    Configure the root logger for our purposes.
    """
    logging.root.setLevel(level)
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    ch2 = logging.FileHandler('penchy.log')
    ch2.setFormatter(formatter)

    logging.root.addHandler(ch)
    logging.root.addHandler(ch2)


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
