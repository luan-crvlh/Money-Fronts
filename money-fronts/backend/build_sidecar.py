"""
Script auxiliar de build do Sidecar (DAS seção 4 e 6).

Gera um executável standalone (PyInstaller) e renomeia o binário incluindo a
tripla de compilação da arquitetura, como o Tauri v2 exige em `externalBin`
(ex.: app-backend-x86_64-pc-windows-msvc.exe).

Uso:
    python build_sidecar.py
"""
import platform
import subprocess
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).parent
DIST = ROOT / "dist"
BIN_NAME = "app-backend"


def rust_target_triple() -> str:
    """Aproximação da tripla de compilação Rust para o SO/arquitetura atuais.
    Para builds cross-platform reais, defina explicitamente via variável de
    ambiente RUST_TARGET_TRIPLE no pipeline de CI."""
    import os

    if os.environ.get("RUST_TARGET_TRIPLE"):
        return os.environ["RUST_TARGET_TRIPLE"]

    system = platform.system()
    machine = platform.machine().lower()
    arch = "x86_64" if "64" in machine else machine

    if system == "Windows":
        return f"{arch}-pc-windows-msvc"
    if system == "Darwin":
        return f"{arch}-apple-darwin" if arch != "x86_64" else "x86_64-apple-darwin"
    return f"{arch}-unknown-linux-gnu"


def main():
    subprocess.run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--name",
            BIN_NAME,
            "--onefile",
            "--noconfirm",
            "--distpath",
            str(DIST),
            str(ROOT / "app" / "main.py"),
            '--add-data=alembic;alembic',
            '--add-data=alembic.ini;.',
        ],
        check=True,
    )

    triple = rust_target_triple()
    src = DIST / (BIN_NAME + (".exe" if platform.system() == "Windows" else ""))
    ext = ".exe" if platform.system() == "Windows" else ""
    dst = DIST / f"{BIN_NAME}-{triple}{ext}"
    shutil.move(str(src), str(dst))
    print(f"Binário gerado: {dst}")
    print("Copie-o para src-tauri/binaries/ conforme referenciado em tauri.conf.json")


if __name__ == "__main__":
    main()
