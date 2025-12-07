import logging
from pathlib import Path
from typing import Any

from ..core import Config

logger = logging.getLogger("plg-sdk")


# region TOML utils
def _to_toml_value(v: Any) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"

    if isinstance(v, (int, float)):
        return str(v)

    if isinstance(v, Path):
        s = v.as_posix()
        if not v.is_absolute() and not s.startswith("./"):
            s = "./" + s

        return f'"{s}"'

    if isinstance(v, str):
        return f'"{v}"'

    if isinstance(v, (list, tuple)):
        inner = ", ".join(_to_toml_value(x) for x in v)
        return f"[{inner}]"

    return f'"{str(v)}"'


def _cast_default(type_name: str, value: Any) -> Any:
    if type_name == "bool":
        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            return value.lower() == "true"

        raise TypeError(f"Invalid bool default: {value}")

    if type_name == "path":
        if isinstance(value, str):
            return Path(value)

        if isinstance(value, Path):
            return value

        raise TypeError(f"Invalid path default: {value}")

    if type_name == "array_str":
        if not isinstance(value, list):
            raise TypeError(f"array_str default must be list: {value}")

        out = []
        for item in value:
            if not isinstance(item, str):
                raise TypeError(f"array_str items must be str: {item}")

            out.append(item)

        return out

    return value


# endregion


# region File builder
class _TomlFile:
    def __init__(self):
        self._sections: dict[str, list[list[str]]] = {}
        self._order: list[str] = []

    def add_header(self, name: str):
        if name not in self._sections:
            self._sections[name] = []
            self._order.append(name)

    def add_config(
        self,
        header: str,
        name: str,
        default: Any,
        desc: str,
        input_desc: str,
        no_comments: bool = False,
    ):
        if header not in self._sections:
            self.add_header(header)

        block = []

        if not no_comments:
            for line in desc.strip().split("\n"):
                block.append(f"# {line}")

            block.append(f"# {input_desc}")

        block.append(f"{name} = {_to_toml_value(default)}")

        self._sections[header].append(block)

    def dump(self):
        config_path = Config.config_file()

        with config_path.open("w", encoding="utf8") as f:
            first_section = True

            for header in self._order:
                if not first_section:
                    f.write("\n")

                first_section = False
                f.write(f"[{header}]\n")
                blocks = self._sections[header]

                section_has_comments = any(len(block) > 1 for block in blocks)

                if not section_has_comments:
                    keys = []
                    for block in blocks:
                        kv = block[-1]
                        key = kv.split("=")[0].strip()
                        keys.append(key)

                    max_key_len = max(len(k) for k in keys)

                for i, block in enumerate(blocks):
                    if section_has_comments:
                        for line in block[:-1]:
                            f.write(line + "\n")

                        f.write(block[-1] + "\n")
                        if i != len(blocks) - 1:
                            f.write("\n")

                    else:
                        kv = block[-1]
                        key, value = kv.split("=", 1)
                        key = key.strip()
                        value = value.strip()

                        pad = " " * (max_key_len - len(key))  # pyright: ignore[reportPossiblyUnboundVariable]
                        f.write(f"{key}{pad} = {value}\n")


# endregion


def init_cmd(version: str, no_comments: bool = False) -> None:
    if Config.config_file().exists():
        inp = (
            input("\nФайл plg-sdk-config.toml уже существует.\nПерезаписать? (y/n) ")
            .strip()
            .lower()
        )
        if inp not in ("y", "yes"):
            return

    schema = Config.load_config_schema()

    type_descriptions = schema["types"]
    allowed_modules: list[str] = schema["allowed_modules"]
    sections = schema["config"]

    file = _TomlFile()

    for section_name, params in sections.items():
        file.add_header(section_name)

        for param_name, meta in params.items():
            input_type = meta["type"]

            raw_default = meta["default"]
            cast_default = _cast_default(input_type, raw_default)

            desc: str = meta["desc"]
            desc = desc.replace("{VERSION}", version)
            desc = desc.replace(
                "{ALLOWED_MODULES}", "\n".join(f"- {m}" for m in allowed_modules)
            )

            file.add_config(
                section_name,
                param_name,
                cast_default,
                desc,
                type_descriptions[input_type],
                no_comments,
            )

    file.dump()
