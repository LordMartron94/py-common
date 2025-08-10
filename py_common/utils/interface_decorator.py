from ..constants import COMMON_LOGGING_PREFIX
from ..exceptions.interface_exceptions import InterfaceInstantiationError
from ..logging import HoornLogger


def interface(logger_kwarg: str = 'logger'):
    """
    A configurable class decorator factory that prevents direct instantiation.

    Args:
        logger_kwarg (str): The name of the keyword argument that will hold the
                            logger instance during instantiation. Defaults to 'logger'.
    """
    def _decorator(cls):
        def new_new(subclass, *args, **kwargs):
            if subclass is cls:
                logger_instance: HoornLogger = kwargs.get(logger_kwarg)

                # If a logger was passed and it has an 'error' method, use it.
                if logger_instance:
                    msg = f"Instantiation of interface '{cls.__name__}' blocked."
                    logger_instance.error(msg, separator=f"{COMMON_LOGGING_PREFIX}.InterfaceValidation")

                raise InterfaceInstantiationError(cls)

            return object.__new__(subclass)

        cls.__new__ = new_new
        return cls

    return _decorator
