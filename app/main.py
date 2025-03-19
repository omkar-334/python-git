import sys
from pathlib import Path

from .ls_tree import LsTreeModel
from .utils import read_object, write_object


def init_repo(parent: Path):
    (parent / ".git").mkdir(parents=True)
    (parent / ".git" / "objects").mkdir(parents=True)
    (parent / ".git" / "refs").mkdir(parents=True)
    (parent / ".git" / "refs" / "heads").mkdir(parents=True)
    (parent / ".git" / "HEAD").write_text("ref: refs/heads/main\n")


def write_tree(path: Path):
    if path.is_file():
        return write_object(Path("."), "blob", Path(path).read_bytes())

    contents = sorted(
        path.iterdir(),
        key=lambda x: x.name if x.is_file() else f"{x.name}/",
    )
    s = b""

    for item in contents:
        if item.name == ".git":
            continue
        mode = "100644" if item.is_file() else "40000"
        s += f"{mode} {item.name}\0".encode()
        obj_hash = int.to_bytes(int(write_tree(item), 16), 20, "big")
        s += obj_hash

    hash = write_object(Path("."), "tree", s)

    return hash


def main():
    match sys.argv[1:]:
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
