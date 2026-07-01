"""Dev helper: generate a signed JWT for Dialogflow webhook configuration.

Usage:
    python scripts/generate_jwt.py

Reads JWT_SECRET_KEY and JWT_EXPIRY_MINUTES from .env.
Prints the signed token to stdout — paste into Dialogflow CX webhook settings.

Implemented in Phase 3b.
"""

import sys
from pathlib import Path

# Ensure the project root is on sys.path when run as a script
sys.path.insert(0, str(Path(__file__).parent.parent))


def main() -> None:
    """Generate and print a signed webhook JWT to stdout."""
    ...


if __name__ == "__main__":
    main()
