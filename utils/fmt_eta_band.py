def _fmt_eta_band(low_sec: int, high_sec: int) -> str:
    def f(s):
        if s >= 3600:
            h = int(round(s / 3600.0))
            return f"~{h}h"
        m = max(1, int(round(s / 60.0)))
        return f"~{m}m"
    return f"{f(low_sec)}–{f(high_sec)}"
