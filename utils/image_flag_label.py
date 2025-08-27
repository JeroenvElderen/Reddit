def image_flag_label(sub) -> str:
    if not hasattr(sub, "title"):
        return "N/A"
    if is_native_reddit_image(sub):
        return "Native"
    if submission_has_any_image(sub):
        return "External"
    return "No"
