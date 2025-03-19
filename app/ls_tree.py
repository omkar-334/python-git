from pathlib import Path

from .utils import read_object


class LsTreeModel:
    """
    usage: git ls-tree [<options>] <tree-ish> [<path>...]

    -d                    only show trees
    -r                    recurse into subtrees
    -t                    show trees when recursing
    # # -z                    terminate entries with NUL byte
    # # -l, --long            include object size
    --name-only           list only filenames
    # # --name-status         list only filenames
    # # --object-only         list only objects
    # # --full-name           use full path names
    # # --full-tree           list entire tree; not just current directory (implies --full-name)
    # # --format <format>     format to use for the output
    # # --abbrev[=<n>]        use <n> digits to display object names

    """

    def __init__(self, hash, parent_name=None):
        self.tree = None
        self.parent_name = parent_name
        self.entries = []

        self.mode_dict = {
            "100644": "blob",
            "100755": "blob",
            "040000": "tree",
        }
        self.parse(hash)
        self.recurse()

    def parse(self, hash):
        # with open(f".git/objects/{hash[:2]}/{hash[2:]}", "rb") as f:
        #     data = zlib.decompress(f.read())
        # tree, content = data.split(b"\0", maxsplit=1)
        self.tree, content = read_object(Path("."), hash)
        while content:
            mode, rest = content.split(b" ", 1)
            name, rest = rest.split(b"\0", 1)
            sha = rest[:20].hex()
            content = rest[20:]

            self.add(mode.decode(), name.decode(), sha)

    def add(self, mode, name, hash):
        if len(mode) == 5:
            mode = "0" + mode
        if self.parent_name:
            name = f"{self.parent_name}/{name}"
        self.entries.append(
            {
                "mode": mode,
                "mode_name": self.mode_dict[mode],
                "name": name,
                "hash": hash,
                "parent": self.tree,
            }
        )

    def call(self, arg):
        arg = arg.replace("-", "_")
        arg = arg.removeprefix("__")
        func = getattr(self, arg)
        func()

    def recurse(self):
        idx = 0
        while idx < len(self.entries):
            entry = self.entries[idx]
            if entry["mode_name"] == "tree":
                temptree = LsTreeModel(entry["hash"], entry["name"])
                self.entries = self.entries[: idx + 1] + temptree.entries + self.entries[idx + 1 :]
            idx += 1

    def name_only(self):
        # print(*[i["name"] for i in self.entries if i["parent"] == self.tree], sep="\n")
        print(*[i["name"] for i in self.entries if "/" not in i["name"]], sep="\n")

    def print_tree(self, filter_func=None):
        for entry in self.entries:
            if filter_func is None or filter_func(entry):
                mode, mode_name, name, sha, parent = entry.values()
                print(f"{mode} {mode_name} {sha} {name}")

    def _d(self):
        """only show trees"""
        self.print_tree(lambda entry: entry["mode_name"] == "tree" and entry["parent"] == self.tree)

    def _t(self):
        """show trees when recursing"""
        self.print_tree()

    def _r(self):
        self.print_tree(lambda entry: entry["mode_name"] == "blob")
