def format_weekly_achievements(rows):
    if not rows:
        return None

    locations, pillars, meta, rare = [], [], [], []

    for row in rows:
        u = row["username"]
        badge = row["badge"]

        # Format line
        line = f"• u/{u} → {badge}"

        # Categorize based on badge text
        if any(loc in badge for loc in [
            "Beach","Forest","Lake","Mountain","Meadow","River",
            "Pool","Backyard","Camping","Sauna","Resort","Island",
            "Countryside","Cave","Tropical","Nordic","Festival"
        ]):
            locations.append(line)
        elif "Lv." in badge and not any(meta_kw in badge for meta_kw in [
            "Seed","Explorer","Adventurer","Voice","Friend","Root",
            "Chaser","Spirit","Child","Legend"
        ]):
            pillars.append(line)
        elif any(meta_kw in badge for meta_kw in [
            "Seed","Explorer","Adventurer","Voice","Friend","Root",
            "Chaser","Spirit","Child","Legend"
        ]):
            meta.append(line)
        else:
            rare.append(line)

    parts = []
    # Big Header
    parts.append("🌟🌿🌞🌿🌟\n✨ Weekly Naturist Achievements ✨\n🌟🌿🌞🌿🌟\n")

    if locations:
        parts.append("🏖️ **Location Achievements**\n" + "\n".join(locations) + "\n\n🌿🌿🌿🌿🌿")
    if pillars:
        parts.append("🧘 **Pillar Progress**\n" + "\n".join(pillars) + "\n\n🌿🌿🌿🌿🌿")
    if meta:
        parts.append("👑 **Meta Ladder**\n" + "\n".join(meta) + "\n\n🌿🌿🌿🌿🌿")
    if rare:
        parts.append("🎉 **Special Unlocks**\n" + "\n".join(rare) + "\n\n🌿🌿🌿🌿🌿")

    parts.append("🌞💚 Keep shining, sharing, and celebrating naturism! ✨🌿")

    return "\n\n".join(parts)
