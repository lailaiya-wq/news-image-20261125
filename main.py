#!/usr/bin/env python3
"""make.fun news-image-20261125 entry program (Python 3.13 stdlib only).

The entry image is pre-rendered and committed next to this file as
entry.png. This program copies it into the output directory, so every
run produces a byte-identical file.

Output directory: $MAKEFUN_OUTPUT_DIR when set, otherwise /output.
"""
import os
import shutil
import sys


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    src = os.path.join(here, "entry.png")
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(out_dir, exist_ok=True)
    dst = os.path.join(out_dir, "entry.png")
    shutil.copyfile(src, dst)
    print(f"wrote {dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
