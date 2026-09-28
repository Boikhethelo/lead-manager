import sys
from pathlib import Path

# Make `src/` importable so `pytest` works from the project root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))