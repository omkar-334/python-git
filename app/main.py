import os
import sys
import zlib
from hashlib import sha1

from .ls_tree import LsTreeModel


def hash_object(path):
    with open(path, "rb").read() as f:
        content = f.read()

    content = f"blob {len(content)}\0".encode("utf-8") + content
    hash = sha1(content).hexdigest()

    dir_path = f".git/objects/{hash[:2]}"
    os.makedirs(dir_path, exist_ok=True)

    with open(f"{dir_path}/{hash[2:]}", "wb") as f:
        f.write(zlib.compress(content))
    return hash


def write_tree(path: str):
    if os.path.isfile(path):
        return hash_object(path)

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
    return sha1


def main():
    command = sys.argv[1]
    if command == "init":
        os.mkdir(".git")
        os.mkdir(".git/objects")
        os.mkdir(".git/refs")
        with open(".git/HEAD", "w") as f:
            f.write("ref: refs/heads/main\n")
        print("Initialized git directory")

    elif command == "cat-file" and sys.argv[2] == "-p":
        hash = sys.argv[3]
        with open(f".git/objects/{hash[:2]}/{hash[2:]}", "rb") as f:
            data = zlib.decompress(f.read())
            header, content = data.split(b"\0", maxsplit=1)
            print(content.decode(encoding="utf-8"), end="")
    elif command == "hash-object" and sys.argv[2] == "-w":
        path = sys.argv[3]
        hash = hash_object(path)
        print(hash)
    elif command == "ls-tree":
        hash = sys.argv[3]
        tree = LsTreeModel(hash)
        tree.call(sys.argv[2])

    elif command == "write-tree":
        print(write_tree("./"))

    else:
        raise RuntimeError(f"Unknown command #{command}")


if __name__ == "__main__":
    main()
