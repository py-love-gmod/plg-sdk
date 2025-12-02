import argparse
import logging
import sys
from importlib.metadata import PackageNotFoundError, version

from colorama import Fore, Style, init

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
    sub.add_parser(
        "init",
        help="Выплёвывает базовый объект plg-sdk-config.toml в текущую деррикторию",
    )
    # endregion

    # region Version cmd
    sub.add_parser("version", help="Показывает версию plg-sdk")
    # endregion

    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    logger.setLevel(logging.DEBUG if args.debug else logging.INFO)

    logger.debug(f"plg-sdk\nVersion: {_verison()}")

    try:
        if args.cmd == "init":
            init_cmd(_verison())

        elif args.cmd == "version":
            print(_verison())

        sys.exit(0)

    except Exception as err:
        logger.error(str(err), exc_info=True)
        logger.error("Exit code 3")
        sys.exit(3)
