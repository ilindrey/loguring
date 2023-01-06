import logging
from atexit import register as atexit_register
from logging.config import dictConfig
from sys import stdout
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    Set,
    Tuple,
    TypeVar,
    Union,
)

from logging_tree import tree as logging_tree  # type: ignore
from loguru import _defaults as defaults
from loguru._logger import Core, Logger


__version__ = "1.0.0"
__all__ = ("logger", "ConfigureLogger")


InterceptHandlerT = TypeVar("InterceptHandlerT", bound="InterceptHandler")
ConfigureLoggerT = TypeVar("ConfigureLoggerT", bound="ConfigureLogger")


logger = Logger(
    core=Core(),
    exception=None,
    depth=0,
    record=False,
    lazy=False,
    colors=False,
    raw=False,
    capture=True,
    patcher=[],
    extra={},
)


class InterceptHandler(logging.Handler):
    """Handler redirecting logging library's logs to loguru.

    https://loguru.readthedocs.io/en/0.6.0/overview.html#entirely-compatible-with-standard-logging
    """

    def __init__(
        self: InterceptHandlerT, loguru_logger: Logger, *args: Any, **kwargs: Any
    ) -> None:
        self._logger = loguru_logger
        super().__init__(*args, **kwargs)

    def emit(self: InterceptHandlerT, record: logging.LogRecord) -> None:
        # Get corresponding Loguru level if it exists
        try:
            level = self._logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back  # type: ignore
            depth += 1

        self._logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


class ConfigureLogger:
    def __init__(
        self: ConfigureLoggerT,
        loguru_logger: Logger = logger,
        override_loggers: Optional[Iterable[str]] = None,
        level: Union[str, int] = defaults.LOGURU_LEVEL,
        format: Union[Callable, str, None] = defaults.LOGURU_FORMAT,
        filter: Union[Callable, str, Dict, None] = defaults.LOGURU_FILTER,
        colorize: bool = defaults.LOGURU_COLORIZE,
        serialize: bool = defaults.LOGURU_SERIALIZE,
        backtrace: bool = defaults.LOGURU_BACKTRACE,
        diagnose: bool = defaults.LOGURU_DIAGNOSE,
        enqueue: bool = defaults.LOGURU_ENQUEUE,
        catch: bool = defaults.LOGURU_CATCH,
    ) -> None:
        self._logger = loguru_logger

        self._level = level
        self._format = format
        self._filter = filter
        self._colorize = colorize
        self._serialize = serialize
        self._backtrace = backtrace
        self._diagnose = diagnose
        self._enqueue = enqueue
        self._catch = catch

        self.initialize(override_loggers)

    def initialize(
        self: ConfigureLoggerT, override_loggers: Optional[Iterable[str]] = None
    ) -> None:
        """Sets the logging configuration.

        :param override_loggers: additional logging library's loggers,
            which must be overridden if the `loguring' library has not done so itself.
        """
        self._logger.remove()  # Remove the default loguru configuration

        # to correctly identify module, file, func, line and
        # other message call parameters
        logging.basicConfig(
            handlers=[InterceptHandler(self._logger)], level=self._level, force=True
        )  # type: ignore

        # '' - root logger
        override_loggers = {"", *(override_loggers or ())}
        self._find_logging_loggers(logging_tree(), override_loggers)

        self._override_logging_config(override_loggers)
        self._configure_logger()

    def _find_logging_loggers(
        self: ConfigureLoggerT, logger_tree: Tuple, override_loggers: Set[str]
    ) -> None:
        """
        Recursively searches for logging library's loggers with handlers installed.
        """
        for standard_logger in logger_tree[2]:
            if not isinstance(standard_logger[1], logging.PlaceHolder):
                override_loggers.add(standard_logger[0])
            self._find_logging_loggers(standard_logger, override_loggers)

    def _get_logging_config(
        self: ConfigureLoggerT, override_loggers: Iterable[str]
    ) -> Dict[str, Any]:
        return {
            "version": 1,
            "disable_existing_loggers": True,
            "incremental": False,
            "handlers": {
                "default": {
                    "loguru_logger": self._logger,
                    "level": self._level,
                    "class": "loguring.InterceptHandler",
                },
            },
            "loggers": {
                logger_name: {
                    "handlers": ("default",),
                    "loguru_logger": self._logger,
                    "level": self._level,
                    "propagate": False,
                }
                for logger_name in override_loggers
            },
        }

    def _override_logging_config(
        self: ConfigureLoggerT, override_loggers: Iterable[str]
    ) -> None:
        config = self._get_logging_config(override_loggers)
        dictConfig(config)  # type: ignore

    def _get_logger_handlers(self: ConfigureLoggerT) -> List[Dict[str, Any]]:
        return [
            {
                "sink": stdout,
                "level": self._level,
                "format": self._format,
                "filter": self._filter,
                "colorize": self._colorize,
                "serialize": self._serialize,
                "backtrace": self._backtrace,
                "diagnose": self._diagnose,
                "enqueue": self._enqueue,
                "catch": self._catch,
            }
        ]

    def _configure_logger(self: ConfigureLoggerT) -> None:
        handlers = self._get_logger_handlers()
        self._logger.configure(handlers=handlers)


if defaults.env("LOGURING_AUTOINIT", bool, True):
    ConfigureLogger()

atexit_register(logger.remove)
