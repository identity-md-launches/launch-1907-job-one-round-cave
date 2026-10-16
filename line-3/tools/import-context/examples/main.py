"""Source-only demonstration: these imports are never executed by the scanner."""
from typing import TYPE_CHECKING
import core

if TYPE_CHECKING:
    import model
else:
    import fallback

try:
    import optional_backend
except ImportError:
    import fallback


def run():
    import core
    if __name__ == '__main__':
        import model


if __name__ == '__main__':
    run()
