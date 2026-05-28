"""
DMW PIED Mech Overlay
Compact always-on-top overlay for PIED boss mechanics.
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
    "red":        "#f43f5e",
    "blue":       "#3b82f6",
    "orange":     "#e07030",
    "purple":     "#a855f7",
}

# (type, pct, note, color, is_sub)
PHASES = [
    ("HEAL",   "",      "choco  →  hoh  →  shield  →  hoh  →  choco  →  chicken", C["red"],    False),
    ("NOTE",   "",      "dayxne: choco · hoh1 · shield · hoh2 · chicken/choco",    C["text_dim"],False),

    ("SEP",    "",      "",                                                          C["border"],  False),

    ("90%",    "",      "Giant split each 30s  ·  65% omea  ·  80% lady",           C["orange"],  False),
    ("",       "",      "LADY: highest DPS only — attacker gets debuff + gone",      C["orange"],  True),

    ("74%",    "",      "Stack each 30s  ·  70% Blue AOE",                          C["blue"],    False),
    ("",       "",      "Blue AOE PREVENTS HEAL ITEMS",                              C["blue"],    True),

    ("60%",    "",      "Smol evilmon chase player  ~1m",                            C["purple"],  False),
    ("",       "",      "Aggros last to enter dg  /  if you swap digi",             C["purple"],  True),

    ("55%",    "",      "Many evilmon  —  must Powerful AOE",                        C["red"],     False),
    ("",       "",      "Use Emergency or Pray skill  (omaewa)",                    C["red"],     True),

    ("SEP",    "",      "",                                                          C["border"],  False),

    ("MINION", "",      "Pied spawns at 20%",                                        C["red"],     False),
    ("APO",    "20–10", "Avoid blue orbs",                                           C["purple"],  False),
    ("APO",    "10–0",  "DPS 55s  —  NO TAMER",                                    C["red"],     False),
]


class PiedMechOverlay:

    def __init__(self, root):
        self.root = root
        self.cur  = -1
        self._dx  = self._dy = 0

        root.overrideredirect(True)
        root.attributes("-topmost", True)
        root.attributes("-alpha", 0.94)
        root.configure(bg=C["bg"])
        root.geometry("+60+60")

        self._build()
        self._refresh()

    def _build(self):
        col = C["red"]

        # ── Title bar ─────────────────────────────────────────────────────────
        bar = tk.Frame(self.root, bg=C["bg2"], pady=6, padx=12)
        bar.pack(fill=tk.X)
        tk.Frame(self.root, bg=col, height=2).pack(fill=tk.X)

        title_lbl = tk.Label(bar, text="PIED  —  MECH",
                             font=("Segoe UI", 10, "bold"),
                             bg=C["bg2"], fg=col)
        title_lbl.pack(side=tk.LEFT)

        src_lbl = tk.Label(bar, text="  DomainLordz / Rzy",
                           font=("Segoe UI", 7),
                           bg=C["bg2"], fg=C["text_dim"])
        src_lbl.pack(side=tk.LEFT)

        btn_x = tk.Label(bar, text=" × ", font=("Segoe UI", 11, "bold"),
                         bg=C["bg2"], fg=C["text_dim"], cursor="hand2")
        btn_x.pack(side=tk.RIGHT)
        btn_x.bind("<Button-1>", lambda e: self.root.destroy())

        btn_r = tk.Label(bar, text=" ↺ ", font=("Segoe UI", 10),
                         bg=C["bg2"], fg=C["text_dim"], cursor="hand2")
        btn_r.pack(side=tk.RIGHT)
        btn_r.bind("<Button-1>", self._reset)

        for w in (bar, title_lbl, src_lbl):
            w.bind("<ButtonPress-1>", self._drag_start)
            w.bind("<B1-Motion>",     self._drag_move)

        # ── Phase rows ────────────────────────────────────────────────────────
        pf = tk.Frame(self.root, bg=C["bg"], pady=6, padx=10)
        pf.pack(fill=tk.X)

        self._rows = []

        for i, (kind, pct, note, pcol, is_sub) in enumerate(PHASES):

            # separator
            if kind == "SEP":
                tk.Frame(pf, bg=C["border"], height=1).pack(fill=tk.X, pady=4)
                self._rows.append((None, kind, pcol, True))
                continue

            is_minion = kind == "MINION"
            is_heal   = kind == "HEAL"
            is_note   = kind == "NOTE"
            is_apo    = kind == "APO"
            row_bg    = C["card"] if is_minion else C["bg2"] if is_heal else C["bg"]

            row = tk.Frame(pf, bg=row_bg,
                           cursor="hand2" if not is_sub and not is_note else "")
            row.pack(fill=tk.X, pady=1)

            if not is_sub:
                row.bind("<Button-1>", lambda e, idx=i: self._click(idx))

            if is_heal:
                # heal order banner
                tk.Frame(pf, bg=C["border"], height=1).pack(fill=tk.X, pady=(0, 4))
                inner = tk.Frame(row, bg=C["bg2"], padx=10, pady=6)
                inner.pack(fill=tk.X)
                tk.Label(inner, text="HEAL ORDER",
                         font=("Segoe UI", 7, "bold"),
                         bg=C["bg2"], fg=C["text_dim"]).pack(anchor="w")
                tk.Label(inner, text=note,
                         font=("Segoe UI", 10, "bold"),
                         bg=C["bg2"], fg=col).pack(anchor="w", pady=(2, 0))
                self._rows.append((row, kind, pcol, True))
                continue

            if is_note:
                inner = tk.Frame(row, bg=C["bg2"], padx=10, pady=3)
                inner.pack(fill=tk.X)
                tk.Label(inner, text=note,
                         font=("Segoe UI", 7),
                         bg=C["bg2"], fg=C["text_dim"]).pack(anchor="w")
                tk.Frame(pf, bg=C["border"], height=1).pack(fill=tk.X, pady=(4, 2))
                self._rows.append((row, kind, pcol, True))
                continue

            if is_sub:
                sr = tk.Frame(row, bg=C["bg"], padx=6, pady=1)
                sr.pack(fill=tk.X)
                tk.Label(sr, text="   ↳", font=("Segoe UI", 8),
                         bg=C["bg"], fg=pcol).pack(side=tk.LEFT)
                tk.Label(sr, text=f"  {note}", font=("Segoe UI", 8),
                         bg=C["bg"], fg=C["text_dim"],
                         wraplength=380, justify="left").pack(side=tk.LEFT)
                self._rows.append((row, kind, pcol, True))
                continue

            # normal phase row
            inner = tk.Frame(row, bg=row_bg, padx=8, pady=5)
            inner.pack(fill=tk.X)
            inner.bind("<Button-1>", lambda e, idx=i: self._click(idx))

            badge = tk.Label(inner, text=f" {kind} ",
                             font=("Segoe UI", 7, "bold"),
                             bg=pcol, fg="#ffffff", padx=4)
            badge.pack(side=tk.LEFT)
            badge.bind("<Button-1>", lambda e, idx=i: self._click(idx))

            if pct:
                pl = tk.Label(inner, text=f"  {pct}%",
                              font=("Segoe UI", 7, "bold"),
                              bg=row_bg, fg=C["text_dim"])
                pl.pack(side=tk.LEFT)
                pl.bind("<Button-1>", lambda e, idx=i: self._click(idx))

            nl = tk.Label(inner, text=f"  {note}",
                          font=("Segoe UI", 9, "bold" if is_minion else "normal"),
                          bg=row_bg, fg=C["gold"] if is_minion else C["text"],
                          wraplength=360, justify="left")
            nl.pack(side=tk.LEFT)
            nl.bind("<Button-1>", lambda e, idx=i: self._click(idx))

            self._rows.append((row, kind, pcol, False))

        tk.Label(pf, text="click phase to mark active  ·  ↺ reset",
                 font=("Segoe UI", 7),
                 bg=C["bg"], fg=C["text_muted"]).pack(anchor="w", pady=(6, 0))

        tk.Frame(self.root, bg=C["bg"], height=6).pack()

    # ── Logic ─────────────────────────────────────────────────────────────────

    def _click(self, idx):
        if self._rows[idx][3]:
            return
        if self.cur == idx:
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
        for i, (row, kind, col, is_skip) in enumerate(self._rows):
            if is_skip or row is None:
                continue

            is_minion = kind == "MINION"
            row_bg    = C["card"] if is_minion else C["bg"]

            def recolor(w, bg, fg):
                try:
                    w.config(bg=bg)
                except Exception:
                    pass
                for child in w.winfo_children():
                    try:
                        child.config(bg=bg)
                        if not isinstance(child, tk.Frame):
                            child.config(fg=fg)
                    except Exception:
                        pass
                    for grandchild in child.winfo_children():
                        try:
                            grandchild.config(bg=bg)
                            if not isinstance(grandchild, tk.Frame):
                                grandchild.config(fg=fg)
                        except Exception:
                            pass

            if i < self.cur:
                recolor(row, C["done_bg"], C["done_fg"])
            elif i == self.cur:
                recolor(row, col, "#ffffff")
            else:
                recolor(row, row_bg, C["gold"] if is_minion else C["text"])

    # ── Drag ──────────────────────────────────────────────────────────────────

    def _drag_start(self, e):
        self._dx = e.x_root - self.root.winfo_x()
        self._dy = e.y_root - self.root.winfo_y()

    def _drag_move(self, e):
        self.root.geometry(f"+{e.x_root - self._dx}+{e.y_root - self._dy}")


def main():
    root = tk.Tk()
    PiedMechOverlay(root)
    root.mainloop()


if __name__ == "__main__":
    main()
