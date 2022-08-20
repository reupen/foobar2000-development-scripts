from zipfile import ZIP_DEFLATED, ZIP_LZMA, ZipFile
from zlib import Z_BEST_COMPRESSION


def write_zip(zip_path, files, use_lzma=False):
    with ZipFile(
        zip_path,
        "w",
        compression=ZIP_LZMA if use_lzma else ZIP_DEFLATED,
        compresslevel=None if use_lzma else Z_BEST_COMPRESSION,
    ) as zip_file:
        for external_path, internal_path in files:
            zip_file.write(
                external_path,
                internal_path,
            )
