#!/usr/bin/env python3
"""统一升级 student-presentation-suite 所有版本字段。"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
MARKETPLACE_ROOT = PLUGIN_ROOT.parents[1]  # 仓库根目录 (claude-plugins)

FILES_TO_UPDATE = [
    (
        MARKETPLACE_ROOT / ".claude-plugin" / "marketplace.json",
        "plugins[0].version",
        lambda data, ver: _update_plugin_entry(data, ver),
    ),
    (
        PLUGIN_ROOT / ".claude-plugin" / "plugin.json",
        "version",
        lambda data, ver: _set_key(data, "version", ver),
    ),
    (
        PLUGIN_ROOT / "package.json",
        "version",
        lambda data, ver: _set_key(data, "version", ver),
    ),
]


def _set_key(data: dict, key: str, value: str) -> dict:
    data[key] = value
    return data


def _update_plugin_entry(data: dict, version: str) -> dict:
    plugins = data.get("plugins")
    if not plugins or not isinstance(plugins, list):
        raise ValueError("marketplace.json 中未找到 plugins 列表")
    if plugins[0].get("name") != "student-presentation-suite":
        raise ValueError("marketplace.json 第一个插件不是 student-presentation-suite")
    plugins[0]["version"] = version
    return data


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict) -> None:
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def current_version() -> str:
    """从 plugin.json 读取当前版本。"""
    manifest = read_json(PLUGIN_ROOT / ".claude-plugin" / "plugin.json")
    return manifest.get("version", "0.0.0")


def bump(target: str, dry_run: bool = False) -> int:
    """更新所有版本字段并同步 lockfile。

    返回 0 表示成功，非 0 表示失败。
    """
    old_version = current_version()
    print(f"当前版本: {old_version} → {target}")

    if not dry_run:
        # 先同步 lockfile，成功后再写 JSON 文件，确保原子性
        print("  正在同步 package-lock.json ...")
        result = subprocess.run(
            ["npm", "--prefix", str(PLUGIN_ROOT), "install", "--package-lock-only"],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            print(f"✗ npm install --package-lock-only 失败: {result.stderr}", file=sys.stderr)
            print("⚠ JSON 文件未修改，请解决 npm 问题后重试。", file=sys.stderr)
            return 1
        print("  ✓ package-lock.json 已同步")

    for path, desc, updater in FILES_TO_UPDATE:
        try:
            data = read_json(path)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"✗ 无法读取 {path}: {exc}", file=sys.stderr)
            return 1
        if dry_run:
            new_data = updater(data, target)
            print(f"  [dry-run] {path.name} {desc}: {new_data.get('version', '?')}")
        else:
            updated = updater(data, target)
            write_json(path, updated)
            print(f"  ✓ {path.name} {desc}: {target}")

    print(f"\n{'[dry-run] ' if dry_run else ''}版本升级完成: {old_version} → {target}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="统一升级 student-presentation-suite 所有版本字段"
    )
    parser.add_argument(
        "version",
        nargs="?",
        help="目标版本号，如 0.5.0。省略则仅显示当前版本。",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="预览修改而不实际写入文件",
    )
    args = parser.parse_args()

    if not args.version:
        print(f"当前版本: {current_version()}")
        return

    raise SystemExit(bump(args.version, args.dry_run))


if __name__ == "__main__":
    main()
