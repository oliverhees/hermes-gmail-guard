#!/usr/bin/env python3
"""Starter für Windows, Mac und Linux – gleicher Befehl überall:

    python start.py        (Mac/Linux: python3 start.py)

Legt beim ersten Mal eine eigene Python-Umgebung (.venv) an, installiert alles Nötige
und startet den Setup-Assistenten. Es wird nichts im System verändert.
"""
import os
import subprocess
import sys
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENV = ROOT / ".venv"
PY = VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def run(*cmd):
    subprocess.run([str(c) for c in cmd], check=True, cwd=ROOT)


def main():
    if sys.version_info < (3, 10):
        sys.exit(f"❌ Python {sys.version_info.major}.{sys.version_info.minor} ist zu alt. "
                 "Bitte Python 3.10 oder neuer installieren: https://www.python.org/downloads/")
    if not PY.exists():
        print("📦 Lege eigene Python-Umgebung an (einmalig, ca. 1 Minute) …")
        venv.create(VENV, with_pip=True)
    marker = VENV / ".installed"
    if not marker.exists():
        print("📦 Installiere Abhängigkeiten …")
        run(PY, "-m", "pip", "install", "--quiet", "-r", "scripts/requirements.txt")
        marker.write_text("ok")
    sys.exit(subprocess.call([str(PY), "scripts/setup.py", *sys.argv[1:]], cwd=ROOT))


if __name__ == "__main__":
    main()
