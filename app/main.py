import os
import sys
import zlib
from hashlib import sha1
from pathlib import Path

from .ls_tree import LsTreeModel


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


def read_object(parent: Path, hash: str):
    p = get_hash_path(parent, hash)
    bs = p.read_bytes()
    header, content = zlib.decompress(bs).split(b"\0", maxsplit=1)
    obj_type, _ = header.split(b" ")
    return obj_type.decode(), content


def init_repo(parent: Path):
    (parent / ".git").mkdir(parents=True)
    (parent / ".git" / "objects").mkdir(parents=True)
    (parent / ".git" / "refs").mkdir(parents=True)
    (parent / ".git" / "refs" / "heads").mkdir(parents=True)
    (parent / ".git" / "HEAD").write_text("ref: refs/heads/main\n")


def write_tree(path: str):
    if os.path.isfile(path):
        content = open(path, "rb").read()
        return write_object("blob", content)

    contents = sorted(
        os.listdir(path),
        key=lambda x: x if os.path.isfile(os.path.join(path, x)) else f"{x}/",
    )
    s = b""
    for item in contents:
        if item == ".git":
            continue
        full = os.path.join(path, item)
        if os.path.isfile(full):
            s += f"100644 {item}\0".encode()
        else:
            s += f"40000 {item}\0".encode()
        hash = int.to_bytes(int(write_tree(full), base=16), length=20, byteorder="big")
        s += hash

    s = f"tree {len(s)}\0".encode() + s
    hash = sha1(s).hexdigest()

    dir_path = f".git/objects/{hash[:2]}"
    os.makedirs(dir_path, exist_ok=True)

    with open(f"{dir_path}/{hash[2:]}", "wb") as f:
        f.write(zlib.compress(s))
    return hash


def main():
    match sys.argv[1]:
        case ["init"]:
            init_repo(Path("."))
            print("Initialized git directory")

        case ["cat-file", "-p", hash]:
            _, content = read_object(Path("."), hash)
            print(content)

        case ["hash-object", "-w", path]:
            hash = write_object(Path("."), "blob", Path(path).read_bytes())
            print(hash)

        case ["ls-tree", mode, hash]:
            tree = LsTreeModel(hash)
            tree.call(mode)

        case ["write-tree"]:
            print(write_tree("./"))

        case ["commit-tree", tree_hash, "-p", parent_hash, "-m", message]:
            parent_clause = f"parent {parent_hash}\n" if parent_hash else ""

            commit_content = (
                f"tree {tree_hash}\n{parent_clause}"
                f"author Omkar Kabde <omkarkabde@gmail.com> 1234567890 -0700\n"
                f"committer Omkar Kabde <omkarkabde@gmail.com> 1234567890 -0700\n\n"
                f"{message}\n"
            )
            hash = write_object(Path("."), "commit", commit_content)
            print(hash)


if __name__ == "__main__":
    main()
