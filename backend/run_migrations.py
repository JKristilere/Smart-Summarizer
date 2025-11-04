"""Helper to run the `migrations` package correctly.

Why: Running the file directly (python migrations\__init__.py) sets sys.path to
the `migrations` folder and prevents sibling package imports like `app` from
being found. This script runs the package in the right context.

Usage (from the `backend` directory):
    python run_migrations.py
or
    python -m migrations
"""
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).parent.resolve()

if str(ROOT) not in sys.path:
    # Ensure the backend folder is on sys.path so sibling package `app` is importable
    sys.path.insert(0, str(ROOT))

if __name__ == "__main__":
    # Run the migrations package as a module so imports resolve properly
    runpy.run_module("migrations", run_name="__main__")
