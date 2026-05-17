from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any


class Config:
    _data: dict[str, Any] = {}
    _path_root = Path(".").resolve()
    _path_resource = Path(__file__).parents[1].resolve() / "resource"

    # region get/set
    @classmethod
    def _resolve_path(cls, key: str):
        if isinstance(key, str):
            return key.split(".")

        elif isinstance(key, list):
            return key

        else:
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
        path = cls._path_root / ".plg-sdk"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @classmethod
    def config_file(cls) -> Path:
        return cls._path_root / "plg-sdk-config.toml"

    @classmethod
    def resource_path(cls) -> Path:
        return cls._path_resource

    @staticmethod
    def version() -> str:
        try:
            return version("plg-sdk")

        except PackageNotFoundError:
            return "0.0.0dev"
