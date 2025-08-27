#!/usr/bin/env python3
"""
Reorganize split_package/ into existing REDDITBOT/ structure.

Usage:
    # Preview only
    python3 reorg_split_package.py --src ./split_package --root ./REDDITBOT --dry-run

    # Move files (overwrites existing stubs)
    python3 reorg_split_package.py --src ./split_package --root ./REDDITBOT --move
"""

import argparse, shutil
from pathlib import Path
from typing import List, Tuple

RULES = {
    "clients_exact": ["reddit_client", "discord_bot", "supabase_client"],
    "tasks_prefixes": [
        "cmd_", "daily_", "weekly_", "apply_", "award_", "check_", "fetch_", "post_", "parse_",
        "generate_", "record_", "prune_", "restore_", "backfill_", "delete_", "compute_", "calc_",
        "save_", "decay_", "pack_", "cah_", "reddit_polling", "reddit_dm_polling",
        "sla_loop", "feedback_loop", "host", "handle_new_item", "upvote_reward_loop",
    ],
    "tasks_suffixes": ["_loop"],
    "utils_prefixes": [
        "get_", "is_", "has_", "fmt_", "normalize_", "current_tz", "likely_",
        "text_flair_without_emoji", "submission_has_any_image", "image_flag_label",
        "increment_location_counter", "avg_", "item_text", "parse_window",
        "parse_keyword_map", "get_flair_for_karma", "get_user_stats",
        "get_permalink_from_embed", "get_last_approved_item",
        "get_weekly_achievements", "globals"
    ]
}

def classify(base: str) -> str:
    if base in RULES["clients_exact"]:
        return "clients"
    for suf in RULES["tasks_suffixes"]:
        if base.endswith(suf):
            return "tasks"
    for pre in RULES["tasks_prefixes"]:
        if base.startswith(pre):
            return "tasks"
    for pre in RULES["utils_prefixes"]:
        if base.startswith(pre):
            return "utils"
    return "tasks"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="Path to flat split_package")
    ap.add_argument("--root", required=True, help="Existing package root (e.g., ./REDDITBOT)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--move", action="store_true", help="Move instead of copy")
    args = ap.parse_args()

    src = Path(args.src)
    root = Path(args.root)
    if not src.exists() or not root.exists():
        print("ERROR: --src or --root not found")
        return

    subdirs = {k: root / k for k in ["clients", "tasks", "utils"]}
    plan: List[Tuple[Path, Path, str]] = []

    for path in src.glob("*.py"):
        if path.name == "__init__.py":
            continue
        base = path.stem
        group = classify(base)
        target_name = "config.py" if base == "globals" else path.name
        dst = subdirs[group] / target_name
        plan.append((path, dst, group))

    # Report
    counts = {"clients": 0, "tasks": 0, "utils": 0}
    print(f"Plan for {len(plan)} files:")
    for s, d, g in plan:
        counts[g] += 1
        print(f"  {s.name:30s} -> {g}/{d.name}")
    print("Totals:", counts)

    if args.dry_run:
        return

    for d in subdirs.values():
        d.mkdir(parents=True, exist_ok=True)

    for s, d, g in plan:
        if d.exists():
            d.unlink()  # overwrite
        if args.move:
            shutil.move(str(s), str(d))
        else:
            shutil.copy2(str(s), str(d))

    for d in [root] + list(subdirs.values()):
        init = d / "__init__.py"
        if not init.exists():
            init.write_text('"""Package init (generated)"""\n', encoding="utf-8")

    report = root / "_mapping.txt"
    report.write_text("\n".join([f"{s.name} -> {g}/{d.name}" for s, d, g in plan]), encoding="utf-8")
    print(f"\nWrote mapping to {report}")
    print("Done.")

if __name__ == "__main__":
    main()
