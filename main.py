#!/usr/bin/env python3
"""Write the Ship It Friday commit message to /output/entry.txt.

Pure stdlib, deterministic: no network, no input files, no clock, no
randomness. The output file is written atomically (temp file inside the
output dir, rename with copy+unlink fallback for EXDEV) and chmodded to
0o644 explicitly, then re-read and self-validated against the gate:
exactly one non-blank UTF-8 line, 1-159 characters, mode 0644, and the
raw bytes match the expected entry content exactly.
"""

import os
import shutil
import sys

ENTRY = "refactor: rewrite prod auth on a Friday afternoon and ship it now, I'm 99% sure nothing breaks (it will)"
OUTPUT_DIR = "/output"
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "entry.txt")


def fail(message):
    print(f"error: {message}", file=sys.stderr)
    sys.exit(1)


def main():
    data = (ENTRY + "\n").encode("utf-8")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    tmp_path = os.path.join(OUTPUT_DIR, ".entry.txt.tmp")
    with open(tmp_path, "wb") as fh:
        fh.write(data)
        fh.flush()
        os.fsync(fh.fileno())
    os.chmod(tmp_path, 0o644)
    try:
        os.rename(tmp_path, OUTPUT_PATH)
    except OSError:
        # EXDEV-safe fallback: copy then unlink.
        shutil.copyfile(tmp_path, OUTPUT_PATH)
        os.unlink(tmp_path)
    os.chmod(OUTPUT_PATH, 0o644)

    # Self-validation: re-read and check the output contract.
    try:
        with open(OUTPUT_PATH, "rb") as fh:
            raw = fh.read()
    except OSError as exc:
        fail(f"cannot re-read output: {exc}")

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        fail(f"output is not valid UTF-8: {exc}")

    # Exact-content self-check: the bytes on disk must be exactly the
    # entry plus a trailing newline — catches any partial or corrupted
    # write that the shape checks below would miss.
    if raw != data:
        fail("output bytes do not exactly match the expected entry content")

    lines = text.splitlines()
    if len(lines) != 1:
        fail(f"expected exactly one line, got {len(lines)}")
    line = lines[0]
    if not line.strip():
        fail("output line is only whitespace")
    if not 1 <= len(line) <= 159:
        fail(f"line is {len(line)} characters, must be 1-159")

    mode = os.stat(OUTPUT_PATH).st_mode & 0o777
    if mode != 0o644:
        fail(f"output mode is {mode:03o}, expected 0644")

    print(f"wrote {OUTPUT_PATH}: {len(line)} chars, mode 0644")
    print(line)


if __name__ == "__main__":
    main()
