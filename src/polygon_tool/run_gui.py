"""Точка входа для src-layout (polygon-tool/src/polygon_tool/).
Положите этот файл в корень проекта, рядом с pyproject.toml."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from polygon_tool.gui import main

if __name__ == "__main__":
    raise SystemExit(main())
