def apply_approval_points_and_flair(item, total_delta: int):
    old_k2, new_k, flair = apply_karma_and_flair(item.author, total_delta, allow_negative=False)
    return old_k2, new_k, flair
