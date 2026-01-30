from pathlib import Path


def get_licence_text(licence_path: Path):
    licence_text = licence_path.read_text(encoding="utf-8")
    return "\r\n".join(licence_text.splitlines())
