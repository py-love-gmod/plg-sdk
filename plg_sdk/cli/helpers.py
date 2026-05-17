import sys
from typing import NoReturn

from .setup_logs import logger

# 0 - ok
# 1 - user error
# 2 - module error
# 3 - sdk error
# 4 - system error


class Shutdown:
    @classmethod
    def type_ok(cls) -> NoReturn:
        sys.exit(0)

    @staticmethod
    def _log_if_reason(reason: str | None) -> None:
        if reason is not None:
            logger.error(reason)

    @classmethod
    def type_user_err(cls, reason: str) -> NoReturn:
        cls._log_if_reason(reason)
        sys.exit(1)

    @classmethod
    def type_module_err(cls, module: str, reason: str | None = None) -> NoReturn:
        logger.error(f"Произошла ошибка в модуле '{module}'")
        cls._log_if_reason(reason)
        sys.exit(2)

    @classmethod
    def type_sdk_err(cls, reason: str | None = None) -> NoReturn:
        logger.error("Произошла ошибка в SDK")
        cls._log_if_reason(reason)
        sys.exit(3)

    @classmethod
    def type_sys_err(cls, reason: str | None = None) -> NoReturn:
        logger.error("Произошла ошибка при работе с OS")
        cls._log_if_reason(reason)
        sys.exit(4)


__all__ = [
    "Shutdown",
]
