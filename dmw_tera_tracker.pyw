"""
DMW Tera Tracker — Nexus Edition
Original dark-sci-fi design with boss portraits and dungeon cards.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json, os, threading, time, re, urllib.request, urllib.error, hashlib, winreg
from datetime import datetime
from io import BytesIO

try:
    import pyperclip
    HAS_PYPERCLIP = True
except ImportError:
    HAS_PYPERCLIP = False

try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import win32clipboard, win32con
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False

WIKI      = "https://digitalmastersworld.wiki.gg/images/"

# ── Auth whitelist ────────────────────────────────────────────────────────────
# Gist ID for the approved hardware ID list — set after first owner run
WHITELIST_GIST_ID = "76497eb1eafe071080de181aae3216e0"
PRICES_GIST_ID    = "4e389c1c812949916cc74b16899b03d4"  # public — friends read from here
OWNER_BYPASS      = True  # owner always has access (token present = owner)

def get_hwid():
    """Return a stable 4-character fingerprint of this machine."""
    try:
        key  = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                              r"SOFTWARE\Microsoft\Cryptography")
        guid = winreg.QueryValueEx(key, "MachineGuid")[0]
        winreg.CloseKey(key)
    except Exception:
        import uuid
        guid = str(uuid.getnode())
    return hashlib.sha256(guid.encode()).hexdigest()[:4].upper()

def check_auth(hwid, token, whitelist_gist_id):
    """
    Returns (allowed: bool, gist_id: str)
    - If token present → owner, always allowed
    - Otherwise checks hwid against the whitelist gist
    """
    if token:
        # Owner machine — always allowed, create whitelist gist in background if needed
        if not whitelist_gist_id:
            try:
                gist_id = _create_whitelist_gist(token, hwid)
                return True, gist_id
            except Exception:
                pass
        return True, whitelist_gist_id
    if not whitelist_gist_id:
        return False, ""
    try:
        url = f"https://api.github.com/gists/{whitelist_gist_id}"
        req = urllib.request.Request(url, headers={
            "Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(req, timeout=8) as r:
            data    = json.loads(r.read().decode())
            content = data["files"]["dmw_whitelist.json"]["content"]
            wl      = json.loads(content)
        return hwid in wl.get("approved", []), whitelist_gist_id
    except Exception:
        return False, whitelist_gist_id

def _create_whitelist_gist(token, owner_hwid):
    """Create the whitelist gist with the owner pre-approved."""
    payload = json.dumps({
        "description": "DMW Base — approved hardware IDs",
        "public":      False,
        "files": {"dmw_whitelist.json": {
            "content": json.dumps({"approved": [owner_hwid]}, indent=2)
        }},
    }).encode()
    req = urllib.request.Request(
        "https://api.github.com/gists",
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept":        "application/vnd.github+json",
            "Content-Type":  "application/json",
        },
        method="POST")
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read().decode())["id"]

# ── GitHub Gist sync config ───────────────────────────────────────────────────
SYNC_INTERVAL = 300   # pull latest prices every 5 minutes
import sys
_BASE_DIR = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable)) if getattr(sys, "frozen", False) \
            else os.path.dirname(os.path.abspath(__file__))
_IMG_DIR  = os.path.join(_BASE_DIR, "images")

# ── Dungeon definitions ────────────────────────────────────────────────────────
DUNGEONS = [
    {
        "id":        "rbh",
        "name":      "Royal Base (Hard)",
        "short":     "RBH",
        "boss":      "Alphamon Ouryuken Awaken",
        "boss_img":  os.path.join(_IMG_DIR, "rbh.jpg"),
        "color":     "#9d6fff",
        "color2":    "#5b2eb0",
        "full_runs": 7,
        "skip_runs": 10,
        "drops": [
            {"name": "Yggdrasil Core",      "qty": 1,  "guaranteed": True},
            {"name": "Gold Bar (1T)",        "qty": 2,  "guaranteed": True,  "fixed_t": 1},
            {"name": "Yggdrasil's Records",  "qty": 1,  "guaranteed": False},
        ],
    },
    {
        "id":       "mdg",
        "name":     "Marine Dragon Domain",
        "short":    "MDG",
        "boss":     "MetalSeadramon",
        "boss_img": os.path.join(_IMG_DIR, "mdg.jpg"),
        "color":    "#00b4d8",
        "color2":   "#005f73",
        "drops": [
            {"name": "Marine Dragon Core",          "qty": 1, "guaranteed": True},
            {"name": "MetalSeadramon's Spirit Box",  "qty": 1, "guaranteed": False},
        ],
    },
    {
        "id":       "pdg",
        "name":     "Front Yard of Marionette Mansion",
        "short":    "PDG",
        "boss":     "Puppetmon",
        "boss_img": os.path.join(_IMG_DIR, "pdg.jpg"),
        "color":    "#4ade80",
        "color2":   "#166534",
        "drops": [
            {"name": "Wooden Puppet Core",      "qty": 1, "guaranteed": True},
            {"name": "Puppetmon's Spirit Box",   "qty": 1, "guaranteed": False},
        ],
    },
    {
        "id":       "mdg2",
        "name":     "Back of the Empire",
        "short":    "MUGEN",
        "boss":     "MugenDramon",
        "boss_img": os.path.join(_IMG_DIR, "mugen.jpg"),
        "color":    "#94a3b8",
        "color2":   "#334155",
        "drops": [
            {"name": "Metallic Beast Core",      "qty": 1, "guaranteed": True},
            {"name": "MugenDramon's Spirit Box",  "qty": 1, "guaranteed": False},
        ],
    },
    {
        "id":       "sog",
        "name":     "Stage of Clown",
        "short":    "PIED",
        "boss":     "Piedmon",
        "boss_img": os.path.join(_IMG_DIR, "pied.jpg"),
        "color":    "#f43f5e",
        "color2":   "#881337",
        "drops": [
            {"name": "Cruelty Clown Core",    "qty": 1, "guaranteed": True},
            {"name": "Piedmon's Spirit Box",   "qty": 1, "guaranteed": False},
        ],
    },
    {
        "id":       "vsd",
        "name":     "Void Space Dungeon",
        "short":    "APO",
        "boss":     "Apocalymon",
        "boss_img": os.path.join(_IMG_DIR, "apo.jpg"),
        "color":    "#a855f7",
        "color2":   "#581c87",
        "drops": [
            {"name": "Core of Nothingness", "qty": 1, "guaranteed": True},
        ],
    },
]

PRICE_ITEMS = [
    {"name": "Yggdrasil Core",      "command": ".storeitem Yggdrasil Core"},
    {"name": "Yggdrasil's Records", "command": ".storeitem Yggdrasil's Records"},
    {"name": "Marine Dragon Core",  "command": ".storeitem Marine Dragon Core"},
    {"name": "Wooden Puppet Core",  "command": ".storeitem Wooden Puppet Core"},
    {"name": "Metallic Beast Core",          "command": ".storeitem Metallic Beast Core"},
    {"name": "Cruelty Clown Core",           "command": ".storeitem Cruelty Clown Core"},
    {"name": "Core of Nothingness",          "command": ".storeitem Core of Nothingness"},
    {"name": "MetalSeadramon's Spirit Box",  "command": ".storeitem MetalSeadramon's Spirit Box"},
    {"name": "Puppetmon's Spirit Box",       "command": ".storeitem Puppetmon's Spirit Box"},
    {"name": "MugenDramon's Spirit Box",     "command": ".storeitem MugenDramon's Spirit Box"},
    {"name": "Piedmon's Spirit Box",         "command": ".storeitem Piedmon's Spirit Box"},
]

# Items shown in Inventory tab (no spirit boxes — those are scanner-only)
INV_ITEMS = [it for it in PRICE_ITEMS if "Spirit Box" not in it["name"]]

DEFAULT_RUN_TIMES = {
    "rbh_full": 0,
    "rbh_skip": 0,
    "mdg":      150,
    "pdg":      210,
    "mdg2":     0,
    "sog":      0,
    "vsd":      0,
}

C = {
    "bg":           "#06090f",
    "bg2":          "#0d1520",
    "card":         "#101b2e",
    "card2":        "#0a1220",
    "border":       "#1a2a45",
    "border_hi":    "#2a4070",
    "gold":         "#f0c040",
    "gold_dim":     "#8a6e10",
    "text":         "#d8e4f8",
    "text_dim":     "#5a7090",
    "text_muted":   "#2a3a50",
    "green":        "#22d35a",
    "red":          "#f04060",
    "cyan":         "#00c8e8",
    "white":        "#ffffff",
    "nav_active":   "#1a2f55",
    "nav_hover":    "#111f35",
}


# ══════════════════════════════════════════════════════════════════════════════
class DMWTeraTracker:

    def __init__(self, root):
        self.root = root
        self.root.title("DMW Tera Tracker  —  Nexus")
        self.root.geometry("1280x820")
        self.root.minsize(1000, 680)
        self.root.configure(bg=C["bg"])

        _dir = os.path.join(os.path.expandvars("%LOCALAPPDATA%"), "DMWTeraTracker")
        os.makedirs(_dir, exist_ok=True)
        self.data_file = os.path.join(_dir, "dmw_tera_data.json")

        self.img_cache    = {}
        self.photo_refs   = []
        self.price_hist   = {}
        self.run_times    = dict(DEFAULT_RUN_TIMES)
        self.scan_enabled = {it["name"]: True for it in PRICE_ITEMS}
        self.inv_qty      = {it["name"]: 0 for it in PRICE_ITEMS}
        self.account_t    = 0.0
        self.custom_inv   = []
        self.scan_active  = False
        self.scan_idx     = 0
        self.clip_prev    = ""
        self.clip_img_id  = None
        self.clip_seq     = 0
        self.rbh_mode    = tk.StringVar(value="full")
        self.rbh_skip_on = tk.BooleanVar(value=False)
        self.active_tab  = tk.StringVar(value="scanner")
        self.item_rows   = {}
        self.pulse_id    = None
        self._sync_bin_id = ""
        self.load_data()
        self._sync_bin_id = self._load_sync_config().get("gist_id", "")
        self.setup_ui()

        if HAS_PIL:
            threading.Thread(target=self._preload_images, daemon=True).start()
        self._sync_init()

    # ── Data ──────────────────────────────────────────────────────────────────

    def load_data(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file) as f:
                    d = json.load(f)
                self.price_hist = d.get("price_history", {})
                saved_times = d.get("run_times", {})
                self.run_times.update(saved_times)
                saved_en = d.get("scan_enabled", {})
                self.scan_enabled.update(saved_en)
                saved_inv = d.get("inv_qty", {})
                self.inv_qty.update(saved_inv)
                self.account_t  = float(d.get("account_t", 0.0))
                self.custom_inv = d.get("custom_inv", [])
            except Exception:
                pass

    def save_data(self):
        try:
            with open(self.data_file, "w") as f:
                json.dump({
                    "price_history": self.price_hist,
                    "run_times":     self.run_times,
                    "scan_enabled":  self.scan_enabled,
                    "inv_qty":       self.inv_qty,
                "account_t":     self.account_t,
                "custom_inv":    self.custom_inv,
                }, f, indent=2)
        except Exception as e:
            messagebox.showerror("Save Error", str(e))

    # ── Run time helpers ──────────────────────────────────────────────────────

    def get_secs(self, key):
        return self.run_times.get(key, 0)

    def set_secs(self, key, secs):
        self.run_times[key] = max(0, int(secs))
        self.save_data()

    def runs_hr(self, key):
        s = self.get_secs(key)
        return round(3600 / s, 2) if s > 0 else 0

    def tera_hr(self, key, price):
        return self.runs_hr(key) * (price or 0)

    def rbh_tera_hr(self, mode="full"):
        ygg_p   = self.get_price("Yggdrasil Core") or 0
        bar_val = 2 * 1_000_000
        if mode == "full":
            runs = self.runs_hr("rbh_full")
        else:
            base = self.get_secs("rbh_full")
            eff  = (base - 120) if base > 120 else base
            runs = round(3600 / eff, 2) if eff > 0 else 0
        return runs * (ygg_p + bar_val)

    @staticmethod
    def secs_to_minsec(secs):
        if not secs:
            return ""
        m, s = divmod(int(secs), 60)
        return f"{m}:{s:02d}"

    @staticmethod
    def minsec_to_secs(text):
        text = text.strip()
        if ":" in text:
            parts = text.split(":")
            try:
                return int(parts[0]) * 60 + int(parts[1])
            except (ValueError, IndexError):
                return 0
        try:
            return int(text)
        except ValueError:
            return 0

    @property
    def active_items(self):
        return [it for it in PRICE_ITEMS if self.scan_enabled.get(it["name"], True)]

    def get_price(self, name):
        h = self.price_hist.get(name, [])
        return h[-1]["price"] if h else None

    def log_price(self, name, price):
        self.price_hist.setdefault(name, []).append(
            {"price": price, "timestamp": datetime.now().isoformat()})
        self.save_data()

    # ── Image loading ─────────────────────────────────────────────────────────

    def _load_img(self, url, size=(180, 220)):
        if not HAS_PIL or not url:
            return None
        key = (url, size)
        if key in self.img_cache:
            return self.img_cache[key]
        try:
            if os.path.isfile(url):
                img = Image.open(url).convert("RGBA")
            else:
                req  = urllib.request.Request(
                    url, headers={"User-Agent": "Mozilla/5.0"})
                data = urllib.request.urlopen(req, timeout=12).read()
                img  = Image.open(BytesIO(data)).convert("RGBA")
            img.thumbnail(size, Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self.img_cache[key] = photo
            self.photo_refs.append(photo)
            return photo
        except Exception:
            return None

    def _preload_images(self):
        for dg in DUNGEONS:
            self._load_img(dg["boss_img"])
        self.root.after(100, self._refresh_current)

    def _refresh_current(self):
        pass

    # ── Parsing ───────────────────────────────────────────────────────────────

    def parse_listing(self, text):
        prices = []
        for line in text.splitlines():
            m = re.match(r"\|\s*[^|]+\|\s*([\d,]+)\s*\|\s*\d+", line)
            if m:
                try:
                    prices.append(int(m.group(1).replace(",", "")))
                    continue
                except ValueError:
                    pass
            nums = re.findall(r"[\d,]{5,}", line)
            for n in nums:
                try:
                    v = int(n.replace(",", ""))
                    if v >= 100_000:
                        prices.append(v)
                except ValueError:
                    pass
        return min(prices) if prices else None

    def _parse_price_from_lines(self, lines):
        prices = []
        for line in lines:
            for m in re.finditer(r"[\d,]{6,}", line):
                try:
                    val = int(m.group().replace(",", ""))
                    if val >= 100_000:
                        prices.append(val)
                except ValueError:
                    pass
        return min(prices) if prices else None

    def fmt(self, price, suffix=True):
        if price is None:
            return "—"
        t = price / 1_000_000
        if t >= 100:
            v = f"{t:,.0f}"
        elif t >= 10:
            v = f"{t:.1f}"
        else:
            v = f"{t:.2f}"
        return f"{v}T" if suffix else v

    # ── Scroll helper ─────────────────────────────────────────────────────────

    def _make_scroll_body(self, parent):
        wrap = tk.Frame(parent, bg=C["bg"])
        wrap.pack(fill=tk.BOTH, expand=True)
        canvas = tk.Canvas(wrap, bg=C["bg"], highlightthickness=0)
        sb = ttk.Scrollbar(wrap, orient=tk.VERTICAL,
                           command=canvas.yview,
                           style="Nexus.Vertical.TScrollbar")
        sf = tk.Frame(canvas, bg=C["bg"])
        sf.bind("<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        win = canvas.create_window((0, 0), window=sf, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfig(win, width=e.width))
        canvas.bind_all("<MouseWheel>",
                        lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        return sf

    # ── UI ────────────────────────────────────────────────────────────────────

    def setup_ui(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Nexus.Vertical.TScrollbar",
                        background=C["card"], troughcolor=C["bg2"],
                        bordercolor=C["border"], arrowcolor=C["text_dim"])

        self._build_titlebar()
        self._build_navbar()
        tk.Frame(self.root, bg=C["border"], height=1).pack(fill=tk.X)
        self.body = tk.Frame(self.root, bg=C["bg"])
        self.body.pack(fill=tk.BOTH, expand=True)
        self._build_statusbar()
        self.show_tab("scanner")

    # ── Title bar ─────────────────────────────────────────────────────────────

    def _build_titlebar(self):
        bar = tk.Frame(self.root, bg=C["bg2"], pady=10, padx=20)
        bar.pack(fill=tk.X)

        left = tk.Frame(bar, bg=C["bg2"])
        left.pack(side=tk.LEFT)

        cv = tk.Canvas(left, width=36, height=36, bg=C["bg2"],
                       highlightthickness=0)
        cv.pack(side=tk.LEFT, padx=(0, 12))
        import math
        cx, cy, r = 18, 18, 16
        pts = []
        for i in range(6):
            a = math.pi / 180 * (60 * i - 30)
            pts += [cx + r * math.cos(a), cy + r * math.sin(a)]
        cv.create_polygon(pts, fill="#1a2a50", outline="#9d6fff", width=2)
        cv.create_text(cx, cy, text="T", fill="#9d6fff",
                       font=("Segoe UI", 14, "bold"))

        tk.Label(left, text="TERA TRACKER",
                 font=("Segoe UI", 18, "bold"),
                 bg=C["bg2"], fg=C["text"]).pack(side=tk.LEFT)
        tk.Label(left, text="  NEXUS EDITION",
                 font=("Segoe UI", 10),
                 bg=C["bg2"], fg=C["text_dim"]).pack(side=tk.LEFT, pady=(5, 0))

        right = tk.Frame(bar, bg=C["bg2"])
        right.pack(side=tk.RIGHT)

        self.last_scan_lbl = tk.Label(right, text="Last scan:  never",
                 font=("Segoe UI", 9),
                 bg=C["bg2"], fg=C["text_dim"])
        self.last_scan_lbl.pack(side=tk.RIGHT, padx=(0, 4))

        self.sync_lbl = tk.Label(right,
                 text="⬡ Sync ready",
                 font=("Segoe UI", 9),
                 bg=C["bg2"], fg=C["text_muted"])
        self.sync_lbl.pack(side=tk.RIGHT, padx=(0, 20))

    # ── Navigation ────────────────────────────────────────────────────────────

    def _build_navbar(self):
        self.navbar = tk.Frame(self.root, bg=C["bg2"])
        self.navbar.pack(fill=tk.X)
        self.nav_btns = {}
        tabs = [
            ("scanner",   "\U0001f50d   Price Scanner"),
            ("dungeons",  "⚔   Dungeons"),
            ("compare",   "⚖   Compare"),
            ("history",   "\U0001f4c8   History"),
            ("inventory", "\U0001f392   Inventory"),
        ]
        for key, label in tabs:
            btn = tk.Label(self.navbar, text=label,
                           font=("Segoe UI", 11, "bold"),
                           bg=C["bg2"], fg=C["text_dim"],
                           padx=28, pady=12, cursor="hand2")
            btn.pack(side=tk.LEFT)
            btn.bind("<Button-1>", lambda e, k=key: self.show_tab(k))
            btn.bind("<Enter>",    lambda e, b=btn: b.config(bg=C["nav_hover"]))
            btn.bind("<Leave>",    lambda e, b=btn, k=key:
                     b.config(bg=C["nav_active"] if self.active_tab.get() == k else C["bg2"]))
            self.nav_btns[key] = btn

    def _update_navbar(self, active):
        for k, btn in self.nav_btns.items():
            if k == active:
                btn.config(bg=C["nav_active"], fg=C["text"])
            else:
                btn.config(bg=C["bg2"], fg=C["text_dim"])

    # ── Status bar ────────────────────────────────────────────────────────────

    def _build_statusbar(self):
        tk.Frame(self.root, bg=C["border"], height=1).pack(fill=tk.X, side=tk.BOTTOM)
        bar = tk.Frame(self.root, bg=C["bg2"], pady=6)
        bar.pack(fill=tk.X, side=tk.BOTTOM)
        self.status = tk.Label(bar, text="  Ready",
                               font=("Segoe UI", 10),
                               bg=C["bg2"], fg=C["text_dim"])
        self.status.pack(side=tk.LEFT)
        self.scan_dot = tk.Label(bar, text="●",
                                 font=("Segoe UI", 12),
                                 bg=C["bg2"], fg=C["text_muted"])
        self.scan_dot.pack(side=tk.RIGHT, padx=12)

    def set_status(self, text, color=None):
        self.status.config(text=f"  {text}", fg=color or C["text_dim"])

    def _pulse_dot(self, on=True):
        if not self.scan_active:
            self.scan_dot.config(fg=C["text_muted"])
            return
        self.scan_dot.config(fg=C["green"] if on else C["text_muted"])
        self.pulse_id = self.root.after(600, self._pulse_dot, not on)

    # ── Tab router ────────────────────────────────────────────────────────────

    def show_tab(self, key):
        self.active_tab.set(key)
        self._update_navbar(key)
        for w in self.body.winfo_children():
            w.destroy()
        {
            "scanner":   self._build_scanner,
            "dungeons":  self._build_dungeons,
            "compare":   self._build_compare,
            "history":   self._build_history,
            "inventory": self._build_inventory,
        }[key]()

    # ══════════════════════════════════════════════════════════════════════════
    # PRICE SCANNER
    # ══════════════════════════════════════════════════════════════════════════

    def _build_scanner(self):
        p = self._make_scroll_body(self.body)

        hero = tk.Frame(p, bg=C["bg2"], pady=18, padx=28)
        hero.pack(fill=tk.X)

        left = tk.Frame(hero, bg=C["bg2"])
        left.pack(side=tk.LEFT, fill=tk.Y)

        tk.Label(left, text="PRICE  SCANNER",
                 font=("Segoe UI", 22, "bold"),
                 bg=C["bg2"], fg=C["cyan"]).pack(anchor="w")
        tk.Label(left,
                 text="Copy command  →  paste in Discord  →  copy bot response  →  logged automatically",
                 font=("Segoe UI", 9),
                 bg=C["bg2"], fg=C["text_dim"]).pack(anchor="w", pady=(4, 0))

        right = tk.Frame(hero, bg=C["bg2"])
        right.pack(side=tk.RIGHT, anchor="e")

        self.start_btn = self._nexus_btn(right, "▶   Start Scan",
                                          C["green"], "#0a1a0f",
                                          self.start_scan)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 8))

        self.stop_btn = self._nexus_btn(right, "■   Stop",
                                         C["red"], "#fff",
                                         self.stop_scan, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 8))

        self._nexus_btn(right, "↺   Restart", C["border_hi"], C["text"],
                        self.restart_scan).pack(side=tk.LEFT)

        tk.Frame(p, bg=C["border"], height=1).pack(fill=tk.X)

        cur = tk.Frame(p, bg=C["card"], pady=20, padx=28)
        cur.pack(fill=tk.X)

        cur_left = tk.Frame(cur, bg=C["card"])
        cur_left.pack(side=tk.LEFT, fill=tk.Y)

        tk.Label(cur_left, text="CURRENT  ITEM",
                 font=("Segoe UI", 7, "bold"),
                 bg=C["card"], fg=C["text_muted"]).pack(anchor="w")

        self.cur_name = tk.Label(cur_left, text="—",
                 font=("Segoe UI", 26, "bold"),
                 bg=C["card"], fg=C["cyan"])
        self.cur_name.pack(anchor="w", pady=(4, 2))

        self.cur_cmd = tk.Label(cur_left, text="",
                 font=("Consolas", 11),
                 bg=C["card"], fg=C["text_dim"])
        self.cur_cmd.pack(anchor="w")

        cur_right = tk.Frame(cur, bg=C["card"])
        cur_right.pack(side=tk.RIGHT, anchor="e", padx=(0, 10))

        self.prog_label = tk.Label(cur_right, text="",
                 font=("Segoe UI", 11),
                 bg=C["card"], fg=C["text_dim"])
        self.prog_label.pack(anchor="e")

        self.prog_bar = tk.Canvas(cur_right, height=6, width=220,
                                  bg=C["bg"], highlightthickness=0)
        self.prog_bar.pack(anchor="e", pady=(6, 0))

        tk.Frame(p, bg=C["border"], height=1).pack(fill=tk.X)

        tk.Label(p, text="  ITEMS IN QUEUE",
                 font=("Segoe UI", 7, "bold"),
                 bg=C["bg"], fg=C["text_muted"], pady=8).pack(anchor="w")

        self.item_rows = {}
        for item in PRICE_ITEMS:
            self._build_queue_row(p, item)

        self._refresh_scan_ui()

    def _build_queue_row(self, parent, item):
        name    = item["name"]
        price   = self.get_price(name)
        enabled = self.scan_enabled.get(name, True)
        bg      = C["bg"]

        row = tk.Frame(parent, bg=bg,
                       highlightbackground=C["border"], highlightthickness=1)
        row.pack(fill=tk.X)

        inner = tk.Frame(row, bg=bg, pady=10, padx=26)
        inner.pack(fill=tk.X)

        dot = tk.Label(inner, text="◆",
                       font=("Segoe UI", 9),
                       bg=bg,
                       fg=C["green"] if price else C["text_muted"])
        dot.pack(side=tk.LEFT, padx=(0, 12))

        name_lbl = tk.Label(inner, text=name,
                            font=("Segoe UI", 11),
                            bg=bg,
                            fg=C["text"] if enabled else C["text_muted"])
        name_lbl.pack(side=tk.LEFT)

        tog_lbl = tk.Label(inner,
                           text=" ON " if enabled else " OFF ",
                           font=("Segoe UI", 8, "bold"),
                           bg=C["green"] if enabled else C["border"],
                           fg=C["bg"] if enabled else C["text_muted"],
                           padx=6, pady=2, cursor="hand2")
        tog_lbl.pack(side=tk.RIGHT, padx=(8, 0))

        price_lbl = tk.Label(inner,
                             text=self.fmt(price) if price else "Not yet checked",
                             font=("Segoe UI", 12, "bold"),
                             bg=bg,
                             fg=C["gold"] if (price and enabled) else C["text_muted"],
                             cursor="hand2")
        price_lbl.pack(side=tk.RIGHT)

        all_w = [row, inner, name_lbl, dot, price_lbl]

        def _toggle(e, n=name, tl=tog_lbl, nl=name_lbl, pl=price_lbl):
            cur = self.scan_enabled.get(n, True)
            new = not cur
            self.scan_enabled[n] = new
            self.save_data()
            tl.config(text=" ON " if new else " OFF ",
                      bg=C["green"] if new else C["border"],
                      fg=C["bg"] if new else C["text_muted"])
            nl.config(fg=C["text"] if new else C["text_muted"])
            p = self.get_price(n)
            pl.config(fg=C["gold"] if (p and new) else C["text_muted"])
            self._refresh_scan_ui()

        tog_lbl.bind("<Button-1>", _toggle)

        def _edit_price(e, n=name, pl=price_lbl, bg=bg):
            cur_price = self.get_price(n)
            cur_t = f"{cur_price / 1_000_000:.2f}" if cur_price else ""
            pl.pack_forget()
            var = tk.StringVar(value=cur_t)
            ent = tk.Entry(inner, textvariable=var,
                           font=("Consolas", 12, "bold"),
                           bg=C["card2"], fg=C["gold"],
                           insertbackground=C["gold"],
                           relief=tk.FLAT, width=8, justify="center")
            ent.pack(side=tk.RIGHT)
            ent.focus_set()
            ent.select_range(0, tk.END)

            def _commit_edit(ev=None):
                try:
                    t_val = float(var.get().replace("T", "").replace(",", "").strip())
                    new_price = int(t_val * 1_000_000)
                except ValueError:
                    new_price = cur_price
                ent.destroy()
                pl.pack(side=tk.RIGHT)
                if new_price and new_price > 0:
                    self.log_price(n, new_price)
                    pl.config(text=self.fmt(new_price),
                              fg=C["gold"] if self.scan_enabled.get(n, True) else C["text_muted"])
                    r = self.item_rows.get(n, {})
                    if "dot" in r:
                        r["dot"].config(fg=C["green"])

            def _cancel_edit(ev=None):
                ent.destroy()
                pl.pack(side=tk.RIGHT)

            ent.bind("<Return>",   _commit_edit)
            ent.bind("<Escape>",   _cancel_edit)
            ent.bind("<FocusOut>", _commit_edit)

        price_lbl.bind("<Button-1>", _edit_price)

        self.item_rows[name] = {"dot": dot, "price_lbl": price_lbl,
                                "row": row, "inner": inner}

        def _enter(e, w=all_w):
            for x in w: x.config(bg=C["card"])
        def _leave(e, w=all_w):
            for x in w: x.config(bg=C["bg"])
        for w in all_w:
            w.bind("<Enter>", _enter)
            w.bind("<Leave>", _leave)

    def _refresh_scan_ui(self):
        if not hasattr(self, "cur_name"):
            return
        items = self.active_items
        n = len(items)
        if n == 0:
            self.cur_name.config(text="No items selected")
            self.cur_cmd.config(text="Toggle items below to enable")
            self.prog_label.config(text="0 / 0")
            self.prog_bar.delete("all")
            return
        if self.scan_idx < n:
            item = items[self.scan_idx]
            self.cur_name.config(text=item["name"])
            self.cur_cmd.config(text=item["command"])
            self.prog_label.config(text=f"{self.scan_idx + 1}  /  {n}")
        else:
            self.cur_name.config(text="✓  Complete")
            self.cur_cmd.config(text="All selected prices updated")
            self.prog_label.config(text=f"{n}  /  {n}")

        pct = min(self.scan_idx / n, 1.0) if n else 0
        w = 220
        self.prog_bar.delete("all")
        self.prog_bar.create_rectangle(0, 0, w, 6, fill=C["bg2"], width=0)
        col = C["green"] if pct >= 1.0 else C["cyan"]
        self.prog_bar.create_rectangle(0, 0, int(w * pct), 6, fill=col, width=0)

    # ── Scan controls ─────────────────────────────────────────────────────────

    def start_scan(self):
        import ctypes
        if self.scan_idx >= len(self.active_items):
            self.scan_idx = 0
        self.scan_active = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self._copy_cmd()
        self.clip_prev = pyperclip.paste() if HAS_PYPERCLIP else ""
        self.clip_seq  = ctypes.windll.user32.GetClipboardSequenceNumber()
        self._pulse_dot()
        threading.Thread(target=self._clip_monitor, daemon=True).start()

    def stop_scan(self):
        self.scan_active = False
        if hasattr(self, "start_btn"):
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
        self.scan_dot.config(fg=C["text_muted"])
        self.set_status("Scan paused", C["gold"])

    def restart_scan(self):
        self.stop_scan()
        self.scan_idx = 0
        self._refresh_scan_ui()
        self.set_status("Reset — press Start to begin")

    def _copy_cmd(self):
        items = self.active_items
        if self.scan_idx < len(items):
            cmd = items[self.scan_idx]["command"]
            if HAS_PYPERCLIP:
                pyperclip.copy(cmd)
            self.set_status(
                f"Copied  →  {cmd}   |   Paste in Discord, then Ctrl+C the bot reply",
                C["cyan"])

    def _clipboard_has_image(self):
        if not HAS_WIN32:
            return False
        try:
            win32clipboard.OpenClipboard()
            try:
                return (win32clipboard.IsClipboardFormatAvailable(win32con.CF_DIB) or
                        win32clipboard.IsClipboardFormatAvailable(win32con.CF_BITMAP))
            finally:
                win32clipboard.CloseClipboard()
        except Exception:
            return False

    def _clip_monitor(self):
        import ctypes
        get_seq = ctypes.windll.user32.GetClipboardSequenceNumber

        while self.scan_active and self.scan_idx < len(self.active_items):
            time.sleep(0.35)
            try:
                items = self.active_items
                if self.scan_idx >= len(items):
                    break

                seq = get_seq()
                if seq == self.clip_seq:
                    continue
                self.clip_seq = seq

                if self._clipboard_has_image():
                    self.root.after(0, lambda: self.set_status(
                        "Snip in clipboard — now Ctrl+C the bot's price text",
                        C["gold"]))
                    continue

                clip = pyperclip.paste() if HAS_PYPERCLIP else ""
                if not clip or clip == self.clip_prev:
                    continue

                price = self.parse_listing(clip)
                if price and price > 0:
                    name = items[self.scan_idx]["name"]
                    self.clip_prev = clip
                    self.log_price(name, price)
                    self.root.after(0, self._price_captured, name, price)

            except Exception:
                pass
        self.root.after(0, self._scan_done)

    def _price_captured(self, name, price):
        if name in self.item_rows:
            r = self.item_rows[name]
            r["price_lbl"].config(text=self.fmt(price), fg=C["gold"])
            r["dot"].config(fg=C["green"])
        self.scan_idx += 1
        self._refresh_scan_ui()
        if self.scan_idx < len(self.active_items):
            self._copy_cmd()
        else:
            ts = datetime.now().strftime("%d %b  %H:%M")
            self.last_scan_lbl.config(text=f"Last scan:  {ts}")

    def _scan_done(self):
        if self.scan_idx >= len(self.active_items):
            self.scan_active = False
            self.scan_dot.config(fg=C["text_muted"])
            if hasattr(self, "start_btn"):
                self.start_btn.config(state=tk.NORMAL)
                self.stop_btn.config(state=tk.DISABLED)
            self.set_status("✓  All prices updated!", C["green"])
            self._sync_push()

    # ══════════════════════════════════════════════════════════════════════════
    # RBH DETAIL
    # ══════════════════════════════════════════════════════════════════════════

    def _open_rbh_detail(self):
        for w in self.body.winfo_children():
            w.destroy()
        p  = self._make_scroll_body(self.body)
        dg = DUNGEONS[0]

        # Back button
        back = tk.Frame(p, bg=C["bg2"], pady=8, padx=16)
        back.pack(fill=tk.X)
        tk.Label(back, text="← Back to Dungeons",
                 font=("Segoe UI", 10),
                 bg=C["bg2"], fg=C["text_dim"],
                 cursor="hand2").pack(side=tk.LEFT).bind(
                     "<Button-1>", lambda e: self.show_tab("dungeons"))

        # Hero
        hero = tk.Frame(p, bg=C["bg2"])
        hero.pack(fill=tk.X)
        tk.Frame(hero, bg=dg["color"], height=3).pack(fill=tk.X)
        hero_inner = tk.Frame(hero, bg=C["bg2"], pady=20, padx=28)
        hero_inner.pack(fill=tk.X)
        hero_left = tk.Frame(hero_inner, bg=C["bg2"])
        hero_left.pack(side=tk.LEFT, fill=tk.Y)
        tk.Label(hero_left, text=dg["name"].upper(),
                 font=("Segoe UI", 9, "bold"),
                 bg=C["bg2"], fg=dg["color"]).pack(anchor="w")
        tk.Label(hero_left, text="RBH  TRACKER",
                 font=("Segoe UI", 26, "bold"),
                 bg=C["bg2"], fg=C["text"]).pack(anchor="w", pady=(4, 0))
        tk.Label(hero_left, text=f"Boss:  {dg['boss']}",
                 font=("Segoe UI", 11),
                 bg=C["bg2"], fg=C["text_dim"]).pack(anchor="w", pady=(6, 0))
        hero_right = tk.Frame(hero_inner, bg=C["bg2"])
        hero_right.pack(side=tk.RIGHT)
        portrait_f = tk.Frame(hero_right, bg=C["bg2"])
        portrait_f.pack()
        self._load_boss_portrait(portrait_f, dg)
        tk.Frame(p, bg=dg["color"], height=1).pack(fill=tk.X)

        # Controls bar: run time + skip toggle
        ctrl_bar = tk.Frame(p, bg=C["card2"], pady=12, padx=28)
        ctrl_bar.pack(fill=tk.X)
        tk.Label(ctrl_bar, text="RUN  TIME",
                 font=("Segoe UI", 7, "bold"),
                 bg=C["card2"], fg=C["text_muted"]).pack(side=tk.LEFT, padx=(0, 24))
        self._time_input(ctrl_bar, "rbh_full", C["card2"],
                         on_change=self._build_rbh_stats).pack(side=tk.LEFT)

        skip_on  = self.rbh_skip_on.get()
        skip_tog = tk.Label(ctrl_bar,
                            text="  ⚡  Skip  −2:00  ",
                            font=("Segoe UI", 9, "bold"),
                            bg=dg["color"] if skip_on else C["border"],
                            fg=C["bg"] if skip_on else C["text_muted"],
                            padx=8, pady=6, cursor="hand2")
        skip_tog.pack(side=tk.LEFT, padx=(20, 0))

        def _toggle_skip(e):
            self.rbh_skip_on.set(not self.rbh_skip_on.get())
            self._open_rbh_detail()

        skip_tog.bind("<Button-1>", _toggle_skip)
        tk.Label(ctrl_bar, text="Toggle — subtracts 2 min from run time",
                 font=("Segoe UI", 8),
                 bg=C["card2"], fg=C["text_muted"]).pack(side=tk.RIGHT)
        tk.Frame(p, bg=C["border"], height=1).pack(fill=tk.X)

        self.rbh_stats_body = tk.Frame(p, bg=C["bg"])
        self.rbh_stats_body.pack(fill=tk.BOTH, expand=True)
        self._build_rbh_stats()

    def _build_rbh_stats(self):
        if not hasattr(self, "rbh_stats_body"):
            return
        for w in self.rbh_stats_body.winfo_children():
            w.destroy()

        dg        = DUNGEONS[0]
        base_secs = self.get_secs("rbh_full")
        skip_on   = self.rbh_skip_on.get()

        if skip_on and base_secs > 120:
            eff_secs   = base_secs - 120
            mode_label = "Skip Run"
        else:
            eff_secs   = base_secs
            mode_label = "Full Run"

        runs_hr = round(3600 / eff_secs, 2) if eff_secs > 0 else 0
        eff_str = self.secs_to_minsec(eff_secs) if eff_secs else "not set"
        bars_hr = runs_hr * 2
        ygg_p   = self.get_price("Yggdrasil Core") or 0
        rec_p   = self.get_price("Yggdrasil's Records") or 0
        ygg_val = runs_hr * ygg_p
        bar_val = bars_hr * 1_000_000
        total   = ygg_val + bar_val

        body = tk.Frame(self.rbh_stats_body, bg=C["bg"], pady=22, padx=28)
        body.pack(fill=tk.BOTH, expand=True)

        grid = tk.Frame(body, bg=C["bg"])
        grid.pack(fill=tk.X)

        runs_display = f"{runs_hr:.1f}" if runs_hr else "— set run time"
        cards = [
            ("Runs / Hour",          runs_display,
                                                  dg["color"],  f"{mode_label}: {eff_str}"),
            ("Yggdrasil Cores / hr", runs_display,
                                                  "#a371f7",    "1 core guaranteed per clear"),
            ("Gold Bars / hr",       f"{bars_hr:.0f}  bars" if runs_hr else "—",
                                                  C["green"],   "2 \xd7 1T Gold Bullion per run"),
            ("Ygg Core Price",       self.fmt(ygg_p) if ygg_p else "—",
                                                  C["gold"],    "Latest logged market price"),
            ("Gold Bar Value / hr",  self.fmt(bar_val) if runs_hr else "—",
                                                  C["green"],   "Fixed 2T \xd7 runs/hr"),
            ("Ygg Core Value / hr",  self.fmt(ygg_val) if ygg_p and runs_hr else "—",
                                                  C["gold"],    "Core price \xd7 runs/hr"),
            ("TOTAL  Tera / hr",     self.fmt(total) if total else "—",
                                                  C["cyan"],    "Guaranteed drops only"),
            ("Yggdrasil's Records",  self.fmt(rec_p) if rec_p else "Chance drop — run scanner",
                                                  "#f778ba",    "Not included in total (RNG)"),
        ]

        for i, (label, value, color, note) in enumerate(cards):
            self._stat_card(grid, i // 4, i % 4, label, value, color, note, dg["color"])

        for col in range(4):
            grid.grid_columnconfigure(col, weight=1)

        note_strip = tk.Frame(body, bg=C["card"],
                              highlightbackground=C["border"], highlightthickness=1)
        note_strip.pack(fill=tk.X, pady=(18, 0))
        tk.Frame(note_strip, bg=dg["color"], width=4).pack(side=tk.LEFT, fill=tk.Y)
        note_t = (f"  ℹ   {mode_label} — {eff_str} per clear.  " if eff_secs else
                  "  ℹ   Set your run time above.  ")
        if skip_on:
            note_t += "Skip saves ~2 min by skipping optional rooms.  "
        note_t += ("Yggdrasil's Records is chance-only and excluded from total.  "
                   "Run Price Scanner to keep values current.")
        tk.Label(note_strip, text=note_t,
                 font=("Segoe UI", 9),
                 bg=C["card"], fg=C["text_dim"],
                 pady=10, wraplength=900, justify="left").pack(side=tk.LEFT)

        self._build_drops_panel(body, dg)

    def _build_drops_panel(self, parent, dg):
        sec = tk.Frame(parent, bg=C["bg"])
        sec.pack(fill=tk.X, pady=(18, 0))

        tk.Label(sec, text="DROPS",
                 font=("Segoe UI", 7, "bold"),
                 bg=C["bg"], fg=C["text_muted"],
                 pady=6).pack(anchor="w")

        for drop in dg["drops"]:
            name  = drop["name"]
            guar  = drop["guaranteed"]
            qty   = drop.get("qty", 1)
            fixed = drop.get("fixed_t")

            row = tk.Frame(sec, bg=C["card"],
                           highlightbackground=C["border"], highlightthickness=1)
            row.pack(fill=tk.X, pady=2)
            tk.Frame(row, bg=dg["color"] if guar else C["border"],
                     width=4).pack(side=tk.LEFT, fill=tk.Y)

            r_in = tk.Frame(row, bg=C["card"], pady=9, padx=16)
            r_in.pack(fill=tk.X, side=tk.LEFT, expand=True)

            badge = "GUARANTEED" if guar else "CHANCE  ❖"
            tk.Label(r_in, text=badge,
                     font=("Segoe UI", 7, "bold"),
                     bg=C["card"],
                     fg=dg["color"] if guar else C["text_muted"],
                     width=12, anchor="w").pack(side=tk.LEFT)

            tk.Label(r_in, text=f"{qty}\xd7   {name}",
                     font=("Segoe UI", 11, "bold"),
                     bg=C["card"], fg=C["text"]).pack(side=tk.LEFT, padx=(8, 0))

            if fixed is not None:
                price_str = self.fmt(fixed * 1_000_000)
                tk.Label(r_in, text=f"{price_str}  (fixed)",
                         font=("Segoe UI", 10),
                         bg=C["card"], fg=C["gold_dim"]).pack(side=tk.RIGHT)
            else:
                p = self.get_price(name)
                tk.Label(r_in,
                         text=self.fmt(p) if p else "—  not scanned",
                         font=("Segoe UI", 11, "bold" if p else "normal"),
                         bg=C["card"],
                         fg=C["gold"] if p else C["text_muted"]).pack(side=tk.RIGHT)

    def _load_boss_portrait(self, frame, dg, size=(170, 200)):
        for w in frame.winfo_children():
            w.destroy()

        outer = tk.Frame(frame, bg=dg["color"], padx=2, pady=2)
        outer.pack()
        inner = tk.Frame(outer, bg=C["bg2"])
        inner.pack()

        img = self._load_img(dg["boss_img"], size)
        if img:
            lbl = tk.Label(inner, image=img, bg=C["bg2"])
            lbl.pack(padx=6, pady=6)
        else:
            cv = tk.Canvas(inner, width=size[0], height=size[1],
                           bg=C["card2"], highlightthickness=0)
            cv.pack(padx=6, pady=6)
            cv.create_text(size[0]//2, size[1]//2,
                           text=dg["short"],
                           fill=dg["color"],
                           font=("Segoe UI", 32, "bold"))
            def _try_later():
                time.sleep(2)
                img2 = self._load_img(dg["boss_img"], size)
                if img2:
                    self.root.after(0, lambda: self._refresh_portrait(frame, dg, size))
            threading.Thread(target=_try_later, daemon=True).start()

        tk.Label(inner, text=dg["boss"],
                 font=("Segoe UI", 9, "bold"),
                 bg=C["bg2"], fg=dg["color"]).pack(pady=(0, 6))

    def _refresh_portrait(self, frame, dg, size):
        self._load_boss_portrait(frame, dg, size)

    # ══════════════════════════════════════════════════════════════════════════
    # DUNGEONS TRACKER
    # ══════════════════════════════════════════════════════════════════════════

    def _build_dungeons(self):
        p = self.body

        hdr = tk.Frame(p, bg=C["bg2"], pady=16, padx=28)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="DUNGEONS",
                 font=("Segoe UI", 22, "bold"),
                 bg=C["bg2"], fg="#a855f7").pack(side=tk.LEFT)
        tk.Label(hdr, text="   Click a dungeon to open its tracker",
                 font=("Segoe UI", 9),
                 bg=C["bg2"], fg=C["text_dim"]).pack(side=tk.LEFT, pady=(6, 0))
        tk.Frame(p, bg=C["border"], height=1).pack(fill=tk.X)

        sf = self._make_scroll_body(p)

        for dg in DUNGEONS:
            self._build_spiral_card(sf, dg)

        tk.Frame(sf, height=16, bg=C["bg"]).pack()

    def _build_spiral_card(self, parent, dg):
        card = tk.Frame(parent, bg=C["card"],
                        highlightbackground=dg["color"], highlightthickness=1)
        card.pack(fill=tk.X, pady=(10, 0), padx=18)
        tk.Frame(card, bg=dg["color"], height=3).pack(fill=tk.X)

        inner = tk.Frame(card, bg=C["card"])
        inner.pack(fill=tk.X)

        # Left: boss portrait
        portrait_frame = tk.Frame(inner, bg=C["card"])
        portrait_frame.pack(side=tk.LEFT, padx=16, pady=14)
        self._load_boss_portrait(portrait_frame, dg, size=(110, 130))

        # Right: info + drops + stats
        info = tk.Frame(inner, bg=C["card"])
        info.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 16), pady=14)

        tk.Label(info, text=dg["short"],
                 font=("Segoe UI", 8, "bold"),
                 bg=C["card"], fg=dg["color"]).pack(anchor="w")
        tk.Label(info, text=dg["name"],
                 font=("Segoe UI", 14, "bold"),
                 bg=C["card"], fg=C["text"]).pack(anchor="w", pady=(2, 0))
        tk.Label(info, text=f"Boss:  {dg['boss']}",
                 font=("Segoe UI", 10),
                 bg=C["card"], fg=C["text_dim"]).pack(anchor="w", pady=(4, 10))

        # Drop rows
        for drop in dg["drops"]:
            price = self.get_price(drop["name"])
            fixed = drop.get("fixed_t")
            row   = tk.Frame(info, bg=C["bg2"],
                             highlightbackground=C["border"], highlightthickness=1)
            row.pack(fill=tk.X, pady=2)
            tk.Frame(row, bg=dg["color"], width=3).pack(side=tk.LEFT, fill=tk.Y)
            r_in = tk.Frame(row, bg=C["bg2"], pady=7, padx=12)
            r_in.pack(fill=tk.X)
            guar_txt = "Guaranteed" if drop.get("guaranteed") else "Chance  ❖"
            tk.Label(r_in,
                     text=f"{drop['name']}  ×{drop['qty']}  —  {guar_txt}",
                     font=("Segoe UI", 10),
                     bg=C["bg2"], fg=C["text"]).pack(side=tk.LEFT)

            if fixed is not None:
                tk.Label(r_in, text=f"{self.fmt(fixed * 1_000_000)}  (fixed)",
                         font=("Segoe UI", 10, "bold"),
                         bg=C["bg2"], fg=C["gold_dim"]).pack(side=tk.RIGHT)
            else:
                tk.Label(r_in,
                         text=self.fmt(price) if price else "Check scanner",
                         font=("Segoe UI", 10, "bold"),
                         bg=C["bg2"],
                         fg=C["gold"] if price else C["text_muted"]).pack(side=tk.RIGHT)

        # Stats strip
        tk.Frame(info, bg=C["border"], height=1).pack(fill=tk.X, pady=(10, 8))
        stats_row = tk.Frame(info, bg=C["card"])
        stats_row.pack(fill=tk.X)

        def _chip(par, lbl_text, val_text, color):
            f = tk.Frame(par, bg=C["card2"],
                         highlightbackground=C["border"], highlightthickness=1)
            f.pack(side=tk.LEFT, padx=(0, 8))
            tk.Frame(f, bg=color, height=2).pack(fill=tk.X)
            p = tk.Frame(f, bg=C["card2"], padx=10, pady=6)
            p.pack()
            tk.Label(p, text=lbl_text, font=("Segoe UI", 7, "bold"),
                     bg=C["card2"], fg=C["text_muted"]).pack(anchor="w")
            tk.Label(p, text=val_text, font=("Segoe UI", 13, "bold"),
                     bg=C["card2"], fg=color).pack(anchor="w", pady=(2, 0))

        if dg["id"] == "rbh":
            skip_on  = self.rbh_skip_on.get()
            base     = self.get_secs("rbh_full")
            eff      = (base - 120) if (skip_on and base > 120) else base
            r_hr     = round(3600 / eff, 2) if eff > 0 else 0
            ygg_p    = self.get_price("Yggdrasil Core") or 0
            rec_p    = self.get_price("Yggdrasil's Records") or 0
            bar_val  = r_hr * 2 * 1_000_000
            ygg_val  = r_hr * ygg_p
            total    = bar_val + ygg_val
            eff_str  = self.secs_to_minsec(eff) if eff else "not set"
            mode_lbl = "Skip Run" if skip_on else "Full Run"

            ctrl = tk.Frame(info, bg=C["card"])
            ctrl.pack(fill=tk.X, pady=(0, 8))

            self._time_input(ctrl, "rbh_full", C["card"],
                             on_change=lambda d=dg, sr=stats_row:
                             self._refresh_spiral_card_stats(d, sr)
                             ).pack(side=tk.LEFT, padx=(0, 18))

            skip_tog = tk.Label(ctrl,
                                text="  ⚡  Skip  −2:00  ",
                                font=("Segoe UI", 9, "bold"),
                                bg=dg["color"] if skip_on else C["border"],
                                fg=C["bg"] if skip_on else C["text_muted"],
                                padx=8, pady=6, cursor="hand2")
            skip_tog.pack(side=tk.LEFT)
            tk.Label(ctrl, text=f"  {mode_lbl}  \xb7  {eff_str} / run",
                     font=("Segoe UI", 9),
                     bg=C["card"], fg=C["text_dim"]).pack(side=tk.LEFT, padx=(12, 0))

            def _toggle_skip(e):
                self.rbh_skip_on.set(not self.rbh_skip_on.get())
                self.show_tab("dungeons")
            skip_tog.bind("<Button-1>", _toggle_skip)

            chips_f = tk.Frame(info, bg=C["card"])
            chips_f.pack(fill=tk.X)

            runs_d = f"{r_hr:.1f}" if r_hr else "—"
            _chip(chips_f, "Runs / hr",        runs_d,                                     dg["color"])
            _chip(chips_f, "Gold Bars / hr",   f"{r_hr*2:.0f}" if r_hr else "—",     C["green"])
            _chip(chips_f, "Ygg Core / hr",    self.fmt(ygg_val) if ygg_val else "—", "#a371f7")
            _chip(chips_f, "TOTAL Tera / hr",  self.fmt(total)   if total   else "—", C["cyan"])
            if rec_p:
                _chip(chips_f, "Records (chance)", self.fmt(rec_p), "#f778ba")

        else:
            ctrl2 = tk.Frame(info, bg=C["card"])
            ctrl2.pack(fill=tk.X, pady=(0, 8))
            self._time_input(ctrl2, dg["id"], C["card"],
                             on_change=lambda d=dg, sr=stats_row:
                             self._refresh_spiral_card_stats(d, sr)
                             ).pack(side=tk.LEFT, padx=(0, 18))

            run_s   = self.get_secs(dg["id"])
            eff_str = self.secs_to_minsec(run_s) if run_s else "not set"
            tk.Label(ctrl2, text=f"  {eff_str} / run",
                     font=("Segoe UI", 9),
                     bg=C["card"], fg=C["text_dim"]).pack(side=tk.LEFT, padx=(4, 0))

            p0      = self.get_price(dg["drops"][0]["name"])
            r_hr    = self.runs_hr(dg["id"])
            t_hr    = self.tera_hr(dg["id"], p0 or 0)
            runs_d  = f"{r_hr:.1f}" if r_hr else "—"
            c_val   = self.fmt(p0 * r_hr) if (p0 and r_hr) else "—"
            t_str   = self.fmt(t_hr) if t_hr else "—"

            chips_f = tk.Frame(info, bg=C["card"])
            chips_f.pack(fill=tk.X)
            _chip(chips_f, "Runs / hr",       runs_d,  dg["color"])
            _chip(chips_f, "Cores / hr",      runs_d,  "#a371f7")
            _chip(chips_f, "Core Value / hr", c_val,   C["gold"])
            _chip(chips_f, "Est. Tera / hr",  t_str,   C["cyan"])

    def _open_spiral_detail(self, dg):
        for w in self.body.winfo_children():
            w.destroy()
        p = self._make_scroll_body(self.body)

        back = tk.Frame(p, bg=C["bg2"], pady=8, padx=16)
        back.pack(fill=tk.X)
        tk.Label(back, text="← Back to Dungeons",
                 font=("Segoe UI", 10),
                 bg=C["bg2"], fg=C["text_dim"],
                 cursor="hand2").pack(side=tk.LEFT).bind(
                     "<Button-1>", lambda e: self.show_tab("dungeons"))

        self._build_spiral_detail(p, dg)

    def _build_spiral_detail(self, p, dg):
        # Hero
        hero = tk.Frame(p, bg=C["bg2"])
        hero.pack(fill=tk.X)
        tk.Frame(hero, bg=dg["color"], height=3).pack(fill=tk.X)

        hero_inner = tk.Frame(hero, bg=C["bg2"], pady=20, padx=28)
        hero_inner.pack(fill=tk.X)

        hero_left = tk.Frame(hero_inner, bg=C["bg2"])
        hero_left.pack(side=tk.LEFT, fill=tk.Y)

        tk.Label(hero_left, text=dg["name"].upper(),
                 font=("Segoe UI", 9, "bold"),
                 bg=C["bg2"], fg=dg["color"]).pack(anchor="w")
        tk.Label(hero_left, text=dg["short"] + "  TRACKER",
                 font=("Segoe UI", 26, "bold"),
                 bg=C["bg2"], fg=C["text"]).pack(anchor="w", pady=(4, 0))
        tk.Label(hero_left, text=f"Boss:  {dg['boss']}",
                 font=("Segoe UI", 11),
                 bg=C["bg2"], fg=C["text_dim"]).pack(anchor="w", pady=(6, 0))

        hero_right = tk.Frame(hero_inner, bg=C["bg2"])
        hero_right.pack(side=tk.RIGHT)
        portrait_f = tk.Frame(hero_right, bg=C["bg2"])
        portrait_f.pack()
        self._load_boss_portrait(portrait_f, dg)

        tk.Frame(p, bg=dg["color"], height=1).pack(fill=tk.X)

        # Run time bar
        time_bar = tk.Frame(p, bg=C["card2"], pady=10, padx=28)
        time_bar.pack(fill=tk.X)
        tk.Label(time_bar, text="RUN  TIME",
                 font=("Segoe UI", 7, "bold"),
                 bg=C["card2"], fg=C["text_muted"]).pack(side=tk.LEFT, padx=(0, 24))

        def _refresh(d=dg):
            self._refresh_spiral_stats(d, p)

        self._time_input(time_bar, dg["id"], C["card2"],
                         on_change=_refresh).pack(side=tk.LEFT)
        tk.Label(time_bar, text="M:SS — updates runs/hr and Tera/hr automatically",
                 font=("Segoe UI", 8),
                 bg=C["card2"], fg=C["text_muted"]).pack(side=tk.RIGHT)

        tk.Frame(p, bg=C["border"], height=1).pack(fill=tk.X)

        # Stat cards
        body = tk.Frame(p, bg=C["bg"], pady=22, padx=28)
        body.pack(fill=tk.BOTH, expand=True)

        grid = tk.Frame(body, bg=C["bg"])
        grid.pack(fill=tk.X)

        drop    = dg["drops"][0]
        price   = self.get_price(drop["name"]) or 0
        r_hr    = self.runs_hr(dg["id"])
        t_hr    = self.tera_hr(dg["id"], price)
        run_s   = self.get_secs(dg["id"])
        t_str   = self.secs_to_minsec(run_s) if run_s else "not set"
        cores_h = f"{r_hr:.1f}" if r_hr else "—"
        t_val   = f"{t_hr/1_000_000:.2f}T" if t_hr else "—"

        cards = [
            ("Runs / Hour",    cores_h,                          dg["color"], f"Based on {t_str} per run"),
            ("Cores / Hour",   cores_h,                          "#a371f7",   f"1 {drop['name']} per clear"),
            ("Core Price",     self.fmt(price) if price else "—",
                                                                 C["gold"],   "Latest logged market price"),
            ("Est. Tera / hr", t_val,                            C["cyan"],   "Core price \xd7 runs/hr"),
        ]

        for i, (label, value, color, note) in enumerate(cards):
            self._stat_card(grid, 0, i, label, value, color, note, dg["color"])

        for col in range(4):
            grid.grid_columnconfigure(col, weight=1)

        note_strip = tk.Frame(body, bg=C["card"],
                              highlightbackground=C["border"], highlightthickness=1)
        note_strip.pack(fill=tk.X, pady=(18, 0))
        tk.Frame(note_strip, bg=dg["color"], width=4).pack(side=tk.LEFT, fill=tk.Y)
        tk.Label(note_strip,
                 text=f"  ℹ   {drop['name']} is a guaranteed drop every clear.  "
                      "Set your run time above to calculate accurate Tera/hr.  "
                      "Run Price Scanner to keep values current.",
                 font=("Segoe UI", 9),
                 bg=C["card"], fg=C["text_dim"],
                 pady=10, wraplength=900, justify="left").pack(side=tk.LEFT)

        self._build_drops_panel(body, dg)

    def _refresh_spiral_stats(self, dg, p):
        """Rebuild the spiral detail view after a run time change."""
        for w in p.winfo_children():
            w.destroy()
        back = tk.Frame(p, bg=C["bg2"], pady=8, padx=16)
        back.pack(fill=tk.X)
        tk.Label(back, text="← Back to Dungeons",
                 font=("Segoe UI", 10),
                 bg=C["bg2"], fg=C["text_dim"],
                 cursor="hand2").pack(side=tk.LEFT).bind(
                     "<Button-1>", lambda e: self.show_tab("dungeons"))
        self._build_spiral_detail(p, dg)

    def _refresh_spiral_card_stats(self, dg, stats_row):
        if dg["id"] == "rbh":
            base  = self.get_secs("rbh_full")
            skip  = self.rbh_skip_on.get()
            eff   = (base - 120) if (skip and base > 120) else base
            r_hr  = round(3600 / eff, 2) if eff > 0 else 0
            ygg_p = self.get_price("Yggdrasil Core") or 0
            t_hr  = r_hr * (ygg_p + 2_000_000)
        else:
            price = self.get_price(dg["drops"][0]["name"]) or 0
            t_hr  = self.tera_hr(dg["id"], price)
        t_val = t_hr / 1_000_000 if t_hr else 0
        t_str = f"{t_val:.2f}T" if t_hr else "—  set run time"
        t_clr = C["cyan"] if t_hr else C["text_muted"]
        for w in stats_row.winfo_children():
            for child in w.winfo_children():
                if hasattr(child, "_tera_dg_id") and child._tera_dg_id == dg["id"]:
                    child.config(text=t_str, fg=t_clr)

    # ══════════════════════════════════════════════════════════════════════════
    # PRICE HISTORY
    # ══════════════════════════════════════════════════════════════════════════

    def _build_history(self):
        p = self.body

        hdr = tk.Frame(p, bg=C["bg2"], pady=16, padx=28)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="PRICE  HISTORY",
                 font=("Segoe UI", 22, "bold"),
                 bg=C["bg2"], fg=C["green"]).pack(side=tk.LEFT)
        tk.Frame(p, bg=C["border"], height=1).pack(fill=tk.X)

        wrap = tk.Frame(p, bg=C["bg"])
        wrap.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(wrap, bg=C["bg"], highlightthickness=0)
        sb     = ttk.Scrollbar(wrap, orient=tk.VERTICAL,
                               command=canvas.yview,
                               style="Nexus.Vertical.TScrollbar")
        sf     = tk.Frame(canvas, bg=C["bg"])
        sf.bind("<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        win = canvas.create_window((0, 0), window=sf, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfig(win, width=e.width))
        canvas.bind_all("<MouseWheel>",
                        lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        for item in PRICE_ITEMS:
            name    = item["name"]
            history = self.price_hist.get(name, [])
            latest  = self.get_price(name)

            sec = tk.Frame(sf, bg=C["bg"])
            sec.pack(fill=tk.X, pady=(10, 0), padx=18)

            hdr_f = tk.Frame(sec, bg=C["card"],
                             highlightbackground=C["border_hi"],
                             highlightthickness=1)
            hdr_f.pack(fill=tk.X)
            tk.Frame(hdr_f, bg=C["cyan"], width=4).pack(side=tk.LEFT, fill=tk.Y)

            h_in = tk.Frame(hdr_f, bg=C["card"], pady=12, padx=16)
            h_in.pack(side=tk.LEFT, fill=tk.X, expand=True)

            tk.Label(h_in, text=name,
                     font=("Segoe UI", 13, "bold"),
                     bg=C["card"], fg=C["text"]).pack(side=tk.LEFT)

            tk.Label(h_in,
                     text=self.fmt(latest) if latest else "No data",
                     font=("Segoe UI", 13, "bold"),
                     bg=C["card"],
                     fg=C["gold"] if latest else C["text_muted"]).pack(side=tk.RIGHT)

            if not history:
                row = tk.Frame(sec, bg=C["bg"],
                               highlightbackground=C["border"], highlightthickness=1)
                row.pack(fill=tk.X)
                tk.Label(row,
                         text="   No entries yet — run the Price Scanner",
                         font=("Segoe UI", 9),
                         bg=C["bg"], fg=C["text_muted"], pady=9).pack(anchor="w")
            else:
                for entry in reversed(history[-12:]):
                    ts    = entry.get("timestamp", "")[:16].replace("T", "   ")
                    price = entry.get("price", 0)
                    row   = tk.Frame(sec, bg=C["bg"],
                                     highlightbackground=C["border"],
                                     highlightthickness=1)
                    row.pack(fill=tk.X)
                    r_in = tk.Frame(row, bg=C["bg"], pady=7, padx=22)
                    r_in.pack(fill=tk.X)

                    tk.Label(r_in, text=ts,
                             font=("Consolas", 9),
                             bg=C["bg"], fg=C["text_muted"]).pack(side=tk.LEFT)

                    tk.Label(r_in,
                             text=self.fmt(price),
                             font=("Segoe UI", 11, "bold"),
                             bg=C["bg"], fg=C["gold"]).pack(side=tk.RIGHT)

        tk.Frame(sf, height=16, bg=C["bg"]).pack()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _nexus_btn(self, parent, text, bg, fg, cmd, state=tk.NORMAL):
        return tk.Button(parent, text=text,
                         font=("Segoe UI", 10, "bold"),
                         bg=bg, fg=fg,
                         relief=tk.FLAT, padx=16, pady=8,
                         cursor="hand2", state=state,
                         activebackground=bg,
                         command=cmd)

    def _stat_card(self, parent, row, col, label, value, color, note, accent):
        card = tk.Frame(parent, bg=C["card"],
                        highlightbackground=C["border"], highlightthickness=1)
        card.grid(row=row, column=col, padx=7, pady=7, sticky="nsew")

        tk.Frame(card, bg=accent if label == "TOTAL  Tera / hr" else color,
                 height=3).pack(fill=tk.X)

        inner = tk.Frame(card, bg=C["card"], pady=14, padx=16)
        inner.pack(fill=tk.BOTH)

        tk.Label(inner, text=label,
                 font=("Segoe UI", 10, "bold"),
                 bg=C["card"], fg=C["text_dim"]).pack(anchor="w")

        tk.Label(inner, text=value,
                 font=("Segoe UI", 20, "bold"),
                 bg=C["card"], fg=color).pack(anchor="w", pady=(6, 4))

        tk.Label(inner, text=note,
                 font=("Segoe UI", 9),
                 bg=C["card"], fg=C["text_dim"]).pack(anchor="w")

    def _time_input(self, parent, key, bg, on_change=None):
        frame = tk.Frame(parent, bg=bg)

        tk.Label(frame, text="Run Time  ✎ click to edit",
                 font=("Segoe UI", 7, "bold"),
                 bg=bg, fg=C["text_muted"]).pack(anchor="w")

        entry_row = tk.Frame(frame, bg=bg)
        entry_row.pack(anchor="w", pady=(2, 0))

        var = tk.StringVar(value=self.secs_to_minsec(self.get_secs(key)))
        entry = tk.Entry(entry_row, textvariable=var,
                         font=("Consolas", 13, "bold"),
                         bg=C["card2"], fg=C["cyan"],
                         insertbackground=C["cyan"],
                         highlightbackground=C["border"],
                         highlightthickness=1,
                         relief=tk.FLAT, width=6,
                         justify="center")
        entry.pack(side=tk.LEFT)
        tk.Label(entry_row, text=" M:SS  then Enter",
                 font=("Segoe UI", 8),
                 bg=bg, fg=C["text_muted"]).pack(side=tk.LEFT)

        def _commit(event=None):
            secs = self.minsec_to_secs(var.get())
            self.set_secs(key, secs)
            var.set(self.secs_to_minsec(secs) if secs else "")
            rph = self.runs_hr(key)
            rph_text = f"{rph:.1f} runs/hr" if rph else "— type time above, press Enter"
            rph_lbl.config(text=rph_text,
                           fg=C["text"] if rph else C["text_muted"])
            if on_change:
                on_change()

        def _focus_in(e):
            entry.config(highlightbackground=C["cyan"], highlightthickness=1)
        def _focus_out(e):
            entry.config(highlightbackground=C["border"], highlightthickness=1)
            _commit()

        entry.bind("<Return>",      _commit)
        entry.bind("<FocusIn>",     _focus_in)
        entry.bind("<FocusOut>",    _focus_out)

        rph = self.runs_hr(key)
        rph_lbl = tk.Label(frame,
                           text=f"{rph:.1f} runs/hr" if rph else "— set time above",
                           font=("Segoe UI", 9),
                           bg=bg,
                           fg=C["text"] if rph else C["text_muted"])
        rph_lbl.pack(anchor="w", pady=(3, 0))
        return frame

    # ══════════════════════════════════════════════════════════════════════════
    # COMPARE
    # ══════════════════════════════════════════════════════════════════════════

    def _build_compare(self):
        p = self._make_scroll_body(self.body)

        hdr = tk.Frame(p, bg=C["bg2"], pady=16, padx=28)
        hdr.pack(fill=tk.X)

        hdr_left = tk.Frame(hdr, bg=C["bg2"])
        hdr_left.pack(side=tk.LEFT, fill=tk.Y)
        tk.Label(hdr_left, text="COMPARE",
                 font=("Segoe UI", 22, "bold"),
                 bg=C["bg2"], fg=C["gold"]).pack(anchor="w")
        tk.Label(hdr_left,
                 text="Estimated Tera / hr per dungeon  —  requires scanned prices + run times",
                 font=("Segoe UI", 9),
                 bg=C["bg2"], fg=C["text_dim"]).pack(anchor="w", pady=(4, 0))

        self._nexus_btn(hdr, "⟳  Refresh", C["border_hi"], C["text"],
                        lambda: self.show_tab("compare")).pack(side=tk.RIGHT, anchor="e")

        tk.Frame(p, bg=C["border"], height=1).pack(fill=tk.X)

        rows = []

        for mode in ("full", "skip"):
            key   = f"rbh_{mode}"
            t_hr  = self.rbh_tera_hr(mode)
            r_hr  = self.runs_hr(key)
            label = f"RBH — {'Full Run' if mode == 'full' else 'Skip Run'}"
            dg    = DUNGEONS[0]
            rows.append({
                "label":    label,
                "color":    dg["color"],
                "short":    f"RBH {'Full' if mode == 'full' else 'Skip'}",
                "runs_hr":  r_hr,
                "drop":     "Yggdrasil Core + 2\xd7 Gold Bar",
                "price":    (self.get_price("Yggdrasil Core") or 0) + 2_000_000,
                "tera_hr":  t_hr,
                "key":      key,
                "tab":      "dungeons",
                "boss_img": dg["boss_img"],
            })

        for dg in DUNGEONS[1:]:
            drop  = dg["drops"][0]
            price = self.get_price(drop["name"]) or 0
            t_hr  = self.tera_hr(dg["id"], price)
            r_hr  = self.runs_hr(dg["id"])
            rows.append({
                "label":    dg["name"],
                "color":    dg["color"],
                "short":    dg["short"],
                "runs_hr":  r_hr,
                "drop":     drop["name"],
                "price":    price,
                "tera_hr":  t_hr,
                "key":      dg["id"],
                "tab":      "dungeons",
                "boss_img": dg["boss_img"],
            })

        rows.sort(key=lambda r: r["tera_hr"], reverse=True)
        max_t = max((r["tera_hr"] for r in rows), default=1) or 1

        wrap = tk.Frame(p, bg=C["bg"])
        wrap.pack(fill=tk.BOTH, expand=True, padx=18, pady=12)

        rank_colors = ["#f0c040", "#c0c8d8", "#cd7f32"]

        for i, row in enumerate(rows):
            rank_fg = rank_colors[i] if i < 3 else C["text_muted"]
            self._compare_row(wrap, i + 1, row, rank_fg, max_t)

        rec_p = self.get_price("Yggdrasil's Records") or 0
        note  = tk.Frame(wrap, bg=C["card"],
                         highlightbackground=C["border"], highlightthickness=1)
        note.pack(fill=tk.X, pady=(14, 0))
        tk.Frame(note, bg=C["gold_dim"], width=4).pack(side=tk.LEFT, fill=tk.Y)
        rec_text = (f"  ❖  Yggdrasil's Records  (RBH chance drop) — "
                    f"latest price: {self.fmt(rec_p) if rec_p else 'not scanned'}  "
                    "  Not included in RBH Tera/hr total.")
        tk.Label(note, text=rec_text,
                 font=("Segoe UI", 9),
                 bg=C["card"], fg=C["text_dim"],
                 pady=10).pack(side=tk.LEFT)

    def _compare_row(self, parent, rank, row, rank_fg, max_t):
        card = tk.Frame(parent, bg=C["card"],
                        highlightbackground=row["color"], highlightthickness=1)
        card.pack(fill=tk.X, pady=4)
        tk.Frame(card, bg=row["color"], height=2).pack(fill=tk.X)

        inner = tk.Frame(card, bg=C["card"], pady=8, padx=18)
        inner.pack(fill=tk.X)

        img = self._load_img(row.get("boss_img", ""), size=(52, 62))
        if img:
            img_frame = tk.Frame(inner, bg=row["color"], padx=1, pady=1)
            img_frame.pack(side=tk.LEFT, padx=(0, 14))
            tk.Label(img_frame, image=img, bg=C["bg2"]).pack()
        else:
            tk.Frame(inner, bg=row["color"], width=4).pack(side=tk.LEFT, fill=tk.Y, padx=(0, 14))

        tk.Label(inner, text=f"#{rank}",
                 font=("Segoe UI", 13, "bold"),
                 bg=C["card"], fg=rank_fg, width=3).pack(side=tk.LEFT)

        chip = tk.Label(inner, text=f" {row['short']} ",
                        font=("Segoe UI", 9, "bold"),
                        bg=row["color"], fg=C["bg"],
                        padx=6, pady=2)
        chip.pack(side=tk.LEFT, padx=(6, 14))

        info = tk.Frame(inner, bg=C["card"])
        info.pack(side=tk.LEFT, fill=tk.Y)
        tk.Label(info, text=row["label"],
                 font=("Segoe UI", 11, "bold"),
                 bg=C["card"], fg=C["text"]).pack(anchor="w")
        price_txt = self.fmt(row["price"]) if row["price"] else "price not scanned"
        tk.Label(info,
                 text=f"{row['drop']}  —  {price_txt}",
                 font=("Segoe UI", 9),
                 bg=C["card"], fg=C["text_dim"]).pack(anchor="w")

        rph_txt = (f"{row['runs_hr']:.1f} runs/hr"
                   if row["runs_hr"] else "run time not set")
        tk.Label(info, text=rph_txt,
                 font=("Segoe UI", 8),
                 bg=C["card"], fg=C["text_muted"]).pack(anchor="w")

        right = tk.Frame(inner, bg=C["card"])
        right.pack(side=tk.RIGHT, anchor="e")

        if row["tera_hr"] > 0:
            t_val = row["tera_hr"] / 1_000_000
            t_str = f"{t_val:.1f}T / hr" if t_val >= 10 else f"{t_val:.2f}T / hr"
            fg = C["cyan"] if rank == 1 else (C["gold"] if rank <= 3 else C["text"])
        else:
            t_str = "—"
            fg    = C["text_muted"]

        tk.Label(right, text=t_str,
                 font=("Segoe UI", 18, "bold"),
                 bg=C["card"], fg=fg).pack(anchor="e")

        bar_w = 260
        pct   = (row["tera_hr"] / max_t) if max_t > 0 else 0
        cv    = tk.Canvas(right, width=bar_w, height=5,
                          bg=C["bg"], highlightthickness=0)
        cv.pack(anchor="e", pady=(4, 0))
        cv.create_rectangle(0, 0, int(bar_w * pct), 5,
                            fill=row["color"], width=0)

    # ══════════════════════════════════════════════════════════════════════════
    # INVENTORY
    # ══════════════════════════════════════════════════════════════════════════

    def _build_inventory(self):
        p = self._make_scroll_body(self.body)

        hdr = tk.Frame(p, bg=C["bg2"], pady=18, padx=28)
        hdr.pack(fill=tk.X)

        hdr_left = tk.Frame(hdr, bg=C["bg2"])
        hdr_left.pack(side=tk.LEFT, fill=tk.Y)
        tk.Label(hdr_left, text="INVENTORY",
                 font=("Segoe UI", 22, "bold"),
                 bg=C["bg2"], fg=C["gold"]).pack(anchor="w")
        tk.Label(hdr_left,
                 text="Enter your stack counts  —  values calculated from latest scan prices",
                 font=("Segoe UI", 9),
                 bg=C["bg2"], fg=C["text_dim"]).pack(anchor="w", pady=(4, 0))

        self._nexus_btn(hdr, "↺  Clear All", C["border_hi"], C["text"],
                        self._inv_clear).pack(side=tk.RIGHT, anchor="e", padx=(12, 0))

        # T balance + grand total box
        t_box = tk.Frame(hdr, bg=C["card2"],
                         highlightbackground=C["cyan"], highlightthickness=1)
        t_box.pack(side=tk.RIGHT, anchor="e")
        tk.Frame(t_box, bg=C["cyan"], height=2).pack(fill=tk.X)
        t_inner = tk.Frame(t_box, bg=C["card2"], padx=14, pady=10)
        t_inner.pack()

        # Left: account T input
        acct_f = tk.Frame(t_inner, bg=C["card2"])
        acct_f.pack(side=tk.LEFT, padx=(0, 18))
        tk.Label(acct_f, text="ACCOUNT T",
                 font=("Segoe UI", 7, "bold"),
                 bg=C["card2"], fg=C["text_muted"]).pack(anchor="w")
        t_var = tk.StringVar(value=f"{self.account_t:.2f}" if self.account_t else "")
        t_entry = tk.Entry(acct_f, textvariable=t_var,
                           font=("Segoe UI", 18, "bold"),
                           bg=C["card2"], fg=C["cyan"],
                           insertbackground=C["cyan"],
                           relief=tk.FLAT, width=8, justify="center")
        t_entry.pack()
        tk.Label(acct_f, text="click to edit",
                 font=("Segoe UI", 7),
                 bg=C["card2"], fg=C["text_muted"]).pack(anchor="w")

        # Divider
        tk.Frame(t_inner, bg=C["border"], width=1).pack(side=tk.LEFT, fill=tk.Y, padx=(0, 18))

        # Middle: inventory value
        inv_f = tk.Frame(t_inner, bg=C["card2"])
        inv_f.pack(side=tk.LEFT, padx=(0, 18))
        tk.Label(inv_f, text="INVENTORY VALUE",
                 font=("Segoe UI", 7, "bold"),
                 bg=C["card2"], fg=C["text_muted"]).pack(anchor="w")
        self._inv_val_display = tk.Label(inv_f, text=self._inv_total_str(),
                                         font=("Segoe UI", 18, "bold"),
                                         bg=C["card2"], fg=C["gold"])
        self._inv_val_display.pack()
        tk.Label(inv_f, text="from item stacks",
                 font=("Segoe UI", 7),
                 bg=C["card2"], fg=C["text_muted"]).pack(anchor="w")

        # Divider
        tk.Frame(t_inner, bg=C["border"], width=1).pack(side=tk.LEFT, fill=tk.Y, padx=(0, 18))

        # Right: grand total
        grand_f = tk.Frame(t_inner, bg=C["card2"])
        grand_f.pack(side=tk.LEFT)
        tk.Label(grand_f, text="GRAND TOTAL",
                 font=("Segoe UI", 7, "bold"),
                 bg=C["card2"], fg=C["text_muted"]).pack(anchor="w")
        self._grand_total_lbl = tk.Label(grand_f, text=self._grand_total_str(),
                                          font=("Segoe UI", 18, "bold"),
                                          bg=C["card2"], fg=C["cyan"])
        self._grand_total_lbl.pack()
        tk.Label(grand_f, text="account + inventory",
                 font=("Segoe UI", 7),
                 bg=C["card2"], fg=C["text_muted"]).pack(anchor="w")

        def _commit_t(e=None):
            try:
                val = float(t_var.get().replace("T", "").replace(",", "").strip())
            except ValueError:
                val = self.account_t
            self.account_t = val
            self.save_data()
            t_var.set(f"{val:.2f}" if val else "")
            if hasattr(self, "_grand_total_lbl"):
                self._grand_total_lbl.config(text=self._grand_total_str())

        t_entry.bind("<Return>",   _commit_t)
        t_entry.bind("<FocusOut>", _commit_t)

        tk.Frame(p, bg=C["border"], height=1).pack(fill=tk.X)

        col_hdr = tk.Frame(p, bg=C["card2"], pady=6, padx=28)
        col_hdr.pack(fill=tk.X)
        for text, anchor, side in [
            ("ITEM",       "w", tk.LEFT),
            ("LAST PRICE", "e", tk.RIGHT),
            ("QTY",        "e", tk.RIGHT),
            ("VALUE",      "e", tk.RIGHT),
        ]:
            tk.Label(col_hdr, text=text,
                     font=("Segoe UI", 7, "bold"),
                     bg=C["card2"], fg=C["text_muted"],
                     width=16 if text == "ITEM" else 10,
                     anchor=anchor).pack(side=side, padx=(0, 24))

        tk.Frame(p, bg=C["border"], height=1).pack(fill=tk.X)

        self._inv_value_lbls = {}
        self._inv_vars       = {}

        for item in INV_ITEMS:
            self._build_inv_row(p, item)

        # ── Custom items section ──────────────────────────────────────────────
        tk.Frame(p, bg=C["border"], height=1).pack(fill=tk.X)

        cust_hdr = tk.Frame(p, bg=C["bg2"], pady=10, padx=28)
        cust_hdr.pack(fill=tk.X)
        tk.Label(cust_hdr, text="CUSTOM ITEMS",
                 font=("Segoe UI", 9, "bold"),
                 bg=C["bg2"], fg=C["text_dim"]).pack(side=tk.LEFT)
        tk.Label(cust_hdr, text="Add anything else in your inventory with a manual T value",
                 font=("Segoe UI", 8),
                 bg=C["bg2"], fg=C["text_muted"]).pack(side=tk.LEFT, padx=(12, 0))

        self._custom_body = tk.Frame(p, bg=C["bg"])
        self._custom_body.pack(fill=tk.X)
        self._refresh_custom_rows()

        add_row = tk.Frame(p, bg=C["bg"], pady=8, padx=28)
        add_row.pack(fill=tk.X)
        self._nexus_btn(add_row, "+  Add Item", C["border_hi"], C["text"],
                        self._add_custom_item).pack(side=tk.LEFT)

        tk.Frame(p, bg=C["border"], height=1).pack(fill=tk.X)

    def _build_inv_row(self, parent, item):
        name    = item["name"]
        price   = self.get_price(name)
        qty     = self.inv_qty.get(name, 0)

        row = tk.Frame(parent, bg=C["bg"],
                       highlightbackground=C["border"], highlightthickness=1)
        row.pack(fill=tk.X)
        inner = tk.Frame(row, bg=C["bg"], pady=11, padx=28)
        inner.pack(fill=tk.X)

        tk.Label(inner, text=name,
                 font=("Segoe UI", 11),
                 bg=C["bg"], fg=C["text"],
                 width=22, anchor="w").pack(side=tk.LEFT)

        val_lbl = tk.Label(inner,
                           text=self._inv_row_val(price, qty),
                           font=("Segoe UI", 12, "bold"),
                           bg=C["bg"],
                           fg=C["gold"] if (price and qty) else C["text_muted"],
                           width=12, anchor="e")
        val_lbl.pack(side=tk.RIGHT)

        var = tk.IntVar(value=qty)
        entry = tk.Entry(inner, textvariable=var,
                         font=("Consolas", 12, "bold"),
                         bg=C["card2"], fg=C["cyan"],
                         insertbackground=C["cyan"],
                         relief=tk.FLAT, width=6,
                         justify="center")
        entry.pack(side=tk.RIGHT, padx=(0, 32))

        tk.Label(inner,
                 text=self.fmt(price) if price else "—",
                 font=("Segoe UI", 11),
                 bg=C["bg"],
                 fg=C["text_dim"] if price else C["text_muted"],
                 width=10, anchor="e").pack(side=tk.RIGHT, padx=(0, 24))

        def _commit(e=None, n=name, v=var, vl=val_lbl):
            try:
                q = max(0, int(v.get()))
            except Exception:
                q = 0
            v.set(q)
            self.inv_qty[n] = q
            self.save_data()
            p = self.get_price(n)
            vl.config(text=self._inv_row_val(p, q),
                      fg=C["gold"] if (p and q) else C["text_muted"])
            self._refresh_inv_totals()

        entry.bind("<Return>",   _commit)
        entry.bind("<FocusOut>", _commit)

        self._inv_vars[name]       = var
        self._inv_value_lbls[name] = val_lbl

        for w in (row, inner):
            w.bind("<Enter>", lambda e, x=[row, inner]: [i.config(bg=C["card"]) for i in x])
            w.bind("<Leave>", lambda e, x=[row, inner]: [i.config(bg=C["bg"])   for i in x])

    def _inv_row_val(self, price, qty):
        if not price or not qty:
            return "—"
        return self.fmt(price * qty)

    def _inv_total_str(self):
        total = sum(
            (self.get_price(it["name"]) or 0) * self.inv_qty.get(it["name"], 0)
            for it in INV_ITEMS
        )
        total += sum(
            int(ci.get("price_t", 0) * 1_000_000) * ci.get("qty", 0)
            for ci in self.custom_inv
        )
        return self.fmt(total) if total else "—"

    def _grand_total_str(self):
        inv_raw  = sum(
            (self.get_price(it["name"]) or 0) * self.inv_qty.get(it["name"], 0)
            for it in INV_ITEMS
        )
        inv_raw += sum(
            int(ci.get("price_t", 0) * 1_000_000) * ci.get("qty", 0)
            for ci in self.custom_inv
        )
        acct_raw = int(self.account_t * 1_000_000)
        total    = acct_raw + inv_raw
        return self.fmt(total) if total else "—"

    def _inv_clear(self):
        for name in self.inv_qty:
            self.inv_qty[name] = 0
        self.save_data()
        self.show_tab("inventory")

    def _refresh_inv_totals(self):
        if hasattr(self, "_inv_val_display"):
            self._inv_val_display.config(text=self._inv_total_str())
        if hasattr(self, "_inv_total_lbl"):
            self._inv_total_lbl.config(text=self._inv_total_str())
        if hasattr(self, "_grand_total_lbl"):
            self._grand_total_lbl.config(text=self._grand_total_str())

    def _add_custom_item(self):
        self.custom_inv.append({"name": "New Item", "qty": 1, "price_t": 0.0})
        self.save_data()
        self._refresh_custom_rows()
        self._refresh_inv_totals()

    def _delete_custom_item(self, idx):
        if 0 <= idx < len(self.custom_inv):
            self.custom_inv.pop(idx)
            self.save_data()
            self._refresh_custom_rows()
            self._refresh_inv_totals()

    def _refresh_custom_rows(self):
        if not hasattr(self, "_custom_body"):
            return
        for w in self._custom_body.winfo_children():
            w.destroy()
        if not self.custom_inv:
            tk.Label(self._custom_body,
                     text="   No custom items yet — click '+ Add Item' below",
                     font=("Segoe UI", 9),
                     bg=C["bg"], fg=C["text_muted"], pady=10).pack(anchor="w", padx=28)
            return
        for i, ci in enumerate(self.custom_inv):
            self._build_custom_row(self._custom_body, i, ci)

    def _build_custom_row(self, parent, idx, ci):
        row   = tk.Frame(parent, bg=C["bg"],
                         highlightbackground=C["border"], highlightthickness=1)
        row.pack(fill=tk.X)
        inner = tk.Frame(row, bg=C["bg"], pady=9, padx=28)
        inner.pack(fill=tk.X)

        # Delete button
        del_btn = tk.Label(inner, text=" × ",
                           font=("Segoe UI", 11, "bold"),
                           bg=C["red"], fg=C["white"],
                           padx=4, cursor="hand2")
        del_btn.pack(side=tk.RIGHT, padx=(8, 0))
        del_btn.bind("<Button-1>", lambda e, i=idx: self._delete_custom_item(i))

        # Value label (right side)
        raw_val = int(ci.get("price_t", 0) * 1_000_000) * ci.get("qty", 0)
        val_lbl = tk.Label(inner,
                           text=self.fmt(raw_val) if raw_val else "—",
                           font=("Segoe UI", 12, "bold"),
                           bg=C["bg"],
                           fg=C["gold"] if raw_val else C["text_muted"],
                           width=10, anchor="e")
        val_lbl.pack(side=tk.RIGHT, padx=(8, 0))

        # Price per item entry
        price_var = tk.StringVar(value=f"{ci.get('price_t', 0):.2f}" if ci.get("price_t") else "")
        price_entry = tk.Entry(inner, textvariable=price_var,
                               font=("Consolas", 11, "bold"),
                               bg=C["card2"], fg=C["gold"],
                               insertbackground=C["gold"],
                               relief=tk.FLAT, width=7, justify="center")
        price_entry.pack(side=tk.RIGHT, padx=(0, 4))
        tk.Label(inner, text="T each",
                 font=("Segoe UI", 8),
                 bg=C["bg"], fg=C["text_muted"]).pack(side=tk.RIGHT, padx=(0, 8))

        # Qty entry
        qty_var = tk.IntVar(value=ci.get("qty", 1))
        qty_entry = tk.Entry(inner, textvariable=qty_var,
                             font=("Consolas", 12, "bold"),
                             bg=C["card2"], fg=C["cyan"],
                             insertbackground=C["cyan"],
                             relief=tk.FLAT, width=6, justify="center")
        qty_entry.pack(side=tk.RIGHT, padx=(0, 28))

        # Name entry
        name_var = tk.StringVar(value=ci.get("name", ""))
        name_entry = tk.Entry(inner, textvariable=name_var,
                              font=("Segoe UI", 11),
                              bg=C["bg"], fg=C["text"],
                              insertbackground=C["text"],
                              relief=tk.FLAT, width=22)
        name_entry.pack(side=tk.LEFT)

        def _commit_custom(e=None, i=idx, nv=name_var, qv=qty_var, pv=price_var, vl=val_lbl):
            try:
                q = max(0, int(qv.get()))
            except Exception:
                q = 0
            try:
                pt = float(pv.get().replace("T", "").replace(",", "").strip())
            except Exception:
                pt = 0.0
            qv.set(q)
            pv.set(f"{pt:.2f}" if pt else "")
            self.custom_inv[i]["name"]    = nv.get().strip() or "Custom Item"
            self.custom_inv[i]["qty"]     = q
            self.custom_inv[i]["price_t"] = pt
            self.save_data()
            rv = int(pt * 1_000_000) * q
            vl.config(text=self.fmt(rv) if rv else "—",
                      fg=C["gold"] if rv else C["text_muted"])
            self._refresh_inv_totals()

        for w in (name_entry, qty_entry, price_entry):
            w.bind("<Return>",   _commit_custom)
            w.bind("<FocusOut>", _commit_custom)

        for w in (row, inner):
            w.bind("<Enter>", lambda e, x=[row,inner]: [i.config(bg=C["card"]) for i in x])
            w.bind("<Leave>", lambda e, x=[row,inner]: [i.config(bg=C["bg"])   for i in x])

    # ══════════════════════════════════════════════════════════════════════════
    # JSONBIN SYNC
    # ══════════════════════════════════════════════════════════════════════════

    def _sync_init(self):
        cfg = self._load_sync_config()
        # Always start sync — everyone gets the hardcoded prices gist at minimum
        threading.Thread(target=self._sync_loop, daemon=True).start()
        label = "⬡ Sync active" if cfg.get("token") else "⬡ Sync (read-only)"
        self.root.after(0, lambda: self._set_sync_status(label, C["cyan"]))

    def _load_sync_config(self):
        try:
            cfg_path = os.path.join(os.path.dirname(self.data_file), "sync_config.json")
            with open(cfg_path) as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_sync_config(self, cfg):
        try:
            cfg_path = os.path.join(os.path.dirname(self.data_file), "sync_config.json")
            with open(cfg_path, "w") as f:
                json.dump(cfg, f, indent=2)
        except Exception:
            pass

    def _sync_loop(self):
        while True:
            try:
                self._sync_pull()
            except Exception:
                pass
            time.sleep(SYNC_INTERVAL)

    def _sync_pull(self):
        cfg     = self._load_sync_config()
        token   = cfg.get("token", "")
        gist_id = cfg.get("gist_id", "") or PRICES_GIST_ID
        url     = f"https://api.github.com/gists/{gist_id}"
        headers = {"Accept": "application/vnd.github+json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                data    = json.loads(r.read().decode())
                content = data["files"]["dmw_prices.json"]["content"]
                remote  = json.loads(content)
        except Exception:
            return

        remote_hist = remote.get("price_history", {})
        updated = False
        for name, entries in remote_hist.items():
            if not entries:
                continue
            remote_latest = entries[-1]
            local_hist    = self.price_hist.get(name, [])
            local_ts      = local_hist[-1].get("timestamp", "") if local_hist else ""
            if remote_latest.get("timestamp", "") > local_ts:
                self.price_hist.setdefault(name, []).append(remote_latest)
                updated = True

        if updated:
            self.save_data()
            self.root.after(0, self._on_sync_update)

    def _sync_push(self):
        cfg = self._load_sync_config()
        if not cfg.get("token"):
            return
        threading.Thread(target=self._do_push, daemon=True).start()

    def _do_push(self):
        cfg     = self._load_sync_config()
        token   = cfg.get("token", "")
        gist_id = cfg.get("gist_id", "")
        if not token:
            return

        content = json.dumps({"price_history": self.price_hist}, indent=2)
        payload = json.dumps({
            "description": "DMW Tera Tracker — shared prices",
            "public":      True,
            "files": {"dmw_prices.json": {"content": content}},
        }).encode()
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept":        "application/vnd.github+json",
            "Content-Type":  "application/json",
        }
        try:
            if not gist_id:
                req = urllib.request.Request(
                    "https://api.github.com/gists",
                    data=payload, headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=10) as r:
                    resp    = json.loads(r.read().decode())
                    gist_id = resp["id"]
                cfg["gist_id"] = gist_id
                self._save_sync_config(cfg)
                self.root.after(0, lambda: self._set_sync_status("✓ Synced — gist created", C["green"]))
            else:
                req = urllib.request.Request(
                    f"https://api.github.com/gists/{gist_id}",
                    data=payload, headers=headers, method="PATCH")
                with urllib.request.urlopen(req, timeout=10) as r:
                    pass
                ts = datetime.now().strftime("%H:%M")
                self.root.after(0, lambda: self._set_sync_status(f"✓ Synced  {ts}", C["green"]))
        except Exception:
            self.root.after(0, lambda: self._set_sync_status("Sync failed", C["red"]))

    def _on_sync_update(self):
        ts = datetime.now().strftime("%H:%M")
        self._set_sync_status(f"↓ Prices updated from sync  {ts}", C["cyan"])
        tab = self.active_tab.get()
        if tab in ("scanner", "inventory", "compare"):
            self.show_tab(tab)

    def _set_sync_status(self, text, color=None):
        if hasattr(self, "sync_lbl"):
            self.sync_lbl.config(text=text, fg=color or C["text_muted"])


# ══════════════════════════════════════════════════════════════════════════════
def _load_cfg():
    try:
        path = os.path.join(os.path.expandvars("%LOCALAPPDATA%"),
                            "DMWTeraTracker", "sync_config.json")
        with open(path) as f:
            return json.load(f)
    except Exception:
        return {}

def _save_cfg(cfg):
    try:
        d = os.path.join(os.path.expandvars("%LOCALAPPDATA%"), "DMWTeraTracker")
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "sync_config.json"), "w") as f:
            json.dump(cfg, f, indent=2)
    except Exception:
        pass

def _show_denied(hwid):
    root = tk.Tk()
    root.title("DMW Base — Access Required")
    root.geometry("480x260")
    root.configure(bg="#06090f")
    root.resizable(False, False)
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    tk.Label(root, text="ACCESS  REQUIRED",
             font=("Segoe UI", 18, "bold"),
             bg="#06090f", fg="#f04060").pack(pady=(36, 8))
    tk.Label(root, text="This copy is not authorised on your machine.",
             font=("Segoe UI", 10),
             bg="#06090f", fg="#5a7090").pack()
    tk.Label(root, text="Send your Hardware ID to the owner to request access:",
             font=("Segoe UI", 10),
             bg="#06090f", fg="#5a7090").pack(pady=(18, 6))
    id_frame = tk.Frame(root, bg="#0d1520", padx=16, pady=10)
    id_frame.pack()
    tk.Label(id_frame, text=hwid,
             font=("Consolas", 16, "bold"),
             bg="#0d1520", fg="#00c8e8").pack(side=tk.LEFT)

    import pyperclip
    def _copy():
        try: pyperclip.copy(hwid)
        except Exception: pass
        copy_btn.config(text="Copied ✓")
    copy_btn = tk.Button(id_frame, text="Copy",
                         font=("Segoe UI", 9),
                         bg="#1a2a45", fg="#d8e4f8",
                         relief=tk.FLAT, padx=10, pady=4,
                         cursor="hand2", command=_copy)
    copy_btn.pack(side=tk.LEFT, padx=(12, 0))
    tk.Button(root, text="Close",
              font=("Segoe UI", 9),
              bg="#1a2a45", fg="#d8e4f8",
              relief=tk.FLAT, padx=20, pady=6,
              cursor="hand2", command=root.destroy).pack(pady=20)
    root.mainloop()

def main():
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    hwid = get_hwid()
    cfg  = _load_cfg()
    token          = cfg.get("token", "")
    whitelist_gist = cfg.get("whitelist_gist_id", WHITELIST_GIST_ID)

    allowed, wl_gist = check_auth(hwid, token, whitelist_gist)

    if wl_gist and wl_gist != whitelist_gist:
        cfg["whitelist_gist_id"] = wl_gist
        _save_cfg(cfg)

    if not allowed:
        _show_denied(hwid)
        return

    root = tk.Tk()
    DMWTeraTracker(root)
    root.mainloop()


if __name__ == "__main__":
    main()
