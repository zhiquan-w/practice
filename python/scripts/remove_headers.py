import argparse
import itertools
import pathlib


def cleanup_py(root, dry_run=False):
    count = 0
    for f in pathlib.Path(root).glob("**/*.py"):
        print(f)
        lines = f.read_text().splitlines()
        start = None
        middle = None
        end = None
        for i, l in enumerate(lines):
            if l == '"""':
                if start is None:
                    start = i
                elif middle is not None:
                    end = i
                    if end - middle < 10:
                        break
            if "This source file is the property of" in l:
                middle = i
                print(start, middle)
        if middle is not None and end is not None:
            if lines[end + 1] == "":
                end += 1
            if not dry_run:
                new_lines = lines[:start] + lines[end + 1 :]
                f.write_text("\n".join(new_lines) + "\n")
            count += 1
    return count


def cleanup_cpp(root, dry_run=False):
    c_files = [
        pathlib.Path(".").glob("**/*.h"),
        pathlib.Path(".").glob("**/*.hpp"),
        pathlib.Path(".").glob("**/*.c"),
        pathlib.Path(".").glob("**/*.cpp"),
    ]

    count = 0
    for f in itertools.chain(*c_files):
        print(f)
        lines = f.read_text().splitlines()
        start = None
        middle = None
        end = None
        for i, l in enumerate(lines):
            if "********************************" in l:
                if start is None:
                    start = i
                elif middle is not None:
                    end = i
                    if end - middle < 10:
                        break
            if "This source file is the property of" in l:
                middle = i
                print(start, middle)
        if middle is not None and end is not None:
            if lines[end + 1] == "":
                end += 1
            if not dry_run:
                new_lines = lines[:start] + lines[end + 1 :]
                f.write_text("\n".join(new_lines) + "\n")
            count += 1
    return count


def main():
    parser = argparse.ArgumentParser(description="Check and remove headers")
    parser.add_argument(
        "root",
        nargs="*",
        help="Directory to walk",
    )
    parser.add_argument("-d", "--dry_run", action="store_true", default=False, required=False)

    args = parser.parse_args()
    count = 0
    for root in args.root:
        count += cleanup_py(root, dry_run=args.dry_run)
        count += cleanup_cpp(root, dry_run=args.dry_run)

    if count > 0 and args.dry_run:
        import sys

        sys.exit(1)


if __name__ == "__main__":
    main()
