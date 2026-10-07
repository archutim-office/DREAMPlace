#!/usr/bin/env python3

import argparse
import base64
from pathlib import Path


FILE_START = "========== FILE: "
FILE_END = "========== END FILE ==========\n"

def is_binary(data: bytes) -> bool:
    """粗略判斷檔案是否為 binary。"""
    if b"\x00" in data:
        return True

    try:
        data.decode("utf-8")
        return False
    except UnicodeDecodeError:
        return True

def flatten_folder(folder_path: str, output_path: str, include_binary: bool):
    folder = Path(folder_path).resolve()
    output = Path(output_path).resolve()

    if not folder.is_dir():
        raise ValueError(f"Folder does not exist: {folder}")

    files = sorted(p for p in folder.rglob("*") if p.is_file())

    processed = 0
    skipped = 0

    with output.open("w", encoding="utf-8") as out:
        for file_path in files:
            # 避免 output txt 本身如果放在 folder 裡又被重新打包
            if file_path.resolve() == output:
                continue

            relative_path = file_path.relative_to(folder)

            data = file_path.read_bytes()

            binary = is_binary(data)

            if binary and not include_binary:
                print(f"[SKIP] {relative_path} (binary / non-UTF-8)")
                skipped += 1
                continue

            out.write(f"{FILE_START}{relative_path.as_posix()} ==========\n")

            if binary:
                encoded = base64.b64encode(data).decode("ascii")

                out.write("TYPE: BASE64\n")
                out.write(encoded)
                out.write("\n")
            else:
                text = data.decode("utf-8")

                out.write("TYPE: UTF-8\n")
                out.write(text)

                if not text.endswith("\n"):
                    out.write("\n")

            out.write(FILE_END)

            processed += 1
            print(f"[OK]   {relative_path}")

    print()
    print(f"Output : {output}")
    print(f"Files  : {processed}")
    print(f"Skipped: {skipped}")


def main():
    parser = argparse.ArgumentParser(
        description="Flatten a folder into a single TXT file."
    )

    parser.add_argument(
        "folder",
        help="Folder to flatten"
    )

    parser.add_argument(
        "-o",
        "--output",
        help="Output TXT file. Default: <folder>.txt"
    )

    parser.add_argument(
        "--binary",
        action="store_true",
        help="Include binary / non-UTF-8 files using Base64 encoding"
    )

    args = parser.parse_args()

    folder = Path(args.folder)

    output = (
        Path(args.output)
        if args.output
        else folder.parent / f"{folder.name}.txt"
    )

    flatten_folder(
        str(folder),
        str(output),
        args.binary
    )


if __name__ == "__main__":
    main()