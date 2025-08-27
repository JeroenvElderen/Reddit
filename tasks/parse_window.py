def _parse_window(s: str):
    a, b = s.split("-")
    h1, m1 = map(int, a.split(":"))
    h2, m2 = map(int, b.split(":"))
    return dtime(h1, m1), dtime(h2, m2)
