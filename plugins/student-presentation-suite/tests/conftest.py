"""pytest configuration — 统一插件根路径引导和通用 fixtures。

本文件将插件根目录加入 sys.path，所有测试文件可直接 `from shared.xxx import ...`
或 `from test_helpers import load_module`，无需各自设置 PYTHONPATH。
"""

from __future__ import annotations

import sys
from pathlib import Path

# 将插件根目录加入 Python path
_PLUGIN_ROOT = Path(__file__).resolve().parents[1]
if str(_PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_ROOT))
