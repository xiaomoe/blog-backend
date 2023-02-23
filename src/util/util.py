from importlib import import_module
from pathlib import Path
from types import ModuleType


def import_all_modules(path: str, query: str = "**/[!__]*.py") -> list[ModuleType]:
    """导入 path 路径下的所有除__开头的 py 文件并返回所有模块
    f'ge
        Args:
            path (str): 所在文件夹或当前文件 __file__
            query (str, optional): 过滤条件. Defaults to "**/[!__]*.py".

        Returns:
            list[ModuleType] | None: 导入的模块列表, 如果没有找到返回空列表.

        Examples:
            >>> import_all_modules(__file__, '')

        Notes:
            - 函数默认只导入 .py 文件, 不包括文件夹和其他类型的文件。
            - 函数默认排除以双下划线开头的文件, 例如 __init__.py。
            - 如果文件名不符合模块命名规范, 导入模块可能会失败。
            - 如果模块依赖其他模块, 可能需要手动导入这些模块。
    """
    _path = Path(path).resolve()
    if _path.is_file():
        _path = _path.parent
    if not _path.is_dir():
        raise ValueError(f"{_path} 不是有效路径")

    modules = []

    for file in _path.rglob(query):
        if file.is_file():
            module_path = ".".join(file.relative_to(_path).parts[:-1])
            module = import_module(f"{module_path}.{file.stem}")
            modules.append(module)

    return modules
