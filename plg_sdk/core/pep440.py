import re

# full version parser (from PEP 440)
_VERSION_PATTERN = r"""
    v?
    (?:
        (?:(?P<epoch>[0-9]+)!)?
        (?P<release>[0-9]+(?:\.[0-9]+)*)
        (?P<pre>
            [-_\.]?
            (?P<pre_l>alpha|a|beta|b|preview|pre|c|rc)
            [-_\.]?
            (?P<pre_n>[0-9]+)?
        )?
        (?P<post>
            (?:-(?P<post_n1>[0-9]+))
            |
            (?:
                [-_\.]?
                (?P<post_l>post|rev|r)
                [-_\.]?
                (?P<post_n2>[0-9]+)?
            )
        )?
        (?P<dev>
            [-_\.]?
            (?P<dev_l>dev)
            [-_\.]?
            (?P<dev_n>[0-9]+)?
        )?
    )
    (?:\+(?P<local>[a-z0-9]+(?:[-_\.][a-z0-9]+)*))?
"""

_VERSION_RE = re.compile(
    r"^\s*" + _VERSION_PATTERN + r"\s*$", re.VERBOSE | re.IGNORECASE
)


def canonicalize(version: str) -> str | None:
    m = _VERSION_RE.match(version)
    if not m:
        return None

    g = m.groupdict()

    # epoch
    out = ""
    epoch = g["epoch"]
    if epoch is not None:
        epoch_i = int(epoch)
        if epoch_i != 0:
            out += f"{epoch_i}!"

    # release segment
    release = ".".join(str(int(x)) for x in g["release"].split("."))
    out += release

    # pre-release
    if g["pre"]:
        tag = g["pre_l"].lower()
        num = g["pre_n"]

        if tag in ("alpha", "a"):
            tag = "a"

        elif tag in ("beta", "b"):
            tag = "b"

        elif tag in ("c", "rc", "preview", "pre"):
            tag = "rc"

        else:
            return None

        num = int(num) if num else 0
        out += f"{tag}{num}"

    # post-release
    if g["post"]:
        n = g["post_n1"] or g["post_n2"]
        n = int(n) if n else 0
        out += f".post{n}"

    # dev-release
    if g["dev"]:
        n = g["dev_n"]
        n = int(n) if n else 0
        out += f".dev{n}"

    # local version (canonical keeps it lowercase)
    if g["local"]:
        out += "+" + g["local"].replace("_", ".").lower()

    return out
