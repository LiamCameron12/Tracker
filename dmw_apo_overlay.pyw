"""
DMW APO Phase Overlay
Compact always-on-top overlay for APO boss phases.
Click a phase to mark it active. Drag title to move.
"""

import tkinter as tk
import ctypes

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

C = {
    "bg":         "#08111c",
    "bg2":        "#0d1a28",
    "card":       "#111f30",
    "border":     "#1e3050",
    "text":       "#d8e4f8",
    "text_dim":   "#4a6080",
    "text_muted": "#1e2e3e",
    "gold":       "#f0c040",
    "done_bg":    "#0d2018",
    "done_fg":    "#2a5035",
    "purple":     "#a855f7",
    "blue":       "#3b82f6",
    "red":        "#f43f5e",
    "orange":     "#f97316",
    "green":      "#22c55e",
}

# (type, pct, note, color)
PHASES = [
    ("APO",    "100–90", "tank chk",                              C["blue"]),
    ("APO",    "89–80",  "big split  ·  omaewa",                  C["orange"]),
    ("MINION", "79",     "spawn  —  DPS chk  (use DPS skills)",   C["red"]),
    ("APO",    "75",     "safe point",                             C["green"]),
    ("APO",    "69–60",  "split/stack 30s  ·  safe zone  ·  big split", C["blue"]),
    ("MINION", "60",     "spawn  —  DO NOT HIT BEFORE TANK",      C["red"]),
    ("APO",    "55",     "omaewa",                                 C["orange"]),
    ("APO",    "50–40",  "avoid blue",                            C["blue"]),
    ("MINION", "",       "DPS chk  (use DPS skills)",              C["red"]),
    ("APO",    "35–20",  "split heal:",                            C["purple"]),
    ("  ",     "",       "nothing · nothing · emer · choco",       C["purple"]),
    ("  ",     "",       "hoh/nothing · nothing · chicken",        C["purple"]),
    ("MINION", "20",     "spawn  —  tank chk",                     C["red"]),
    ("APO",    "20–10",  "avoid blue",                             C["blue"]),
    ("APO",    "10–0",   "DPS 55s  —  ALL DPS",                   C["red"]),
]


class APOOverlay:

    def __init__(self, root):
        self.root = root
        self.cur  = -1
        self._dx  = self._dy = 0

        root.overrideredirect(True)
        root.attributes("-topmost", True)
        root.attributes("-alpha", 0.94)
        root.configure(bg=C["bg"])
        root.geometry("+900+40")

        self._build()
        self._refresh()

    def _build(self):
        # ── Title bar ─────────────────────────────────────────────────────────
        bar = tk.Frame(self.root, bg=C["bg2"], pady=6, padx=12)
        bar.pack(fill=tk.X)
        tk.Frame(self.root, bg=C["purple"], height=2).pack(fill=tk.X)

        title_lbl = tk.Label(bar, text="APO  —  PHASES",
                             font=("Segoe UI", 10, "bold"),
                             bg=C["bg2"], fg=C["purple"])
        title_lbl.pack(side=tk.LEFT)

        btn_x = tk.Label(bar, text=" × ", font=("Segoe UI", 11, "bold"),
                         bg=C["bg2"], fg=C["text_dim"], cursor="hand2")
        btn_x.pack(side=tk.RIGHT)
        btn_x.bind("<Button-1>", lambda e: self.root.destroy())

        btn_r = tk.Label(bar, text=" ↺ ", font=("Segoe UI", 10),
                         bg=C["bg2"], fg=C["text_dim"], cursor="hand2")
        btn_r.pack(side=tk.RIGHT)
        btn_r.bind("<Button-1>", self._reset)

        for w in (bar, title_lbl):
            w.bind("<ButtonPress-1>", self._drag_start)
            w.bind("<B1-Motion>",     self._drag_move)

        # ── Phase rows ────────────────────────────────────────────────────────
        pf = tk.Frame(self.root, bg=C["bg"], pady=6, padx=10)
        pf.pack(fill=tk.X)

        self._rows = []
        for i, (kind, pct, note, col) in enumerate(PHASES):
            is_minion = kind.strip() == "MINION"
            is_sub    = kind.strip() == ""

            row = tk.Frame(pf, bg=C["card"] if is_minion else C["bg"],
                           cursor="hand2" if not is_sub else "")
            row.pack(fill=tk.X, pady=1)
            row.bind("<Button-1>", lambda e, idx=i: self._click(idx))

            if not is_sub:
                badge = tk.Label(row, text=f" {kind.strip()} ",
                                 font=("Segoe UI", 7, "bold"),
                                 bg=col, fg="#ffffff", padx=3)
                badge.pack(side=tk.LEFT, padx=(0, 4))
                badge.bind("<Button-1>", lambda e, idx=i: self._click(idx))

                if pct:
                    pct_lbl = tk.Label(row, text=f"{pct}%",
                                       font=("Segoe UI", 7, "bold"),
                                       bg=C["card"] if is_minion else C["bg"],
                                       fg=C["text_dim"], width=7, anchor="w")
                    pct_lbl.pack(side=tk.LEFT)
                    pct_lbl.bind("<Button-1>", lambda e, idx=i: self._click(idx))

                note_lbl = tk.Label(row, text=note,
                                    font=("Segoe UI", 9, "bold" if is_minion else "normal"),
                                    bg=C["card"] if is_minion else C["bg"],
                                    fg=C["gold"] if is_minion else C["text"],
                                    anchor="w")
                note_lbl.pack(side=tk.LEFT, padx=(0 if pct else 6, 8))
                note_lbl.bind("<Button-1>", lambda e, idx=i: self._click(idx))
            else:
                # sub-line (heal order continuation)
                tk.Label(row, text="", width=2, bg=C["bg"]).pack(side=tk.LEFT)
                tk.Label(row, text="       ↳ ", font=("Segoe UI", 8),
                         bg=C["bg"], fg=col).pack(side=tk.LEFT)
                tk.Label(row, text=note, font=("Segoe UI", 8, "bold"),
                         bg=C["bg"], fg=col, anchor="w").pack(side=tk.LEFT)

            self._rows.append((row, kind.strip(), col, is_sub))

        tk.Label(pf, text="click phase to mark active  ·  ↺ reset",
                 font=("Segoe UI", 7),
                 bg=C["bg"], fg=C["text_muted"]).pack(anchor="w", pady=(4, 0))

        tk.Frame(self.root, bg=C["bg"], height=6).pack()

    # ── Logic ─────────────────────────────────────────────────────────────────

    def _click(self, idx):
        if self._rows[idx][3]:   # sub-line, skip
            return
        if self.cur == idx:
            # advance to next non-sub row
            nxt = idx + 1
            while nxt < len(self._rows) and self._rows[nxt][3]:
                nxt += 1
            self.cur = nxt if nxt < len(self._rows) else -1
        else:
            self.cur = idx
        self._refresh()

    def _reset(self, e=None):
        self.cur = -1
        self._refresh()

    def _refresh(self):
        for i, (row, kind, col, is_sub) in enumerate(self._rows):
            is_minion = kind == "MINION"
            base_bg   = C["card"] if is_minion else C["bg"]

            if is_sub:
                continue

            if i < self.cur:
                for w in row.winfo_children():
                    try:
                        w.config(bg=C["done_bg"],
                                 fg=C["done_fg"] if not isinstance(w, tk.Frame) else C["done_bg"])
                    except Exception:
                        pass
                row.config(bg=C["done_bg"])
            elif i == self.cur:
                for w in row.winfo_children():
                    try:
                        w.config(bg=col,
                                 fg="#ffffff" if not isinstance(w, tk.Frame) else col)
                    except Exception:
                        pass
                row.config(bg=col)
            else:
                for w in row.winfo_children():
                    try:
                        lbl_fg = C["gold"] if is_minion else C["text"]
                        if hasattr(w, 'cget') and w.cget("bg") == C["done_bg"]:
                            w.config(bg=base_bg, fg=lbl_fg)
                        else:
                            w.config(bg=base_bg)
                    except Exception:
                        pass
                row.config(bg=base_bg)

    # ── Drag ──────────────────────────────────────────────────────────────────

    def _drag_start(self, e):
        self._dx = e.x_root - self.root.winfo_x()
        self._dy = e.y_root - self.root.winfo_y()

    def _drag_move(self, e):
        self.root.geometry(f"+{e.x_root - self._dx}+{e.y_root - self._dy}")


def main():
    root = tk.Tk()
    APOOverlay(root)
    root.mainloop()


if __name__ == "__main__":
    main()
