#!/usr/bin/env python3
"""Check capabilities required by the suite-owned Student Presentation PPTX runtime."""

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

from shared.pptx_runtime.openxml import build_openxml_validator, dotnet_sdk_path
from shared.pptx_runtime.soffice import af_unix_available
from shared.runtime_paths import project_root

COMMON_SOFFICE_PATHS = [
    Path(r"C:\Program Files\LibreOffice\program\soffice.exe"),
    Path(r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check suite-owned Student Presentation PPTX runtime")
    parser.add_argument("--json", action="store_true", help="Emit JSON result")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero when required tools are missing")
    parser.add_argument("--project-root", type=Path, help="Override the active Claude project root")
    parser.add_argument(
        "--mode",
        choices=("all", "create", "edit_ooxml", "rebuild_from_source"),
        default="all",
        help="Evaluate required capabilities for one production mode",
    )
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


def poppler_path() -> str | None:
    candidate = command_path("pdftoppm")
    if not candidate:
        return None
    path = Path(candidate)
    parents = list(path.parents)
    if len(parents) >= 3:
        bundled = parents[2] / "native" / "poppler" / "Library" / "bin" / "pdftoppm.exe"
        if bundled.is_file():
            return str(bundled)
    return candidate


def run_probe(command: list[str], env: dict[str, str] | None = None) -> tuple[bool, str]:
    try:
        proc = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=20,
            env=env,
        )
    except (OSError, subprocess.TimeoutExpired, UnicodeDecodeError) as exc:
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


def inspect_environment(project: Path | None = None, mode: str = "all") -> dict[str, Any]:
    active_project = (project or project_root()).resolve()
    runtime_probe = run_probe(
        [sys.executable, "-B", str(ROOT / "scripts" / "pptx_tool.py"), "--help"],
        {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    unix_socket_ready = af_unix_available()
    shim_compiler = None
    if not unix_socket_ready:
        shim_compiler = command_path(os.environ.get("CC", "")) if os.environ.get("CC") else next(
            (candidate for name in ("cc", "gcc", "clang") if (candidate := command_path(name))),
            None,
        )
    dotnet = dotnet_sdk_path()
    openxml_detail = None
    if dotnet:
        try:
            openxml_detail = str(build_openxml_validator())
        except RuntimeError as exc:
            openxml_detail = str(exc)
    checks = {
        "node": {"ok": command_path("node") is not None, "path": command_path("node")},
        "npm": {"ok": command_path("npm") is not None, "path": command_path("npm")},
        "pptxgenjs": resolve_pptxgenjs(active_project),
        "markitdown": {"ok": python_module("markitdown"), "module": "markitdown"},
        "Pillow": {"ok": python_module("PIL"), "module": "PIL"},
        "defusedxml": {"ok": python_module("defusedxml"), "module": "defusedxml"},
        "Open XML schema validator": {
            "ok": bool(dotnet and openxml_detail and Path(openxml_detail).is_file()),
            "dotnet": dotnet,
            "assembly": openxml_detail,
        },
        "PPTX runtime": {
            "ok": runtime_probe[0],
            "path": str(ROOT / "scripts" / "pptx_tool.py"),
            "detail": runtime_probe[1],
        },
        "LibreOffice": {
            "ok": command_path("soffice", COMMON_SOFFICE_PATHS) is not None,
            "path": command_path("soffice", COMMON_SOFFICE_PATHS),
        },
        "LibreOffice sandbox": {
            "ok": unix_socket_ready or shim_compiler is not None,
            "af_unix_available": unix_socket_ready,
            "shim_required": not unix_socket_ready,
            "compiler": shim_compiler,
        },
        "Poppler pdftoppm": {
            "ok": poppler_path() is not None,
            "path": poppler_path(),
        },
        "jsonschema": {"ok": python_module("jsonschema"), "module": "jsonschema"},
        "PyYAML": {"ok": python_module("yaml"), "module": "yaml"},
    }
    common_required = [
        "markitdown",
        "Pillow",
        "defusedxml",
        "Open XML schema validator",
        "PPTX runtime",
    ]
    create_required = ["node", "pptxgenjs", *common_required]
    edit_required = list(common_required)
    required_by_mode = {
        "all": sorted(set(create_required + edit_required)),
        "create": create_required,
        "edit_ooxml": edit_required,
        "rebuild_from_source": create_required,
    }
    required = required_by_mode[mode]
    # LibreOffice 和 Poppler 为推荐项：缺失时警告但不阻断
    recommended = [
        "LibreOffice",
        "LibreOffice sandbox",
        "Poppler pdftoppm",
    ]
    missing_required = [name for name in required if not checks[name]["ok"]]
    missing_recommended = [name for name in recommended if not checks[name]["ok"]]
    capabilities = {
        "create_ready": all(checks[name]["ok"] for name in create_required),
        "edit_ready": all(checks[name]["ok"] for name in edit_required),
        "package_validation_ready": all(
            checks[name]["ok"]
            for name in ("PPTX runtime", "defusedxml", "Open XML schema validator")
        ),
        "visual_qa_ready": all(
            checks[name]["ok"]
            for name in ("LibreOffice", "LibreOffice sandbox", "Poppler pdftoppm", "Pillow")
        ),
        "pdf_export_ready": checks["LibreOffice"]["ok"],
    }
    return {
        "ok": not missing_required,
        "project_root": str(active_project),
        "plugin_root": str(ROOT),
        "mode": mode,
        "missing_required": missing_required,
        "missing_recommended": missing_recommended,
        "checks": checks,
        "capabilities": capabilities,
        "note": (
            "规划和审查可在缺少部分工具的情况下运行。"
            "候选 PPTX 创建需要 node/pptxgenjs；完整创建/编辑流程还需要文本提取、"
            "Pillow、suite-owned runtime、defusedxml 和 Open XML schema validator。"
            "LibreOffice/Poppler 缺失不阻止候选生成，"
            "但无法完成视觉 QA，因此交付状态只能是 incomplete。"
        ),
    }


def main() -> None:
    args = parse_args()
    result = inspect_environment(args.project_root, args.mode)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result["note"])
        for name, check in result["checks"].items():
            status = "ok" if check["ok"] else "缺失"
            extra = ""
            if name in ("LibreOffice", "Poppler pdftoppm") and not check["ok"]:
                extra = "（不阻止候选 PPTX 生成，但阻止 complete 视觉验收）"
            print(f"  {name}: {status}{extra}")
        if result.get("missing_recommended"):
            print(
                "\n⚠ 以下视觉 QA 工具缺失（候选文件可生成，但最终状态只能是 incomplete）: "
                + ", ".join(result["missing_recommended"])
            )
    if args.strict and result["missing_required"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
