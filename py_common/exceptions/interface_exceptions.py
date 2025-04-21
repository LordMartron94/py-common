from ..logging import HoornLogger


class InterfaceInstantiationException(BaseException):
    """An exception that is thrown when trying to instantiate an interface directly."""

    def __init__(self, logger: HoornLogger, separator: str):
        message: str = "You cannot instantiate an interface directly."
        logger.error("You cannot instantiate an interface directly.", separator=separator)
        super().__init__(message)
