class EdiException(Exception):
    """
    Base EdiException
    """


class EdiUnknownMessageType(EdiException):
    """
    Unknown/Unhandled Message
    """
