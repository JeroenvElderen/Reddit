def get_flair_for_karma(karma: int) -> str:
    if karma < 0:
        return "Needs Growth"   # 👈 use your special flair
    unlocked = "Cover Curious"
    for flair, threshold in flair_ladder:
        if karma >= threshold:
            unlocked = flair
        else:
            break
    return unlocked
