"""Minimal idalib example that opens and analyzes a binary.

Usage:
    python test.py path/to/binary
"""

import argparse
import sys
from pathlib import Path

# idapro must be imported before other IDA modules to initialize idalib.
import idapro


def main() -> int:
    parser = argparse.ArgumentParser(description="Open a binary with idalib")
    parser.add_argument("path", type=Path, help="Binary or IDB path to open")
    args = parser.parse_args()

    path = args.path.expanduser().resolve()
    if not path.is_file():
        print(f"Error: file not found: {path}", file=sys.stderr)
        return 1

    idapro.enable_console_messages(True)
    print(f"Opening: {path}")
    if idapro.open_database(str(path), run_auto_analysis=True) != 0:
        print(f"Error: failed to open database: {path}", file=sys.stderr)
        return 1

    try:
        import ida_auto
        import idaapi

        ida_auto.auto_wait()
        print(f"Opened: {idaapi.get_root_filename()}")
        print(
            "Address range: "
            f"{idaapi.inf_get_min_ea():#x} - {idaapi.inf_get_max_ea():#x}"
        )
        return 0
    finally:
        idapro.close_database(False)


if __name__ == "__main__":
    raise SystemExit(main())
