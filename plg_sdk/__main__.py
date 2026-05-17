import argparse
import logging

from cli import Shutdown, logger
from core import Config


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="plg-sdk",
        description="Оркестровый инструмент для всех утилит python love gmod",
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

    # region Version cmd
    sub.add_parser("version", help="Показывает версию plg-sdk")
    # endregion

    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    if args.debug:
        Config.set("config.plg-sdk.debug", True)

    logger.setLevel(
        logging.DEBUG if Config.get("config.plg-sdk.debug", False) else logging.INFO
    )
    logger.debug(
        "plg-sdk\n"
        f"Version     : {Config.version()}\n"
        f"DataPath    : {Config.sdk_path()}\n"
        f"ConfigFile  : {Config.config_file()}\n"
        f"ResourcePath: {Config.resource_path()}"
    )

    try:
        match args.cmd:
            case "version":
                print(Config.version())

            case _:
                pass

        Shutdown.type_ok()

    except KeyboardInterrupt:
        Shutdown.type_ok()

    except Exception as err:
        Shutdown.type_sdk_err(str(err))


if __name__ == "__main__":
    main()
