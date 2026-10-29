"""Conservative local document and ZIP processing boundaries."""

from __future__ import annotations

import os
import shutil
import stat
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit

_MAX_FILES = 200
_MAX_UNCOMPRESSED = 64 * 1024 * 1024
_BLOCKED_NAMES = {".env", ".git", ".ssh", ".aws", ".config", ".kube",
                  "id_rsa", "id_ed25519", "credentials", "secrets"}


def require_local_document(path: str) -> Path:
    if not isinstance(path, str) or not path.strip():
        raise ValueError("Document path cannot be empty.")
    if urlsplit(path).scheme in {"http", "https", "ftp", "file"}:
        raise PermissionError("Remote documents are disabled. Download and review locally.")
    root = Path(os.environ.get("OWL_DOCUMENT_ROOT", os.getcwd())).expanduser().resolve()
    target = Path(path).expanduser().resolve()
    if root == Path("/") or not target.is_relative_to(root):
        raise PermissionError("Document path is outside OWL_DOCUMENT_ROOT.")
    if set(target.relative_to(root).parts) & _BLOCKED_NAMES:
        raise PermissionError("Access to private configuration files is not allowed.")
    if not target.is_file():
        raise FileNotFoundError("Document does not exist.")
    return target


def extract_zip_safely(zip_path: str, cache_dir: str) -> list[str]:
    archive = require_local_document(zip_path)
    if archive.suffix.lower() != ".zip":
        raise ValueError("Only .zip archives are supported.")
    root = Path(cache_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    destination = root / archive.stem
    if destination.exists():
        raise FileExistsError("Archive destination already exists.")

    with zipfile.ZipFile(archive) as zipped:
        members = zipped.infolist()
        if len(members) > _MAX_FILES or sum(m.file_size for m in members) > _MAX_UNCOMPRESSED:
            raise ValueError("Archive exceeds extraction limits.")
        for entry in members:
            name = PurePosixPath(entry.filename)
            mode = entry.external_attr >> 16
            if (name.is_absolute() or ".." in name.parts or "\\" in entry.filename
                    or "\x00" in entry.filename or stat.S_ISLNK(mode)):
                raise ValueError("Unsafe ZIP entry path or symlink.")
        stage = Path(tempfile.mkdtemp(prefix="owl-extract-", dir=root))
        extracted = []
        try:
            total = 0
            for entry in members:
                relative = PurePosixPath(entry.filename)
                target = stage.joinpath(*relative.parts)
                if not target.resolve().is_relative_to(stage.resolve()):
                    raise ValueError("ZIP extraction would escape the destination.")
                if entry.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                with zipped.open(entry) as source, target.open("xb") as sink:
                    while block := source.read(65536):
                        total += len(block)
                        if total > _MAX_UNCOMPRESSED:
                            raise ValueError("Archive decompression limit exceeded.")
                        sink.write(block)
                extracted.append(str(destination.joinpath(*relative.parts)))
            stage.rename(destination)
            return extracted
        except Exception:
            shutil.rmtree(stage, ignore_errors=True)
            raise
