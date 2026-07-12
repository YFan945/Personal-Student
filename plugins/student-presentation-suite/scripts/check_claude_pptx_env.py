#!/usr/bin/env python3
"""Check tools required by the Claude document-skills/pptx workflow."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared.runtime_paths import document_skills_compatibility, project_root


COMMON_SOFFICE_PATHS = [
    Path(r"C:\Program Files\LibreOffice\program\soffice.exe"),
    Path(r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Claude document-skills/pptx environment")
    parser.add_argument("--json", action="store_true", help="Emit JSON result")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero when required tools are missing")
    parser.add_argument("--project-root", type=Path, help="Override the active Claude project root")
    return parser.parse_args()


def command_path(name: str, extra_paths: list[Path] | None = None) -> str | None:
    if os.name == "nt" and not Path(name).suffix:
        for suffix in (".cmd", ".exe", ".bat"):
            found = shutil.which(name + suffix)
            if found:
                return found
    found = shutil.which(name)
    if found:
        return found
    for path in extra_paths or []:
        if path.is_file():
            return str(path)
    return None


def python_module(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def run_probe(command: list[str], env: dict[str, str] | None = None) -> tuple[bool, str]:
    try:
        proc = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
            env=env,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, str(exc)
    output = (proc.stdout or proc.stderr or "").strip()
    return proc.returncode == 0, output


def npm_global_root(npm: str | None) -> Path | None:
    if not npm:
        return None
    ok, output = run_probe([npm, "root", "-g"])
    if not ok or not output:
        return None
    return Path(output.splitlines()[-1].strip()).expanduser().resolve()


def resolve_pptxgenjs(project: Path) -> dict[str, Any]:
    node = command_path("node")
    npm = command_path("npm")
    if not node:
        return {"ok": False, "module_source": None, "detail": "node is not available"}

    candidates: list[tuple[str, Path]] = [
        ("project", project),
        ("plugin", ROOT),
    ]
    global_root = npm_global_root(npm)
    if global_root:
        candidates.append(("global", global_root))

    probe = (
        "const fs=require('node:fs'),p=require('node:path');"
        "const modulePath=require.resolve('pptxgenjs',{paths:[process.argv[1]]});"
        "let dir=p.dirname(modulePath),pkgPath=null;"
        "while(dir!==p.dirname(dir)){"
        "const candidate=p.join(dir,'package.json');"
        "if(fs.existsSync(candidate)){"
        "const pkg=JSON.parse(fs.readFileSync(candidate,'utf8'));"
        "if(pkg.name==='pptxgenjs'){pkgPath=candidate;break;}}"
        "dir=p.dirname(dir);}"
        "if(!pkgPath)throw new Error('pptxgenjs package.json not found');"
        "const pkg=JSON.parse(fs.readFileSync(pkgPath,'utf8'));"
        "console.log(JSON.stringify({path:modulePath,version:pkg.version}));"
    )
    attempts: list[dict[str, str]] = []
    for source, base in candidates:
        ok, output = run_probe([node, "-e", probe, str(base)])
        if ok:
            data = json.loads(output.splitlines()[-1])
            return {
                "ok": True,
                "module_source": source,
                "module_root": str(base),
                "module_path": data["path"],
                "module_version": data["version"],
                "attempts": attempts,
            }
        attempts.append({"source": source, "root": str(base), "detail": output})
    return {
        "ok": False,
        "module_source": None,
        "module_version": None,
        "attempts": attempts,
        "detail": "pptxgenjs was not resolvable from project, plugin, or global npm roots",
    }


def inspect_environment(project: Path | None = None) -> dict[str, Any]:
    active_project = (project or project_root()).resolve()
    dependency = document_skills_compatibility()
    checks = {
        "node": {"ok": command_path("node") is not None, "path": command_path("node")},
        "npm": {"ok": command_path("npm") is not None, "path": command_path("npm")},
        "pptxgenjs": resolve_pptxgenjs(active_project),
        "markitdown": {"ok": python_module("markitdown"), "module": "markitdown"},
        "Pillow": {"ok": python_module("PIL"), "module": "PIL"},
        "LibreOffice": {
            "ok": command_path("soffice", COMMON_SOFFICE_PATHS) is not None,
            "path": command_path("soffice", COMMON_SOFFICE_PATHS),
        },
        "Poppler pdftoppm": {
            "ok": command_path("pdftoppm") is not None,
            "path": command_path("pdftoppm"),
        },
        "jsonschema": {"ok": python_module("jsonschema"), "module": "jsonschema"},
        "PyYAML": {"ok": python_module("yaml"), "module": "yaml"},
        "document-skills": dependency,
    }
    required = [
        "node",
        "pptxgenjs",
        "markitdown",
        "Pillow",
        "document-skills",
    ]
    # LibreOffice 和 Poppler 为推荐项：缺失时警告但不阻断
    recommended = [
        "LibreOffice",
        "Poppler pdftoppm",
    ]
    missing_required = [name for name in required if not checks[name]["ok"]]
    missing_recommended = [name for name in recommended if not checks[name]["ok"]]
    return {
        "ok": not missing_required,
        "project_root": str(active_project),
        "plugin_root": str(ROOT),
        "dependency_compatibility": dependency,
        "missing_required": missing_required,
        "missing_recommended": missing_recommended,
        "checks": checks,
        "note": (
            "规划和审查可在缺少部分工具的情况下运行。"
            "PPTX 生产需要所有必需工具（node, pptxgenjs, markitdown, Pillow, document-skills）。"
            "LibreOffice 和 Poppler 用于渲染检查和 PDF 导出，缺失时仅影响视觉 QA，"
            "不阻断 PPTX 生成。"
        ),
    }


def main() -> None:
    args = parse_args()
    result = inspect_environment(args.project_root)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result["note"])
        for name, check in result["checks"].items():
            status = "ok" if check["ok"] else "缺失"
            extra = ""
            if name in ("LibreOffice", "Poppler pdftoppm") and not check["ok"]:
                extra = "（推荐但非必需 — 缺失不影响 PPTX 生成）"
            print(f"  {name}: {status}{extra}")
        if result.get("missing_recommended"):
            print(
                "\n⚠ 以下推荐工具缺失（不影响 PPTX 生成，但会跳过渲染检查与 PDF 导出）: "
                + ", ".join(result["missing_recommended"])
            )
    if args.strict and result["missing_required"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
