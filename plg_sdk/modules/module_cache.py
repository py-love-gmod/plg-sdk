from datetime import datetime, timezone
from pathlib import Path

from ..core import Config


class ModulesCache:
    NO_DATA = datetime.fromtimestamp(0, timezone.utc), {}
    _path: Path = Config.sdk_path() / "cache/pip_modules.bin"

    # Структура бинарника.
    # Может потом скажу себе спасибо когда через месяц открою этот файл

    # HEADER:
    #   uint8      modules_len
    #   uint64 LE  cache_time (unix timestamp)

    # BODY (repeat modules_len):
    #   uint16 LE  name_len
    #   uint16 LE  version_len (0 = no version)
    #   bytes      name
    #   bytes      version

    @classmethod
    def load(cls) -> tuple[datetime, dict[str, str]]:
        if not cls._path.exists():
            return cls.NO_DATA

        data = cls._path.read_bytes()
        pos = 0
        length = len(data)

        def read(n: int) -> bytes:
            nonlocal pos
            if pos + n > length:
                return b""

            out = data[pos : pos + n]
            pos += n
            return out

        # region header

        # region modules_len
        count_b = read(1)
        if not count_b:
            return cls.NO_DATA

        count = int.from_bytes(count_b, "little")
        # endregion

        # region cache_time
        ts_b = read(8)
        if not ts_b:
            return cls.NO_DATA

        timestamp = int.from_bytes(ts_b, "little")
        cache_time = datetime.fromtimestamp(timestamp, timezone.utc)
        # endregion

        # endregion

        # region body
        modules: dict[str, str] = {}

        for _ in range(count):
            name_len_b = read(2)
            version_len_b = read(2)
            if not name_len_b or not version_len_b:
                return cls.NO_DATA

            name_len = int.from_bytes(name_len_b, "little")
            version_len = int.from_bytes(version_len_b, "little")

            name_b = read(name_len)
            version_b = read(version_len)

            if len(name_b) != name_len or len(version_b) != version_len:
                return cls.NO_DATA

            name = name_b.decode("utf-8")
            version = version_b.decode("utf-8") if version_len > 0 else ""

            modules[name] = version
        # endregion

        return cache_time, modules

    @classmethod
    def save(cls, cache_time: datetime, modules_version: dict[str, str]) -> None:
        cls._path.parent.mkdir(parents=True, exist_ok=True)

        items = list(modules_version.items())
        count = len(items)
        time = int(cache_time.timestamp())

        with cls._path.open("wb") as file:
            # header
            file.write(count.to_bytes(1, "little"))
            file.write(time.to_bytes(8, "little"))

            # body
            for name, version in items:
                name_b = name.encode(encoding="utf-8")
                version_b = (
                    version.encode(encoding="utf-8") if version is not None else b""
                )

                file.write(len(name_b).to_bytes(2, "little"))
                file.write(len(version_b).to_bytes(2, "little"))

                file.write(name_b)
                file.write(version_b)
