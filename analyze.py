import os
import ast
from pathlib import Path

ROOT = Path("/workspaces/daner")

def get_py_files(root: Path):
    """Return all .py files in root and 'pages/' folder."""
    py_files = []

    # main directory
    for f in root.iterdir():
        if f.suffix == ".py":
            py_files.append(f)

    # pages directory
    pages_dir = root / "pages"
    if pages_dir.exists():
        for f in pages_dir.iterdir():
            if f.suffix == ".py":
                py_files.append(f)

    return py_files


def extract_functions(file_path: Path):
    """Extract functions and docstrings from a Python file."""
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()

    tree = ast.parse(content)

    functions = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            name = node.name
            doc = ast.get_docstring(node)
            functions.append((name, doc))

    return functions


def print_report():
    print("\n============================")
    print("  PROJECT FUNCTION SUMMARY")
    print("============================\n")

    py_files = get_py_files(ROOT)

    for file_path in py_files:
        print(f"\n📄 FILE: {file_path.name}")
        print("-" * (7 + len(file_path.name)))

        funcs = extract_functions(file_path)

        if not funcs:
            print("  No functions found.")
            continue

        for name, doc in funcs:
            print(f"🔹 Function: {name}")
            if doc:
                print(f"    └─ Docstring: {doc.strip()}")
            else:
                print("    └─ Docstring: (none)")
        print()

    print("Analysis complete.\n")


if __name__ == "__main__":
    print_report()
