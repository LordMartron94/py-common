from ..logging import HoornLogger


class InterfaceInstantiationException(BaseException):
    """An exception that is thrown when trying to instantiate an interface directly."""

    def __init__(self, logger: HoornLogger, separator: str):
        message: str = "You cannot instantiate an interface directly."
        logger.error("You cannot instantiate an interface directly.", separator=separator)
        super().__init__(message)

class InterfaceInstantiationError(TypeError):
    """Raised when an attempt is made to directly instantiate a class
    that is decorated with @interface.
    """
    def __init__(self, cls):
        message = f"Cannot instantiate the interface '{cls.__name__}' directly. You must subclass it."
        super().__init__(message)
