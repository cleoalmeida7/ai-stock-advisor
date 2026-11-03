class DuplicateHoldingError(Exception):
    """Raised when a user already holds the given instrument (unique (user_id, instrument_id))."""


class InstrumentNotFoundError(Exception):
    """Raised when a holding references an instrument_id that doesn't exist in the instrument master."""
