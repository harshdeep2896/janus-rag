"""Raw file storage on local disk.

Uploaded files are stored under `raw_dir`, named by their SHA-256 content hash
(no extension). The same bytes always map to the same file name, so saving a
file twice is safe. `filename` and `mime_type` live in the `documents` table.
"""

import asyncio
import hashlib
import os
import re
import uuid
from pathlib import Path

# A valid content hash: exactly 64 lowercase hex characters (SHA-256 hexdigest).
_HASH_RE = re.compile(r"[0-9a-f]{64}")


def _path_for(raw_dir: Path, content_hash: str) -> Path:
    """Return the storage path for a content hash.

    Validates the hash first, so names like "../../.env" can never
    escape `raw_dir` (path traversal).

    Raises:
        ValueError: if `content_hash` is not 64 lowercase hex characters.
    """
    if _HASH_RE.fullmatch(content_hash) is None:
        raise ValueError("invalid content_hash")
    return raw_dir / content_hash


def compute_content_hash(data: bytes) -> str:
    """Return the SHA-256 hex digest of `data`.

    Same bytes always give the same hash, which is what makes storage,
    the `documents.content_hash` unique constraint, and the Temporal
    workflow ID idempotent.
    """
    return hashlib.sha256(data).hexdigest()


def _write_atomic(path: Path, data: bytes) -> None:
    """Write `data` to `path` so the file is either complete or absent.

    Blocking (runs in a worker thread via `asyncio.to_thread`).

    Steps:
        1. Create the parent folder if missing.
        2. If the file already exists, do nothing (idempotent).
        3. Write to a uniquely named temp file next to it.
        4. Rename the temp file to the real name with `os.replace`,
           which is atomic on the same disk.
    If anything fails, the temp file is deleted and the error is re-raised.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return

    # Unique name so two workers saving the same hash never share a temp file.
    tmp = path.with_name(f"{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        tmp.write_bytes(data)
        os.replace(tmp, path)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise


async def save_raw(raw_dir: Path, content_hash: str, data: bytes) -> Path:
    """Save raw file bytes under `raw_dir` and return the file path.

    Safe to call more than once with the same hash: the second call
    finds the file and returns without writing.

    Raises:
        ValueError: if `content_hash` is invalid.
    """
    path = _path_for(raw_dir, content_hash)
    await asyncio.to_thread(_write_atomic, path, data)
    return path


async def read_raw(raw_dir: Path, content_hash: str) -> bytes:
    """Read and return the raw file bytes for `content_hash`.

    Raises:
        ValueError: if `content_hash` is invalid.
        FileNotFoundError: if no file is stored for this hash.
    """
    path = _path_for(raw_dir, content_hash)
    return await asyncio.to_thread(path.read_bytes)
