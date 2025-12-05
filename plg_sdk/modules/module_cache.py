from pathlib import Path


class ModulesCache:
    path = Path()

    # Пока я не забыл структуру бинарного пакета:
    #
    # [HEADER]
    # 8u - count of modules
    # 64u - time of cache
    #
    # [BODY]
    # for x in range(modules count):
    #   16u - len of name
    #   16u - len of version (0 for None)
    #   bytes - name
    #   bytes - version

    # TODO: load, save
