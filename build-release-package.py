#!/usr/bin/env python3.11
import os
import subprocess
import tomllib
from functools import cache
from pathlib import Path

from utils.version import get_version
from utils.zip import write_zip

BUILD_CONFIG_FILE_NAME = "build-config.toml"


@cache
def get_root_dir():
    parent_dir = Path(__file__).parent
    root_dir = parent_dir
    while not (root_dir / BUILD_CONFIG_FILE_NAME).exists():
        root_dir = root_dir.parent

        if not root_dir:
            raise FileNotFoundError(
                f"{BUILD_CONFIG_FILE_NAME} not found in any parent directories."
            )

    return root_dir


def build(msbuild_path, platform, solution_path):
    root_dir = get_root_dir()
    subprocess.run(
        [
            msbuild_path,
            f"/p:Configuration=Release;Platform={platform}",
            "/t:Rebuild",
            root_dir / solution_path,
        ],
        check=True,
    )


def main():
    root_dir = get_root_dir()

    with open(root_dir / "build-config.toml", "rb") as file:
        build_config = tomllib.load(file)

    component_name = build_config["component_name"]
    solution_path = build_config["solution_path"]
    output_path = build_config["output_path"]
    x86_build_path = build_config["x86_build_path"]
    x64_build_path = build_config["x64_build_path"]

    version = get_version()

    program_files_x86_path = os.environ["ProgramFiles(x86)"]
    vswhere_result = subprocess.run(
        [
            rf"{program_files_x86_path}\Microsoft Visual Studio\Installer\vswhere.exe",
            "-utf8",
            "-version",
            "17",
            "-requires",
            "Microsoft.Component.MSBuild",
            "-find",
            r"MSBuild\**\Bin\MSBuild.exe",
        ],
        capture_output=True,
        check=True,
    )

    msbuild_path = vswhere_result.stdout.decode("utf-8").strip("\r\n")

    if not msbuild_path:
        raise FileNotFoundError("MSBuild could not be found")

    build(msbuild_path, "Win32", solution_path)
    build(msbuild_path, "x64", solution_path)

    Path(root_dir / output_path).mkdir(exist_ok=True)

    component_archive_name = f"{component_name}-{version}.x86-x64.fb2k-component"
    component_archive_path = root_dir / output_path / component_archive_name

    print("Building component package...")
    print(f"Output path: {component_archive_path}")

    write_zip(
        component_archive_path,
        [
            (
                root_dir / x86_build_path / f"{component_name}.dll",
                rf"{component_name}.dll",
            ),
            (
                root_dir / x64_build_path / f"{component_name}.dll",
                rf"x64\{component_name}.dll",
            ),
        ],
    )

    symbols_archive_name = f"{component_name}-{version}.x86-x64.symbols.lzma.zip"
    symbols_archive_path = root_dir / output_path / symbols_archive_name

    print("Building symbols package...")
    print(f"Output path: {symbols_archive_path}")

    write_zip(
        symbols_archive_path,
        [
            (
                root_dir / x86_build_path / f"{component_name}.pdb",
                rf"{component_name}.pdb",
            ),
            (
                root_dir / x64_build_path / f"{component_name}.pdb",
                rf"x64\{component_name}.pdb",
            ),
        ],
        use_lzma=True,
    )

    print("Done!")


if __name__ == "__main__":
    main()
