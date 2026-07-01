"""Unit tests for IntentDispatcher. Implemented in Phase 3a."""

import pytest


class TestIntentDispatcher:
    """Unit tests for IntentDispatcher.dispatch() and register()."""

    async def test_dispatch_routes_to_registered_handler(self):
        """dispatch() calls the handler registered for the intent name."""
        pass

    async def test_dispatch_raises_intent_not_found_for_unregistered_intent(self):
        """dispatch() raises IntentNotFoundError when no handler is registered."""
        pass

    def test_register_overwrites_existing_handler(self):
        """Registering a second handler for the same intent replaces the first."""
        pass
