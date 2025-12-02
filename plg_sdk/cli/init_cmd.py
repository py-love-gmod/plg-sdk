import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger("plg-sdk")


# region TOML utils
def _to_toml_value(v: Any) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"

    if isinstance(v, (int, float)):
        return str(v)

    if isinstance(v, Path):
        return f'"{v.as_posix()}"'

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
        self, header: str, name: str, default: Any, desc: str, input_desc: str
    ):
        if header not in self._sections:
            self.add_header(header)

        block = []
        for line in desc.strip().split("\n"):
            block.append(f"# {line}")

        block.append(f"# {input_desc}")
        block.append(f"{name} = {_to_toml_value(default)}")

        self._sections[header].append(block)

    def dump(self, path: str | Path = "plg-sdk-config.toml"):
        p = Path(path)

        with p.open("w", encoding="utf8") as f:
            for header in self._order:
                f.write(f"[{header}]\n")
                for block in self._sections[header]:
                    for line in block:
                        f.write(line + "\n")
                    f.write("\n")


# endregion


def init_cmd(version: str) -> None:
    schema_path = Path(__file__).parents[1] / "resource/config_schema.json"

    with schema_path.open("r", encoding="utf8") as f:
        schema = json.load(f)

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
            )

    file.dump()
