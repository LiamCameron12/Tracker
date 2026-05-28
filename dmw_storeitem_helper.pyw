"""
DMW Store Item Helper — GitHub-Inspired Edition
Sidebar navigation · Collapsible folders · Click to copy
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import threading
import urllib.request
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


class DMWStoreHelper:
    def __init__(self, root):
        self.root = root
        self.root.title("DMW Store Item Helper")
        self.root.geometry("1200x800")
        self.root.minsize(980, 620)

        self.colors = {
            'bg_dark':        '#0d1117',
            'bg_card':        '#161b22',
            'bg_hover':       '#21262d',
            'bg_button':      '#1f2937',
            'border':         '#30363d',
            'border_muted':   '#21262d',
            'accent_cyan':    '#00d4ff',
            'accent_green':   '#3fb950',
            'accent_red':     '#f85149',
            'accent_orange':  '#ff9500',
            'accent_purple':  '#a371f7',
            'accent_blue':    '#58a6ff',
            'accent_pink':    '#f778ba',
            'accent_yellow':  '#ffd700',
            'accent_white':   '#ffffff',
            'text_primary':   '#e6edf3',
            'text_secondary': '#8b949e',
            'text_muted':     '#484f58',
            'text_location':  '#ffcc00',
        }

        self.root.configure(bg=self.colors['bg_dark'])

        _data_dir = os.path.join(os.path.expandvars('%LOCALAPPDATA%'), 'DMWHelper')
        os.makedirs(_data_dir, exist_ok=True)
        self.data_file = os.path.join(_data_dir, 'dmw_custom_items.json')

        self.icon_cache = {}
        self.photo_refs = []

        # Tracks which category folders are collapsed
        self.collapsed_categories = set()

        # Tracks hidden built-in items (by name)
        self.hidden_items = set()

        # Tracks hidden sidebar category tabs (by category name)
        self.hidden_categories = set()

        # Tracks permanently deleted categories and items (persisted to JSON)
        self.deleted_categories = set()
        self.deleted_items = set()

        self.item_database = self.get_item_database()
        self.custom_items = self.load_custom_items()

        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self.filter_items())
        self.category_var = tk.StringVar(value="All")

        self.setup_ui()

        if HAS_PIL:
            threading.Thread(target=self.preload_icons, daemon=True).start()

    # ================================================================
    #  DATA
    # ================================================================

    def get_item_database(self):
        """Comprehensive item database"""
        wiki_base = "https://digitalmastersworld.wiki.gg/images/"

        return {
            # ==================== ESSENCES ====================
            "Essences": {
                "color": "#ff0066",
                "items": [
                    {"name": "Scar Essence", "command": ".storeitem Scar Essence",
                     "location": "Glacier Area", "icon": f"{wiki_base}Scar_Essence.png", "bulk": True},
                    {"name": "Piece [Uprising Flame]", "command": ".storeitem Piece [Uprising Flame]",
                     "location": "Glacier Area", "icon": f"{wiki_base}Piece_Uprising_Flame.png", "bulk": True},
                    {"name": "Energy of Steel", "command": ".storeitem Energy of Steel",
                     "location": "Glacier Area", "icon": f"{wiki_base}Energy_of_Steel.png", "bulk": True},
                    {"name": "Energy of Thunder God", "command": ".storeitem Energy of Thunder God",
                     "location": "Maze B2 Giromons", "icon": f"{wiki_base}Energy_of_Thunder_God_icon.png", "bulk": False},
                    {"name": "Wasteland Essence", "command": ".storeitem Wasteland Essence",
                     "location": "Wasteland Area (Digital Area)", "icon": f"{wiki_base}Wasteland_Essence.png", "bulk": True},
                    {"name": "Cloud Essence", "command": ".storeitem Cloud Essence",
                     "location": "Cloud Area (Digital Area)", "icon": f"{wiki_base}Cloud_Essence.png", "bulk": True},
                    {"name": "Forest Essence", "command": ".storeitem Forest Essence",
                     "location": "Forest Area (Digital Area)", "icon": f"{wiki_base}Forest_Essence.png", "bulk": True},
                    {"name": "Ocean Essence", "command": ".storeitem Ocean Essence",
                     "location": "Ocean Area (Digital Area)", "icon": f"{wiki_base}Ocean_Essence.png", "bulk": True},
                    {"name": "Beast Essence", "command": ".storeitem Beast Essence",
                     "location": "Four Holy Beast Area (Digital Area)", "icon": f"{wiki_base}Beast_Essence.png", "bulk": True},
                    {"name": "Chaotic Essence", "command": ".storeitem Chaotic Essence",
                     "location": "Wasteland Area, Cloud Area", "icon": f"{wiki_base}Chaotic_Essence.png", "bulk": True},
                    {"name": "Burning Essence", "command": ".storeitem Burning Essence",
                     "location": "Forest Area, Ocean Area", "icon": f"{wiki_base}Burning_Essence.png", "bulk": True},
                    {"name": "Final Essence", "command": ".storeitem Final Essence",
                     "location": "Collapsed Four Holy Beast Area", "icon": f"{wiki_base}Final_Essence.png", "bulk": True},
                    {"name": "Essence of Vikaralamon", "command": ".storeitem Essence of Vikaralamon",
                     "location": "Shinjuku Western Maps", "icon": f"{wiki_base}Essence_of_Vikaralamon.png", "bulk": True},
                    {"name": "Essence of Vajramon", "command": ".storeitem Essence of Vajramon",
                     "location": "Shinjuku East Maps", "icon": f"{wiki_base}Essence_of_Vajiramon.png", "bulk": True},
                    {"name": "Stadium Essence [Vajramon]", "command": ".storeitem Stadium Essence [Vajramon]",
                     "location": "Shinjuku East Maps", "icon": f"{wiki_base}Essence_of_Vajiramon.png", "bulk": True},
                    {"name": "Observatory Energy", "command": ".storeitem Observatory",
                     "location": "Tokyo Tower / Valley of Light", "icon": f"{wiki_base}Observatory_Energy.png", "bulk": False},
                    {"name": "Rooftop Energy", "command": ".storeitem Rooftop",
                     "location": "Fuji TV Rooftop / Shibuya", "icon": f"{wiki_base}Rooftop_Energy.png", "bulk": False},
                    {"name": "Vortex Energy", "command": ".storeitem Vortex Energy",
                     "location": "Big Sight", "icon": f"{wiki_base}Vortex_Energy.png", "bulk": False},
                    {"name": "Essence of Marine Dragon", "command": ".storeitem Essence of Marine Dragon",
                     "location": "Forest of the Beginning (Spiral Mountain)", "icon": f"{wiki_base}Marine_Essence.png", "bulk": True},
                    {"name": "Floras Essence", "command": ".storeitem Floras Essence",
                     "location": "Forest of Marionette (Spiral Mountain)", "icon": f"{wiki_base}Flora_Essence.png", "bulk": True},
                    {"name": "Metal Essence", "command": ".storeitem Metal Essence",
                     "location": "Metal Empire / Underground City", "icon": f"{wiki_base}Metalic_Essence.png", "bulk": True},
                    {"name": "Essence of Evolution", "command": ".storeitem Essence of Evolution",
                     "location": "Digital Area", "icon": None, "bulk": True},
                    {"name": "Scar Essence [Hard]", "command": ".storeitem Scar Essence [Hard]",
                     "location": "Glacier Area (Hard)", "icon": f"{wiki_base}Scar_Essence.png", "bulk": True},
                    {"name": "Nightmare Essence", "command": ".storeitem Nightmare Essence",
                     "location": "The Top of a Nightmare (Spiral Mountain)", "icon": f"{wiki_base}Nightmare_Essence.png", "bulk": True},
                    {"name": "Spiral Essence", "command": ".storeitem Spiral Essence",
                     "location": "Spiral Mountain Area (KeyRing Crafting)", "icon": f"{wiki_base}Spiral_Essence.png", "bulk": True},
                    {"name": "Raid Essence", "command": ".storeitem Raid Essence",
                     "location": "Spiral Mountain Dungeons", "icon": f"{wiki_base}Raid_Essence.png", "bulk": True},
                    {"name": "Yin and Yang Spirit", "command": ".storeitem Yin and Yang Spirit",
                     "location": "Verdandi Terminal", "icon": f"{wiki_base}Yin_and_Yang_Spirit.png", "bulk": True},
                ]
            },

            # ==================== DUNGEON CRYSTALS ====================
            "Dungeon Crystals": {
                "color": "#a371f7",
                "items": [
                    {"name": "Jack Frost of Water Crystal", "command": ".storeitem Jack Frost of Water Crystal",
                     "location": "EDGN Hard (Xuanwumon)", "icon": f"{wiki_base}Jack_Frost_of_Water_Crystal.png", "bulk": True},
                    {"name": "Uprising Infernal Flame Crystal", "command": ".storeitem Uprising Infernal Flame Crystal",
                     "location": "ZDGN Hard (Zhuqiaomon)", "icon": f"{wiki_base}Uprising_Infernal_Flame_Crystal.png", "bulk": True},
                    {"name": "Flawless Crystal of Trace", "command": ".storeitem Flawless Crystal of Trace",
                     "location": "BDGN Hard (Baihumon)", "icon": f"{wiki_base}Flawless_Crystal_of_Trace.png", "bulk": True},
                    {"name": "Thunder God's Lightning Crystal", "command": ".storeitem Thunder God's Lightning Crystal",
                     "location": "QDGN Hard (Qinglongmon)", "icon": f"{wiki_base}Thunder_Gods_Lightning_Crystal.png", "bulk": True},
                    {"name": "Crown of Greed", "command": ".storeitem Crown of Greed",
                     "location": "Chaotic Battle Field", "icon": f"{wiki_base}Crown_of_Greed.png", "bulk": True},
                    {"name": "Mark of Digital Hazard", "command": ".storeitem Mark of Digital Hazard",
                     "location": "Burning Battle Field", "icon": f"{wiki_base}Digital_Hazard.png", "bulk": True},
                    {"name": "Incandescent Flame", "command": ".storeitem Incandescent Flame",
                     "location": "Final Battle", "icon": f"{wiki_base}Phoenix_Fire.png", "bulk": True},
                ]
            },

            # ==================== SPIRAL CORES ====================
            "Spiral Cores": {
                "color": "#00b4d8",
                "items": [
                    {"name": "Marine Dragon Core", "command": ".storeitem Marine Dragon Core",
                     "location": "Marine Dragon Domain — MetalSeadramon (SSS)",
                     "icon": f"{wiki_base}Marine_Dragon_Core.png", "bulk": False},
                    {"name": "Wooden Puppet Core", "command": ".storeitem Wooden Puppet Core",
                     "location": "Front Yard of Marionette Mansion — Puppetmon (SSS)",
                     "icon": f"{wiki_base}Wooden_Puppet_Core.png", "bulk": False},
                    {"name": "Metallic Beast Core", "command": ".storeitem Metallic Beast Core",
                     "location": "Back of the Empire — MugenDramon (SSS)",
                     "icon": f"{wiki_base}Metalic_Beast_Core.png", "bulk": False},
                    {"name": "Cruelty Clown Core", "command": ".storeitem Cruelty Clown Core",
                     "location": "Stage of Clown — Piedmon (SSS)",
                     "icon": f"{wiki_base}Cruelty_Clown_Core.png", "bulk": False},
                    {"name": "Core of Nothingness", "command": ".storeitem Core of Nothingness",
                     "location": "Void Space Dungeon — Apocalymon (SSS)",
                     "icon": f"{wiki_base}Core_of_Nothingness.png", "bulk": False},
                ]
            },

            # ==================== XUANWUMON NORMAL ====================
            "Xuanwumon Set (Water) - NORMAL": {
                "color": "#00d4ff",
                "items": [
                    {"name": "Xuanwumon's Sealed Ring", "command": ".storeitem Xuanwumon's Sealed Ring",
                     "location": "EDGNN - Xuanwumon Box", "icon": f"{wiki_base}Sealed_Xuanwumon_Ring.png", "bulk": False},
                    {"name": "Xuanwumon's Sealed Necklace", "command": ".storeitem Xuanwumon's Sealed Necklace",
                     "location": "EDGNN - Xuanwumon Box", "icon": f"{wiki_base}Sealed_Xuanwumon_Necklace.png", "bulk": False},
                ]
            },

            # ==================== ZHUQIAOMON NORMAL ====================
            "Zhuqiaomon Set (Fire) - NORMAL": {
                "color": "#ff4444",
                "items": [
                    {"name": "Zhuqiaomon's Sealed Ring", "command": ".storeitem Zhuqiaomon's Sealed Ring",
                     "location": "ZDGNN - Phoenixmon Box", "icon": f"{wiki_base}Ring_of_Sealed_Zhuqiaomon.png", "bulk": False},
                    {"name": "Zhuqiaomon's Sealed Necklace", "command": ".storeitem Zhuqiaomon's Sealed Necklace",
                     "location": "ZDGNN - Phoenixmon Box", "icon": f"{wiki_base}Necklace_of_Sealed_Zhuqiaomon.png", "bulk": False},
                    {"name": "Zhuqiaomon's Sealed Earring", "command": ".storeitem Zhuqiaomon's Sealed Earring",
                     "location": "ZDGNN - Phoenixmon Box", "icon": f"{wiki_base}Earring_of_Sealed_Zhuqiaomon.png", "bulk": False},
                ]
            },

            # ==================== BAIHUMON NORMAL ====================
            "Baihumon Set (Steel) - NORMAL": {
                "color": "#ecf0f1",
                "items": [
                    {"name": "Baihumon's Sealed Ring", "command": ".storeitem Baihumon's Sealed Ring",
                     "location": "BDGNN - SaberLeomon Box", "icon": f"{wiki_base}Ring_of_Sealed_Baihumon.png", "bulk": False},
                    {"name": "Baihumon's Sealed Necklace", "command": ".storeitem Baihumon's Sealed Necklace",
                     "location": "BDGNN - SaberLeomon Box", "icon": f"{wiki_base}Necklace_of_Sealed_Baihumon.png", "bulk": False},
                    {"name": "Baihumon's Sealed Earring", "command": ".storeitem Baihumon's Sealed Earring",
                     "location": "BDGNN - SaberLeomon Box", "icon": f"{wiki_base}Earring_of_Sealed_Baihumon.png", "bulk": False},
                ]
            },

            # ==================== QINGLONGMON NORMAL ====================
            "Qinglongmon Set (Thunder) - NORMAL": {
                "color": "#ffd700",
                "items": [
                    {"name": "Qinglongmon's Sealed Ring", "command": ".storeitem Qinglongmon's Sealed Ring",
                     "location": "QDGNN - Goldramon Box", "icon": f"{wiki_base}Qinglongmon%27s_Sealed_Radiant_Ring.png", "bulk": False},
                    {"name": "Qinglongmon's Sealed Necklace", "command": ".storeitem Qinglongmon's Sealed Necklace",
                     "location": "QDGNN - Goldramon Box", "icon": f"{wiki_base}Qinglongmon%27s_Sealed_Radiant_Necklace.png", "bulk": False},
                    {"name": "Qinglongmon's Sealed Earring", "command": ".storeitem Qinglongmon's Sealed Earring",
                     "location": "QDGNN - Goldramon Box", "icon": f"{wiki_base}Qinglongmon%27s_Sealed_Radiant_Earring.png", "bulk": False},
                ]
            },

            # ==================== XUANWUMON HARD ====================
            "Xuanwumon Set (Water) - HARD": {
                "color": "#00d4ff",
                "items": [
                    {"name": "Xuanwumon's Sealed Shiny Ring", "command": ".storeitem Xuanwumon's Sealed Shiny Ring",
                     "location": "EDGN - Xuanwumon Box", "icon": f"{wiki_base}Xuanwumon_Sealed_Shiny_Ring.png", "bulk": False},
                    {"name": "Xuanwumon's Sealed Shiny Necklace", "command": ".storeitem Xuanwumon's Sealed Shiny Necklace",
                     "location": "EDGN - Xuanwumon Box", "icon": f"{wiki_base}Ebonwumon_Shiny_Necklace.png", "bulk": False},
                ]
            },

            # ==================== ZHUQIAOMON HARD ====================
            "Zhuqiaomon Set (Fire) - HARD": {
                "color": "#ff4444",
                "items": [
                    {"name": "Zhuqiaomon's Sealed Flame Ring", "command": ".storeitem Zhuqiaomon's Sealed Flame Ring",
                     "location": "ZDGN - Phoenixmon Box", "icon": f"{wiki_base}Flame_Ring_of_Sealed_Zhuqiaomon.png", "bulk": False},
                    {"name": "Flame Necklace of Sealed Zhuqiaomon", "command": ".storeitem Flame Necklace of Sealed Zhuqiaomon",
                     "location": "ZDGN - Phoenixmon Box", "icon": f"{wiki_base}Flame_Necklace_of_Sealed_Zhuqiamon.png", "bulk": False},
                    {"name": "Zhuqiaomon Shiny Earring", "command": ".storeitem Zhuqiaomon Shiny Earring",
                     "location": "ZDGN - Phoenixmon Box", "icon": f"{wiki_base}Zhuqiaomon_Shiny_Earring.png", "bulk": False},
                ]
            },

            # ==================== BAIHUMON HARD ====================
            "Baihumon Set (Steel) - HARD": {
                "color": "#ecf0f1",
                "items": [
                    {"name": "Baihumon's Sealed Aural Ring", "command": ".storeitem Baihumon's Sealed Aural Ring",
                     "location": "BDGN - SaberLeomon Box", "icon": f"{wiki_base}Aural_Ring_of_Sealed_Baihumon.png", "bulk": False},
                    {"name": "Baihumon Shiny Necklace", "command": ".storeitem Baihumon Shiny Necklace",
                     "location": "BDGN - SaberLeomon Box", "icon": f"{wiki_base}Baihumon_Shiny_Necklace.png", "bulk": False},
                    {"name": "Baihumon's Sealed Aural Earring", "command": ".storeitem Baihumon's Sealed Aural Earring",
                     "location": "BDGN - SaberLeomon Box", "icon": f"{wiki_base}Aural_Earring_of_Sealed_Baihumon.png", "bulk": False},
                ]
            },

            # ==================== QINGLONGMON HARD ====================
            "Qinglongmon Set (Thunder) - HARD": {
                "color": "#ffd700",
                "items": [
                    {"name": "Qinglongmon's Sealed Radiant Ring", "command": ".storeitem Qinglongmon's Sealed Radiant Ring",
                     "location": "QDGN - Goldramon Box", "icon": f"{wiki_base}Qinglongmon%27s_Sealed_Radiant_Ring.png", "bulk": False},
                    {"name": "Qinglongmon's Sealed Radiant Necklace", "command": ".storeitem Qinglongmon's Sealed Radiant Necklace",
                     "location": "QDGN - Goldramon Box", "icon": f"{wiki_base}Qinglongmon%27s_Sealed_Radiant_Necklace.png", "bulk": False},
                    {"name": "Qinglongmon's Sealed Radiant Earring", "command": ".storeitem Qinglongmon's Sealed Radiant Earring",
                     "location": "QDGN - Goldramon Box", "icon": f"{wiki_base}Qinglongmon%27s_Sealed_Radiant_Earring.png", "bulk": False},
                ]
            },

            # ==================== FANGLONGMON (YIN YANG) ====================
            "Fanglongmon Set (Yin Yang)": {
                "color": "#ffffff",
                "items": [
                    {"name": "Fanronkou", "command": ".storeitem Fanronkou",
                     "location": "FDG - Fanglongmon", "icon": f"{wiki_base}Fanronkou_.png", "bulk": False},
                    {"name": "Divine Crystal", "command": ".storeitem Divine Crystal",
                     "location": "FDG - Fanglongmon", "icon": f"{wiki_base}Divine_Crystal.png", "bulk": False},
                ]
            },

            # ==================== FANGLONGMON ULTIMATE ANCIENT [Lv.10] ====================
            "Fanglongmon Ultimate Ancient Set [Lv.10]": {
                "color": "#c0a0ff",
                "items": [
                    {"name": "Sealed Fanglongmon's Ultimate Ancient Necklace [Lv.10]",
                     "command": ".storeitem Sealed Fanglongmon's Ultimate Ancient Necklace [Lv.10]",
                     "location": "End Game — Fanglongmon Dungeon",
                     "icon": f"{wiki_base}Fanglongmon%27s_Ancient_Necklace_Lv.G.png", "bulk": False},
                    {"name": "Sealed Fanglongmon's Ultimate Ancient Ring [Lv.10]",
                     "command": ".storeitem Sealed Fanglongmon's Ultimate Ancient Ring [Lv.10]",
                     "location": "End Game — Fanglongmon Dungeon",
                     "icon": f"{wiki_base}Fanglongmon%27s_Ancient_Ring_Lv.G.png", "bulk": False},
                    {"name": "Sealed Fanglongmon's Ultimate Ancient Earrings [Lv.10]",
                     "command": ".storeitem Sealed Fanglongmon's Ultimate Ancient Earrings [Lv.10]",
                     "location": "End Game — Fanglongmon Dungeon",
                     "icon": f"{wiki_base}Fanglongmon%27s_Ancient_Earring_LvG.png", "bulk": False},
                ]
            },

            # ==================== DARK MASTERS DUNGEON CORES (RBH+) ====================
            "Dark Masters Dungeon Cores": {
                "color": "#ff6b35",
                "items": [
                    {"name": "Marine Dragon Core", "command": ".storeitem Marine Dragon Core",
                     "location": "Marine Dragon Domain — MetalSeadramon (SSS)",
                     "icon": f"{wiki_base}Marine_Dragon_Core.png", "bulk": False},
                    {"name": "Wooden Puppet Core", "command": ".storeitem Wooden Puppet Core",
                     "location": "Front Yard of Marionette Mansion — Puppetmon (SSS)",
                     "icon": f"{wiki_base}Wooden_Puppet_Core.png", "bulk": False},
                    {"name": "Metallic Beast Core", "command": ".storeitem Metallic Beast Core",
                     "location": "Back of the Empire — MugenDramon (SSS)",
                     "icon": f"{wiki_base}Metalic_Beast_Core.png", "bulk": False},
                    {"name": "Cruelty Clown Core", "command": ".storeitem Cruelty Clown Core",
                     "location": "Stage of Clown — Piedmon (SSS)",
                     "icon": f"{wiki_base}Cruelty_Clown_Core.png", "bulk": False},
                    {"name": "Yggdrasil Core", "command": ".storeitem Yggdrasil Core",
                     "location": "Royal Base (Hard) Room 3 — Alphamon Ouryuken (SSS+)",
                     "icon": f"{wiki_base}Yggdrasil_Core.png", "bulk": False},
                ]
            },

            # ==================== SSS — SKILL (SK) ====================
            "SSS \u2014 Skill (SK)": {
                "color": "#ff6b6b",
                "items": [
                    {"name": "X-Antibody Factor Megidramon", "command": ".storeitem X-Antibody Factor Megidramon",
                     "location": "SSS \u2014 Megidramon X", "icon": f"{wiki_base}Megidramon_X_Icon.png", "bulk": False},
                    {"name": "Extreme Evolution Codex Fallen", "command": ".storeitem Extreme Evolution Codex Fallen",
                     "location": "SSS \u2014 Beelzemon X Fallen", "icon": f"{wiki_base}Beelzemon_X_Fallen_Icon.png", "bulk": False},
                    {"name": "El Evangelio", "command": ".storeitem El Evangelio",
                     "location": "SSS \u2014 Beelzemon X Fallen", "icon": f"{wiki_base}Beelzemon_X_Fallen_Icon.png", "bulk": False},
                    {"name": "X-Antibody Factor Gaioumon", "command": ".storeitem X-Antibody Factor Gaioumon",
                     "location": "SSS \u2014 Gaioumon", "icon": f"{wiki_base}Gaioumon_Icon.png", "bulk": False},
                    {"name": "X-Antibody Factor Minervamon", "command": ".storeitem X-Antibody Factor Minervamon",
                     "location": "SSS \u2014 Minervamon X", "icon": f"{wiki_base}Minervamon_X_Icon.png", "bulk": False},
                    {"name": "Judgment of Olympia", "command": ".storeitem Judgment of Olympia",
                     "location": "SSS \u2014 Minervamon X", "icon": f"{wiki_base}Minervamon_X_Icon.png", "bulk": False},
                    {"name": "X-Antibody Factor Daemon", "command": ".storeitem X-Antibody Factor Daemon",
                     "location": "SSS \u2014 Demon X", "icon": f"{wiki_base}Demon_X_Icon.png", "bulk": False},
                    {"name": "Upsurge of Rage", "command": ".storeitem Upsurge of Rage",
                     "location": "SSS \u2014 Demon X", "icon": f"{wiki_base}Demon_X_Icon.png", "bulk": False},
                    {"name": "Matrix Evolution - Dukemon", "command": ".storeitem Matrix Evolution - Dukemon",
                     "location": "SSS \u2014 Dukemon Shin", "icon": f"{wiki_base}Dukemon_%28Shin%29_Icon.png", "bulk": False},
                    {"name": "Broken Alarm Clock", "command": ".storeitem Broken Alarm Clock",
                     "location": "SSS \u2014 Belphemon Rage Mode Shin", "icon": f"{wiki_base}Belphemon_%28Rage_Mode%29_Shin_Icon.png", "bulk": False},
                    {"name": "Dark Horn", "command": ".storeitem Dark Horn",
                     "location": "SSS \u2014 Belphemon Rage Mode Shin", "icon": f"{wiki_base}Belphemon_%28Rage_Mode%29_Shin_Icon.png", "bulk": False},
                    {"name": "Rafflesia", "command": ".storeitem Rafflesia",
                     "location": "SSS \u2014 Rafflesimon (DATA)", "icon": f"{wiki_base}Rafflesimon.png", "bulk": False},
                    {"name": "Rafflesimon Data Core Lotusmon", "command": ".storeitem Rafflesimon Data Core Lotusmon",
                     "location": "Quest (20 steps) \u2014 Rafflesimon (DATA)", "icon": f"{wiki_base}Rafflesimon.png", "bulk": False},
                    {"name": "Rafflesimon Data Core Rosemon", "command": ".storeitem Rafflesimon Data Core Rosemon",
                     "location": "Cash Shop / Event \u2014 Rafflesimon (DATA)", "icon": f"{wiki_base}Rafflesimon.png", "bulk": False},
                    {"name": "X-Antibody Factor Jesmon", "command": ".storeitem X-Antibody Factor Jesmon",
                     "location": "SSS \u2014 Jesmon X (DATA)", "icon": f"{wiki_base}Jesmon_X.png", "bulk": False},
                    {"name": "Holy Blade of Honorable Ruler", "command": ".storeitem Holy Blade of Honorable Ruler",
                     "location": "SSS \u2014 Jesmon X (DATA)", "icon": f"{wiki_base}Jesmon_X.png", "bulk": False},
                    {"name": "Data of Fallen Angel Wrath", "command": ".storeitem Data of Fallen Angel Wrath",
                     "location": "Quest (26 steps, Meicoomon) \u2014 Ordinemon", "icon": f"{wiki_base}Ordinemon_Icon.png", "bulk": False},
                    {"name": "Data of Fallen Angel Sorrow", "command": ".storeitem Data of Fallen Angel Sorrow",
                     "location": "Cash Shop \u2014 Ordinemon", "icon": f"{wiki_base}Ordinemon_Icon.png", "bulk": False},
                ]
            },

            # ==================== SSS — AUTO (AA) ====================
            "SSS \u2014 Auto (AA)": {
                "color": "#ffa94d",
                "items": [
                    {"name": "X-Antibody Factor Alphamon Ouryuken Alpha", "command": ".storeitem X-Antibody Factor Alphamon Ouryuken Alpha",
                     "location": "Quest \u2192 NPC Craft \u2014 Alphamon Ouryuken (PA)", "icon": f"{wiki_base}Alphamon_Ouryuken_%28X-Antibody_System%29_Icon.png", "bulk": False},
                    {"name": "X-Antibody Factor Alphamon Ouryuken Beta", "command": ".storeitem X-Antibody Factor Alphamon Ouryuken Beta",
                     "location": "Cash Shop / Event \u2014 Alphamon Ouryuken (PA)", "icon": f"{wiki_base}Alphamon_Ouryuken_%28X-Antibody_System%29_Icon.png", "bulk": False},
                    {"name": "X-Antibody Factor Lilithmon", "command": ".storeitem X-Antibody Factor Lilithmon",
                     "location": "SSS \u2014 Lilithmon X", "icon": f"{wiki_base}X-Antibody_Factor_Lilithmon.png", "bulk": False},
                    {"name": "Embrace of Lust", "command": ".storeitem Embrace of Lust",
                     "location": "SSS \u2014 Lilithmon X", "icon": f"{wiki_base}X-Antibody_Factor_Lilithmon.png", "bulk": False},
                    {"name": "Vengeful Ring", "command": ".storeitem Vengeful Ring",
                     "location": "SSS \u2014 Imperialdramon Paladin Mode Vengeful", "icon": f"{wiki_base}Vengeful_Ring.png", "bulk": False},
                    {"name": "X-Antibody Factor LordKnightmon", "command": ".storeitem X-Antibody Factor LordKnightmon",
                     "location": "SSS \u2014 LordKnightmon X", "icon": f"{wiki_base}X-Antibody_Factor_LordKnightmon.png", "bulk": False},
                    {"name": "Chivalry", "command": ".storeitem Chivalry",
                     "location": "SSS \u2014 LordKnightmon X", "icon": f"{wiki_base}X-Antibody_Factor_LordKnightmon.png", "bulk": False},
                    {"name": "Boltboutamon Data Code - Myotismon", "command": ".storeitem Boltboutamon Data Code - Myotismon",
                     "location": "Quest (17 steps) \u2014 Boltboutamon Fallen", "icon": f"{wiki_base}Extreme_Evolution_Codex_Fallen.png", "bulk": False},
                    {"name": "Piece of Metal", "command": ".storeitem Piece of Metal",
                     "location": "SSS \u2014 PlatinumSukamon", "icon": f"{wiki_base}Piece_of_Metal.png", "bulk": False},
                    {"name": "Xros Fusion Light - Alpha", "command": ".storeitem Xros Fusion Light - Alpha",
                     "location": "Quest \u2014 Jet Mervamon", "icon": f"{wiki_base}Xros_Fusion_Light_-_Alpha.png", "bulk": False},
                    {"name": "Xros Fusion Light - Beta", "command": ".storeitem Xros Fusion Light - Beta",
                     "location": "Cash Shop / Event \u2014 Jet Mervamon", "icon": f"{wiki_base}Xros_Fusion_Light_-_Alpha.png", "bulk": False},
                ]
            },

            # ==================== SSS — TANK ====================
            "SSS \u2014 Tank": {
                "color": "#74c0fc",
                "items": [
                    {"name": "X-Antibody Factor IcyMagnamon", "command": ".storeitem X-Antibody Factor IcyMagnamon",
                     "location": "SSS \u2014 IcyMagnamon X", "icon": f"{wiki_base}IcyMagnamonX.png", "bulk": False},
                    {"name": "X-Antibody Factor Barbamon", "command": ".storeitem X-Antibody Factor Barbamon",
                     "location": "SSS \u2014 Barbamon X", "icon": f"{wiki_base}X-AntibodyFactor_Barbamon.png", "bulk": False},
                    {"name": "Paradise of Greed", "command": ".storeitem Paradise of Greed",
                     "location": "SSS \u2014 Barbamon X", "icon": f"{wiki_base}X-AntibodyFactor_Barbamon.png", "bulk": False},
                    {"name": "Tyranno Data Devouring", "command": ".storeitem Tyranno Data Devouring",
                     "location": "Quest (20 steps) \u2014 RustTyrannomon", "icon": f"{wiki_base}Tyranno_Data_Devouring.png", "bulk": False},
                    {"name": "Tyranno Data Destruction", "command": ".storeitem Tyranno Data Destruction",
                     "location": "Cash Shop \u2014 RustTyrannomon", "icon": f"{wiki_base}Tyranno_Data_Devouring.png", "bulk": False},
                    {"name": "Death Slinger", "command": ".storeitem Death Slinger",
                     "location": "SSS \u2014 Beelzemon Blast Mode Shin", "icon": f"{wiki_base}Death_Slinger.png", "bulk": False},
                    {"name": "Strength of Potestas - A", "command": ".storeitem Strength of Potestas - A",
                     "location": "Quest \u2014 SlashAngemon", "icon": f"{wiki_base}SlashAngemon_Icon.png", "bulk": False},
                    {"name": "Strength of Potestas - B", "command": ".storeitem Strength of Potestas - B",
                     "location": "Cash Shop / Event \u2014 SlashAngemon", "icon": f"{wiki_base}SlashAngemon_Icon.png", "bulk": False},
                ]
            },

            # ==================== SSS — SUPPORT ====================
            "SSS \u2014 Support": {
                "color": "#a9e34b",
                "items": [
                    {"name": "Yamata no Orochi", "command": ".storeitem Yamata no Orochi",
                     "location": "SSS \u2014 Orochimon", "icon": f"{wiki_base}Orochimon_Icon.png", "bulk": False},
                    {"name": "Matrix Evolution - Sakuyamon", "command": ".storeitem Matrix Evolution - Sakuyamon",
                     "location": "SSS \u2014 Sakuyamon Shin", "icon": f"{wiki_base}Sakuyamon_Shin_Icon.png", "bulk": False},
                    {"name": "Bangang Magic", "command": ".storeitem Bangang Magic",
                     "location": "SSS \u2014 Sakuyamon Shin", "icon": f"{wiki_base}Sakuyamon_Shin_Icon.png", "bulk": False},
                    {"name": "Digimental - Code F", "command": ".storeitem Digimental - Code F",
                     "location": "Quest \u2192 NPC Craft (Dats Center)", "icon": f"{wiki_base}UlforceVeedramon_Future_Mode_Icon.png", "bulk": False},
                    {"name": "Piedmon's Spirit", "command": ".storeitem Piedmon's Spirit",
                     "location": "SSS \u2014 Piedmon Shin", "icon": f"{wiki_base}Piedmon_%28Shin%29_Icon.png", "bulk": False},
                ]
            },

            # ==================== SSS+ — SKILL (SK) ====================
            "SSS+ \u2014 Skill (SK)": {
                "color": "#ff2d55",
                "items": [
                    {"name": "X-Antibody Factor Omegamon-Alpha", "command": ".storeitem X-Antibody Factor Omegamon-Alpha",
                     "location": "Quest + NPC Craft (D-Terminal)", "icon": f"{wiki_base}Omegamon_X_Icon.png", "bulk": False},
                    {"name": "X-Antibody Factor Omegamon-Beta", "command": ".storeitem X-Antibody Factor Omegamon-Beta",
                     "location": "Cash Shop (Gamble Box)", "icon": f"{wiki_base}Omegamon_X_Icon.png", "bulk": False},
                    {"name": "Will for Justice", "command": ".storeitem Will for Justice",
                     "location": "Colosseum (Hero Rounds) \u2014 Omegamon X (VA)", "icon": f"{wiki_base}Omegamon_X_Icon.png", "bulk": False},
                    {"name": "X-Antibody Factor - Alphamon Ouryuken(Awaken) \u2013 Alpha", "command": ".storeitem X-Antibody Factor - Alphamon Ouryuken(Awaken) - Alpha",
                     "location": "NPC Craft (Dats Center) \u2014 Royal Base Hard", "icon": f"{wiki_base}Alphamon_Ouryuken_Awaken_Icon.png", "bulk": False},
                    {"name": "X-Antibody Factor - Alphamon Ouryuken(Awaken) \u2013 Beta", "command": ".storeitem X-Antibody Factor - Alphamon Ouryuken(Awaken) - Beta",
                     "location": "Cash Shop (Gamble Box)", "icon": f"{wiki_base}Alphamon_Ouryuken_Awaken_Icon.png", "bulk": False},
                    {"name": "Wings of Justice", "command": ".storeitem Wings of Justice",
                     "location": "SSS+ \u2014 Alphamon Ouryuken Awaken", "icon": f"{wiki_base}Alphamon_Ouryuken_Awaken_Icon.png", "bulk": False},
                    {"name": "X-Antibody Factor Lucemon", "command": ".storeitem X-Antibody Factor Lucemon",
                     "location": "NPC Craft (Dats Center) \u2014 Infinite Mountain 3.0", "icon": f"{wiki_base}X-Antibody_Factor_Lucemon.png", "bulk": False},
                    {"name": "Paradise of Loss", "command": ".storeitem Paradise of Loss",
                     "location": "SSS+ \u2014 Lucemon X (VI)", "icon": f"{wiki_base}X-Antibody_Factor_Lucemon.png", "bulk": False},
                    {"name": "D Antivirus A", "command": ".storeitem D Antivirus A",
                     "location": "NPC Craft (Dats Center) \u2014 Berserk Arena", "icon": f"{wiki_base}Omegamon_Zwart_D_Icon.png", "bulk": False},
                    {"name": "D Antivirus B", "command": ".storeitem D Antivirus B",
                     "location": "Cash Shop (Gamble Box)", "icon": f"{wiki_base}Omegamon_Zwart_D_Icon.png", "bulk": False},
                    {"name": "Deteriorated Dark Will", "command": ".storeitem Deteriorated Dark Will",
                     "location": "SSS+ \u2014 Omegamon Zwart D (VI)", "icon": f"{wiki_base}Omegamon_Zwart_D_Icon.png", "bulk": False},
                    {"name": "Ultimate Dragon Energy", "command": ".storeitem Ultimate Dragon Energy",
                     "location": "SSS+ Dungeon", "icon": None, "bulk": False},
                    {"name": "X-Antibody Factor Examon Alpha", "command": ".storeitem X-Antibody Factor Examon Alpha",
                     "location": "NPC Craft (Colo Extreme) \u2014 Dats Center", "icon": f"{wiki_base}Examon_X_Icon.png", "bulk": False},
                    {"name": "X-Antibody Factor Examon Beta", "command": ".storeitem X-Antibody Factor Examon Beta",
                     "location": "Cash Shop (Gamble Box) \u2014 Examon X", "icon": f"{wiki_base}Examon_X_Icon.png", "bulk": False},
                ]
            },

            # ==================== SSS+ — AUTO (AA) ====================
            "SSS+ \u2014 Auto (AA)": {
                "color": "#ff8c00",
                "items": [
                    {"name": "X-Antibody Factor DeathXmon (Awaken)", "command": ".storeitem X-Antibody Factor DeathXmon (Awaken)",
                     "location": "NPC Craft (Royal Base Hard) \u2014 Dats Center", "icon": f"{wiki_base}Death-X-mon_Awaken_Icon.png", "bulk": False},
                    {"name": "Procces-D", "command": ".storeitem Procces-D",
                     "location": "SSS+ \u2014 Death-X-mon Awaken", "icon": f"{wiki_base}Death-X-mon_Awaken_Icon.png", "bulk": False},
                    {"name": "X-Antibody Factor Gaioumon Itto Mode", "command": ".storeitem X-Antibody Factor Gaioumon Itto Mode",
                     "location": "NPC Craft (Dats Center) \u2014 Gaioumon Itto Mode", "icon": f"{wiki_base}Gaioumon_Itto_Mode_Icon.png", "bulk": False},
                    {"name": "Tenrin Itto-ryu Sou", "command": ".storeitem Tenrin Itto-ryu Sou",
                     "location": "SSS+ \u2014 Gaioumon Itto Mode", "icon": f"{wiki_base}Gaioumon_Itto_Mode_Icon.png", "bulk": False},
                    {"name": "King's Data Code", "command": ".storeitem King's Data Code",
                     "location": "SSS+ \u2014 KingSukamon", "icon": f"{wiki_base}KingSukamon_Icon.png", "bulk": False},
                    {"name": "Soul of Sukamon", "command": ".storeitem Soul of Sukamon",
                     "location": "SSS+ \u2014 KingSukamon", "icon": f"{wiki_base}KingSukamon_Icon.png", "bulk": False},
                    {"name": "Last Evolution - Friendship", "command": ".storeitem Last Evolution - Friendship",
                     "location": "NPC Craft (Dats Center) \u2014 Never-Land Dungeon", "icon": f"{wiki_base}Gabumon_-_Bond_of_Friendship_Icon.png", "bulk": False},
                    {"name": "Friendship Sheet", "command": ".storeitem Friendship Sheet",
                     "location": "SSS+ \u2014 Gabumon Bond of Friendship (DA)", "icon": f"{wiki_base}Gabumon_-_Bond_of_Friendship_Icon.png", "bulk": False},
                ]
            },

            # ==================== SSS+ — TANK ====================
            "SSS+ \u2014 Tank": {
                "color": "#339af0",
                "items": [
                    {"name": "Shining Wings of Courage", "command": ".storeitem Shining Wings of Courage",
                     "location": "NPC Craft (Quest + Cash Shop) \u2014 WarGreymon Shin (VA)", "icon": f"{wiki_base}Shining_Wings_of_Courage.png", "bulk": False},
                    {"name": "Miracle of Courage", "command": ".storeitem Miracle of Courage",
                     "location": "SSS+ \u2014 WarGreymon Shin (VA)", "icon": f"{wiki_base}Miracle_of_Courage.png", "bulk": False},
                ]
            },

            # ==================== SPIRIT BOXES ====================
            "Spirit Boxes": {
                "color": "#3fb950",
                "items": [
                    {"name": "Raid Summon Card Lv3", "command": ".storeitem raid summon card lv3",
                     "location": "Various Raids", "icon": f"{wiki_base}Raid_Summon_Card_Lv3.png", "bulk": True},
                ]
            },

            # ==================== REBORN CLONES ====================
            "Reborn Clones": {
                "color": "#ff8800",
                "items": [
                    {"name": "[Reborn] - Digiclone[A]", "command": ".storeitem [Reborn] - Digiclone[A]",
                     "location": "Battle Field Dungeons", "icon": f"{wiki_base}DigiClone_%28Reborn%29_%28A%29.png", "bulk": False},
                    {"name": "[Reborn] - Digiclone[B]", "command": ".storeitem [Reborn] - Digiclone[B]",
                     "location": "Battle Field Dungeons", "icon": f"{wiki_base}DigiClone_%28Reborn%29_%28B%29.png", "bulk": False},
                    {"name": "[Reborn] - Digiclone[C]", "command": ".storeitem [Reborn] - Digiclone[C]",
                     "location": "Battle Field Dungeons", "icon": f"{wiki_base}DigiClone_%28Reborn%29_%28C%29.png", "bulk": False},
                    {"name": "[Reborn] - Digiclone[D]", "command": ".storeitem [Reborn] - Digiclone[D]",
                     "location": "Battle Field Dungeons", "icon": f"{wiki_base}DigiClone_%28Reborn%29_%28D%29.png", "bulk": False},
                    {"name": "[Reborn] - Digiclone[S]", "command": ".storeitem [Reborn] - Digiclone[S]",
                     "location": "Battle Field Dungeons", "icon": f"{wiki_base}DigiClone_%28Reborn%29_%28S%29.png", "bulk": False},
                ]
            },

            # ==================== UPGRADE STONES ====================
            "Upgrade Stones": {
                "color": "#d29922",
                "items": [
                    {"name": "Amazing Renewal Increase Stone", "command": ".storeitem Amazing Renewal Increase Stone",
                     "location": "Various Dungeons", "icon": f"{wiki_base}Amazing_Renewal_Increase_Stone.png", "bulk": True},
                    {"name": "Option Change Stone", "command": ".storeitem Option Change Stone",
                     "location": "Cash Shop / Events", "icon": f"{wiki_base}Option_Change_Stone.png", "bulk": False},
                    {"name": "Number Change Stone", "command": ".storeitem Number Change Stone",
                     "location": "Cash Shop / Events", "icon": f"{wiki_base}Number_Change_Stone.png", "bulk": False},
                ]
            },

            # ==================== DIGITAL HAZARD SET ====================
            "Digital Hazard Set": {
                "color": "#ff4444",
                "items": [
                    {"name": "Digital Hazard Cap", "command": ".storeitem Digital Hazard Cap Box",
                     "location": None, "icon": f"{wiki_base}Digital_Hazard_Cap.png", "bulk": False},
                    {"name": "Digital Hazard Cape", "command": ".storeitem Digital Hazard Cape Box",
                     "location": None, "icon": f"{wiki_base}Digital_Hazard_Cape.png", "bulk": False},
                    {"name": "Digital Hazard Shirt", "command": ".storeitem Digital Hazard Shirt Box",
                     "location": None, "icon": f"{wiki_base}Digital_Hazard_Shirt.png", "bulk": False},
                    {"name": "Digital Hazard Pants", "command": ".storeitem Digital Hazard Pants Box",
                     "location": None, "icon": f"{wiki_base}Digital_Hazard_Pants.png", "bulk": False},
                    {"name": "Digital Hazard Gloves", "command": ".storeitem Digital Hazard Gloves Box",
                     "location": None, "icon": f"{wiki_base}Digital_Hazard_Gloves.png", "bulk": False},
                ]
            },

            # ==================== WARRIOR SET ====================
            "Warrior Set": {
                "color": "#c0c0c0",
                "items": [
                    {"name": "Warrior Ornament", "command": ".storeitem Warrior Ornament",
                     "location": "Vajramon Dungeon (Hard)", "icon": f"{wiki_base}Warrior_Ornament_.png", "bulk": False},
                    {"name": "Warrior Top", "command": ".storeitem Warrior Top",
                     "location": "Vajramon Dungeon (Hard)", "icon": f"{wiki_base}Warrior_Top.png", "bulk": False},
                    {"name": "Warrior Pants", "command": ".storeitem Warrior Pants",
                     "location": "Vajramon Dungeon (Hard)", "icon": f"{wiki_base}Warrior_Pants.png", "bulk": False},
                    {"name": "Warrior Gloves", "command": ".storeitem Warrior Gloves",
                     "location": "Vajramon Dungeon (Hard)", "icon": f"{wiki_base}Warrior_Gloves.png", "bulk": False},
                ]
            },

            # ==================== WARRIOR SHINING SET ====================
            "Warrior Shining Set": {
                "color": "#ffd700",
                "items": [
                    {"name": "Warrior Ornament [Shining]", "command": ".storeitem Warrior Ornament [Shining]",
                     "location": "Vajramon Dungeon (Hard)", "icon": f"{wiki_base}Warrior_Ornament_%28Shining%29.png", "bulk": False},
                    {"name": "Warrior Top [Shining]", "command": ".storeitem Warrior Top [Shining]",
                     "location": "Vajramon Dungeon (Hard)", "icon": f"{wiki_base}Warrior_Top_%28Shining%29.png", "bulk": False},
                    {"name": "Warrior Pants [Shining]", "command": ".storeitem Warrior Pants [Shining]",
                     "location": "Vajramon Dungeon (Hard)", "icon": f"{wiki_base}Warrior_Pants_%28Shining%29.png", "bulk": False},
                    {"name": "Warrior Gloves [Shining]", "command": ".storeitem Warrior Gloves [Shining]",
                     "location": "Vajramon Dungeon (Hard)", "icon": f"{wiki_base}Warrior_Gloves_%28Shining%29.png", "bulk": False},
                ]
            },

            # ==================== DIGICODES ====================
            "DigiCodes": {
                "color": "#58a6ff",
                "items": [
                    {"name": "Skill DigiCode (Armor)", "command": ".storeitem skill digicode (armor)",
                     "location": "Arena / Colosseum", "icon": f"{wiki_base}Skill_DigiCode_%28Armor%29.png", "bulk": False},
                    {"name": "Skill DigiCode (Burst Mode)", "command": ".storeitem skill digicode (burst mode)",
                     "location": "Arena / Colosseum", "icon": f"{wiki_base}Skill_DigiCode_%28Burst_Mode%29.png", "bulk": False},
                    {"name": "Skill DigiCode (Burst Mode X)", "command": ".storeitem skill digicode (burst mode x)",
                     "location": "Arena / Colosseum", "icon": f"{wiki_base}Skill_DigiCode_%28Burst_Mode_X%29.png", "bulk": False},
                    {"name": "Skill DigiCode (Riding Mode)", "command": ".storeitem skill digicode (riding mode)",
                     "location": "Arena / Colosseum", "icon": f"{wiki_base}Skill_DigiCode_%28Riding_Mode%29.png", "bulk": False},
                    {"name": "Skill DigiCode (Jogress)", "command": ".storeitem skill digicode (jogress)",
                     "location": "Arena / Colosseum", "icon": f"{wiki_base}Skill_DigiCode_%28Jogress%29.png", "bulk": False},
                ]
            },

            # ==================== FOUR PILLARS OF RUIN ====================
            "Four Pillars of Ruin": {
                "color": "#c0392b",
                "items": [
                    {"name": "Apocalypse Catalyst [Alpha]", "command": ".storeitem Apocalypse Catalyst [Alpha]",
                     "location": "Four Pillars of Ruin (Alpha) — All Bosses Defeated",
                     "icon": f"{wiki_base}Apocalypse_Catalyst_Alpha.png", "bulk": True},
                    {"name": "Apocalypse Catalyst [Beta]", "command": ".storeitem Apocalypse Catalyst [Beta]",
                     "location": "Four Pillars of Ruin (Beta) — All Bosses Defeated",
                     "icon": f"{wiki_base}Apocalypse_Catalyst_Beta.png", "bulk": True},
                ]
            },

            # ==================== VOID SPACE DUNGEON ====================
            "Void Space Dungeon": {
                "color": "#6c3483",
                "items": [
                    {"name": "Core of Nothingness", "command": ".storeitem Core of Nothingness",
                     "location": "Void Space Dungeon — Unsealed Box of Nothingness",
                     "icon": f"{wiki_base}Core_of_Nothingness.png", "bulk": False},
                    {"name": "Fragment of Nothingness", "command": ".storeitem Fragment of Nothingness",
                     "location": "Void Space Dungeon — Void Box (random)",
                     "icon": f"{wiki_base}Fragment_of_Nothingness.png", "bulk": False},
                    {"name": "Void Crystal", "command": ".storeitem Void Crystal",
                     "location": "Void Space Dungeon — Void Box (random)",
                     "icon": f"{wiki_base}Void_Crystal.png", "bulk": False},
                    {"name": "Void Power Stone (Tradeable)", "command": ".storeitem Void Power Stone",
                     "location": "Void Space Dungeon — Void Space Box",
                     "icon": f"{wiki_base}Void_Power_Stone.png", "bulk": False},
                    {"name": "Void Power Stone (CB)", "command": ".storeitem Void Power Stone (CB)",
                     "location": "Void Space Dungeon — Void Space Box",
                     "icon": f"{wiki_base}Void_Power_Stone.png", "bulk": False},
                ]
            },

            # ==================== DARK MASTERS SPIRIT BOXES ====================
            "Dark Masters Spirit Boxes": {
                "color": "#27ae60",
                "items": [
                    {"name": "MetalSeadramon's Spirit", "command": ".storeitem MetalSeadramon's Spirit",
                     "location": "Marine Dragon Domain — Spirit Box (rare)",
                     "icon": f"{wiki_base}MetalSeadramon%27s_Spirit.png", "bulk": False},
                    {"name": "MetalSeadramon's Saddle", "command": ".storeitem MetalSeadramon's Saddle",
                     "location": "Marine Dragon Domain — Spirit Box (rare)",
                     "icon": f"{wiki_base}MetalSeadramon%27s_Saddle.png", "bulk": False},
                    {"name": "Puppetmon's Spirit", "command": ".storeitem Puppetmon's Spirit",
                     "location": "Front Yard of Marionette Mansion — Spirit Box (rare)",
                     "icon": f"{wiki_base}Puppetmon%27s_Spirit.png", "bulk": False},
                    {"name": "Housemon's Saddle", "command": ".storeitem Housemon's Saddle",
                     "location": "Front Yard of Marionette Mansion — Spirit Box (rare)",
                     "icon": f"{wiki_base}Housemon%27s_Saddle.png", "bulk": False},
                    {"name": "MugenDramon's Spirit", "command": ".storeitem MugenDramon's Spirit",
                     "location": "Back of the Empire — Spirit Box (rare)",
                     "icon": f"{wiki_base}MugenDramon%27s_Spirit.png", "bulk": False},
                    {"name": "MugenDramon's Saddle", "command": ".storeitem MugenDramon's Saddle",
                     "location": "Back of the Empire — Spirit Box (rare)",
                     "icon": f"{wiki_base}MugenDramon%27s_Saddle.png", "bulk": False},
                    {"name": "Piedmon's Spirit", "command": ".storeitem Piedmon's Spirit",
                     "location": "Stage of Clown — Spirit Box (rare)",
                     "icon": f"{wiki_base}Piedmon%27s_Spirit.png", "bulk": False},
                ]
            },

            # ==================== SPIRAL MOUNTAIN ACCESSORIES ====================
            "Spiral Mountain Accessories": {
                "color": "#1abc9c",
                "items": [
                    {"name": "Ring of the Marine Dragon [AA]",
                     "command": ".storeitem Ring of the Marine Dragon [AA]",
                     "location": "Taichi NPC — Marine Dragon Core x100 + Spiral Essence x500",
                     "icon": f"{wiki_base}Ring_of_the_Marine_Dragon_AA.png", "bulk": False},
                    {"name": "Ring of the Marine Dragon [SK]",
                     "command": ".storeitem Ring of the Marine Dragon [SK]",
                     "location": "Taichi NPC — Marine Dragon Core x100 + Spiral Essence x500",
                     "icon": f"{wiki_base}Ring_of_the_Marine_Dragon_SK.png", "bulk": False},
                    {"name": "Ring of the Marine Dragon [TANK]",
                     "command": ".storeitem Ring of the Marine Dragon [TANK]",
                     "location": "Taichi NPC — Marine Dragon Core x100 + Spiral Essence x500",
                     "icon": f"{wiki_base}Ring_of_the_Marine_Dragon_TANK.png", "bulk": False},

                    {"name": "Necklace of the Wooden Puppet [AA]",
                     "command": ".storeitem Necklace of the Wooden Puppet [AA]",
                     "location": "Taichi NPC — Wooden Puppet Core x100 + Marine Dragon Core x100 + Spiral Essence x500",
                     "icon": f"{wiki_base}Necklace_of_the_Wooden_Puppet_AA.png", "bulk": False},
                    {"name": "Necklace of the Wooden Puppet [SK]",
                     "command": ".storeitem Necklace of the Wooden Puppet [SK]",
                     "location": "Taichi NPC — Wooden Puppet Core x100 + Marine Dragon Core x100 + Spiral Essence x500",
                     "icon": f"{wiki_base}Necklace_of_the_Wooden_Puppet_SK.png", "bulk": False},
                    {"name": "Necklace of the Wooden Puppet [TANK]",
                     "command": ".storeitem Necklace of the Wooden Puppet [TANK]",
                     "location": "Taichi NPC — Wooden Puppet Core x100 + Marine Dragon Core x100 + Spiral Essence x500",
                     "icon": f"{wiki_base}Necklace_of_the_Wooden_Puppet_TANK.png", "bulk": False},

                    {"name": "Earring of the Metallic Beast [AA]",
                     "command": ".storeitem Earring of the Metallic Beast [AA]",
                     "location": "Taichi NPC — Metallic Beast Core x100 + Wooden Puppet Core x25 + Marine Dragon Core x25 + Spiral Essence x500",
                     "icon": f"{wiki_base}Earring_of_the_Metalic_Beast_AA.png", "bulk": False},
                    {"name": "Earring of the Metallic Beast [SK]",
                     "command": ".storeitem Earring of the Metallic Beast [SK]",
                     "location": "Taichi NPC — Metallic Beast Core x100 + Wooden Puppet Core x25 + Marine Dragon Core x25 + Spiral Essence x500",
                     "icon": f"{wiki_base}Earring_of_the_Metalic_Beast_SK.png", "bulk": False},
                    {"name": "Earring of the Metallic Beast [TANK]",
                     "command": ".storeitem Earring of the Metallic Beast [TANK]",
                     "location": "Taichi NPC — Metallic Beast Core x100 + Wooden Puppet Core x25 + Marine Dragon Core x25 + Spiral Essence x500",
                     "icon": f"{wiki_base}Earring_of_the_Metalic_Beast_TANK.png", "bulk": False},

                    {"name": "Bracelet of the Cruel Clown [AA]",
                     "command": ".storeitem Bracelet of the Cruel Clown [AA]",
                     "location": "Taichi NPC — Cruelty Clown Core x100 + Metallic Beast Core x25 + Wooden Puppet Core x25 + Marine Dragon Core x25 + Spiral Essence x500",
                     "icon": f"{wiki_base}Bracelet_of_the_Cruel_Clown_AA.png", "bulk": False},
                    {"name": "Bracelet of the Cruel Clown [SK]",
                     "command": ".storeitem Bracelet of the Cruel Clown [SK]",
                     "location": "Taichi NPC — Cruelty Clown Core x100 + Metallic Beast Core x25 + Wooden Puppet Core x25 + Marine Dragon Core x25 + Spiral Essence x500",
                     "icon": f"{wiki_base}Bracelet_of_the_Cruel_Clown_SK.png", "bulk": False},
                    {"name": "Bracelet of the Cruel Clown [TANK]",
                     "command": ".storeitem Bracelet of the Cruel Clown [TANK]",
                     "location": "Taichi NPC — Cruelty Clown Core x100 + Metallic Beast Core x25 + Wooden Puppet Core x25 + Marine Dragon Core x25 + Spiral Essence x500",
                     "icon": f"{wiki_base}Bracelet_of_the_Cruel_Clown_TANK.png", "bulk": False},
                ]
            },


        }

    # ================================================================
    #  ICON LOADING
    # ================================================================

    def load_icon(self, icon_url):
        if not icon_url or not HAS_PIL:
            return None
        if icon_url in self.icon_cache:
            return self.icon_cache[icon_url]
        try:
            req = urllib.request.Request(
                icon_url,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
            response = urllib.request.urlopen(req, timeout=10)
            image_data = response.read()
            image = Image.open(BytesIO(image_data))
            image = image.resize((32, 32), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            self.icon_cache[icon_url] = photo
            self.photo_refs.append(photo)
            return photo
        except Exception:
            return None

    def preload_icons(self):
        for category, data in self.item_database.items():
            for item in data['items']:
                if item.get('icon'):
                    self.load_icon(item['icon'])
        self.root.after(100, self.render_items)

    # ================================================================
    #  PERSISTENCE
    # ================================================================

    def load_custom_items(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.hidden_items = set(data.get('Hidden Items', []))
                    self.hidden_categories = set(data.get('Hidden Categories', []))
                    self.deleted_categories = set(data.get('Deleted Categories', []))
                    self.deleted_items = set(data.get('Deleted Items', []))
                    for cat in self.deleted_categories:
                        self.item_database.pop(cat, None)
                    return data.get('Custom Items', [])
            except Exception:
                pass
        return []

    def save_custom_items(self):
        try:
            with open(self.data_file, 'w') as f:
                json.dump({
                    'Custom Items': self.custom_items,
                    'Hidden Items': list(self.hidden_items),
                    'Hidden Categories': list(self.hidden_categories),
                    'Deleted Categories': list(self.deleted_categories),
                    'Deleted Items': list(self.deleted_items)
                }, f, indent=2)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {e}")

    # ================================================================
    #  CLIPBOARD
    # ================================================================

    def copy_to_clipboard(self, text):
        if HAS_PYPERCLIP:
            try:
                pyperclip.copy(text)
            except Exception:
                self.root.clipboard_clear()
                self.root.clipboard_append(text)
                self.root.update()
        else:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.root.update()

        self.status_label.config(
            text=f"  Copied:  {text}",
            fg=self.colors['accent_green'])
        self.root.after(2500, lambda: self.status_label.config(
            text="  Click any item to copy its .storeitem command",
            fg=self.colors['text_secondary']))

    # ================================================================
    #  UI SETUP
    # ================================================================

    def setup_ui(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Vertical.TScrollbar',
                        background=self.colors['bg_card'],
                        troughcolor=self.colors['bg_dark'],
                        bordercolor=self.colors['border'],
                        arrowcolor=self.colors['text_secondary'])

        # ── TOP BAR ──────────────────────────────────────────────────
        top_bar = tk.Frame(self.root, bg=self.colors['bg_card'], pady=12, padx=18)
        top_bar.pack(fill=tk.X, side=tk.TOP)

        left_top = tk.Frame(top_bar, bg=self.colors['bg_card'])
        left_top.pack(side=tk.LEFT)

        tk.Label(left_top, text="DMW Store Item Helper",
                 font=('Segoe UI', 20, 'bold'),
                 bg=self.colors['bg_card'],
                 fg=self.colors['accent_cyan']).pack(anchor='w')

        tk.Label(left_top,
                 text="Sidebar navigation  ·  Collapsible folders  ·  Click to copy",
                 font=('Segoe UI', 9),
                 bg=self.colors['bg_card'],
                 fg=self.colors['text_secondary']).pack(anchor='w', pady=(2, 0))

        right_top = tk.Frame(top_bar, bg=self.colors['bg_card'])
        right_top.pack(side=tk.RIGHT)

        # Add custom button
        tk.Button(right_top, text="＋  Add Custom Item",
                  font=('Segoe UI', 10, 'bold'),
                  bg=self.colors['accent_green'], fg='#0d1117',
                  relief=tk.FLAT, padx=14, pady=6,
                  cursor='hand2',
                  command=self.add_item_dialog).pack(side=tk.RIGHT, padx=(10, 0))

        # Search box
        search_wrap = tk.Frame(right_top,
                               bg=self.colors['bg_hover'],
                               highlightbackground=self.colors['border'],
                               highlightthickness=1)
        search_wrap.pack(side=tk.RIGHT)

        tk.Label(search_wrap, text="  🔍",
                 font=('Segoe UI', 11),
                 bg=self.colors['bg_hover'],
                 fg=self.colors['text_secondary']).pack(side=tk.LEFT)

        self.search_entry = tk.Entry(search_wrap,
                                     textvariable=self.search_var,
                                     font=('Segoe UI', 11),
                                     bg=self.colors['bg_hover'],
                                     fg=self.colors['text_primary'],
                                     insertbackground=self.colors['text_primary'],
                                     relief=tk.FLAT, width=24)
        self.search_entry.pack(side=tk.LEFT, ipady=7, padx=(4, 10))

        # ── TOP BORDER ────────────────────────────────────────────────
        tk.Frame(self.root, bg=self.colors['border'], height=1).pack(fill=tk.X)

        # ── MAIN CONTENT (sidebar + panel) ───────────────────────────
        content = tk.Frame(self.root, bg=self.colors['bg_dark'])
        content.pack(fill=tk.BOTH, expand=True)

        # ── SIDEBAR ──────────────────────────────────────────────────
        self.sidebar = tk.Frame(content, bg=self.colors['bg_card'], width=220)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)

        tk.Label(self.sidebar, text="  CATEGORIES",
                 font=('Segoe UI', 8, 'bold'),
                 bg=self.colors['bg_card'],
                 fg=self.colors['text_muted'],
                 pady=10).pack(anchor='w')

        tk.Frame(self.sidebar, bg=self.colors['border'], height=1).pack(fill=tk.X)

        # Sidebar scroll — scrollbar packed first so it claims space within fixed-width sidebar
        sb_scroll = ttk.Scrollbar(self.sidebar, orient=tk.VERTICAL)
        sb_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.sb_canvas = tk.Canvas(self.sidebar, bg=self.colors['bg_card'],
                                   highlightthickness=0,
                                   yscrollcommand=sb_scroll.set)
        sb_scroll.config(command=self.sb_canvas.yview)
        self.sb_frame = tk.Frame(self.sb_canvas, bg=self.colors['bg_card'])
        self.sb_frame.bind("<Configure>",
                           lambda e: self.sb_canvas.configure(
                               scrollregion=self.sb_canvas.bbox("all")))
        self.sb_canvas.create_window((0, 0), window=self.sb_frame, anchor="nw")
        self.sb_canvas.bind('<Configure>',
                            lambda e: self.sb_canvas.itemconfig(
                                self.sb_canvas.find_withtag("all")[0], width=e.width))
        self.sb_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # ── VERTICAL DIVIDER ─────────────────────────────────────────
        tk.Frame(content, bg=self.colors['border'], width=1).pack(side=tk.LEFT, fill=tk.Y)

        # ── MAIN PANEL ───────────────────────────────────────────────
        main_panel = tk.Frame(content, bg=self.colors['bg_dark'])
        main_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Count bar
        count_bar = tk.Frame(main_panel, bg=self.colors['bg_card'], pady=6, padx=16)
        count_bar.pack(fill=tk.X)

        self.count_label = tk.Label(count_bar, text="",
                                    font=('Segoe UI', 9),
                                    bg=self.colors['bg_card'],
                                    fg=self.colors['text_secondary'])
        self.count_label.pack(side=tk.LEFT)

        tk.Frame(main_panel, bg=self.colors['border'], height=1).pack(fill=tk.X)

        # Scrollable items area
        scroll_area = tk.Frame(main_panel, bg=self.colors['bg_dark'])
        scroll_area.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(scroll_area, bg=self.colors['bg_dark'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(scroll_area, orient=tk.VERTICAL, command=self.canvas.yview)

        self.scroll_frame = tk.Frame(self.canvas, bg=self.colors['bg_dark'])
        self.scroll_frame.bind("<Configure>",
                               lambda e: self.canvas.configure(
                                   scrollregion=self.canvas.bbox("all")))

        self.canvas_window = self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.bind('<Configure>',
                         lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width))
        def route_mousewheel(e):
            try:
                sx = self.sb_canvas.winfo_rootx()
                sy = self.sb_canvas.winfo_rooty()
                sw = self.sb_canvas.winfo_width()
                sh = self.sb_canvas.winfo_height()
                if sx <= e.x_root < sx + sw and sy <= e.y_root < sy + sh:
                    self.sb_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
                    return
            except Exception:
                pass
            self.canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        self.root.bind_all("<MouseWheel>", route_mousewheel)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # ── STATUS BAR ───────────────────────────────────────────────
        tk.Frame(self.root, bg=self.colors['border'], height=1).pack(fill=tk.X, side=tk.BOTTOM)
        status_bar = tk.Frame(self.root, bg=self.colors['bg_card'], pady=7)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)

        self.status_label = tk.Label(
            status_bar,
            text="  Click any item to copy its .storeitem command",
            font=('Segoe UI', 10),
            bg=self.colors['bg_card'],
            fg=self.colors['text_secondary'])
        self.status_label.pack(side=tk.LEFT)

        tk.Button(status_bar, text="  Restore Hidden  ",
                  font=('Segoe UI', 9),
                  bg=self.colors['bg_button'],
                  fg=self.colors['text_secondary'],
                  relief=tk.FLAT, cursor='hand2',
                  command=self.unhide_all).pack(side=tk.RIGHT, padx=(0, 8))

        tk.Label(status_bar,
                 text="Ctrl+F  Search  ·  Ctrl+N  Add  ·  Right-click  Remove  ·  ",
                 font=('Segoe UI', 9),
                 bg=self.colors['bg_card'],
                 fg=self.colors['text_muted']).pack(side=tk.RIGHT)

        # Keybinds
        self.root.bind('<Control-n>', lambda e: self.add_item_dialog())
        self.root.bind('<Control-f>', lambda e: self.search_entry.focus())
        self.root.bind('<Escape>', lambda e: self.clear_search())

        self.render_sidebar()
        self.render_items()

    # ================================================================
    #  SIDEBAR
    # ================================================================

    def render_sidebar(self):
        for w in self.sb_frame.winfo_children():
            w.destroy()

        active = self.category_var.get()

        entries = [("All", "#58a6ff")] + \
                  [(k, v['color']) for k, v in self.item_database.items()] + \
                  ([("Custom Items", self.colors['accent_pink'])] if self.custom_items else [])

        for cat_name, color in entries:
            if cat_name not in ("All", "Custom Items") and cat_name in self.hidden_categories:
                continue

            is_active = (active == cat_name)
            row_bg = self.colors['bg_hover'] if is_active else self.colors['bg_card']

            row = tk.Frame(self.sb_frame, bg=row_bg)
            row.pack(fill=tk.X)

            # Left accent bar
            accent_color = color if is_active else self.colors['bg_card']
            tk.Frame(row, bg=accent_color, width=3).pack(side=tk.LEFT, fill=tk.Y)

            inner = tk.Frame(row, bg=row_bg, pady=8, padx=10)
            inner.pack(side=tk.LEFT, fill=tk.X, expand=True)

            # Truncate long names for sidebar
            short = cat_name if len(cat_name) <= 24 else cat_name[:22] + "…"

            lbl = tk.Label(inner,
                           text=f"▸  {short}",
                           font=('Segoe UI', 10, 'bold' if is_active else 'normal'),
                           bg=row_bg,
                           fg=self.colors['text_primary'] if is_active else self.colors['text_secondary'],
                           anchor='w')
            lbl.pack(fill=tk.X)

            def on_click(e, c=cat_name):
                self.category_var.set(c)
                self.render_sidebar()
                self.render_items()
                self.canvas.yview_moveto(0)

            def on_enter(e, f=row, i=inner, l=lbl, active=is_active):
                if not active:
                    for w in [f, i, l]:
                        w.config(bg=self.colors['border_muted'])

            def on_leave(e, f=row, i=inner, l=lbl, active=is_active):
                bg = self.colors['bg_hover'] if active else self.colors['bg_card']
                for w in [f, i, l]:
                    w.config(bg=bg)

            for w in [row, inner, lbl]:
                w.bind('<Button-1>', on_click)
                w.bind('<Enter>', on_enter)
                w.bind('<Leave>', on_leave)
                w.config(cursor='hand2')

            # Right-click to hide tab (not available for "All" or "Custom Items")
            if cat_name not in ("All", "Custom Items"):
                def on_tab_right_click(e, c=cat_name):
                    self.show_category_menu(e, c)
                for w in [row, inner, lbl]:
                    w.bind('<Button-3>', on_tab_right_click)

            # Thin separator
            tk.Frame(self.sb_frame,
                     bg=self.colors['border_muted'], height=1).pack(fill=tk.X)

    # ================================================================
    #  ITEM RENDERING
    # ================================================================

    def filter_items(self):
        self.render_items()

    def clear_search(self):
        self.search_var.set("")
        self.category_var.set("All")
        self.render_sidebar()
        self.render_items()

    def render_items(self):
        for w in self.scroll_frame.winfo_children():
            w.destroy()

        search = self.search_var.get().lower()
        selected_cat = self.category_var.get()
        total = 0
        shown = 0

        for cat_name, data in self.item_database.items():
            if cat_name in self.hidden_categories:
                continue
            if selected_cat != "All" and selected_cat != cat_name:
                continue

            cat_items = []
            for item in data['items']:
                if item['name'] in self.hidden_items or item['name'] in self.deleted_items:
                    continue
                total += 1
                if search and \
                   search not in item['name'].lower() and \
                   search not in (item.get('location') or '').lower():
                    continue
                cat_items.append(item)
                shown += 1

            self.render_folder(cat_name, data['color'], cat_items, bool(search))

        # Custom items
        if selected_cat in ["All", "Custom Items"] and self.custom_items:
            custom_shown = []
            for item in self.custom_items:
                total += 1
                name = item[0] if isinstance(item, list) else item.get('name', '')
                if search and search not in name.lower():
                    continue
                custom_shown.append(item)
                shown += 1
            if custom_shown:
                self.render_custom_folder(custom_shown)

        self.count_label.config(
            text=f"  {shown} item{'s' if shown != 1 else ''} shown  ·  {total} total")

    def render_folder(self, name, color, items, force_open=False):
        """GitHub-style collapsible folder section"""
        is_collapsed = (name in self.collapsed_categories) and not force_open

        section = tk.Frame(self.scroll_frame, bg=self.colors['bg_dark'])
        section.pack(fill=tk.X, pady=(4, 0))

        # ── Folder header ─────────────────────────────────────────────
        header_bg = self.colors['bg_card']
        header = tk.Frame(section, bg=header_bg,
                          highlightbackground=self.colors['border'],
                          highlightthickness=1)
        header.pack(fill=tk.X)

        # Left color accent bar
        tk.Frame(header, bg=color, width=4).pack(side=tk.LEFT, fill=tk.Y)

        h_inner = tk.Frame(header, bg=header_bg, pady=11, padx=14)
        h_inner.pack(side=tk.LEFT, fill=tk.X, expand=True)

        arrow_text = "▶" if is_collapsed else "▼"
        arrow_lbl = tk.Label(h_inner, text=arrow_text,
                             font=('Segoe UI', 9),
                             bg=header_bg, fg=color)
        arrow_lbl.pack(side=tk.LEFT, padx=(0, 10))

        folder_icon = tk.Label(h_inner,
                               text="📂" if not is_collapsed else "📁",
                               font=('Segoe UI', 11),
                               bg=header_bg, fg=color)
        folder_icon.pack(side=tk.LEFT, padx=(0, 8))

        name_lbl = tk.Label(h_inner, text=name,
                            font=('Segoe UI', 12, 'bold'),
                            bg=header_bg,
                            fg=self.colors['text_primary'])
        name_lbl.pack(side=tk.LEFT)

        # Count badge
        badge = tk.Label(h_inner,
                         text=f"  {len(items)}  ",
                         font=('Segoe UI', 9),
                         bg=self.colors['border'],
                         fg=self.colors['text_secondary'],
                         padx=2, pady=1)
        badge.pack(side=tk.LEFT, padx=10)

        # ── Items frame ───────────────────────────────────────────────
        items_frame = tk.Frame(section, bg=self.colors['bg_dark'])

        if not is_collapsed:
            items_frame.pack(fill=tk.X)
            for item in items:
                self.render_item_row(item, color, items_frame)

        # Bottom border
        tk.Frame(section, bg=self.colors['border_muted'], height=1).pack(fill=tk.X)

        # ── Toggle logic ──────────────────────────────────────────────
        def toggle(e, n=name, s=section, ifrm=items_frame,
                   c=color, itms=items,
                   arr=arrow_lbl, fld=folder_icon,
                   hbg=header_bg):
            if n in self.collapsed_categories:
                self.collapsed_categories.discard(n)
                arr.config(text="▼")
                fld.config(text="📂")
                for it in itms:
                    self.render_item_row(it, c, ifrm)
                ifrm.pack(fill=tk.X)
            else:
                self.collapsed_categories.add(n)
                arr.config(text="▶")
                fld.config(text="📁")
                for child in ifrm.winfo_children():
                    child.destroy()
                ifrm.pack_forget()

        def h_enter(e, f=header, i=h_inner):
            f.config(bg=self.colors['bg_hover'])
            i.config(bg=self.colors['bg_hover'])
            for child in i.winfo_children():
                if isinstance(child, tk.Label):
                    child.config(bg=self.colors['bg_hover'])

        def h_leave(e, f=header, i=h_inner, hbg=header_bg):
            f.config(bg=hbg)
            i.config(bg=hbg)
            for child in i.winfo_children():
                if isinstance(child, tk.Label):
                    child.config(bg=hbg)

        for w in [header, h_inner, arrow_lbl, folder_icon, name_lbl]:
            w.bind('<Button-1>', toggle)
            w.bind('<Enter>', h_enter)
            w.bind('<Leave>', h_leave)
            w.config(cursor='hand2')

    def render_item_row(self, item, accent_color, parent):
        """Single item row — GitHub file row style with command subtitle"""
        row_bg = self.colors['bg_dark']

        row = tk.Frame(parent, bg=row_bg,
                       highlightbackground=self.colors['border_muted'],
                       highlightthickness=1)
        row.pack(fill=tk.X, padx=0, pady=0)

        inner = tk.Frame(row, bg=row_bg, pady=13, padx=16)
        inner.pack(fill=tk.X)

        # Left indent accent
        tk.Frame(inner, bg=accent_color, width=2).pack(side=tk.LEFT, fill=tk.Y, padx=(0, 12))

        # Icon
        icon = self.icon_cache.get(item.get('icon'))
        if icon:
            icon_lbl = tk.Label(inner, image=icon, bg=row_bg)
            icon_lbl.pack(side=tk.LEFT, padx=(0, 12))
        else:
            icon_lbl = None

        # Location pill badge — packed RIGHT before text frame so it floats right
        if item.get('location'):
            loc_pill = tk.Label(inner,
                                text=f"  {item['location']}  ",
                                font=('Segoe UI', 10),
                                bg=self.colors['bg_button'],
                                fg=self.colors['text_location'],
                                padx=4, pady=3)
            loc_pill.pack(side=tk.RIGHT, padx=(8, 0))
        else:
            loc_pill = None

        # Name + command subtitle stacked vertically
        text_frame = tk.Frame(inner, bg=row_bg)
        text_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        name_lbl = tk.Label(text_frame,
                            text=item['name'],
                            font=('Segoe UI', 12),
                            bg=row_bg,
                            fg=self.colors['text_primary'],
                            anchor='w')
        name_lbl.pack(anchor='w')

        cmd_lbl = tk.Label(text_frame,
                           text=item['command'],
                           font=('Consolas', 9),
                           bg=row_bg,
                           fg=self.colors['text_muted'],
                           anchor='w')
        cmd_lbl.pack(anchor='w')

        # Left-click copies, right-click shows menu
        def on_click(e, cmd=item['command']):
            self.copy_to_clipboard(cmd)

        def on_right_click(e, n=item['name'], cmd=item['command']):
            self.show_item_menu(e, n, cmd, is_custom=False)

        def on_enter(e):
            for w in [row, inner, text_frame, name_lbl, cmd_lbl]:
                w.config(bg=self.colors['bg_hover'])
            if icon_lbl:
                icon_lbl.config(bg=self.colors['bg_hover'])
            if loc_pill:
                loc_pill.config(bg=self.colors['bg_hover'])

        def on_leave(e):
            for w in [row, inner, text_frame, name_lbl, cmd_lbl]:
                w.config(bg=row_bg)
            if icon_lbl:
                icon_lbl.config(bg=row_bg)
            if loc_pill:
                loc_pill.config(bg=self.colors['bg_button'])

        targets = ([row, inner, text_frame, name_lbl, cmd_lbl]
                   + ([icon_lbl] if icon_lbl else [])
                   + ([loc_pill] if loc_pill else []))
        for w in targets:
            w.bind('<Button-1>', on_click)
            w.bind('<Button-3>', on_right_click)
            w.bind('<Enter>', on_enter)
            w.bind('<Leave>', on_leave)
            w.config(cursor='hand2')

    def render_custom_folder(self, items):
        """Custom items as a collapsible folder"""
        name = "Custom Items"
        color = self.colors['accent_pink']
        is_collapsed = name in self.collapsed_categories

        section = tk.Frame(self.scroll_frame, bg=self.colors['bg_dark'])
        section.pack(fill=tk.X, pady=(4, 0))

        header_bg = self.colors['bg_card']
        header = tk.Frame(section, bg=header_bg,
                          highlightbackground=self.colors['border'],
                          highlightthickness=1)
        header.pack(fill=tk.X)

        tk.Frame(header, bg=color, width=4).pack(side=tk.LEFT, fill=tk.Y)

        h_inner = tk.Frame(header, bg=header_bg, pady=9, padx=14)
        h_inner.pack(side=tk.LEFT, fill=tk.X, expand=True)

        arrow_lbl = tk.Label(h_inner,
                             text="▶" if is_collapsed else "▼",
                             font=('Segoe UI', 9), bg=header_bg, fg=color)
        arrow_lbl.pack(side=tk.LEFT, padx=(0, 10))

        folder_icon = tk.Label(h_inner,
                               text="📂" if not is_collapsed else "📁",
                               font=('Segoe UI', 11), bg=header_bg, fg=color)
        folder_icon.pack(side=tk.LEFT, padx=(0, 8))

        tk.Label(h_inner, text="Custom Items",
                 font=('Segoe UI', 12, 'bold'),
                 bg=header_bg, fg=self.colors['text_primary']).pack(side=tk.LEFT)

        tk.Label(h_inner, text=f"  {len(items)}  ",
                 font=('Segoe UI', 9),
                 bg=self.colors['border'],
                 fg=self.colors['text_secondary'],
                 padx=2).pack(side=tk.LEFT, padx=10)

        items_frame = tk.Frame(section, bg=self.colors['bg_dark'])

        if not is_collapsed:
            items_frame.pack(fill=tk.X)
            for item in items:
                self._render_custom_row(item, items_frame)

        tk.Frame(section, bg=self.colors['border_muted'], height=1).pack(fill=tk.X)

        def toggle(e):
            if name in self.collapsed_categories:
                self.collapsed_categories.discard(name)
                arrow_lbl.config(text="▼")
                folder_icon.config(text="📂")
                for it in items:
                    self._render_custom_row(it, items_frame)
                items_frame.pack(fill=tk.X)
            else:
                self.collapsed_categories.add(name)
                arrow_lbl.config(text="▶")
                folder_icon.config(text="📁")
                for child in items_frame.winfo_children():
                    child.destroy()
                items_frame.pack_forget()

        for w in [header, h_inner, arrow_lbl, folder_icon]:
            w.bind('<Button-1>', toggle)
            w.config(cursor='hand2')

    def _render_custom_row(self, item, parent):
        name = item[0] if isinstance(item, list) else item.get('name', '')
        cmd = (item[1] if isinstance(item, list) and len(item) > 1
               else f".storeitem {name}")

        row_bg = self.colors['bg_dark']
        row = tk.Frame(parent, bg=row_bg,
                       highlightbackground=self.colors['border_muted'],
                       highlightthickness=1)
        row.pack(fill=tk.X)

        inner = tk.Frame(row, bg=row_bg, pady=15, padx=16)
        inner.pack(fill=tk.X)

        tk.Frame(inner, bg=self.colors['accent_pink'], width=2).pack(
            side=tk.LEFT, fill=tk.Y, padx=(0, 12))

        name_lbl = tk.Label(inner, text=name,
                            font=('Segoe UI', 12),
                            bg=row_bg,
                            fg=self.colors['text_primary'],
                            anchor='w')
        name_lbl.pack(side=tk.LEFT, fill=tk.X, expand=True)

        def on_click(e, c=cmd):
            self.copy_to_clipboard(c)

        def on_right_click(e, i=item, n=name, c=cmd):
            self.show_item_menu(e, n, c, is_custom=True, item_obj=i)

        def on_enter(e):
            row.config(bg=self.colors['bg_hover'])
            inner.config(bg=self.colors['bg_hover'])
            name_lbl.config(bg=self.colors['bg_hover'])

        def on_leave(e):
            row.config(bg=row_bg)
            inner.config(bg=row_bg)
            name_lbl.config(bg=row_bg)

        for w in [row, inner, name_lbl]:
            w.bind('<Button-1>', on_click)
            w.bind('<Button-3>', on_right_click)
            w.bind('<Enter>', on_enter)
            w.bind('<Leave>', on_leave)
            w.config(cursor='hand2')

    # ================================================================
    #  RIGHT-CLICK CONTEXT MENU
    # ================================================================

    def show_item_menu(self, event, name, command, is_custom=False, item_obj=None):
        """Right-click dropdown for any item row"""
        menu = tk.Menu(self.root, tearoff=0,
                       bg=self.colors['bg_card'],
                       fg=self.colors['text_primary'],
                       activebackground=self.colors['bg_hover'],
                       activeforeground=self.colors['text_primary'],
                       relief=tk.FLAT,
                       font=('Segoe UI', 10))

        menu.add_command(
            label=f"  📋  Copy Command",
            command=lambda: self.copy_to_clipboard(command))

        menu.add_separator()

        if is_custom and item_obj is not None:
            menu.add_command(
                label="  ✕   Remove Item",
                command=lambda: self.delete_custom(item_obj))
        else:
            menu.add_command(
                label="  🙈  Hide Item",
                command=lambda: self.hide_item(name))
            menu.add_command(
                label="  🗑️  Delete Item",
                command=lambda: self.delete_item(name))

        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def hide_item(self, name):
        """Hide a built-in item from the list"""
        self.hidden_items.add(name)
        self.save_custom_items()
        self.render_items()
        self.status_label.config(
            text=f"  Hidden: {name}  (restore via Edit > Show Hidden)",
            fg=self.colors['accent_orange'])
        self.root.after(3000, lambda: self.status_label.config(
            text="  Click any item to copy its .storeitem command",
            fg=self.colors['text_secondary']))

    def delete_item(self, name):
        """Permanently delete a built-in item"""
        if not messagebox.askyesno("Delete Item", f"Delete '{name}'?\n\nRestore later via  Restore Hidden."):
            return
        self.deleted_items.add(name)
        self.save_custom_items()
        self.render_items()
        self.status_label.config(
            text=f"  Deleted: {name}  (restore via Restore Hidden)",
            fg=self.colors['accent_orange'])
        self.root.after(3000, lambda: self.status_label.config(
            text="  Click any item to copy its .storeitem command",
            fg=self.colors['text_secondary']))

    def hide_category(self, name):
        """Hide an entire sidebar category tab"""
        self.hidden_categories.add(name)
        self.save_custom_items()
        self.render_sidebar()
        self.render_items()
        self.status_label.config(
            text=f"  Tab hidden: {name}  (restore via Restore Hidden)",
            fg=self.colors['accent_orange'])
        self.root.after(3000, lambda: self.status_label.config(
            text="  Click any item to copy its .storeitem command",
            fg=self.colors['text_secondary']))

    def delete_category(self, name):
        """Permanently delete a sidebar category and all its items"""
        count = len(self.item_database.get(name, {}).get('items', []))
        if not messagebox.askyesno(
                "Delete Tab",
                f"Delete '{name}'?\n\n{count} item{'s' if count != 1 else ''} will be removed.\n"
                f"Restore later via  Restore Hidden."):
            return
        self.deleted_categories.add(name)
        self.item_database.pop(name, None)
        if self.category_var.get() == name:
            self.category_var.set("All")
        self.save_custom_items()
        self.render_sidebar()
        self.render_items()
        self.status_label.config(
            text=f"  Deleted tab: {name}  (restore via Restore Hidden)",
            fg=self.colors['accent_orange'])
        self.root.after(3000, lambda: self.status_label.config(
            text="  Click any item to copy its .storeitem command",
            fg=self.colors['text_secondary']))

    def show_category_menu(self, event, cat_name):
        """Right-click dropdown for a sidebar category tab"""
        menu = tk.Menu(self.root, tearoff=0,
                       bg=self.colors['bg_card'],
                       fg=self.colors['text_primary'],
                       activebackground=self.colors['bg_hover'],
                       activeforeground=self.colors['text_primary'],
                       relief=tk.FLAT,
                       font=('Segoe UI', 10))
        menu.add_command(
            label="  🙈  Hide Tab",
            command=lambda: self.hide_category(cat_name))
        menu.add_separator()
        menu.add_command(
            label="  🗑️  Delete Tab",
            command=lambda: self.delete_category(cat_name))
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def unhide_all(self):
        """Restore all hidden and deleted items and categories"""
        count = (len(self.hidden_items) + len(self.hidden_categories)
                 + len(self.deleted_categories) + len(self.deleted_items))
        self.hidden_items.clear()
        self.hidden_categories.clear()
        self.deleted_categories.clear()
        self.deleted_items.clear()
        self.item_database = self.get_item_database()
        self.save_custom_items()
        self.render_sidebar()
        self.render_items()
        self.status_label.config(
            text=f"  Restored {count} item{'s' if count != 1 else ''}",
            fg=self.colors['accent_green'])
        self.root.after(2500, lambda: self.status_label.config(
            text="  Click any item to copy its .storeitem command",
            fg=self.colors['text_secondary']))

    # ================================================================
    #  DIALOGS
    # ================================================================

    def add_item_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Custom Item")
        dialog.geometry("480x230")
        dialog.configure(bg=self.colors['bg_dark'])
        dialog.transient(self.root)
        dialog.grab_set()

        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 240
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 115
        dialog.geometry(f"+{x}+{y}")

        tk.Label(dialog, text="Item Name",
                 font=('Segoe UI', 11, 'bold'),
                 bg=self.colors['bg_dark'],
                 fg=self.colors['text_primary']).pack(pady=(20, 6))

        name_entry = tk.Entry(dialog, font=('Segoe UI', 12),
                              bg=self.colors['bg_card'],
                              fg=self.colors['text_primary'],
                              insertbackground=self.colors['text_primary'],
                              relief=tk.FLAT, width=38)
        name_entry.pack(ipady=7)
        name_entry.focus()

        tk.Label(dialog, text="Command",
                 font=('Segoe UI', 11, 'bold'),
                 bg=self.colors['bg_dark'],
                 fg=self.colors['text_primary']).pack(pady=(14, 6))

        cmd_entry = tk.Entry(dialog, font=('Segoe UI', 12),
                             bg=self.colors['bg_card'],
                             fg=self.colors['text_primary'],
                             insertbackground=self.colors['text_primary'],
                             relief=tk.FLAT, width=38)
        cmd_entry.pack(ipady=7)
        cmd_entry.insert(0, ".storeitem ")

        def save():
            name = name_entry.get().strip()
            cmd = cmd_entry.get().strip() or f".storeitem {name}"
            if not name:
                return
            self.custom_items.append([name, cmd])
            self.save_custom_items()
            dialog.destroy()
            self.render_sidebar()
            self.render_items()
            self.status_label.config(
                text=f"  Added: {name}", fg=self.colors['accent_green'])

        btns = tk.Frame(dialog, bg=self.colors['bg_dark'])
        btns.pack(pady=20)

        tk.Button(btns, text="Add Item",
                  font=('Segoe UI', 11, 'bold'),
                  bg=self.colors['accent_green'], fg='#0d1117',
                  relief=tk.FLAT, padx=22, pady=6,
                  command=save).pack(side=tk.LEFT, padx=8)

        tk.Button(btns, text="Cancel",
                  font=('Segoe UI', 11, 'bold'),
                  bg=self.colors['bg_button'], fg=self.colors['text_secondary'],
                  relief=tk.FLAT, padx=18, pady=6,
                  command=dialog.destroy).pack(side=tk.LEFT, padx=8)

        dialog.bind('<Return>', lambda e: save())

    def delete_custom(self, item):
        name = item[0] if isinstance(item, list) else item.get('name', '')
        if messagebox.askyesno("Delete", f"Delete '{name}'?"):
            try:
                self.custom_items.remove(item)
                self.save_custom_items()
                self.render_sidebar()
                self.render_items()
            except Exception:
                pass


# ================================================================
#  ENTRY POINT
# ================================================================

def main():
    root = tk.Tk()
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    app = DMWStoreHelper(root)
    root.mainloop()


if __name__ == "__main__":
    main()
