"""The module init."""
import logging


try:  # Python 2.7+
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        """Null logging handler."""

        def emit(self, record):
            """Noop."""
            pass

logging.getLogger(__name__).addHandler(NullHandler())
