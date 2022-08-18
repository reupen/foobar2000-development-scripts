import argparse
import os
from pathlib import PurePath
from zipfile import ZipFile

from utils.version import get_version

parser = argparse.ArgumentParser()
parser.add_argument("component_path", type=str)
parser.add_argument("output_dir", type=str)
parser.add_argument("platform", type=str, choices=["Win32", "x64", "ARM64"])


PLATFORM_MAPPING = {
    "Win32": "x86",
    "x64": "x64",
    "ARM64": "arm64",
}


def main():
    args = parser.parse_args()
    version = get_version()

    component_path = PurePath(args.component_path)
    input_base_name = component_path.stem
    annotation = f"-{version}" if os.getenv("CI") else ""
    platform = PLATFORM_MAPPING[args.platform]
    output_path = (
        f"{args.output_dir}{input_base_name}{annotation}.{platform}.fb2k-component"
    )

    with ZipFile(output_path, "w") as zip_file:
        zip_file.write(
            component_path,
            component_path.name,
        )

    print(f"Archive created: {output_path}")


if __name__ == "__main__":
    main()
