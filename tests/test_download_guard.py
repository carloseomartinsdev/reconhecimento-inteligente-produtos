from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_download_check_does_not_create_archive(project_root: Path) -> None:
    script = project_root / "scripts" / "download_rpc.py"
    completed = subprocess.run(
        [sys.executable, str(script), "--check"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0
    assert "Download não iniciado" in completed.stdout
    assert "CC BY-NC-SA 4.0" in completed.stdout
    assert not (project_root / "data" / "public" / "downloads").exists()


def test_download_without_license_flag_is_rejected(project_root: Path) -> None:
    script = project_root / "scripts" / "download_rpc.py"
    completed = subprocess.run(
        [sys.executable, str(script), "--confirm-download"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 2
    assert not (project_root / "data" / "public" / "downloads").exists()
