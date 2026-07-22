"""共享测试工具模块。"""

from __future__ import annotations

import importlib.util
import types
from pathlib import Path


def load_module(script_path: Path) -> types.ModuleType:
    """通过文件路径动态加载 Python 模块。

    Args:
        script_path: .py 文件的完整路径。

    Returns:
        加载后的模块对象。

    Raises:
        AssertionError: 如果无法从文件路径创建模块规范。
    """
    spec = importlib.util.spec_from_file_location(script_path.stem, script_path)
    assert spec is not None, f"无法为 {script_path} 创建模块规范"
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None, f"{script_path} 的加载器不存在"
    spec.loader.exec_module(module)
    return module
