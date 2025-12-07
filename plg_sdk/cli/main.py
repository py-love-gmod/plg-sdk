import argparse
import logging
import sys
from importlib.metadata import PackageNotFoundError, version

from colorama import Fore, Style, init

from ..core import Config, ConfigValidator
from .init_cmd import init_cmd

init(autoreset=True)


# region Logger and color
class AlignedColorFormatter(logging.Formatter):
    COLORS = {
        "DEBUG": Fore.CYAN,
        "INFO": Fore.GREEN,
        "WARNING": Fore.YELLOW,
        "ERROR": Fore.RED,
        "CRITICAL": Fore.MAGENTA + Style.BRIGHT,
    }

    def __init__(self, fmt=None, datefmt=None, level_width=8):
        super().__init__(fmt, datefmt)
        self.level_width = level_width

    def format(self, record):
        if not isinstance(record.msg, str):
            record.msg = str(record.msg)

        levelname = record.levelname
        color = self.COLORS.get(levelname, "")
        padded_level = f"{color}{levelname:<{self.level_width}}{Style.RESET_ALL}"

        if "\n" in record.msg:
            lines = record.msg.splitlines()
            record.msg = ("\n" + " " * (self.level_width + 3)).join(lines)

        record.levelname = padded_level
        return super().format(record)


logger = logging.getLogger("plg-sdk")
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
formatter = AlignedColorFormatter("[%(levelname)s] %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)
# endregion


def _verison() -> str:
    try:
        return version("plg-sdk")

    except PackageNotFoundError:
        return "0.0.0dev"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="plg-sdk",
        description="Оркестровый инстурмент для всех утилит python love gmod",
    )

    # region Main args
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="Включить режим отладки",
    )
    # endregion

    sub = parser.add_subparsers(dest="cmd", required=True)

    # region init cmd
    init_cmd = sub.add_parser(
        "init",
        help="Выплёвывает базовый объект plg-sdk-config.toml в текущую деррикторию",
    )
    init_cmd.add_argument(
        "-n",
        "--no-comments",
        action="store_true",
        help="Убирает комментарии из toml файла при генерации",
    )
    # endregion

    # region Version cmd
    sub.add_parser("version", help="Показывает версию plg-sdk")
    # endregion

    # region config-validate
    sub.add_parser("config-validate", help="Вызывает только валидацию конфига")
    # endregion

    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    Config.init()

    if args.debug:
        Config.set("config.plg-sdk.debug", True)

    logger.setLevel(
        logging.DEBUG if Config.get("config.plg-sdk.debug", False) else logging.INFO
    )
    logger.debug(
        "plg-sdk\n"
        f"Version     : {_verison()}\n"
        f"DataPath    : {Config.sdk_path()}\n"
        f"ConfigFile  : {Config.config_file()}\n"
        f"ResourcePath: {Config.resource_path()}"
    )

    try:
        match args.cmd:
            case "init":
                init_cmd(_verison(), args.no_comments)

            case "version":
                print(_verison())

            case "config-validate":
                ConfigValidator.validate()
                for war_log in ConfigValidator.warnings():
                    logger.warning(war_log)

                for err_log in ConfigValidator.errors():
                    logger.error(err_log)

                if ConfigValidator.errors():
                    logger.error("Exit code 1")
                    sys.exit(1)

                if ConfigValidator.warnings():
                    logger.warning("Конфиг рабочий, но есть предупреждения")

                else:
                    logger.info("Всё в порядке\nOwO")

            case _:
                pass

        sys.exit(0)

    except KeyboardInterrupt:
        logger.debug("Пользователь самостоятельно прервал выполнение программы")
        sys.exit(0)

    except Exception as err:
        logger.error(str(err), exc_info=True)
        logger.error("Exit code 3")
        sys.exit(3)
