#!/usr/bin/env python3
"""持久化演示文稿工作流状态，并在确认前阻断生产脚本。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SEQUENCE = (
    "intake_pending",
    "intake_confirmed",
    "planned",
    "producing",
    "qa",
    "complete",
)
TERMINAL = {"incomplete", "blocked"}

# 使用正则精确匹配脚本调用路径，避免注释/echo 中的子串误判
_PRODUCTION_PATTERNS = (
    re.compile(
        r"(?:^|\s|['\"]|&|;)\s*(?:python3?|node)\s+.*(?:"
        r"slide_spec_to_pptx_brief\.py"
        r"|run_with_pptxgenjs\.js"
        r"|build_support_outputs\.py"
        r"|pptx_delivery_check\.py"
        r"|create_revision_manifest\.py"
        r"|\$[{]CLAUDE_PLUGIN_ROOT[}].*slide_spec_to_pptx_brief\.py"
        r"|\$[{]CLAUDE_PLUGIN_ROOT[}].*run_with_pptxgenjs\.js"
        r"|\$[{]CLAUDE_PLUGIN_ROOT[}].*build_support_outputs\.py"
        r"|\$[{]CLAUDE_PLUGIN_ROOT[}].*pptx_delivery_check\.py"
        r"|\$[{]CLAUDE_PLUGIN_ROOT[}].*create_revision_manifest\.py"
        r")",
        re.IGNORECASE,
    ),
)

# 快速子串预扫描清单（用于跳过 JSON 解析）
_FAST_MARKERS = (
    "slide_spec_to_pptx_brief.py",
    "run_with_pptxgenjs.js",
    "build_support_outputs.py",
    "pptx_delivery_check.py",
    "create_revision_manifest.py",
)

HOOK_DENY_REASON = (
    "演示文稿生产命令被阻断：尚未确认 Production Summary。"
    "请先完成需求确认，然后运行 workflow_guard.py confirm --summary-file <摘要文件>。"
    "状态文件位于: {state_path}"
)
HOOK_DENY_CONTEXT = (
    "请先让用户确认完整的 Production Summary，然后运行 "
    "workflow_guard.py confirm 命令。"
)

STATE_MISSING_MSG = (
    "工作流状态文件不存在。请先运行 'workflow_guard.py init' 初始化状态，"
    "然后完成需求确认。状态文件路径: {state_path}"
)


def project_root(cwd: Path | None = None) -> Path:
    """优先使用 CLAUDE_PROJECT_DIR，其次使用 hook payload 的 cwd，最后用进程 cwd。"""
    configured = os.environ.get("CLAUDE_PROJECT_DIR")
    if configured:
        return Path(configured).expanduser().resolve()
    return (cwd or Path.cwd()).resolve()


def default_state_file(cwd: Path | None = None) -> Path:
    return project_root(cwd) / "outputs" / ".student-presentation-state.json"


def load_state(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def save_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def transition_allowed(before: str, after: str) -> bool:
    if after in TERMINAL:
        return before != "intake_pending"
    if before not in SEQUENCE or after not in SEQUENCE:
        return False
    return SEQUENCE.index(after) == SEQUENCE.index(before) + 1


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def has_valid_summary(state: dict[str, Any] | None) -> bool:
    if not state or not state.get("summary_sha256") or not state.get("summary_file"):
        return False
    try:
        return sha256_file(Path(state["summary_file"])) == state["summary_sha256"]
    except OSError:
        return False


def count_slides(pptx: Path) -> int | None:
    try:
        with zipfile.ZipFile(pptx) as archive:
            return sum(
                name.startswith("ppt/slides/slide") and name.endswith(".xml")
                for name in archive.namelist()
            )
    except (OSError, zipfile.BadZipFile):
        return None


def validate_completion_manifest(manifest_path: Path | None, pptx: Path | None) -> list[str]:
    if manifest_path is None or pptx is None:
        return ["转换到 complete 必须提供 --qa-manifest 和 --pptx。"]
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"无法读取 QA manifest: {exc}"]
    if not isinstance(manifest, dict) or not pptx.is_file():
        return ["QA manifest 或 PPTX 无效。"]
    slide_count = count_slides(pptx)
    inspection = manifest.get("visual_inspection")
    errors: list[str] = []
    if manifest.get("pptx_sha256") != sha256_file(pptx):
        errors.append("QA manifest 的 pptx_sha256 与当前 PPTX 不一致。")
    if slide_count is None or manifest.get("slide_count") != slide_count or manifest.get("rendered_page_count") != slide_count:
        errors.append("QA manifest 的页数证据与 PPTX 不一致。")
    if not isinstance(inspection, dict) or inspection.get("completed") is not True:
        errors.append("QA manifest 未记录完成视觉检查。")
    elif inspection.get("remaining_blockers") != 0:
        errors.append("QA manifest 仍有未解决 blocker。")
    return errors


def _contains_production_command(command: str) -> bool:
    """使用正则精确匹配生产脚本调用，避免注释/echo 中的子串误判。"""
    return any(pattern.search(command) for pattern in _PRODUCTION_PATTERNS)


def hook_decision(payload: dict[str, Any]) -> dict[str, Any] | None:
    if payload.get("tool_name") != "Bash":
        return None
    command = str((payload.get("tool_input") or {}).get("command") or "")
    if not _contains_production_command(command):
        return None
    cwd_raw = payload.get("cwd")
    cwd = Path(cwd_raw) if cwd_raw else None
    state_path = default_state_file(cwd)
    state = load_state(state_path)
    current = state.get("state") if state else None
    allowed = current in {"intake_confirmed", "planned", "producing", "qa"} and has_valid_summary(state)
    if allowed:
        return None
    if current is None:
        reason = STATE_MISSING_MSG.format(state_path=state_path)
    else:
        reason = HOOK_DENY_REASON.format(state_path=state_path)
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
            "additionalContext": HOOK_DENY_CONTEXT,
        }
    }


def _check_and_parse_stdin() -> dict[str, Any] | None:
    """快速预扫描 stdin：如果内容不包含生产标记则跳过 JSON 解析。

    对 99% 的非 PPT 相关 Bash 调用，避免了 json.loads 的开销。
    """
    raw = sys.stdin.read()
    if not raw.strip():
        return None
    # 快速子串扫描
    if not any(marker in raw for marker in _FAST_MARKERS):
        return None
    # 只有潜在匹配时才解析 JSON
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, OSError):
        return None


def state_command(args: argparse.Namespace) -> int:
    state_path = args.state_file or default_state_file()
    current = load_state(state_path)

    if args.action == "show":
        if current is None:
            info = {"state": "missing", "path": str(state_path),
                    "hint": "运行 'init' 创建初始状态，或 'reset' 强制重置"}
        else:
            info = current
            info["state_file"] = str(state_path)
        print(json.dumps(info, ensure_ascii=False, indent=2))
        return 0

    if args.action == "init":
        if current is not None:
            print(
                f"⚠ 状态文件已存在（当前状态: {current.get('state')}）。"
                f"如需重新开始，请使用 'reset' 命令。",
                file=sys.stderr,
            )
            return 1
        save_state(
            state_path,
            {
                "workflow_version": "1.0",
                "state": "intake_pending",
                "topic": args.topic,
                "summary_sha256": None,
            },
        )
        print(f"✅ 工作流状态已初始化（intake_pending）→ {state_path}")

    elif args.action == "reset":
        save_state(
            state_path,
            {
                "workflow_version": "1.0",
                "state": "intake_pending",
                "topic": args.topic,
                "summary_sha256": None,
            },
        )
        print(f"✅ 工作流状态已重置为 intake_pending → {state_path}")

    elif args.action == "unblock":
        if not current:
            raise SystemExit(
                f"状态文件不存在，无需 unblock。请先运行 'init' 创建状态。\n"
                f"状态文件路径: {state_path}"
            )
        before = current.get("state")
        if before != "blocked":
            raise SystemExit(
                f"当前状态为 '{before}'，只有 'blocked' 状态才能 unblock。"
                f"如需强制重置，请使用 'reset' 命令。"
            )
        # unblock 必须重新走确认门禁，不能留在无 hash 的 intake_confirmed。
        current["state"] = "intake_pending"
        current["summary_sha256"] = None
        save_state(state_path, current)
        print(
            f"✅ 状态已从 blocked 恢复到 intake_pending → {state_path}\n"
            f"⚠ 注意：您需要重新确认 Production Summary 后才能继续生产。"
        )

    elif args.action == "confirm":
        if not args.summary_file or not args.summary_file.is_file():
            raise SystemExit(
                f"摘要文件不存在: {args.summary_file}\n"
                f"请提供有效的 Production Summary 文件路径。"
            )
        summary_hash = hashlib.sha256(args.summary_file.read_bytes()).hexdigest()
        base = current or {"workflow_version": "1.0", "topic": args.topic}
        allowed_from = {None, "intake_pending"}
        if base.get("state") not in allowed_from:
            raise SystemExit(
                f"无法从 '{base.get('state')}' 状态确认。"
                f"当前状态必须是 intake_pending 或未初始化。"
                f"如需重新开始，请先运行 'reset'。"
            )
        base.update(
            {
                "state": "intake_confirmed",
                "summary_file": str(args.summary_file.resolve()),
                "summary_sha256": summary_hash,
            }
        )
        save_state(state_path, base)
        print(f"✅ 状态已确认（intake_confirmed），生产门禁已解除 → {state_path}")

    elif args.action == "transition":
        if not current:
            raise SystemExit(
                f"工作流状态文件不存在。请先运行 'init' 创建状态。\n"
                f"状态文件路径: {state_path}"
            )
        before = str(current.get("state"))
        if not transition_allowed(before, args.to):
            valid_next = []
            try:
                idx = SEQUENCE.index(before)
                valid_next.append(SEQUENCE[idx + 1])
            except (ValueError, IndexError):
                pass
            if before != "intake_pending":
                valid_next.extend(sorted(TERMINAL))
            raise SystemExit(
                f"无效的状态转换: {before} → {args.to}\n"
                f"从 '{before}' 只能转换到: {', '.join(valid_next) if valid_next else '无法转换，请使用 reset'}"
            )
        if args.to == "complete":
            errors = validate_completion_manifest(args.qa_manifest, args.pptx)
            if errors:
                raise SystemExit("无法完成交付：\n- " + "\n- ".join(errors))
        current["state"] = args.to
        save_state(state_path, current)
        print(f"✅ 状态转换: {before} → {args.to}")

    print(json.dumps(load_state(state_path), ensure_ascii=False, indent=2))
    return 0


def main() -> None:
    if len(sys.argv) == 1:
        # Hook 模式：快速预扫描避免每次 Bash 调用都解析 JSON
        payload = _check_and_parse_stdin()
        if payload is None:
            return
        decision = hook_decision(payload)
        if decision:
            print(json.dumps(decision, ensure_ascii=False))
        return

    parser = argparse.ArgumentParser(
        description="管理 Student Presentation 工作流状态",
    )
    sub = parser.add_subparsers(dest="action", required=True)

    for name in ("init", "show", "reset"):
        command = sub.add_parser(name, help={
            "init": "初始化状态为 intake_pending",
            "show": "显示当前状态",
            "reset": "强制重置状态为 intake_pending（丢弃当前进度）",
        }[name])
        command.add_argument("--state-file", type=Path, help="状态文件路径")
        command.add_argument("--topic", help="演示文稿主题")

    unblock = sub.add_parser(
        "unblock",
        help="从 blocked 状态恢复到 intake_pending，并重新确认摘要",
    )
    unblock.add_argument("--state-file", type=Path, help="状态文件路径")

    confirm = sub.add_parser("confirm", help="确认 Production Summary")
    confirm.add_argument("--state-file", type=Path, help="状态文件路径")
    confirm.add_argument("--topic", help="演示文稿主题")
    confirm.add_argument(
        "--summary-file", type=Path, required=True,
        help="Production Summary 文件路径",
    )

    transition = sub.add_parser("transition", help="推进工作流状态")
    transition.add_argument("--state-file", type=Path, help="状态文件路径")
    transition.add_argument(
        "--to",
        choices=(*SEQUENCE[2:], *sorted(TERMINAL)),
        required=True,
        help=f"目标状态（正向: {', '.join(SEQUENCE[2:])}；终态: {', '.join(sorted(TERMINAL))}）",
    )
    transition.add_argument("--qa-manifest", type=Path, help="转换到 complete 所需的 QA manifest")
    transition.add_argument("--pptx", type=Path, help="转换到 complete 所需的交付 PPTX")

    raise SystemExit(state_command(parser.parse_args()))


if __name__ == "__main__":
    main()
