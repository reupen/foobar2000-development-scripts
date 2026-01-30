#!/usr/bin/env python3.11
import argparse
import os
import subprocess
from pathlib import Path

from utils.config import get_build_config
from utils.licence import get_licence_text
from utils.path import get_root_dir
from utils.version import get_version
from utils.zip import write_zip

parser = argparse.ArgumentParser()
parser.add_argument(
    "--symstore",
    choices=["silent", "skip", "prompt"],
    default="silent",
)
parser.add_argument("--msbuild-extra-args", default="")


def build(msbuild_path, msbuild_extra_args, platform, solution_path):
    root_dir = get_root_dir()
    subprocess.run(
        [
            msbuild_path,
            "/m",
            f"/p:Configuration=Release;Platform={platform}",
            msbuild_extra_args,
            "/t:Rebuild",
            root_dir / solution_path,
        ],
        check=True,
    )


def add_to_symbol_store(path, component_name, version):
    program_files_x86_path = os.environ["ProgramFiles(x86)"]
    symbols_path = os.environ["FB2K_SYMBOL_STORE"]

    print(f"\nAdding file to symbol store: {path}")

    subprocess.run(
        [
            rf"{program_files_x86_path}\Windows Kits\10\Debuggers\x64\symstore.exe",
            "add",
            "/f",
            path,
            "/s",
            symbols_path,
            "/t",
            component_name,
            "/v",
            str(version),
        ],
        check=True,
    )


def main():
    args = parser.parse_args()
    root_dir = get_root_dir()

    build_config = get_build_config()

    component_name = build_config["component_name"]
    solution_path = build_config["solution_path"]
    output_path = build_config["output_path"]
    x86_build_path = build_config["x86_build_path"]
    x64_build_path = build_config["x64_build_path"]
    vs_version = build_config.get("vs_version", "[17,18)")

    version = get_version()

    program_files_x86_path = os.environ["ProgramFiles(x86)"]
    vswhere_result = subprocess.run(
        [
            rf"{program_files_x86_path}\Microsoft Visual Studio\Installer\vswhere.exe",
            "-utf8",
            "-latest",
            "-version",
            vs_version,
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

    build(msbuild_path, args.msbuild_extra_args, "Win32", solution_path)
    build(msbuild_path, args.msbuild_extra_args, "x64", solution_path)

    Path(root_dir / output_path).mkdir(exist_ok=True)

    component_archive_name = f"{component_name}-{version}.x86-x64.fb2k-component"
    component_archive_path = root_dir / output_path / component_archive_name

    print("Building component package...")
    print(f"Output path: {component_archive_path}")

    x86_dll_path = root_dir / x86_build_path / f"{component_name}.dll"
    x86_pdb_path = root_dir / x86_build_path / f"{component_name}.pdb"
    x64_dll_path = root_dir / x64_build_path / f"{component_name}.dll"
    x64_pdb_path = root_dir / x64_build_path / f"{component_name}.pdb"

    if licence_file := build_config.get("licence_file"):
        licence_path = root_dir / licence_file
        memory_files = {"LICENSE.txt": get_licence_text(licence_path)}
    else:
        memory_files = None

    files = [
        (x86_dll_path, rf"{component_name}.dll"),
        (x64_dll_path, rf"x64\{component_name}.dll"),
    ]

    write_zip(component_archive_path, files, memory_files=memory_files)

    symbols_archive_name = f"{component_name}-{version}.x86-x64.symbols.lzma.zip"
    symbols_archive_path = root_dir / output_path / symbols_archive_name

    print("Building symbols package...")
    print(f"Output path: {symbols_archive_path}")

    write_zip(
        symbols_archive_path,
        [
            (x86_pdb_path, rf"{component_name}.pdb"),
            (x64_pdb_path, rf"x64\{component_name}.pdb"),
        ],
        use_lzma=True,
    )

    skip_symstore = args.symstore == "skip"

    if args.symstore == "prompt":
        user_input = input(
            "Do you want to add the generated symbols to the symbol store? (y/n): "
        )
        skip_symstore = user_input.strip().lower() != "y"

    if skip_symstore:
        print("Skipping update of symbol store...")
        print("Done!")
        return

    symstore_paths = [x86_dll_path, x86_pdb_path, x64_dll_path, x64_pdb_path]

    for path in symstore_paths:
        add_to_symbol_store(path, component_name, version)

    print("Done!")


if __name__ == "__main__":
    main()
