import os
import re
import sys
import zlib


def main():
    command = sys.argv[1]
    if command == "init":
        os.mkdir(".git")
        os.mkdir(".git/objects")
        os.mkdir(".git/refs")
        with open(".git/HEAD", "w") as f:
            f.write("ref: refs/heads/main\n")
        print("Initialized git directory")

    elif command == "cat-file":
        hash = sys.argv[3]
        with open(f".git/objects/{hash[:2]}/{hash[2:]}", "rb") as f:
            data = zlib.decompress(f.read()).decode()
            data = re.sub("blob [1-9]*", "", data)
            data = data.removesuffix("\n")
        return data
    else:
        raise RuntimeError(f"Unknown command #{command}")


if __name__ == "__main__":
    main()
