"""
DMW Heal Order Overlay
Always-on-top overlay showing heal sequence + boss notes.
Click a step to mark it active, click again to advance.
Drag title bar to move. X to close.
"""

import tkinter as tk
import ctypes, subprocess, sys, os

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

# ── Data ──────────────────────────────────────────────────────────────────────

BOSSES = {
    "PIED": {
        "title":  "PIED  —  HEAL ORDER",
        "source": "LordXX + dayxne",
        "color":  "#f43f5e",
        "steps":  ["choco", "hoh", "shield", "hoh", "choco", "chicken"],
        "notes": [
            ("dayxne alt:", "choco → hoh1 → shield → hoh2 → chicken/choco"),
            ("",            "(if HP low: do both choco)"),
            ("55% omaewa:", "Use Emergency or Pray skill"),
        ],
        "phases": [
            ("MINION", "Pied spawns at 20%",               "#f43f5e"),
            ("APO",    "20→10%   avoid blue orbs",          "#a855f7"),
            ("APO",    "10→0%    DPS check 55s  (NO TAMER)", "#f04060"),
        ],
        "mechs": [
            {
                "pct":   "90%",
                "color": "#e07030",
                "main":  "Giant split each 30s  |  65% omea  |  80% lady",
                "subs":  ["LADY: highest DPS only attacks — attacker gets debuff and will be gone, others remain"],
            },
            {
                "pct":   "74%",
                "color": "#3b82f6",
                "main":  "Stack each 30s  |  70% Blue AOE circle",
                "subs":  ["Blue AOE PREVENTS HEAL ITEMS — do not use heals inside"],
            },
            {
                "pct":   "60%",
                "color": "#a855f7",
                "main":  "Smol evilmon chase player for ~1m",
                "subs":  ["Aggros onto last person to enter dungeon",
                          "Also aggros if you swap your digi"],
            },
            {
                "pct":   "55%",
                "color": "#f43f5e",
                "main":  "Many evilmon spawn",
                "subs":  ["Must use Powerful AOE to clear"],
            },
        ],
    },
}

STEP_ICONS = {
    "choco":   "🍫",
    "hoh":     "🌿",
    "shield":  "🛡",
    "chicken": "🍗",
}

C = {
    "bg":         "#08111c",
    "bg2":        "#0d1a28",
    "card":       "#111f30",
    "card2":      "#0f1c2e",
    "border":     "#1e3050",
    "text":       "#d8e4f8",
    "text_dim":   "#4a6080",
    "text_muted": "#1e2e3e",
    "gold":       "#f0c040",
    "done_bg":    "#0d2018",
    "done_fg":    "#2a5035",
}


# ─────────────────────────────────────────────────────────────────────────────
class HealOverlay:

    def __init__(self, root, boss_key="PIED"):
        self.root  = root
        self.data  = BOSSES[boss_key]
        self.steps = self.data["steps"]
        self.cur   = -1
        self._dx   = self._dy = 0

        root.overrideredirect(True)
        root.attributes("-topmost", True)
        root.attributes("-alpha", 0.94)
        root.configure(bg=C["bg"])
        root.geometry("+60+60")

        self._build()
        self._refresh()

    def _build(self):
        col = self.data["color"]

        # ── Title / drag bar ──────────────────────────────────────────────────
        bar = tk.Frame(self.root, bg=C["bg2"], pady=6, padx=12)
        bar.pack(fill=tk.X)
        tk.Frame(self.root, bg=col, height=2).pack(fill=tk.X)

        title_lbl = tk.Label(bar, text=self.data["title"],
                             font=("Segoe UI", 10, "bold"),
                             bg=C["bg2"], fg=col)
        title_lbl.pack(side=tk.LEFT)

        src_lbl = tk.Label(bar, text=f"  {self.data['source']}",
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

        btn_m = tk.Label(bar, text=" 📋 Mech ", font=("Segoe UI", 8, "bold"),
                         bg=col, fg="#ffffff", cursor="hand2", padx=2)
        btn_m.pack(side=tk.RIGHT, padx=(0, 6))
        btn_m.bind("<Button-1>", lambda e: self._open_mech())

        btn_s = tk.Label(bar, text=" 🛒 Store ", font=("Segoe UI", 8, "bold"),
                         bg=C["border"], fg=C["text"], cursor="hand2", padx=2)
        btn_s.pack(side=tk.RIGHT, padx=(0, 4))
        btn_s.bind("<Button-1>", lambda e: self._open_store())

        for w in (bar, title_lbl, src_lbl):
            w.bind("<ButtonPress-1>", self._drag_start)
            w.bind("<B1-Motion>",     self._drag_move)

        # ── Steps ─────────────────────────────────────────────────────────────
        sf = tk.Frame(self.root, bg=C["bg"], pady=10, padx=12)
        sf.pack(fill=tk.X)
        tk.Label(sf, text="HEAL  ORDER",
                 font=("Segoe UI", 7, "bold"),
                 bg=C["bg"], fg=C["text_dim"]).pack(anchor="w", pady=(0, 6))

        row = tk.Frame(sf, bg=C["bg"])
        row.pack(anchor="w")
        self._btns = []

        for i, step in enumerate(self.steps):
            if i > 0:
                tk.Label(row, text="→", font=("Segoe UI", 11),
                         bg=C["bg"], fg=C["text_muted"]).pack(side=tk.LEFT, padx=2)
            icon = STEP_ICONS.get(step.lower(), "•")
            btn = tk.Label(row, text=f"{icon} {step}",
                           font=("Segoe UI", 11, "bold"),
                           bg=C["card"], fg=C["text"],
                           padx=10, pady=7, cursor="hand2")
            btn.pack(side=tk.LEFT)
            btn.bind("<Button-1>", lambda e, idx=i: self._click(idx))
            self._btns.append(btn)

        tk.Label(sf, text="click step to activate  ·  ↺ reset",
                 font=("Segoe UI", 7),
                 bg=C["bg"], fg=C["text_muted"]).pack(anchor="w", pady=(6, 0))

        # ── Notes ─────────────────────────────────────────────────────────────
        tk.Frame(self.root, bg=C["border"], height=1).pack(fill=tk.X)
        nf = tk.Frame(self.root, bg=C["bg2"], pady=8, padx=12)
        nf.pack(fill=tk.X)
        tk.Label(nf, text="NOTES", font=("Segoe UI", 7, "bold"),
                 bg=C["bg2"], fg=C["text_dim"]).pack(anchor="w", pady=(0, 4))

        for label, value in self.data["notes"]:
            r = tk.Frame(nf, bg=C["bg2"])
            r.pack(anchor="w", pady=1)
            tk.Label(r, text=label, font=("Segoe UI", 8, "bold"),
                     bg=C["bg2"], fg=C["gold"], width=10, anchor="w").pack(side=tk.LEFT)
            tk.Label(r, text=value, font=("Segoe UI", 8),
                     bg=C["bg2"], fg=C["text"]).pack(side=tk.LEFT)

        # ── Phases ────────────────────────────────────────────────────────────
        tk.Frame(self.root, bg=C["border"], height=1).pack(fill=tk.X)
        pf = tk.Frame(self.root, bg=C["bg"], pady=8, padx=12)
        pf.pack(fill=tk.X)
        tk.Label(pf, text="PHASES", font=("Segoe UI", 7, "bold"),
                 bg=C["bg"], fg=C["text_dim"]).pack(anchor="w", pady=(0, 4))

        for tag, text, pcol in self.data["phases"]:
            r = tk.Frame(pf, bg=C["bg"])
            r.pack(anchor="w", pady=2)
            tk.Label(r, text=f" {tag} ", font=("Segoe UI", 7, "bold"),
                     bg=pcol, fg="#ffffff", padx=4).pack(side=tk.LEFT)
            tk.Label(r, text=f"  {text}", font=("Segoe UI", 8),
                     bg=C["bg"], fg=C["text"]).pack(side=tk.LEFT)

        tk.Frame(self.root, bg=C["bg"], height=8).pack()

    # ── Step logic ────────────────────────────────────────────────────────────

    def _click(self, idx):
        if self.cur == idx:
            self.cur = idx + 1 if idx + 1 < len(self.steps) else -1
        else:
            self.cur = idx
        self._refresh()

    def _reset(self, e=None):
        self.cur = -1
        self._refresh()

    def _refresh(self):
        col = self.data["color"]
        for i, btn in enumerate(self._btns):
            if i < self.cur:
                btn.config(bg=C["done_bg"], fg=C["done_fg"])
            elif i == self.cur:
                btn.config(bg=col, fg="#ffffff")
            else:
                btn.config(bg=C["card"], fg=C["text"])

    # ── Drag ──────────────────────────────────────────────────────────────────

    def _drag_start(self, e):
        self._dx = e.x_root - self.root.winfo_x()
        self._dy = e.y_root - self.root.winfo_y()

    def _drag_move(self, e):
        self.root.geometry(f"+{e.x_root - self._dx}+{e.y_root - self._dy}")

    def _open_mech(self):
        win = tk.Toplevel(self.root)
        win.attributes("-topmost", True)
        MechApp(win, self.data)

    def _open_store(self):
        helper = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "dmw_storeitem_helper.pyw")
        if os.path.exists(helper):
            subprocess.Popen([sys.executable, helper])


# ─────────────────────────────────────────────────────────────────────────────
#  Full-app mech reference window
# ─────────────────────────────────────────────────────────────────────────────

class MechApp:

    def __init__(self, root, data):
        self.root = root
        self.data = data
        col = data["color"]

        root.title(f"{data['title'].split('—')[0].strip()}  —  Mech Notes")
        root.geometry("720x700")
        root.minsize(620, 500)
        root.configure(bg=C["bg"])
        root.resizable(True, True)

        # ── Top bar ───────────────────────────────────────────────────────────
        top = tk.Frame(root, bg=C["bg2"], pady=10, padx=18)
        top.pack(fill=tk.X)
        tk.Frame(root, bg=col, height=3).pack(fill=tk.X)

        tk.Label(top, text="PIED  —  MECH  NOTES",
                 font=("Segoe UI", 14, "bold"),
                 bg=C["bg2"], fg=col).pack(side=tk.LEFT)
        tk.Label(top, text="  source: DomainLordz / Rzy",
                 font=("Segoe UI", 8),
                 bg=C["bg2"], fg=C["text_dim"]).pack(side=tk.LEFT, pady=(4, 0))

        # ── Scrollable body ───────────────────────────────────────────────────
        outer = tk.Frame(root, bg=C["bg"])
        outer.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(outer, bg=C["bg"], highlightthickness=0, bd=0)
        sb = tk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        body = tk.Frame(canvas, bg=C["bg"])
        win_id = canvas.create_window((0, 0), window=body, anchor="nw")

        def _on_resize(e):
            canvas.itemconfig(win_id, width=e.width)
        canvas.bind("<Configure>", _on_resize)

        def _on_frame(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
        body.bind("<Configure>", _on_frame)

        canvas.bind_all("<MouseWheel>",
                        lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        # ── Heal order banner ─────────────────────────────────────────────────
        banner = tk.Frame(body, bg=C["card2"], pady=16, padx=20)
        banner.pack(fill=tk.X, padx=16, pady=(16, 0))
        tk.Frame(banner, bg=col, height=2).pack(fill=tk.X, pady=(0, 10))
        tk.Label(banner, text="HEAL ORDER",
                 font=("Segoe UI", 8, "bold"),
                 bg=C["card2"], fg=C["text_dim"]).pack(anchor="w")
        tk.Label(banner,
                 text="choco  →  hoh  →  shield  →  hoh  →  choco  →  chicken",
                 font=("Segoe UI", 13, "bold"),
                 bg=C["card2"], fg=col).pack(anchor="w", pady=(4, 0))

        # ── dayxne note ───────────────────────────────────────────────────────
        dn = tk.Frame(body, bg=C["bg2"], pady=12, padx=20)
        dn.pack(fill=tk.X, padx=16, pady=(8, 0))
        tk.Label(dn, text="dayxne alt",
                 font=("Segoe UI", 8, "bold"),
                 bg=C["bg2"], fg=C["text_dim"]).pack(anchor="w", pady=(0, 4))
        tk.Label(dn, text="choco  →  hoh1  →  shield  →  hoh2  →  chicken / choco",
                 font=("Segoe UI", 10),
                 bg=C["bg2"], fg=C["text"]).pack(anchor="w")
        tk.Label(dn, text="(depends on HP — if low, do both choco)",
                 font=("Segoe UI", 9),
                 bg=C["bg2"], fg=C["text_dim"]).pack(anchor="w", pady=(2, 0))

        # ── 55% omaewa ────────────────────────────────────────────────────────
        ow = tk.Frame(body, bg=C["card"], pady=12, padx=20)
        ow.pack(fill=tk.X, padx=16, pady=(8, 0))
        tk.Frame(ow, bg=C["gold"], height=2).pack(fill=tk.X, pady=(0, 8))
        tk.Label(ow, text="After omaewa  (55%)",
                 font=("Segoe UI", 10, "bold"),
                 bg=C["card"], fg=C["gold"]).pack(anchor="w")
        tk.Label(ow, text="Use Emergency or Pray skill",
                 font=("Segoe UI", 9),
                 bg=C["card"], fg=C["text"]).pack(anchor="w", pady=(3, 0))

        # ── Section header ────────────────────────────────────────────────────
        sh = tk.Frame(body, bg=C["bg"], pady=6, padx=20)
        sh.pack(fill=tk.X, padx=16, pady=(16, 0))
        tk.Label(sh, text="MECHANICS",
                 font=("Segoe UI", 9, "bold"),
                 bg=C["bg"], fg=C["text_dim"]).pack(side=tk.LEFT)
        tk.Frame(sh, bg=C["border"], height=1).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0), pady=(6, 0))

        # ── Mech cards ────────────────────────────────────────────────────────
        grid = tk.Frame(body, bg=C["bg"])
        grid.pack(fill=tk.X, padx=16, pady=(4, 0))
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

        for idx, m in enumerate(data.get("mechs", [])):
            row_i = idx // 2
            col_i = idx % 2
            card = tk.Frame(grid, bg=C["card2"],
                            highlightbackground=C["border"], highlightthickness=1)
            card.grid(row=row_i, column=col_i, padx=(0 if col_i else 0, 8 if col_i == 0 else 0),
                      pady=6, sticky="nsew", ipadx=0)
            grid.rowconfigure(row_i, weight=0)

            tk.Frame(card, bg=m["color"], height=3).pack(fill=tk.X)
            inner = tk.Frame(card, bg=C["card2"], padx=14, pady=10)
            inner.pack(fill=tk.BOTH, expand=True)

            # badge + main text
            hdr = tk.Frame(inner, bg=C["card2"])
            hdr.pack(fill=tk.X, pady=(0, 6))
            tk.Label(hdr, text=f" {m['pct']} ",
                     font=("Segoe UI", 9, "bold"),
                     bg=m["color"], fg="#ffffff", padx=6).pack(side=tk.LEFT)
            tk.Label(hdr, text=f"  {m['main']}",
                     font=("Segoe UI", 9, "bold"),
                     bg=C["card2"], fg=C["text"],
                     wraplength=260, justify="left").pack(side=tk.LEFT, fill=tk.X)

            # sub-notes
            for sub in m.get("subs", []):
                sr = tk.Frame(inner, bg=C["card2"])
                sr.pack(anchor="w", pady=1)
                tk.Label(sr, text="↳", font=("Segoe UI", 8),
                         bg=C["card2"], fg=m["color"]).pack(side=tk.LEFT, padx=(4, 6))
                tk.Label(sr, text=sub, font=("Segoe UI", 8),
                         bg=C["card2"], fg=C["text_dim"],
                         wraplength=250, justify="left").pack(side=tk.LEFT)

        # ── Phase transitions ─────────────────────────────────────────────────
        ph = tk.Frame(body, bg=C["bg"], pady=6, padx=20)
        ph.pack(fill=tk.X, padx=16, pady=(16, 0))
        tk.Label(ph, text="PHASE TRANSITIONS",
                 font=("Segoe UI", 9, "bold"),
                 bg=C["bg"], fg=C["text_dim"]).pack(side=tk.LEFT)
        tk.Frame(ph, bg=C["border"], height=1).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0), pady=(6, 0))

        pt = tk.Frame(body, bg=C["bg2"], pady=12, padx=20)
        pt.pack(fill=tk.X, padx=16, pady=(4, 16))
        for tag, text, pcol in data["phases"]:
            r = tk.Frame(pt, bg=C["bg2"])
            r.pack(anchor="w", pady=3)
            tk.Label(r, text=f" {tag} ", font=("Segoe UI", 8, "bold"),
                     bg=pcol, fg="#ffffff", padx=6).pack(side=tk.LEFT)
            tk.Label(r, text=f"  {text}", font=("Segoe UI", 9),
                     bg=C["bg2"], fg=C["text"]).pack(side=tk.LEFT)


# ─────────────────────────────────────────────────────────────────────────────

def main():
    root = tk.Tk()
    HealOverlay(root, "PIED")
    root.mainloop()


if __name__ == "__main__":
    main()
