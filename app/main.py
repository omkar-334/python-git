import os
import sys
import zlib
from hashlib import sha1

from .ls_tree import LsTreeModel


def hash_object(obj_type, content):
    content = f"{obj_type} {len(content)}\0".encode("utf-8") + content
    hash = sha1(content).hexdigest()

    dir_path = f".git/objects/{hash[:2]}"
    os.makedirs(dir_path, exist_ok=True)

    with open(f"{dir_path}/{hash[2:]}", "wb") as f:
        f.write(zlib.compress(content))
    return hash


def write_tree(path: str):
    if os.path.isfile(path):
        content = open(path, "rb").read()
        return hash_object("blob", content)

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


# case ["commit-tree", tree_sha, "-p", commit_sha, "-m", message]:
# contents = b"".join(
#     [
#         b"tree %b\n" % tree_sha.encode(),
#         b"parent %b\n" % commit_sha.encode(),
#         b"author ggzor <30713864+ggzor@users.noreply.github.com> 1714599041 -0600\n",
#         b"committer ggzor <30713864+ggzor@users.noreply.github.com> 1714599041 -0600\n\n",
#         message.encode(),
#         b"\n",
#     ]
# )
# hash = write_object(Path("."), "commit", contents)
# print(hash)


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
        content = open(path, "rb").read()
        hash = hash_object("blob", content)
        print(hash)
    elif command == "ls-tree":
        hash = sys.argv[3]
        tree = LsTreeModel(hash)
        tree.call(sys.argv[2])

    elif command == "write-tree":
        print(write_tree("./"))

    elif command == "commit-tree":
        tree_hash = sys.argv[2]
        commit_message = None
        parent_hash = None
        if sys.argv[3] == "-m":
            commit_message = sys.argv[4]
        if sys.argv[3] == "-p":
            parent_hash = sys.argv[4]
            if sys.argv[5] == "-m":
                commit_message = sys.argv[6]
        if parent_hash:
            parent_clause = f"parent {parent_hash}\n"
        commit_content = (
            f"tree {tree_hash}\n{parent_clause}"
            f"author Omkar Kabde <omkarkabde@gmail.com> 1234567890 -0700\n"
            f"committer Omkar Kabde <omkarkabde@gmail.com> 1234567890 -0700\n\n"
            f"{commit_message}\n"
        )
        hash = hash_object("commit ", commit_content.encode("utf-8"))
        print(hash)

    else:
        raise RuntimeError(f"Unknown command #{command}")


if __name__ == "__main__":
    main()
