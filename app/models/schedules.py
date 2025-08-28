# =========================
# Seasonal pack schedule (month/day)
# =========================
PACK_SCHEDULE = {
    "spring": {"start": (3, 1), "end": (5, 31)},      # Mar 1 – May 31
    "summer": {"start": (6, 1), "end": (8, 31)},      # Jun 1 – Aug 31
    "autumn": {"start": (9, 1), "end": (11, 30)},     # Sep 1 – Nov 30
    "winter": {"start": (12, 1), "end": (2, 28)},     # Dec 1 – Feb 28 (ignore leap day)
    "halloween": {"start": (10, 25), "end": (11, 1)}, # late Oct → Nov 1
    "christmas": {"start": (12, 20), "end": (12, 27)},
    "newyear": {"start": (12, 30), "end": (1, 2)},
    "easter": {"start": (3, 25), "end": (4, 5)},      # varies yearly, approx
    "midsummer": {"start": (6, 20), "end": (6, 25)},
    "pride": {"start": (6, 1), "end": (6, 30)},
    "stpatricks": {"start": (3, 15), "end": (3, 18)},
    "valentines": {"start": (2, 13), "end": (2, 15)},
    "earthday": {"start": (4, 22), "end": (4, 23)},
}

