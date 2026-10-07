#!/usr/bin/env python3

import argparse
import base64
from pathlib import Path


FILE_START = "========== FILE: "
FILE_END = "========== END FILE =========="


def rebuild_folder(input_path: str, output_folder: str):
    input_file = Path(input_path).resolve()
    output_root = Path(output_folder).resolve()

    if not input_file.is_file():
        raise ValueError(f"Input file does not exist: {input_file}")

    output_root.mkdir(parents=True, exist_ok=True)

    content = input_file.read_text(encoding="utf-8")

    position = 0
    restored = 0

    while True:
        start = content.find(FILE_START, position)

        if start == -1:
            break

        # 找 filename
        filename_start = start + len(FILE_START)
        filename_end = content.find(" ==========\n", filename_start)

        if filename_end == -1:
            raise ValueError(
                f"Invalid file header near position {start}"
            )

        relative_path = content[filename_start:filename_end]

        data_start = filename_end + len(" ==========\n")

        # TYPE
        if content.startswith("TYPE: BASE64\n", data_start):
            file_type = "BASE64"
            data_start += len("TYPE: BASE64\n")

        elif content.startswith("TYPE: UTF-8\n", data_start):
            file_type = "UTF-8"
            data_start += len("TYPE: UTF-8\n")

        else:
            raise ValueError(
                f"Missing TYPE information for {relative_path}"
            )

        end = content.find(FILE_END, data_start)

        if end == -1:
            raise ValueError(
                f"Missing END FILE marker for {relative_path}"
            )

        file_data = content[data_start:end]

        # Remove the newline immediately before END FILE
        if file_data.endswith("\n"):
            file_data = file_data[:-1]

        target = output_root / relative_path

        # 防止 ../ 路徑逃出 output folder
        target_resolved = target.resolve()

        try:
            target_resolved.relative_to(output_root)
        except ValueError:
            raise ValueError(
                f"Unsafe path detected: {relative_path}"
            )

        target_resolved.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        if file_type == "BASE64":
            data = base64.b64decode(file_data)
            target_resolved.write_bytes(data)

        else:
            target_resolved.write_text(
                file_data,
                encoding="utf-8"
            )

        print(f"[OK] {relative_path}")

        restored += 1
        position = end + len(FILE_END)

    print()
    print(f"Output : {output_root}")
    print(f"Files  : {restored}")


def main():
    parser = argparse.ArgumentParser(
        description="Rebuild a folder from a flattened TXT file."
    )

    parser.add_argument(
        "input",
        help="Flattened TXT file"
    )

    parser.add_argument(
        "-o",
        "--output",
        help="Output folder. Default: folder with same name as TXT"
    )

    args = parser.parse_args()

    input_file = Path(args.input)

    output = (
        Path(args.output)
        if args.output
        else input_file.parent / input_file.stem
    )
    rebuild_folder(
        str(input_file),
        str(output)
    )


if __name__ == "__main__":
    main()