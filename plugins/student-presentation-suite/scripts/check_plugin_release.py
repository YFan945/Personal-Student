#!/usr/bin/env python3
"""验证独立的 Claude Code 插件发布包结构。"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = ROOT.parents[1]
REQUIRED_FILES = [
    ".claude-plugin/plugin.json",
    "README.md",
    "README-zh.md",
    "requirements.txt",
    "requirements-claude-pptx.txt",
    "package.json",
    "package-lock.json",
    "references/presentation-intake.md",
    "references/presentation-brief.md",
    "references/presentation-brief.schema.json",
    "references/content-workflow.md",
    "references/evidence-and-citations.md",
    "references/revision-training-export.md",
    "skills/student-presentation/SKILL.md",
    "skills/student-presentation-ppt/SKILL.md",
    "skills/student-presentation-review/SKILL.md",
    "scripts/check_claude_pptx_env.py",
    "scripts/run_with_pptxgenjs.js",
    "scripts/smoke_pptx.py",
    "scripts/slide_spec_to_pptx_brief.py",
    "scripts/validate_slide_spec.py",
    "scripts/validate_presentation_brief.py",
    "scripts/analyze_presentation_spec.py",
    "scripts/create_revision_manifest.py",
    "scripts/build_support_outputs.py",
    "scripts/workflow_guard.py",
    "scripts/manage_versions.py",
    "hooks/hooks.json",
    "tests/test_runtime_paths.py",
]
FORBIDDEN_PATH_PARTS = {".codex-plugin", "agents", "__pycache__", ".pytest_cache", "node_modules"}
FORBIDDEN_SUFFIXES = {".pyc", ".pptx", ".png"}
REQUIRED_METADATA = ("homepage", "repository", "license", "keywords")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="检查 Claude Code 插件结构")
    parser.add_argument("--json", action="store_true", help="输出 JSON 格式")
    return parser.parse_args()


def run_git(*args: str) -> list[str]:
    proc = subprocess.run(
        ["git", *args],
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=20,
    )
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout or "git 命令失败").strip())
    return proc.stdout.splitlines()


def tracked_files(errors: list[str]) -> list[str]:
    try:
        return run_git("ls-files")
    except RuntimeError as exc:
        errors.append(f"无法检查已跟踪文件: {exc}")
        return []


def check_structure(errors: list[str]) -> None:
    for rel in REQUIRED_FILES:
        if not (ROOT / rel).is_file():
            errors.append(f"缺少必需文件: {rel}")


def _version_compare(versions: dict[str, str]) -> str | None:
    """比较所有版本字段，返回不一致信息或 None。"""
    unique = set(versions.values())
    if len(unique) > 1:
        return (
            f"版本不一致: {json.dumps(versions, ensure_ascii=False)}"
        )
    return None


def check_manifest(errors: list[str]) -> None:
    try:
        manifest = json.loads((ROOT / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
        package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"manifest/package.json 解析失败: {exc}")
        return
    if manifest.get("name") != "student-presentation-suite":
        errors.append("manifest name 必须为 student-presentation-suite")
    # 不硬编码版本号，只检查各文件一致性
    version_error = _version_compare({
        "manifest": manifest.get("version", ""),
        "package.json": package.get("version", ""),
    })
    if version_error:
        errors.append(version_error)
    if manifest.get("author", {}).get("name") in {None, "", "Local developer"}:
        errors.append("manifest author.name 必须提供发布者名称")
    if not any("document-skills@anthropic-agent-skills" in dep
               for dep in manifest.get("dependencies", [])):
        errors.append("manifest 必须依赖 document-skills@anthropic-agent-skills")
    for field in REQUIRED_METADATA:
        if not manifest.get(field):
            errors.append(f"manifest 缺少必要元数据: {field}")
    if len(manifest.get("keywords", [])) < 5:
        errors.append("manifest 应提供至少 5 个关键词")


def check_runtime_contract(errors: list[str]) -> None:
    combined = "\n".join(
        (ROOT / rel).read_text(encoding="utf-8")
        for rel in (
            "skills/student-presentation-ppt/SKILL.md",
            "skills/student-presentation-review/SKILL.md",
            "skills/student-presentation-ppt/references/pptx-production.md",
        )
    )
    for expected in (
        "${CLAUDE_PLUGIN_ROOT}",
        "${CLAUDE_PROJECT_DIR}",
        "document-skills@anthropic-agent-skills",
        "run_with_pptxgenjs.js",
        "blocked",
        "incomplete",
    ):
        if expected not in combined:
            errors.append(f"运行时契约缺失必要的引用: {expected}")
    for forbidden in ("artifact-tool", "Presentations` skill", "agents/openai.yaml"):
        if forbidden in combined:
            errors.append(f"运行时指令包含 Codex-only 文本: {forbidden}")


def check_tracked_files(errors: list[str]) -> None:
    files = tracked_files(errors)
    folded: dict[str, str] = {}
    for rel in files:
        path = Path(rel)
        if not rel.startswith("plugins/student-presentation-suite/"):
            continue
        local = rel.removeprefix("plugins/student-presentation-suite/")
        local_path = Path(local)
        if any(part in FORBIDDEN_PATH_PARTS for part in local_path.parts):
            errors.append(f"禁止的生成文件或 Codex 路径被跟踪: {local}")
        if local_path.suffix.lower() in FORBIDDEN_SUFFIXES:
            errors.append(f"生成的产物被跟踪: {local}")
        key = local.casefold()
        if key in folded and folded[key] != local:
            errors.append(f"大小写冲突的跟踪路径: {folded[key]} 与 {local}")
        folded[key] = local
        disk_path = ROOT / local
        if disk_path.is_file() and disk_path.read_bytes().startswith(b"\xef\xbb\xbf"):
            errors.append(f"不允许 UTF-8 BOM: {local}")


def main() -> None:
    args = parse_args()
    errors: list[str] = []
    check_structure(errors)
    check_manifest(errors)
    check_runtime_contract(errors)
    check_tracked_files(errors)
    result = {"ok": not errors, "error_count": len(errors), "errors": errors}
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif errors:
        print("插件发布检查失败:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
    else:
        print("插件发布检查通过。")
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
