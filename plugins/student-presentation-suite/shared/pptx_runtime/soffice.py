"""LibreOffice process environment, including Linux AF_UNIX sandbox fallback."""

from __future__ import annotations

import hashlib
import os
import platform
import shutil
import socket
import subprocess
import tempfile
from pathlib import Path


def af_unix_available() -> bool:
    if platform.system() != "Linux" or not hasattr(socket, "AF_UNIX"):
        return True
    try:
        channel = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    except OSError:
        return False
    channel.close()
    return True


def _shim_source() -> Path:
    return Path(__file__).with_name("assets") / "lo_socket_shim.c"


def build_socket_shim() -> Path:
    source = _shim_source()
    if not source.is_file():
        raise RuntimeError(f"LibreOffice AF_UNIX shim source is missing: {source}")
    compiler = os.environ.get("CC") or next(
        (candidate for name in ("cc", "gcc", "clang") if (candidate := shutil.which(name))),
        None,
    )
    if not compiler:
        raise RuntimeError(
            "AF_UNIX is blocked and no C compiler is available to build the LibreOffice shim"
        )
    digest = hashlib.sha256(
        source.read_bytes() + platform.machine().encode("ascii", errors="ignore")
    ).hexdigest()[:16]
    cache = Path(tempfile.gettempdir()) / "student-presentation-suite" / "libreoffice"
    cache.mkdir(parents=True, exist_ok=True)
    output = cache / f"lo-socket-shim-{digest}.so"
    if output.is_file():
        return output
    temporary = cache / f".{output.name}.{os.getpid()}.tmp"
    try:
        completed = subprocess.run(
            [
                compiler,
                "-shared",
                "-fPIC",
                "-O2",
                "-Wall",
                "-Wextra",
                "-Werror",
                "-o",
                str(temporary),
                str(source),
                "-ldl",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
        )
        if completed.returncode or not temporary.is_file():
            raise RuntimeError(
                "failed to build LibreOffice AF_UNIX shim: "
                + (completed.stderr or completed.stdout or "compiler produced no output").strip()
            )
        temporary.replace(output)
    finally:
        if temporary.exists():
            temporary.unlink()
    return output


def soffice_environment() -> tuple[dict[str, str], list[str]]:
    environment = {**os.environ, "SAL_USE_VCLPLUGIN": "svp"}
    messages: list[str] = []
    force_shim = environment.get("PPTX_RUNTIME_FORCE_AF_UNIX_SHIM") == "1"
    if platform.system() == "Linux" and (force_shim or not af_unix_available()):
        shim = build_socket_shim()
        existing = environment.get("LD_PRELOAD")
        environment["LD_PRELOAD"] = (
            f"{shim}{os.pathsep}{existing}" if existing else str(shim)
        )
        if force_shim:
            environment["PPTX_RUNTIME_TEST_DENY_AF_UNIX"] = "1"
            messages.append(f"AF_UNIX denial simulation active; loaded compatibility shim {shim.name}")
        else:
            messages.append(f"AF_UNIX blocked; loaded compatibility shim {shim.name}")
    return environment, messages
