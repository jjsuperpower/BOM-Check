class PartSearchError(Exception):
    pass
class PartSearchRateLimitError(PartSearchError):
    pass
class PartSearchConnectionError(PartSearchError):
    pass
class PartSearchAuthError(PartSearchError):
    pass
class PartSearchBadRequestError(PartSearchError):
    pass