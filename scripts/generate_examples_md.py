#!/usr/bin/env python3
import os
import ast
import textwrap
from typing import List

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
EX_DIR = os.path.join(ROOT, "examples")
OUT = os.path.join(ROOT, "EXAMPLES.md")


def read_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def title_from_docstring(doc: str, fallback: str) -> str:
    if doc:
        first = doc.strip().splitlines()[0].strip()
        if first:
            return first
    # Fallback: transform filename like example5_project_plan_basic -> "Example 5 Project Plan Basic"
    name = os.path.splitext(os.path.basename(fallback))[0]
    name = name.replace("_", " ")
    return name.title()


def extract_run_example_code(src: str) -> str:
    tree = ast.parse(src)
    run_fn = None
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "run_example":
            run_fn = node
            break
    if not run_fn:
        return ""
    if not run_fn.body:
        return ""
    start = run_fn.body[0].lineno
    end = getattr(run_fn.body[-1], "end_lineno", run_fn.body[-1].lineno)
    lines = src.splitlines()
    segment = "\n".join(lines[start - 1 : end])
    return textwrap.dedent(segment).rstrip() + "\n"


def extract_plugin_code(src: str) -> str:
    lines = src.splitlines()
    tree = ast.parse(src)
    # Collect top-level imports
    import_snippets: List[str] = []
    class_snippets: List[str] = []
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            s = "\n".join(lines[node.lineno - 1 : getattr(node, "end_lineno", node.lineno)])
            import_snippets.append(s)
        elif isinstance(node, ast.ClassDef):
            # Heuristic: include all classes as plugin code
            s = "\n".join(lines[node.lineno - 1 : getattr(node, "end_lineno", node.lineno)])
            class_snippets.append(s)
    if not class_snippets:
        return ""
    # Dedent combined class code lightly
    plugin_code = "\n\n".join(class_snippets).rstrip() + "\n"
    import_code = "\n".join(import_snippets).strip()
    combined = []
    if import_code:
        combined.append(import_code)
        combined.append("")
    combined.append(plugin_code)
    return "\n".join(combined)


def build_section(code_path: str) -> str:
    rel_code = os.path.relpath(code_path, ROOT)
    base = os.path.basename(code_path)
    test_path = os.path.join(EX_DIR, "tests", f"test_{base}")
    rel_test = os.path.relpath(test_path, ROOT)

    src = read_file(code_path)
    mod = ast.parse(src)
    doc = ast.get_docstring(mod) or ""
    title = title_from_docstring(doc, base)
    description = doc.strip() if doc else ""

    plugin_code = extract_plugin_code(src)
    usage_code = extract_run_example_code(src)

    section: List[str] = []
    section.append(f"## {title}")
    if description:
        section.append("")
        section.append(description)
    section.append("")

    if plugin_code:
        section.append("Plugin code")
        section.append("")
        section.append("```python")
        section.append(plugin_code.rstrip())
        section.append("```")
        section.append("")

    if usage_code:
        section.append("Usage (run_example)")
        section.append("")
        section.append("```python")
        section.append(usage_code.rstrip())
        section.append("```")
        section.append("")

    section.append(f"- Code: `{rel_code}`")
    section.append(f"- Test: `{rel_test}`")
    section.append(f"- Run: `pytest -q {rel_test}`")
    section.append("")
    return "\n".join(section)


def main() -> None:
    files = [
        os.path.join(EX_DIR, f)
        for f in os.listdir(EX_DIR)
        if f.startswith("example") and f.endswith(".py")
    ]
    files.sort()
    sections: List[str] = ["# Examples", ""]
    for path in files:
        sections.append(build_section(path))
    content = "\n".join(sections).rstrip() + "\n"
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Wrote {OUT} with {len(files)} examples.")

if __name__ == "__main__":
    main()
