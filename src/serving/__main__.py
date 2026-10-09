"""``python3 -m serving`` entry point (PYTHONPATH=src)."""

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
