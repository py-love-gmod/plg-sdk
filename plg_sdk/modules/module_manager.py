import concurrent.futures
import importlib.metadata
import json
import logging
import subprocess
import sys
import urllib.request

logger = logging.getLogger("plg-sdk")


class ModuleManager:
    _modules: set[str] = set()

    # region get module version
    @staticmethod
    def _get_version_via_pip_api(module: str) -> str | None:
        try:
            with urllib.request.urlopen(
                f"https://pypi.org/pypi/{module}/json",
                timeout=5,
            ) as resp:
                return json.load(resp)["info"]["version"]

        except Exception as err:
            # Я не считаю что это должно быть именно error
            # По факту тут может быть что угодно, от таймаута до битого json
            # Не вижу смысла ловить каждое отдельно. Всё однофигственно
            logger.debug(f"Обращение к апи pip для модуля {module} не удалось\n{err}")
            return None

    @staticmethod
    def _get_version_via_local_api(module: str) -> str | None:
        try:
            return importlib.metadata.version(module)

        except importlib.metadata.PackageNotFoundError:
            return None

        except Exception as err:
            # Аналогично тому что выше
            # Может не нашли наш модуль или ещё какая-то параша
            logger.debug(f"Обращение к локали для модуля {module} не удалось\n{err}")
            return None

    # endregion

    @classmethod
    def setup_modules(cls, modules: set[str]) -> None:
        cls._modules = modules.copy()

    @classmethod
    def update_install_modules(cls, modules: set[str]) -> None:
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-U", *modules],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

        except Exception as err:
            logger.debug(f"pip install для модулей {modules} не удался\n{err}")
            return

        cls._modules.update(modules)

    @classmethod
    def request_pip_versions(cls) -> dict[str, str | None]:
        out = {}

        def _thread_func(module):
            return module, cls._get_version_via_pip_api(module)

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=min(4, len(cls._modules))
        ) as pool:
            futures = [pool.submit(_thread_func, module) for module in cls._modules]
            for future in concurrent.futures.as_completed(futures):
                module, version = future.result()
                out[module] = version

        return out

    @classmethod
    def request_local_versions(cls) -> dict[str, str | None]:
        out = {}
        for module in cls._modules:
            out[module] = cls._get_version_via_local_api(module)

        return out
