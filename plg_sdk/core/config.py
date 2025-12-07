import json
import re
import tomllib
from pathlib import Path
from typing import Any

from .pep440 import canonicalize


class ConfigValidator:
    _errors: list[str] = []
    _warnings: list[str] = []

    @classmethod
    def validate(
        cls,
    ) -> None:
        cls._errors = []
        cls._warnings = []

        # MODULES.allowed
        allowed = list(Config.get("config.modules.allowed", []))  # pyright: ignore[reportArgumentType]
        all_modules = list(Config.get("all_modules", []))  # pyright: ignore[reportArgumentType]

        if "all" not in allowed:
            for m in allowed:
                if m not in all_modules:
                    cls._errors.append(f'MODULES.allowed: модуль "{m}" не разрешён')

        # Обязательные поля
        required_fields = [
            "config.project.name",
            "config.project.author",
            "config.project.version",
        ]
        for key in required_fields:
            if Config.get(key) is None:
                _, err_key, cfg_key = key.split(".")
                cls._errors.append(f"{err_key.upper()}.{cfg_key} не задано")

        # Проверка версии
        ver = Config.get("config.project.version")
        if ver is not None:
            ver_c = canonicalize(str(ver))
            if ver_c is None:
                cls._errors.append("PROJECT.version не соответствует PEP440")

            elif ver_c != ver:
                cls._warnings.append(
                    "PROJECT.version не является канонической.\n"
                    f"Используется нормализованная версия: {ver_c}"
                )

        # Проверка namespace
        ns = Config.get("config.project.namespace")

        if ns == "%!DEFAULT!%":
            auto_ns = (
                str(Config.get("config.project.name"))
                + "_"
                + str(Config.get("config.project.author"))
            )

            if not re.fullmatch(r"[A-Za-z0-9_]+", auto_ns):
                cls._errors.append(
                    "PROJECT.namespace установлен в режим %!DEFAULT!%\n"
                    "Ошибка в автоматически сформированном значении namespace\n\n"
                    "Шаблон     : <PROJECT.name>_<PROJECT.author>\n"
                    f"Подставлено: {auto_ns}\n"
                    "Ожидается  : только символы [A-Za-z0-9_]"
                )

        elif isinstance(ns, str):
            if not re.fullmatch(r"[A-Za-z0-9_]+", ns):
                cls._errors.append(
                    "PROJECT.namespace содержит недопустимые символы.\n"
                    "Ожидается: только символы [A-Za-z0-9_]"
                )

    @classmethod
    def warnings(cls) -> list[str]:
        return cls._warnings

    @classmethod
    def errors(cls) -> list[str]:
        return cls._errors


class Config:
    _data: dict[str, Any] = {}

    @classmethod
    def init(cls) -> None:
        cls.load_default_toml_config()
        cls.load_user_toml()

    # region get/set
    @classmethod
    def _resolve_path(cls, key: str):
        if isinstance(key, str):
            return key.split(".")

        return [key]

    @classmethod
    def get(cls, key: str, default=None):
        key = key.lower()
        parts = cls._resolve_path(key)
        current = cls._data

        for part in parts:
            if not isinstance(current, dict) or part not in current:
                return default
            current = current[part]

        return current

    @classmethod
    def set(cls, key: str, value):
        key = key.lower()
        parts = cls._resolve_path(key)
        current = cls._data

        for part in parts[:-1]:
            if part not in current or not isinstance(current[part], dict):
                current[part] = {}

            current = current[part]

        current[parts[-1]] = value

    # endregion

    # region default data
    @classmethod
    def sdk_path(cls) -> Path:
        path = Path(".plg-sdk").resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path

    @classmethod
    def config_file(cls) -> Path:
        return Path("plg-sdk-config.toml").resolve()

    @classmethod
    def resource_path(cls) -> Path:
        return (Path(__file__).parents[1] / "resource").resolve()

    @classmethod
    def load_config_schema(cls) -> dict[str, Any]:
        return json.loads(
            (Path(__file__).parents[1] / "resource/config_schema.json")
            .resolve()
            .read_text(encoding="utf-8")
        )

    # endregion

    # region config file
    @staticmethod
    def _transfom_data(data: Any, data_type: str) -> Any:
        if data == "%!NOT_SET!%":
            return None

        match data_type:
            case "str":
                return str(data)

            case "bool":
                return bool(data)

            case "path":
                return Path(data)

            case "array_str":
                return list(data)

            case _:
                raise ValueError(
                    f"Неизвестное значение {data_type} при трансформации {data}"
                )

    @classmethod
    def load_default_toml_config(cls) -> None:
        schema = cls.load_config_schema()
        cls._data["all_modules"] = schema.get("allowed_modules", [])

        for header_key, header_values in schema.get("config", {}).items():
            for block_key, values in header_values.items():
                cls.set(
                    f"config.{header_key}.{block_key}",
                    cls._transfom_data(values["default"], values["type"]),
                )

    @classmethod
    def load_user_toml(cls) -> None:
        config_path = cls.config_file()
        if not config_path.exists():
            return

        user_data = tomllib.loads(config_path.read_text(encoding="utf-8"))
        schema = cls.load_config_schema()

        schema_config: dict[str, Any] = schema.get("config", {})

        for header_key, header_blocks in schema_config.items():
            user_header = user_data.get(header_key, {})
            if not isinstance(user_header, dict):
                continue

            for block_key, meta in header_blocks.items():
                if block_key not in user_header:
                    continue

                raw_user_value = user_header[block_key]
                expected_type = meta["type"]

                cls.set(
                    f"config.{header_key}.{block_key}",
                    cls._transfom_data(raw_user_value, expected_type),
                )

    # endregion
