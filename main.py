#!/usr/bin/env python3
"""擬人化 Gijinkai — language-aware AI fingerprint removal.

Usage:
  python3 main.py file <path> [--light|-l] [--aggressive|-a] [--write|-w]
  python3 main.py dir  <path> [--light|-l] [--aggressive|-a] [--write|-w] [--dry-run|-n]
  python3 main.py gui
  python3 main.py langs
  python3 main.py version
"""

import sys
from pathlib import Path

# Ensure the package is importable
sys.path.insert(0, str(Path(__file__).resolve().parent))

from gijinkai.cli import app

if __name__ == "__main__":
    # Support `gui` as a quick subcommand
    if len(sys.argv) > 1 and sys.argv[1] == "gui":
        from gijinkai.gui import launch_gui
        launch_gui()
    else:
        app()
