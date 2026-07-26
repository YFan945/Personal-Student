#!/usr/bin/env python3
"""验证独立的 Claude Code 插件发布包结构。"""

from __future__ import annotations

import argparse
import json
import re
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
    "references/pptx-runtime-provenance.md",
    "references/presentation-intake.md",
    "references/presentation-brief.md",
    "references/presentation-brief.schema.json",
    "references/content-workflow.md",
    "references/evidence-and-citations.md",
    "references/revision-training-export.md",
    "skills/student-presentation/SKILL.md",
    "skills/student-presentation-ppt/SKILL.md",
    "skills/student-presentation-ppt/references/pptx-production.md",
    "skills/student-presentation-ppt/references/pptx-runtime.md",
    "skills/student-presentation-ppt/references/pptxgenjs-safety.md",
    "skills/student-presentation-ppt/references/pptx-editing.md",
    "skills/student-presentation-ppt/references/pptx-qa.md",
    "skills/student-presentation-review/SKILL.md",
    "scripts/check_claude_pptx_env.py",
    "scripts/pptx_tool.py",
    "scripts/run_with_pptxgenjs.js",
    "scripts/smoke_pptx.py",
    "scripts/slide_spec_to_pptx_brief.py",
    "scripts/validate_slide_spec.py",
    "scripts/validate_presentation_brief.py",
    "scripts/analyze_presentation_spec.py",
    "scripts/compile_visual_plan.py",
    "scripts/pptx-helpers.js",
    "scripts/pptx-visuals.js",
    "scripts/create_revision_manifest.py",
    "scripts/build_support_outputs.py",
    "scripts/workflow_guard.py",
    "scripts/manage_versions.py",
    "shared/pptx_runtime/__init__.py",
    "shared/pptx_runtime/charts.py",
    "shared/pptx_runtime/findings.py",
    "shared/pptx_runtime/package.py",
    "shared/pptx_runtime/edit.py",
    "shared/pptx_runtime/normalize.py",
    "shared/pptx_runtime/openxml.py",
    "shared/pptx_runtime/openxml_validator/OpenXmlValidator.csproj",
    "shared/pptx_runtime/openxml_validator/packages.lock.json",
    "shared/pptx_runtime/openxml_validator/Program.cs",
    "shared/pptx_runtime/validate.py",
    "shared/pptx_runtime/render.py",
    "shared/pptx_runtime/soffice.py",
    "shared/pptx_runtime/thumbnail.py",
    "shared/pptx_runtime/assets/lo_socket_shim.c",
    "hooks/hooks.json",
    "tests/test_pptx_tool.py",
    "tests/test_pptx_runtime.py",
    "tests/test_runtime_paths.py",
]
FORBIDDEN_PATH_PARTS = {
    ".codex-plugin",
    "agents",
    "__pycache__",
    ".pytest_cache",
    "node_modules",
    "bin",
    "obj",
}
FORBIDDEN_SUFFIXES = {".pyc", ".pptx", ".png"}
REQUIRED_METADATA = ("homepage", "repository", "license", "keywords")
_SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-([a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*))?"
    r"(?:\+([a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*))?$"
)


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
        encoding="utf-8",
        errors="replace",
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
    # 验证版本号非空且符合 semver
    version_fields = {
        "manifest": manifest.get("version", ""),
        "package.json": package.get("version", ""),
    }
    for source, ver in version_fields.items():
        if not ver:
            errors.append(f"{source} 的版本号为空，必须提供有效版本")
        elif not _SEMVER_RE.fullmatch(ver):
            errors.append(f"{source} 的版本号不是合法 semver: {ver}")
    # 不硬编码版本号，只检查各文件一致性（空版本已在上面拦截）
    version_error = _version_compare(version_fields)
    if version_error:
        errors.append(version_error)
    author = manifest.get("author") if isinstance(manifest.get("author"), dict) else {}
    if author.get("name") in {None, "", "Local developer"}:
        errors.append("manifest author.name 必须提供发布者名称")
    for field in REQUIRED_METADATA:
        if not manifest.get(field):
            errors.append(f"manifest 缺少必要元数据: {field}")
    if len(manifest.get("keywords", [])) < 5:
        errors.append("manifest 应提供至少 5 个关键词")


def check_runtime_contract(errors: list[str]) -> None:
    try:
        combined = "\n".join(
            (ROOT / rel).read_text(encoding="utf-8")
            for rel in (
                "skills/student-presentation-ppt/SKILL.md",
                "skills/student-presentation-review/SKILL.md",
                "skills/student-presentation-ppt/references/pptx-production.md",
            )
        )
    except OSError as exc:
        errors.append(f"运行时契约文件读取失败: {exc}")
        return
    for expected in (
        "${CLAUDE_PLUGIN_ROOT}",
        "${CLAUDE_PROJECT_DIR}",
        "run_with_pptxgenjs.js",
        "blocked",
        "incomplete",
    ):
        if expected not in combined:
            errors.append(f"运行时契约缺失必要的引用: {expected}")
    for forbidden in ("artifact-tool", "Presentations` skill", "agents/openai.yaml"):
        if forbidden in combined:
            errors.append(f"运行时指令包含 Codex-only 文本: {forbidden}")
    if "tokens truncated" in combined:
        errors.append("PPTX 运行时文档包含截断标记")
    for rel in (
        "skills/student-presentation-ppt/SKILL.md",
        "skills/student-presentation-ppt/references/pptx-production.md",
        "skills/student-presentation-ppt/references/pptx-runtime.md",
        "skills/student-presentation-ppt/references/pptxgenjs-safety.md",
        "skills/student-presentation-ppt/references/pptx-editing.md",
        "skills/student-presentation-ppt/references/pptx-qa.md",
    ):
        text = (ROOT / rel).read_text(encoding="utf-8")
        if text.count("```") % 2:
            errors.append(f"Markdown code fence 未闭合: {rel}")


def check_embedded_runtime(errors: list[str]) -> None:
    probe = subprocess.run(
        [sys.executable, "-B", str(ROOT / "scripts" / "pptx_tool.py"), "--help"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if probe.returncode != 0:
        errors.append(f"suite-owned PPTX runtime 无法启动: {(probe.stderr or probe.stdout).strip()}")
    legacy_runtime = ROOT / "skills/student-presentation-ppt/scripts/pptx_skill"
    if legacy_runtime.is_dir() and any(
        path.is_file() and "__pycache__" not in path.parts
        for path in legacy_runtime.rglob("*")
    ):
        errors.append("已移除的上游 pptx_skill runtime 不应出现在发布包中")


def check_hooks(errors: list[str]) -> None:
    """验证 hooks.json 格式及其指向的脚本存在。"""
    hooks_path = ROOT / "hooks" / "hooks.json"
    try:
        hooks = json.loads(hooks_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"hooks.json 解析失败: {exc}")
        return
    pre = hooks.get("hooks", {}).get("PreToolUse")
    if not isinstance(pre, list) or not pre:
        errors.append("hooks.json 缺少 PreToolUse 配置")
        return
    entry = pre[0]
    if entry.get("matcher") != "Bash":
        errors.append("hooks.json PreToolUse matcher 必须是 Bash")
    commands = [h.get("command") for h in entry.get("hooks", []) if h.get("type") == "command"]
    if not commands:
        errors.append("hooks.json PreToolUse 中缺少 command 类型 hook")
        return
    for cmd in commands:
        # The command references workflow_guard.py by path ending.
        if "workflow_guard.py" not in cmd:
            errors.append(f"hooks.json 命令未指向 workflow_guard.py: {cmd}")


def check_tracked_files(errors: list[str]) -> None:
    files = tracked_files(errors)
    tracked = set(files)
    for rel in REQUIRED_FILES:
        repository_path = f"plugins/student-presentation-suite/{rel}"
        if repository_path not in tracked:
            errors.append(f"必需发布文件尚未被 Git 跟踪: {rel}")
    folded: dict[str, str] = {}
    for rel in files:
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
    check_hooks(errors)
    check_manifest(errors)
    check_runtime_contract(errors)
    check_embedded_runtime(errors)
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
