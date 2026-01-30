import argparse
import os
from pathlib import PurePath

from utils.config import get_build_config
from utils.licence import get_licence_text
from utils.path import get_root_dir
from utils.version import get_version
from utils.zip import write_zip

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
    root_dir = get_root_dir()
    build_config = get_build_config()

    component_path = PurePath(args.component_path)
    input_base_name = component_path.stem
    annotation = f"-{version}" if os.getenv("CI") else ""
    platform = PLATFORM_MAPPING[args.platform]
    output_path = (
        f"{args.output_dir}{input_base_name}{annotation}.{platform}.fb2k-component"
    )

    if licence_file := build_config.get("licence_file"):
        licence_path = root_dir / licence_file
        memory_files = {"LICENSE.txt": get_licence_text(licence_path)}
    else:
        memory_files = None

    files = [(component_path, component_path.name)]

    write_zip(output_path, files, memory_files=memory_files)

    print(f"Archive created: {output_path}")


if __name__ == "__main__":
    main()
