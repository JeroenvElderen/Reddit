"""
Flair ladder, flair templates, and location flair → Supabase field mapping.
"""

from app.utils.flair_text import _normalize_flair_key

# =========================
# Flair ladder + user flair templates 
# =========================
flair_ladder = [
    ("Cover Curious", 0),
    ("First Bare", 10),
    ("Skin Fresh", 50),
    ("Sun Chaser", 100),
    ("Breeze Walker", 250),
    ("Clothing Free", 500),
    ("Open Air", 1000),
    ("True Naturist", 2000),
    ("Bare Master", 5000),
    ("Naturist Legend", 10000),
]

flair_templates = {
    "Needs Growth": "75c23a86-7f6d-11f0-8745-f666d1d62ce4",
    "Cover Curious": "ae791af4-7d22-11f0-934a-2e3446070201",
    "First Bare": "bbf4d5d8-7d22-11f0-b485-d64b23d9d74f",
    "Skin Fresh": "c5be4a5e-7d22-11f0-b278-0298fe10eba2",
    "Sun Chaser": "d72ca790-7d22-11f0-a0de-a687510f7c1a",
    "Breeze Walker": "e35fc826-7d22-11f0-8742-d64b23d9d74f",
    "Clothing Free": "f01b2e02-7d22-11f0-bee0-7e43d54e1cf4",
    "Open Air": "7cfdbc2c-7dd7-11f0-9936-9e1c00b89022",
    "True Naturist": "8a5fbeb0-7dd7-11f0-9fa7-2e98a4cf4302",
    "Bare Master": "987da246-7dd7-11f0-ae7f-8206f7eb2e0a",
    "Naturist Legend": "a3f1f8fc-7dd7-11f0-b2c1-227301a06778",
    "Daily Prompt": "8b04873e-80d8-11f0-81d2-260f76f8fd83",
    "Quiet Observer": "a3d0f81c-81c6-11f0-a40f-028908714e28",
}

# =========================
# Location flair -> Supabase mapping
# =========================
FLAIR_TO_FIELD = {
    "Beach": "beach_posts_count",
    "Lake": "lake_posts_count",
    "River": "river_posts_count",
    "Hot Spring": "hotspring_posts_count",
    "Poolside": "pool_posts_count",
    "Forest": "forest_posts_count",
    "Mountain": "mountain_posts_count",
    "Meadow": "meadow_posts_count",
    "Desert": "desert_posts_count",
    "Cave": "cave_posts_count",
    "Tropical": "tropical_posts_count",
    "Nordic / Cold": "nordic_posts_count",
    "Island": "island_posts_count",
    "Urban": "urban_posts_count",
    "Countryside": "countryside_posts_count",
    "Festival": "festival_posts_count",
    "Resort / Club": "resort_posts_count",
    "Camping": "camping_posts_count",
    "Backyard / Home": "backyard_posts_count",
    "Sauna / Spa": "sauna_posts_count",
}

# =========================
# Normalized lookup
# =========================
FLAIR_TO_FIELD_NORM = { _normalize_flair_key(k): v for k, v in FLAIR_TO_FIELD.items() }
