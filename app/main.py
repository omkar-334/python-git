import os
import sys
import zlib
from hashlib import sha1


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
        content = open(sys.argv[3], "rb").read()
        size = len(content)
        content = f"blob {size}".encode() + b"\0" + content
        data = zlib.compress(content)
        hash = sha1(content).hexdigest()
        os.makedirs(f".git/objects/{hash[:2]}", exist_ok=True)
        with open(f".git/objects/{hash[:2]}/{hash[2:]}", "wb") as f:
            f.write(content)
        print(hash)
    else:
        raise RuntimeError(f"Unknown command #{command}")


if __name__ == "__main__":
    main()
