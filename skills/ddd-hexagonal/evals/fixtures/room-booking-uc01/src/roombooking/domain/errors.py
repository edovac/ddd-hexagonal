class BookingRejected(Exception):
    """A business rule refused the request. `code` is the rule's error code in business-rules.md."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code
