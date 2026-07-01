"""Seed script for mock integration data documentation.

Prints a summary of all mock users (Active Directory) and mock tickets
(ServiceNow) available in development. Useful for onboarding and testing.

Usage:
    python scripts/seed_mock_data.py

Implemented in Phase 3c.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def main() -> None:
    """Print a summary of available mock data for development."""
    ...


if __name__ == "__main__":
    main()
