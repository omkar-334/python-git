import zlib
from hashlib import sha1
from pathlib import Path


def get_hash_path(parent: Path, hash: str):
    pre = hash[:2]
    post = hash[2:]
    p = parent / ".git" / "objects" / pre / post
    return p


def write_object(parent: Path, obj_type: str, content: bytes):
    content = f"{obj_type} {len(content)}\0".encode("utf-8") + content
    compressed_content = zlib.compress(content, level=zlib.Z_BEST_SPEED)
    hash = sha1(content).hexdigest()

    p = get_hash_path(parent, hash)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(compressed_content)
    return hash


def read_object(parent: Path, hash: str):
    p = get_hash_path(parent, hash)
    bs = p.read_bytes()
    header, content = zlib.decompress(bs).split(b"\0", maxsplit=1)
    obj_type, _ = header.split(b" ")
    return obj_type.decode(), content
