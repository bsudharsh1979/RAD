"""Notebook / document content is DATA. Never execute it."""

from __future__ import annotations

import re

DANGEROUS_PATTERNS: list[tuple[str, str]] = [
    (r"\bkubectl\b", "kubectl"),
    (r"\bhelm\b", "helm"),
    (r"\bdocker\b", "docker"),
    (r"\brm\s+-rf\b", "rm -rf"),
    (r"%%bash", "jupyter_bash_magic"),
    (r"%%sh\b", "jupyter_sh_magic"),
    (r"os\.system\(", "os.system"),
    (r"subprocess\.", "subprocess"),
    (r"\bexec\(", "exec"),
    (r"\beval\(", "eval"),
    (r"do_shutdown\(", "kernel_shutdown"),
    (r"nvidia-smi", "nvidia_smi"),
    (r"from_pretrained\(", "model_download"),
    (r"requests\.(get|post|put|delete)", "network"),
    (r"urllib", "network"),
    (r"open\(['\"]/", "absolute_file_open"),
]


def inspect_code(source: str) -> list[str]:
    flags: list[str] = []
    for pattern, name in DANGEROUS_PATTERNS:
        if re.search(pattern, source or "", re.IGNORECASE):
            flags.append(name)
    return flags


def assert_not_executable(source: str) -> None:
    """Public API used by tests: ingestion must never treat source as a program."""
    _ = inspect_code(source)
    return None
