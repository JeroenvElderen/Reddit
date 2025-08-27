#!/usr/bin/env python3
"""
split_monolith.py — split a large Python file into multiple modules.

Usage:
    python split_monolith.py main.py --out ./split_package --dry-run
    python split_monolith.py main.py --out ./split_package
"""

import ast, re, sys, argparse
from pathlib import Path
from dataclasses import dataclass, field
from typing import List

@dataclass
class Piece:
    name: str
    code: str
    kind: str  # "class" | "function" | "other"
    lineno: int

@dataclass
class ModulePlan:
    filename: str
    pieces: List[Piece] = field(default_factory=list)

def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")

def write_text(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")

def ast_top_level_pieces(src: str) -> List[Piece]:
    pieces: List[Piece] = []
    tree = ast.parse(src)
    for node in tree.body:
        segment = ast.get_source_segment(src, node) or ""
        if isinstance(node, ast.ClassDef):
            pieces.append(Piece(node.name, segment, "class", node.lineno))
        elif isinstance(node, ast.FunctionDef):
            if not (node.name.startswith("__") and node.name.endswith("__")):
                pieces.append(Piece(node.name, segment, "function", node.lineno))
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            continue  # imports handled separately
        else:
            if segment.strip():
                pieces.append(Piece("globals", segment, "other", node.lineno))
    return pieces

def safe_mod_name(name: str) -> str:
    return re.sub(r"[^0-9A-Za-z_]+", "_", name).strip("_").lower() or "module"

def plan_modules(pieces: List[Piece]) -> List[ModulePlan]:
    plans = {}
    for p in pieces:
        fname = f"{safe_mod_name(p.name)}.py"
        plans.setdefault(fname, ModulePlan(fname)).pieces.append(p)
    return list(plans.values())

def generate_init(plans: List[ModulePlan]) -> str:
    lines = ['"""Auto-generated init"""', "__all__ = []", ""]
    for plan in plans:
        mod = plan.filename[:-3]
        exported = [p.name for p in plan.pieces if p.kind in ("class","function")]
        if exported:
            lines.append(f"from .{mod} import {', '.join(exported)}")
            lines.append(f"__all__ += {exported!r}")
    return "\n".join(lines) + "\n"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source", help="Path to big .py file")
    ap.add_argument("--out", required=True, help="Output directory")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    src_path = Path(args.source)
    src = read_text(src_path)
    pieces = ast_top_level_pieces(src)
    plans = plan_modules(pieces)

    out_dir = Path(args.out)
    module_texts = {}
    for plan in plans:
        body = "\n\n".join(p.code for p in plan.pieces) + "\n"
        module_texts[plan.filename] = body

    init_text = generate_init(plans)

    if args.dry_run:
        print(f"Would create {out_dir}/")
        for fname, text in module_texts.items():
            print(f"  - {fname} ({text.count(chr(10))} lines)")
        print("  - __init__.py")
        return

    out_dir.mkdir(parents=True, exist_ok=True)
    for fname, text in module_texts.items():
        write_text(out_dir / fname, text)
    write_text(out_dir / "__init__.py", init_text)

    print(f"Created package at {out_dir}")

if __name__ == "__main__":
    main()
